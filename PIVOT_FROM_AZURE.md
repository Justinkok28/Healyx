# Pivot from Azure to Open Source

This document explains why Project Healyx was rebuilt on open source tooling and exactly what changed.

## Why pivot

The original Project Healyx (Azure version) was finishing Week 1, Saturday — repo scaffolding done, no Azure resources provisioned yet. That timing made a pivot cheap. The reasons for the pivot:

### 1. Skill depth, not surface area

Azure Sentinel is configured through a portal. You enable data connectors, you click "create analytic rule," you write KQL. It works, but it hides every interesting layer beneath it. Open source forces those layers into the open:

| Azure abstraction | Open source equivalent | What you actually learn |
|---|---|---|
| Sentinel data connectors | Wazuh agents + decoders | Log shipping, parsing, normalization |
| KQL analytic rules | Sigma + Wazuh XML rules | Detection logic without vendor lock-in |
| Entra ID | Keycloak | OIDC token flows, SAML assertions, OAuth consent grants from scratch |
| Azure Monitor | Grafana + Loki + Prometheus | Time-series + log aggregation primitives |
| Container Apps | Docker Compose | Container networking, volumes, healthchecks |
| Logic Apps automation | Webhook → FastAPI | Real HTTP integration, no low-code |
| Defender for Cloud | (intentionally omitted) | You realize what it was actually doing |

### 2. Sigma is more valuable than KQL

KQL only runs in Microsoft Sentinel and Azure Data Explorer. Sigma is portable: write a detection once, compile to Wazuh, Elastic, Splunk, Chronicle, *and* KQL. Every serious detection-engineering team uses Sigma as the source format. Having a portfolio of well-written Sigma rules is a stronger signal than the same rules locked into KQL.

### 3. The Oracle Free Tier is genuinely capable

Oracle's Always Free Ampere A1 ARM VM allocation: up to 4 OCPUs and 24 GB RAM. That's enough to run the full stack (Wazuh + Keycloak + Grafana + Loki + Caddy + two agents + the Sage chatbot) comfortably. The constraint is real but workable — it forces architectural discipline.

### 4. Cost goes to ~zero

The Azure plan projected ~$80–150/month if discipline held, much more if it slipped. The OSS plan: Oracle VM is free, OpenRouter is the only metered cost ($10–20/month hard cap). That's a 10x reduction with no loss of portfolio signal.

### 5. AI security on managed Azure OpenAI hides the model

Azure OpenAI gives you GPT-4o behind a Microsoft contract. OpenRouter exposes the whole open ecosystem — Hermes, Llama, Qwen, DeepSeek, Mistral — *plus* the closed-source models, all behind one OpenAI-compatible API. Swapping models becomes a one-line config change, which makes A/B model evaluation trivial to demonstrate.

## What stays the same

The conceptual project is unchanged:

- **Anchor adversary:** UNC3944 / Scattered Spider (MITRE G1015)
- **Secondary actor:** APT41 (week 14, for variety)
- **Fictional target company:** Halcyon Care Pte Ltd (25-person Singaporean healthtech)
- **Four centerpieces:** identity detection (ITDR/UEBA), incident investigation writeups, two AI agents, AI chatbot security
- **The Healyx feedback loop:** red → detection → triage → tuning → red adapts
- **Sage chatbot** as deliberately attackable AI target
- **Five incident writeups** across identity, host, network, cloud, LLM-app categories
- **16-week build arc**

## What changed concretely

### Infrastructure

| Was | Now |
|---|---|
| Azure subscription + resource group | Oracle Cloud Always Free tenancy |
| Azure VM (B-series) | Oracle Ampere A1 ARM VM, Ubuntu 24.04 |
| Microsoft Sentinel workspace | Wazuh manager + indexer + dashboard |
| Entra ID dev tenant | Keycloak realm |
| Log Analytics workspace | Loki + Grafana |
| Azure Container Apps | Docker Compose services |
| Azure DNS + App Gateway | Caddy reverse proxy with auto-Let's-Encrypt |
| Azure OpenAI (GPT-4o) | OpenRouter (Hermes 3 70B default) |
| Defender for Cloud | omitted |
| Microsoft Defender XDR connectors | omitted (use Wazuh's built-in capabilities) |
| Azure Monitor metric alerts | Prometheus + Alertmanager (optional, Week 5+) |

### Repo layout

| Was | Now |
|---|---|
| `infra/bicep/` Azure Bicep templates | `infra/docker-compose.yml` + per-service configs |
| `detections/kql/` KQL rules | `detections/sigma/` Sigma source + `detections/wazuh-rules/` compiled output |
| `automation/logic-apps/` | (removed — triage agent webhook replaces it) |
| `agent/triage/main.py` (Sentinel webhook payload schema) | same file, Wazuh webhook payload schema |
| `agent/redteam/scenarios/*.py` referencing Graph API / Az CLI | scenarios reference Keycloak admin API, Wazuh API, local OS |
| Azure auth via managed identity | OAuth client credentials against Keycloak; OpenRouter API key in `.env` |

### Detections

The five-category writeup plan stays, but the *targets* shift:

| Category | Was (Azure) | Now (OSS) |
|---|---|---|
| Identity | Entra ID sign-in logs, risky sign-in events | Keycloak event logs, session anomalies |
| Host | Defender for Endpoint telemetry | Wazuh agent on the VM (FIM, syscheck, rootcheck) |
| Network | Azure Firewall logs | Wazuh + suricata logs from the Caddy host |
| Cloud | Azure Activity Log | Docker daemon events, Caddy access logs, Keycloak admin events |
| LLM-app | Sage app logs to Log Analytics | Sage app logs to Loki, surfaced in Wazuh via integration |

The MITRE technique coverage is preserved — only the data sources change.

## What you lose (be honest)

- **The Sentinel name on your CV.** "I built a SOC lab on Microsoft Sentinel" is a recognizable signal to recruiters who don't read deeply. If your target role is specifically a Sentinel shop, weigh this.
- **Managed identity / RBAC complexity.** Azure has real, complex IAM. Keycloak is good but it's not the same beast.
- **Defender XDR cross-product correlation.** You can't replicate the Microsoft cross-product story (M365 + Entra + Defender) with open source alone.
- **One-click compliance dashboards.** Microsoft has prebuilt CIS/NIST workbooks. You'd build dashboards yourself in Grafana.

Mitigations:

- Keep **one** Azure-side artifact: write the Sigma rules so they include a compile target for KQL, and publish a `detections/kql/` directory of the auto-generated KQL alongside the Wazuh output. Now you have *both* on the CV.
- Use Keycloak's OIDC flows to teach the *protocol*, then add a short writeup in `docs/cti/` describing how the same attack maps to Entra ID concepts. Demonstrating you understand the mapping is the actual signal.

## When to NOT do this pivot

Skip the pivot if:

- You're more than ~3 weeks into the Azure build (sunk cost is real — the resource setup, custom KQL, and Logic Apps wiring take time).
- Your target role is explicitly Microsoft-stack (a Sentinel-focused SOC, Microsoft FastTrack, a Microsoft partner).
- You already have an Azure subscription with prepaid credits.

If none of those apply: pivot.
