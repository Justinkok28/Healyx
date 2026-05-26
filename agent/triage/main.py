"""Triage agent — receives Wazuh alerts, investigates, returns structured verdict.

Wazuh's `integrator` daemon calls our webhook with the alert JSON. We:
  1. Validate the shared-secret token
  2. Sanitize the alert (strip secrets that may have been logged)
  3. Gather evidence via the tools in `triage.tools`
  4. Send everything to OpenRouter (Hermes 3 70B by default)
  5. Validate the response against `TriageResult`
  6. Append to the incident log
  7. Return the verdict

The agent is read-only. It never auto-contains.
"""

from __future__ import annotations

import json
import logging
import os
import secrets
from datetime import UTC, datetime
from pathlib import Path

from fastapi import Body, FastAPI, Header, HTTPException, status
from pydantic import BaseModel

from agent.common import OpenRouterClient, TriageResult
from agent.triage import tools
from agent.triage.sanitize import sanitize_alert

logger = logging.getLogger(__name__)
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))

app = FastAPI(title="Healyx Triage Agent", version="0.1.0")

# Load the triage prompt from disk at startup (faster + easier to edit)
PROMPT_PATH = Path(__file__).parent / "prompts" / "triage_v1.txt"
TRIAGE_PROMPT = PROMPT_PATH.read_text(encoding="utf-8")

INCIDENT_LOG = Path(
    os.environ.get("INCIDENT_LOG_PATH", "/var/log/healyx/triage-incidents.jsonl")
)
WEBHOOK_TOKEN = os.environ["TRIAGE_WEBHOOK_TOKEN"]
TRIAGE_MODEL = os.environ.get(
    "TRIAGE_MODEL", "nousresearch/hermes-3-llama-3.1-70b"
)


client = OpenRouterClient(default_model=TRIAGE_MODEL)


class WazuhAlert(BaseModel):
    """Loose Wazuh alert payload schema.

    Wazuh sends rich JSON; we only require enough to identify and route.
    The full payload is preserved and passed to the LLM after sanitization.
    """

    id: str | None = None
    timestamp: str | None = None
    rule: dict | None = None
    agent: dict | None = None
    data: dict | None = None

    model_config = {"extra": "allow"}


@app.get("/health")
def health() -> dict:
    return {"ok": True, "model": TRIAGE_MODEL}


@app.post("/webhook/wazuh", status_code=status.HTTP_200_OK)
def wazuh_webhook(
    alert: WazuhAlert = Body(...),
    x_webhook_token: str | None = Header(default=None),
) -> dict:
    """Entry point Wazuh calls when a rule fires."""
    # 1. Verify shared secret in constant time
    if not x_webhook_token or not secrets.compare_digest(
        x_webhook_token, WEBHOOK_TOKEN
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "bad token")

    alert_dict = alert.model_dump(exclude_none=True)
    alert_id = alert_dict.get("id") or f"unknown-{datetime.now(UTC).isoformat()}"
    logger.info("triage start alert_id=%s rule=%s", alert_id, (alert.rule or {}).get("id"))

    # 2. Strip sensitive material before it hits the LLM
    sanitized = sanitize_alert(alert_dict)

    # 3. Gather evidence using tools (each tool is a documented function call;
    #    Hermes' tool-calling support means we can let the model choose, but
    #    for the v1 agent we pre-fetch a fixed evidence bundle. Move to
    #    real tool calling in week 12.)
    evidence_bundle = {
        "related_loki_logs": tools.query_loki_recent(
            alert_ts=sanitized.get("timestamp"), window_minutes=15
        ),
        "wazuh_rule_metadata": tools.get_rule_metadata(
            (alert.rule or {}).get("id")
        ),
        "agent_recent_alerts": tools.get_recent_alerts_for_agent(
            (alert.agent or {}).get("id"), limit=10
        ),
    }

    # 4. Ask the LLM
    messages = [
        {"role": "system", "content": TRIAGE_PROMPT},
        {
            "role": "user",
            "content": (
                "Triage this Wazuh alert. Use the bundled evidence. "
                "Reply with a single JSON object matching the TriageResult schema.\n\n"
                f"ALERT:\n{json.dumps(sanitized, indent=2)}\n\n"
                f"EVIDENCE:\n{json.dumps(evidence_bundle, indent=2, default=str)}"
            ),
        },
    ]

    try:
        result: TriageResult = client.chat_json(messages, schema=TriageResult)
    except Exception as exc:
        logger.exception("triage failed alert_id=%s", alert_id)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc)) from exc

    # 5. Persist
    INCIDENT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with INCIDENT_LOG.open("a", encoding="utf-8") as f:
        f.write(result.model_dump_json() + "\n")

    logger.info(
        "triage done alert_id=%s severity=%s fp_likely=%s",
        alert_id,
        result.severity,
        result.is_false_positive_likely,
    )

    return result.model_dump(mode="json")
