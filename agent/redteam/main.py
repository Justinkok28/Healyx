"""Red-team agent — emulates UNC3944 TTPs against the lab.

CLI:
    python -m redteam.main run --scenario mfa_fatigue
    python -m redteam.main plan --rounds 3       # let the LLM planner choose

Every run appends a GroundTruthEntry to `ground_truth.jsonl`. The triage agent's
output is scored against these entries in the eval harness.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path

from agent.common import (
    AttackOutcome,
    GroundTruthEntry,
    OpenRouterClient,
    RedTeamPlan,
)
from agent.redteam import scenarios

logger = logging.getLogger(__name__)
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))

GROUND_TRUTH = Path(
    os.environ.get(
        "GROUND_TRUTH_LOG_PATH",
        "/var/log/healyx/redteam-ground-truth.jsonl",
    )
)
PLANNER_MODEL = os.environ.get(
    "REDTEAM_PLANNER_MODEL", "nousresearch/hermes-3-llama-3.1-70b"
)

PLANNER_PROMPT = """You are the red-team planner for Project Healyx, a purple-team SOC lab.

Your job: choose which UNC3944 attack scenarios to run this round, and how to vary them. You are NOT executing the attacks — you decide what should run; deterministic Python scripts then execute. You must respect the scenario inventory exactly.

## Available scenarios
- mfa_fatigue: spam MFA push prompts to a Keycloak account
- helpdesk_password_reset: simulate a phishing call to help-desk; trigger a password reset workflow
- oauth_consent_grant: register a malicious OAuth client in Keycloak; trick a user into granting consent
- priv_role_burst: assign and revoke admin roles in rapid succession to evade naive monitoring
- sp_credential_addition: add a new client secret to a Keycloak service account
- port_scan_then_ssh_bf: nmap the VM then attempt SSH brute-force with rockyou subset
- cloud_storage_exfil: copy "patient records" CSV out via the Sage app's data endpoint
- chatbot_prompt_injection: send prompt-injection payloads to Sage attempting to extract system prompt

## Rules
- Pick 1–5 scenarios per round. Variety is more valuable than volume.
- Vary parameter overrides between rounds so blue can't pattern-match against fixed inputs.
- Bias toward scenarios that blue has previously CAUGHT — that's where the interesting eval signal is.
- If blue has been catching everything trivially, escalate (faster, quieter, multi-stage).
- If blue has been missing everything, repeat to confirm signal vs noise.

## Output

Return a single JSON object matching the RedTeamPlan schema. No prose outside the JSON.
"""


def _run_scenario(scenario_name: str, params: dict | None = None) -> GroundTruthEntry:
    """Look up and execute one scenario, returning its ground-truth entry."""
    run_id = str(uuid.uuid4())
    started = datetime.now(UTC)
    params = params or {}

    fn = scenarios.REGISTRY.get(scenario_name)
    if fn is None:
        raise SystemExit(f"unknown scenario: {scenario_name}")

    logger.info("redteam start scenario=%s run_id=%s", scenario_name, run_id)
    try:
        result = fn(params)
        outcome = AttackOutcome(result.get("outcome", "executed"))
        target = result.get("target", "unknown")
        techniques = result.get("mitre_techniques", [])
        expected_alerts = result.get("expected_alerts", [])
        notes = result.get("notes")
    except Exception as exc:
        logger.exception("scenario failed")
        outcome = AttackOutcome.ERROR
        target = "unknown"
        techniques = []
        expected_alerts = []
        notes = f"exception: {exc!r}"

    ended = datetime.now(UTC)

    entry = GroundTruthEntry(
        run_id=run_id,
        scenario=scenario_name,
        started_at=started,
        ended_at=ended,
        outcome=outcome,
        target=target,
        mitre_techniques=techniques or ["T1078"],  # fallback to generic
        expected_alerts=expected_alerts,
        parameters=params,
        notes=notes,
    )

    GROUND_TRUTH.parent.mkdir(parents=True, exist_ok=True)
    with GROUND_TRUTH.open("a", encoding="utf-8") as f:
        f.write(entry.model_dump_json() + "\n")

    logger.info("redteam done scenario=%s outcome=%s", scenario_name, outcome)
    return entry


def cmd_run(args: argparse.Namespace) -> None:
    """Execute one named scenario."""
    params = json.loads(args.params) if args.params else {}
    entry = _run_scenario(args.scenario, params)
    print(entry.model_dump_json(indent=2))


def cmd_plan(args: argparse.Namespace) -> None:
    """Let the LLM planner pick scenarios for N rounds."""
    client = OpenRouterClient(default_model=PLANNER_MODEL)

    # Read recent triage results to inform planning (cheap context)
    recent_context = _read_recent_triage_summary()

    for round_num in range(args.rounds):
        round_id = str(uuid.uuid4())
        messages = [
            {"role": "system", "content": PLANNER_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Plan round {round_num + 1} of {args.rounds}. "
                    f"Round ID: {round_id}.\n\n"
                    f"Recent blue performance:\n{recent_context}\n\n"
                    "Reply with a single JSON object matching RedTeamPlan."
                ),
            },
        ]
        plan: RedTeamPlan = client.chat_json(messages, schema=RedTeamPlan)
        logger.info(
            "planner picked scenarios=%s rationale=%r",
            plan.chosen_scenarios,
            plan.rationale[:100],
        )
        print(plan.model_dump_json(indent=2))

        for scenario_name in plan.chosen_scenarios:
            params = plan.parameter_overrides.get(scenario_name, {})
            _run_scenario(scenario_name, params)


def _read_recent_triage_summary(limit: int = 20) -> str:
    """Build a tiny digest of recent triage results for the planner."""
    incident_log = Path(
        os.environ.get(
            "INCIDENT_LOG_PATH", "/var/log/healyx/triage-incidents.jsonl"
        )
    )
    if not incident_log.exists():
        return "(no triage history yet)"

    lines = incident_log.read_text(encoding="utf-8").splitlines()[-limit:]
    if not lines:
        return "(no triage history yet)"

    summaries = []
    for line in lines:
        try:
            r = json.loads(line)
            summaries.append(
                f"- {r.get('alert_id')[:8]}: {r.get('severity')} | "
                f"FP-likely={r.get('is_false_positive_likely')} | "
                f"actor={r.get('suspected_actor')}"
            )
        except Exception:
            continue
    return "\n".join(summaries) or "(empty)"


def main() -> None:
    parser = argparse.ArgumentParser(prog="redteam")
    sub = parser.add_subparsers(dest="cmd", required=True)

    run_p = sub.add_parser("run", help="run one named scenario")
    run_p.add_argument("--scenario", required=True)
    run_p.add_argument("--params", help="JSON dict of parameter overrides")
    run_p.set_defaults(func=cmd_run)

    plan_p = sub.add_parser("plan", help="let the LLM planner pick scenarios")
    plan_p.add_argument("--rounds", type=int, default=1)
    plan_p.set_defaults(func=cmd_plan)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
