"""Read-only tools the triage agent uses to gather evidence.

These functions are called from `triage.main` to assemble the evidence
bundle that goes to the LLM. In Week 12 we move to true tool-calling (let
the model decide which tools to call), but v1 pre-fetches a fixed bundle.

All tools are READ-ONLY. None of them mutate state.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

LOKI_URL = os.environ.get("LOKI_URL", "http://loki:3100")
WAZUH_API_URL = os.environ.get("WAZUH_API_URL", "https://wazuh-manager:55000")
WAZUH_API_USER = os.environ.get("WAZUH_API_USER", "wazuh-admin")
WAZUH_API_PASSWORD = os.environ.get("WAZUH_API_PASSWORD", "")

# In dev / CI we frequently can't reach these. The tools degrade gracefully —
# returning an empty list is fine and gets reflected in the LLM's evidence.


def query_loki_recent(
    *, alert_ts: str | None, window_minutes: int = 15, limit: int = 50
) -> list[dict[str, Any]]:
    """Query Loki for logs in a window around the alert timestamp."""
    if not alert_ts:
        return []
    try:
        # Loki LogQL example — narrow per environment
        params = {
            "query": '{job=~".+"}',
            "limit": limit,
            "since": f"{window_minutes}m",
        }
        with httpx.Client(timeout=5.0, verify=False) as c:
            r = c.get(f"{LOKI_URL}/loki/api/v1/query_range", params=params)
            if r.status_code != 200:
                logger.warning("loki query failed: %s", r.text[:200])
                return []
            data = r.json().get("data", {}).get("result", [])
            # Flatten the structure for easier LLM consumption
            return [
                {"stream": item.get("stream"), "values": item.get("values", [])[:5]}
                for item in data[:limit]
            ]
    except Exception as exc:
        logger.warning("loki query error: %s", exc)
        return []


def get_rule_metadata(rule_id: str | int | None) -> dict[str, Any]:
    """Look up the Wazuh rule that fired, so the LLM has context."""
    if not rule_id:
        return {}
    try:
        with httpx.Client(timeout=5.0, verify=False) as c:
            r = c.get(
                f"{WAZUH_API_URL}/rules?rule_ids={rule_id}",
                auth=(WAZUH_API_USER, WAZUH_API_PASSWORD),
            )
            if r.status_code != 200:
                return {}
            items = r.json().get("data", {}).get("affected_items", [])
            return items[0] if items else {}
    except Exception as exc:
        logger.warning("wazuh rule lookup error: %s", exc)
        return {}


def get_recent_alerts_for_agent(
    agent_id: str | None, *, limit: int = 10
) -> list[dict[str, Any]]:
    """Get this Wazuh agent's recent alerts to spot patterns."""
    if not agent_id:
        return []
    try:
        with httpx.Client(timeout=5.0, verify=False) as c:
            r = c.get(
                f"{WAZUH_API_URL}/agents/{agent_id}/alerts?limit={limit}",
                auth=(WAZUH_API_USER, WAZUH_API_PASSWORD),
            )
            if r.status_code != 200:
                return []
            return r.json().get("data", {}).get("affected_items", [])
    except Exception as exc:
        logger.warning("wazuh agent alerts error: %s", exc)
        return []
