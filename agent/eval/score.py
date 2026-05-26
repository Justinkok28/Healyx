"""A/B model comparison harness.

Runs each triage prompt against the curated MODEL_OPTIONS and scores them
against the red-team ground truth log.

Outputs a CSV in `metrics/` with one row per (incident, model) pair.

Usage:
    python -m eval.score              # score all incidents against all models
    python -m eval.score --limit 10   # quick smoke test
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
from datetime import UTC, datetime
from pathlib import Path

from agent.common import MODEL_OPTIONS, OpenRouterClient, TriageResult
from agent.triage.sanitize import sanitize_alert

logger = logging.getLogger(__name__)
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))

GROUND_TRUTH = Path(
    os.environ.get(
        "GROUND_TRUTH_LOG_PATH",
        "/var/log/healyx/redteam-ground-truth.jsonl",
    )
)
METRICS_DIR = Path(__file__).parent.parent.parent / "metrics"


def load_ground_truth() -> list[dict]:
    if not GROUND_TRUTH.exists():
        return []
    return [json.loads(line) for line in GROUND_TRUTH.read_text().splitlines() if line]


def load_alerts(*, limit: int | None = None) -> list[dict]:
    """Load Wazuh alerts to triage.

    For week 13 (eval bring-up) we use a fixture file of canned alerts so
    scoring is deterministic. Replace with live Wazuh API pulls later.
    """
    fixture = Path(__file__).parent / "fixtures" / "alerts.jsonl"
    if not fixture.exists():
        logger.warning("No fixture at %s — eval will be empty", fixture)
        return []
    rows = [json.loads(l) for l in fixture.read_text().splitlines() if l.strip()]
    return rows[:limit] if limit else rows


def score_one(
    *,
    alert: dict,
    truth: dict | None,
    result: TriageResult,
) -> dict:
    """Compare one triage output against ground truth."""
    if truth is None:
        return {
            "alert_id": alert.get("id"),
            "model": None,
            "category": result.category.value,
            "severity": result.severity.value,
            "mitre_overlap_count": 0,
            "techniques_correct": False,
            "actor_correct": None,  # unknown without truth
            "fp_calibrated": None,
            "tuning_suggested": result.suggested_tuning is not None,
        }

    expected_techniques = set(truth.get("mitre_techniques", []))
    got_techniques = set(result.mitre_techniques)
    overlap = expected_techniques & got_techniques

    return {
        "alert_id": alert.get("id"),
        "category": result.category.value,
        "severity": result.severity.value,
        "expected_techniques": ",".join(sorted(expected_techniques)),
        "got_techniques": ",".join(sorted(got_techniques)),
        "mitre_overlap_count": len(overlap),
        "techniques_correct": expected_techniques.issubset(got_techniques),
        "actor_correct": result.suspected_actor == truth.get("actor_emulated"),
        "fp_calibrated": (
            result.is_false_positive_likely
            == (truth.get("outcome") in ("skipped", "blocked", "error"))
        ),
        "tuning_suggested": result.suggested_tuning is not None,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, help="cap alerts per model")
    parser.add_argument("--models", help="comma-separated model slugs (default all)")
    args = parser.parse_args()

    alerts = load_alerts(limit=args.limit)
    truth = {t["scenario"]: t for t in load_ground_truth()}

    if not alerts:
        print("No alerts to score. Put fixtures in agent/eval/fixtures/alerts.jsonl")
        return

    models = MODEL_OPTIONS
    if args.models:
        wanted = set(args.models.split(","))
        models = tuple(m for m in MODEL_OPTIONS if m.slug in wanted)

    METRICS_DIR.mkdir(exist_ok=True)
    out_path = METRICS_DIR / f"eval-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}.csv"

    with out_path.open("w", newline="") as f:
        writer: csv.DictWriter | None = None

        for model_choice in models:
            client = OpenRouterClient(default_model=model_choice.slug)
            logger.info("=== scoring against %s ===", model_choice.display_name)

            for alert in alerts:
                sanitized = sanitize_alert(alert)
                scenario_hint = alert.get("_scenario_for_eval")
                try:
                    result: TriageResult = client.chat_json(
                        [
                            {"role": "system", "content": "You are the Healyx triage agent. Return TriageResult JSON."},
                            {"role": "user", "content": f"Triage:\n{json.dumps(sanitized)}"},
                        ],
                        schema=TriageResult,
                        model=model_choice.slug,
                    )
                except Exception as exc:
                    logger.exception("model %s failed: %s", model_choice.slug, exc)
                    continue

                row = {
                    "model_slug": model_choice.slug,
                    "model_name": model_choice.display_name,
                    "model_family": model_choice.family,
                    **score_one(
                        alert=alert,
                        truth=truth.get(scenario_hint) if scenario_hint else None,
                        result=result,
                    ),
                }
                if writer is None:
                    writer = csv.DictWriter(f, fieldnames=list(row.keys()))
                    writer.writeheader()
                writer.writerow(row)

    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
