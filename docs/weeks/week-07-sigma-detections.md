# Week 7 — Sigma Detections

## Objectives

- A `detections/sigma/` directory with at least 6 rules
- A working compile pipeline: `make compile-rules` produces Wazuh XML in `detections/wazuh-rules/_generated/`
- Compiled rules loaded into the Wazuh manager (mounted as the `custom` rules dir)
- At least one detection that fires when you manually trigger its condition

## Why Sigma

Sigma is a **portable detection language**. Write a rule once; compile it to Wazuh, Splunk, Elastic, KQL, Sentinel, Chronicle, whatever. The detection logic is the source of truth; vendor-specific rule files are *outputs*, not inputs.

This is one of the biggest learning wins of the OSS pivot. Sentinel KQL only runs in Sentinel. Sigma travels.

## Saturday — author rules

Open `detections/sigma/` and create these six rules over the day:

1. `healyx-keycloak-mfa-fatigue-v1.yml` — 5+ failed Keycloak `LOGIN_ERROR` events for same user within 5 min, followed by a `LOGIN` event
2. `healyx-keycloak-oauth-client-create-v1.yml` — admin event `CREATE_CLIENT` for a client not on the allowlist
3. `healyx-keycloak-admin-role-burst-v1.yml` — `ROLE_ASSIGNMENT` for an admin role followed by `ROLE_REVOKE` of the same role within 60 min
4. `healyx-sage-prompt-injection-v1.yml` — Sage app log lines matching prompt-injection regex patterns
5. `healyx-host-ssh-bf-v1.yml` — 10+ SSH auth failures from the same source IP in 5 minutes
6. `healyx-host-suid-creation-v1.yml` — Wazuh syscheck reports a new SUID binary outside `/usr/bin`

Each rule should have:

```yaml
title: <human-readable>
id: <UUID>
status: experimental
description: <what + why>
references:
  - https://attack.mitre.org/techniques/<T-ID>/
author: <you>
date: 2026/01/15
tags:
  - attack.<tactic>
  - attack.<technique>
logsource:
  product: keycloak  # or linux, sage, etc.
  service: <service>
detection:
  selection:
    ...
  condition: selection
falsepositives:
  - <known noise sources>
level: high
```

## Sunday — compile + load

Set up the compile script:

```bash
pip install pysigma sigma-cli pysigma-backend-elasticsearch
python scripts/compile_sigma.py \
  --in detections/sigma \
  --out-wazuh detections/wazuh-rules/_generated
```

The script uses pySigma to walk each YAML, render to Wazuh XML, and write to the output dir. The included `compile_sigma.py` is a starting template — extend it to handle your custom logsources.

Mount the compiled rules into Wazuh (already done in `docker-compose.yml`):

```yaml
- ../detections/wazuh-rules:/var/ossec/etc/rules/custom:ro
```

Restart the manager:

```bash
docker compose restart wazuh-manager
docker compose logs -f wazuh-manager | grep -i rule
```

Look for "Loaded rule" lines matching your filenames.

## Trigger a test

For the SSH brute-force rule:

```bash
# From another host:
for i in {1..15}; do ssh -o ConnectTimeout=2 -o PreferredAuthentications=password \
  baduser@<your-vm-ip> echo test; done
```

Check the Wazuh dashboard → Security events. The rule should fire.

## Done conditions

- [ ] At least 6 Sigma rules in `detections/sigma/`
- [ ] `make compile-rules` produces matching files in `detections/wazuh-rules/_generated/`
- [ ] Compiled rules load in Wazuh without errors
- [ ] At least one rule manually fires from a triggering event
- [ ] Compile job is also wired into CI — `validate-sigma` step is green

## Pitfalls

- **Custom log sources.** Sigma doesn't ship a Wazuh backend for app logs like Sage's. You may need to hand-write a backend mapping or shoehorn Sage logs into the `linux/auth` category. Document the choice.
- **Rule IDs collide with Wazuh's stock ranges.** Use IDs in the 100000+ range to avoid collisions with bundled rules.
