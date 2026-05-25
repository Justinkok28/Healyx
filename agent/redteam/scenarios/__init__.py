"""Scenario registry — each callable executes one TTP and returns a result dict.

Each scenario:
  - Accepts a `params` dict (planner-provided overrides)
  - Returns a dict with keys:
      outcome: "executed" | "blocked" | "partial" | "skipped" | "error"
      target: short string describing the target
      mitre_techniques: list of T-IDs
      expected_alerts: list of Sigma rule UUIDs that *should* fire
      notes: optional free text

To add a new scenario, write a function and add it to REGISTRY at the bottom.
"""

from __future__ import annotations

from typing import Callable

from agent.redteam.scenarios import (
    chatbot_prompt_injection,
    cloud_storage_exfil,
    helpdesk_password_reset,
    mfa_fatigue,
    oauth_consent_grant,
    port_scan_then_ssh_bf,
    priv_role_burst,
    sp_credential_addition,
)

REGISTRY: dict[str, Callable[[dict], dict]] = {
    "mfa_fatigue": mfa_fatigue.run,
    "helpdesk_password_reset": helpdesk_password_reset.run,
    "oauth_consent_grant": oauth_consent_grant.run,
    "priv_role_burst": priv_role_burst.run,
    "sp_credential_addition": sp_credential_addition.run,
    "port_scan_then_ssh_bf": port_scan_then_ssh_bf.run,
    "cloud_storage_exfil": cloud_storage_exfil.run,
    "chatbot_prompt_injection": chatbot_prompt_injection.run,
}
