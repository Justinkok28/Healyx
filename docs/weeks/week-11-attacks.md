# Week 11 — Full attack scenarios

## Objectives

- Implement the remaining 3 scenarios deferred from Week 8: `helpdesk_password_reset`, `sp_credential_addition`, `cloud_storage_exfil`
- Run a full multi-round attack session (`plan --rounds 5`)
- Confirm each scenario produces the alert it expects (or document why not)

## Saturday — finish the three deferred scenarios

### `helpdesk_password_reset`

Simulates the human side of a UNC3944 vish call. The "operator" — represented by an LLM call — generates a request like *"This is alice, my MFA device broke, I need a password reset to a new email."* The script then either:

- (Mode A) Uses Keycloak admin API directly to reset alice's password (simulating a help-desk that capitulated)
- (Mode B) Calls a separate "helpdesk-bot" endpoint that has its own decision logic

Either way: the password change event is the detection signal. The Wazuh rule should catch a password reset for an account that hasn't logged in recently.

### `sp_credential_addition`

Adds a new client secret to an existing Keycloak service account via the admin API. Two clicks in the GUI; two API calls in script:

```python
# Get the client UUID
client_uuid = httpx.get(f"{kc}/admin/realms/halcyon-care/clients?clientId=halcyon-portal", headers=auth).json()[0]["id"]
# Add a new secret
httpx.post(f"{kc}/admin/realms/halcyon-care/clients/{client_uuid}/client-secret", headers=auth)
```

Expected alert: `healyx-keycloak-client-secret-add-v1` (you'll write this Sigma rule this week).

### `cloud_storage_exfil`

Bulk-pull "patient records" via Sage's data endpoints. Two-stage attack:

1. Use a prompt injection (or auth bypass if you've left one in) to convince Sage to call `lookup_booking` repeatedly across many IDs
2. Concatenate responses into a CSV

The Week-10 Layer 4 PII sweep should catch this. If it doesn't, that's a *finding* — and a more interesting writeup than a clean catch.

## Sunday — multi-round session + observation

```bash
make agent-redteam-plan
# Watch Wazuh dashboard + triage logs in real time
docker compose logs -f triage-agent | jq -r '.alert_id + " " + .severity'
```

Take notes on:

- Which scenarios fire alerts
- Which scenarios get correctly triaged
- Which the triage agent gets wrong (overconfident FPs, missed actor attribution, severity miscalibration)

These notes are raw material for Week 12's tuning work.

## Done conditions

- [ ] All 8 scenarios implemented (4 from Week 8, 3 here, 1 from Week 11 done earlier as MFA fatigue baseline)
- [ ] Full `plan --rounds 5` session runs end-to-end without crashing
- [ ] At least 5 different Sigma rules fire across the session
- [ ] You have a notes file (`docs/weeks/week-11-observations.md`) listing what worked and what didn't
