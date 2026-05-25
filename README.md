# Project Ouroboros (OSS Edition)

> A self-improving purple-team SOC lab on Oracle Cloud Free Tier, built entirely with open source tooling. Red attacks, blue detects, the triage agent proposes tuning, the rules sharpen, and the red side adapts. The cycle is the point.

[![CI](https://github.com/justinkok28/project-ouroboros-oss/actions/workflows/ci.yml/badge.svg)](https://github.com/justinkok28/project-ouroboros-oss/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/badge/docs-site-blue)](https://justinkok28.github.io/project-ouroboros-oss/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

A solo portfolio project modeling **Halcyon Care Pte Ltd**, a fictional 25-person Singaporean healthcare-SaaS, and the SOC defending it. Built around **Wazuh + Keycloak + Grafana/Loki**, with two custom AI agents (red-team adversary emulator + triage agent) and a deliberately attackable AI booking assistant ("Sage") embedded in the public web app.

The architecture *is* the feedback loop: a red agent emulates Scattered Spider (UNC3944) TTPs, Wazuh detects what it can, the triage agent investigates the resulting alerts and proposes detection tuning, those tunings get compiled from Sigma into Wazuh rules, and the red agent's LLM planner varies its next round of attacks against the improved defenses.

## Why open source instead of Azure?

This project was originally built on Microsoft Sentinel + Entra ID. It was rebuilt on the open source stack because:

1. **You learn how a SIEM actually works.** Wazuh exposes decoders, rule XML, and log shippers — Sentinel hides them.
2. **Sigma > KQL for portability.** Detections written once, compiled to any SIEM.
3. **Identity protocols from first principles.** Keycloak makes you configure OIDC/SAML/OAuth flows by hand.
4. **Real Linux + Docker operations.** systemd, reverse proxy, TLS, networking — none of which Azure exposes.
5. **No cloud bill.** Oracle Free Tier hosts the lot.

See [`PIVOT_FROM_AZURE.md`](PIVOT_FROM_AZURE.md) for the full migration story.

## The stack

| Concern | Tool |
|---|---|
| Host | Oracle Cloud Free Tier ARM VM (Ampere A1, 4 OCPU / 24 GB RAM) |
| Runtime | Docker + Docker Compose |
| SIEM | Wazuh |
| Identity | Keycloak |
| Observability | Grafana + Loki + Prometheus |
| Reverse proxy / TLS | Caddy |
| Detections | Sigma (source) → Wazuh rules (compiled) |
| LLM API | OpenRouter |
| Default model | Nous Hermes 3 70B |
| Vulnerable target | "Sage" booking chatbot (FastAPI + LLM + layered defenses) |

## The two AI agents

**`agent/redteam/`** — emulates UNC3944 TTPs across eight scenarios (MFA fatigue, helpdesk impersonation, OAuth consent grant, privilege role burst, service principal credential addition, port scan + SSH brute-force, cloud storage exfil, chatbot prompt injection). An LLM planner picks scenarios and varies parameters between rounds.

**`agent/triage/`** — receives Wazuh alerts via webhook, queries Loki/Wazuh for evidence, outputs validated JSON: incident classification, MITRE technique mapping, severity, false-positive likelihood, and (optionally) a proposed Sigma rule tuning.

Both agents talk to OpenRouter using the OpenAI-compatible API. Default model is Hermes 3 70B, swappable per-agent via env vars. An A/B harness in `agent/eval/` scores Hermes against Claude Haiku, GPT-4o-mini, and others on the same prompts.

## Quick start

```bash
git clone https://github.com/justinkok28/project-ouroboros-oss.git
cd project-ouroboros-oss
cp .env.example .env
# fill in OPENROUTER_API_KEY, KEYCLOAK_ADMIN_PASSWORD, WAZUH_API_PASSWORD
make up
```

For the full Oracle VM setup, see [`docs/weeks/week-02-oracle-vm.md`](docs/weeks/week-02-oracle-vm.md).

## Status

Week 1 (Saturday) carried over from the Azure version: repo + docs scaffolding complete. Week 1 (Sunday) onward follows the playbooks under [`docs/weeks/`](docs/weeks/).

## License

MIT. Inspired by public CTI (MITRE ATT&CK, CISA, Mandiant, Microsoft, HHS) but containing no proprietary or non-public material.
