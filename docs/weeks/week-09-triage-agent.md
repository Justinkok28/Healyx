# Week 9 — Triage Agent

## Objectives

- Triage agent runs as a Docker service, accepts webhook calls from Wazuh
- Wazuh integrator is configured to call the agent on every rule match above level 5
- Each call produces a `TriageResult` JSON, validated against the schema, persisted to `triage-incidents.jsonl`
- End-to-end: red-team `mfa_fatigue` → Keycloak events → Wazuh alert → webhook → triage agent → incident log

## Saturday — start the triage agent

```bash
cd infra
docker compose up -d triage-agent
docker compose logs -f triage-agent
```

Health check it:

```bash
curl -s https://triage.<your-domain>/health
# {"ok": true, "model": "nousresearch/hermes-3-llama-3.1-70b"}
```

(Note: `triage.<your-domain>` only routes `/webhook/*` per the Caddyfile. `/health` is intentionally not exposed externally — exec into the container or hit it on the compose network.)

## Wire Wazuh → triage webhook

Edit `infra/wazuh/ossec.conf` (or add a config snippet that the manager picks up):

```xml
<ossec_config>
  <integration>
    <name>triage-webhook</name>
    <hook_url>http://triage-agent:8001/webhook/wazuh</hook_url>
    <level>5</level>
    <alert_format>json</alert_format>
    <api_key>__TRIAGE_WEBHOOK_TOKEN_FROM_ENV__</api_key>
  </integration>
</ossec_config>
```

The included `infra/wazuh/integrations/triage-webhook.sh` is the wrapper Wazuh calls; it shells `curl` to forward the alert JSON with the auth header.

Restart Wazuh manager:

```bash
docker compose restart wazuh-manager
```

## Sunday — end-to-end test

Trigger the MFA fatigue scenario:

```bash
docker compose run --rm redteam-agent run --scenario mfa_fatigue
```

Then:

1. Watch Wazuh dashboard for the alert
2. Watch triage-agent logs — should see "triage start alert_id=..."
3. Read the persisted incident:
   ```bash
   docker compose exec triage-agent tail -n 1 /var/log/healyx/triage-incidents.jsonl | jq
   ```

Inspect the JSON. Did the LLM:

- Correctly classify category as `identity`?
- Pick reasonable MITRE techniques (T1621, T1078.004)?
- Identify the actor as UNC3944?
- Set severity appropriately?
- Cite evidence rows from the bundle?

If yes — the loop works.

## Improving the triage prompt

The first version is in `agent/triage/prompts/triage_v1.txt`. Iterate on it through this week. Common improvements:

- Add few-shot examples of well-formatted `TriageResult` JSON
- Add explicit guidance about severity calibration ("a rule with default high can be low in this lab's noise context")
- Add a list of well-known false-positive sources
- Tell it about Halcyon Care's working hours so it can flag off-hours activity

Version the prompts: `triage_v1.txt`, `triage_v2.txt`, etc. The eval harness later compares them.

## Done conditions

- [ ] Triage agent webhook reachable from Wazuh manager
- [ ] At least one full end-to-end run (red attack → Wazuh alert → triage verdict)
- [ ] Persisted incident JSON validates against the schema
- [ ] Triage agent logs are flowing to Loki

## Pitfalls

- **Webhook fires for every alert, including its own self-test alerts.** Add a filter in the prompt or in `triage/main.py` to skip alerts where source = "triage-webhook" (Wazuh's `integrator` rule).
- **Hermes returns prose around the JSON despite the system message.** The `chat_json` helper retries with the validation error. If it still happens, lower the temperature to 0.0 and add an example response to the prompt.
- **LLM picks generic techniques like T1078 when a sub-technique is correct.** Add a one-line note in the prompt: "Prefer sub-techniques when applicable (T1078.004 over T1078)."
