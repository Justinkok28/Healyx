# CLAUDE.md — Context for Claude Code

> Read this file at the start of every Claude Code session. It's the single source of truth for what this project is, what it isn't, and how to work in it.

## What this project is

**Project Ouroboros (OSS edition)** — a self-improving purple-team SOC lab that runs entirely on an Oracle Cloud Always Free ARM VM using open source tooling. Red attacks, blue detects, the triage agent proposes detection tuning, the rules sharpen, the red agent's LLM planner adapts.

Modeling a fictional 25-person Singaporean healthtech, **Halcyon Care Pte Ltd**.

This is the open-source pivot of an earlier Azure version (Sentinel + Entra ID). The pivot is documented in `PIVOT_FROM_AZURE.md`.

## The stack

| Layer | Tool | Why |
|---|---|---|
| Host | Oracle Cloud Free Tier ARM VM (4 OCPU / 24 GB RAM Ampere A1) | Free, generous, real Linux |
| Container runtime | Docker + Docker Compose | Standard, portable |
| SIEM | **Wazuh** | OSSEC-derived, has rules/alerts/dashboards |
| Identity | **Keycloak** | Real OIDC/SAML; supports the UNC3944 OAuth scenarios |
| Logs/metrics | **Grafana + Loki + Prometheus** | Dashboards + log aggregation |
| Reverse proxy / TLS | **Caddy** | Auto Let's Encrypt, dead simple |
| Detection language | **Sigma** (YAML) → compile to Wazuh rules | Portable, industry standard |
| LLM API | **OpenRouter** | Single endpoint, model-agnostic, spend caps |
| Primary model | **Nous Hermes 3 70B** | Strong tool calling, structured JSON output |
| Vulnerable target | "Sage" booking assistant (FastAPI + LLM) | Deliberately attackable AI chatbot |
| Agent framework | FastAPI + Pydantic + OpenAI Python client (OpenRouter-compatible) | Simple, no LangChain bloat |

## The two AI agents

1. **`agent/redteam/`** — emulates UNC3944 (Scattered Spider) TTPs and attacks the Sage chatbot. LLM planner varies scenarios over time.
2. **`agent/triage/`** — receives Wazuh alerts via webhook, investigates by querying logs through tools, outputs structured JSON (incident classification + MITRE mapping + suggested rule tuning).

## Hard rules (do not violate)

- **Read-only by default.** Triage agent never auto-contains. Red agent only attacks resources inside this lab.
- **Structured JSON output.** Every agent decision validated against a Pydantic schema before persistence.
- **Cite evidence.** Triage cites Wazuh alert IDs and log row IDs. Red agent appends ground truth to `ground_truth.jsonl`.
- **No secrets in prompts.** Sanitize Wazuh alert JSON before sending to OpenRouter — strip tokens, full credentials, internal IPs of the host.
- **Spend cap on OpenRouter is sacred.** Hard cap $20/month. The red agent loop must respect it.
- **Sigma is the source of truth for detections.** Wazuh rules are *compiled outputs*, never hand-edited.

## Where things live

```
Ouroboros/
├── CLAUDE.md                  ← you are here
├── README.md                  ← public-facing project overview
├── PIVOT_FROM_AZURE.md        ← migration guide from the Azure version
├── PIVOT_CHECKLIST.md         ← tactical checklist for the pivot itself
├── WEEKEND_QUICKSTART.md      ← what to do this weekend
├── .github/workflows/         ← CI/CD pipelines
├── docs/                      ← MkDocs site (deployed to GitHub Pages)
│   ├── weeks/                 ← 16 weekly playbooks
│   └── cti/                   ← threat actor profiles
├── infra/                     ← docker-compose + service configs
├── agent/                     ← red + triage agents
│   ├── common/                ← shared OpenRouter client, schemas
│   ├── redteam/
│   ├── triage/
│   └── eval/                  ← scoring harness for agent outputs
├── chatbot/sage/              ← the vulnerable target app
├── detections/
│   ├── sigma/                 ← source detections (YAML)
│   └── wazuh-rules/           ← compiled output (generated, gitignored except samples)
└── scripts/                   ← bootstrap + helper scripts
```

## How to work on this project in Claude Code

When the user asks you to do something:

1. **Check the relevant week's playbook first** (`docs/weeks/week-NN-*.md`). The playbooks are the spec.
2. **Never invent infrastructure.** If a service isn't in `infra/docker-compose.yml`, ask before adding it.
3. **Test before committing.** Run `make test` (or `pytest agent/`) before any commit involving agent code.
4. **Lint before committing.** `make lint` runs ruff and prettier.
5. **CI must stay green.** If you push and CI fails, fix it before continuing other work.
6. **Detections workflow:** edit `detections/sigma/*.yml`, then run `make compile-rules` to regenerate `detections/wazuh-rules/*.xml`. Both get committed.
7. **Secrets:** never commit `.env`. Use `.env.example` as the template. OpenRouter key, Keycloak admin password, Wazuh API password all live in `.env`.

## Commands you'll use a lot

```bash
make up                  # docker compose up -d (start the lab)
make down                # docker compose down
make logs SERVICE=wazuh  # tail logs for one service
make test                # pytest across all agent code
make lint                # ruff + prettier
make compile-rules       # Sigma → Wazuh rule XML
make agent-redteam       # run one red-team scenario locally
make agent-triage        # start the triage agent webhook server
make docs-serve          # MkDocs local preview
```

## The 16-week arc at a glance

- **Weeks 1–2:** Repo + Oracle VM + Docker + Caddy + TLS
- **Weeks 3–5:** Wazuh + Keycloak + Grafana/Loki wired up
- **Week 6:** Sage chatbot deployed as vulnerable target
- **Week 7:** First batch of Sigma detections + Wazuh rule compilation
- **Weeks 8–9:** Red agent + triage agent (skeleton → working)
- **Week 10:** Layered defenses for Sage (regex + classifier + Guardrails + PII sweep)
- **Weeks 11–12:** Full attack scenarios + feedback loop wired end-to-end
- **Week 13:** Eval harness, scoring, A/B model comparison
- **Week 14:** APT41 secondary actor for variety
- **Weeks 15–16:** Five full incident writeups + portfolio polish

## What this project is **not**

- Not a production SOC. It's a portfolio lab.
- Not a multi-tenant system. Single operator, single VM.
- Not a LangChain showcase. Plain FastAPI + OpenAI client is fine.
- Not a Kubernetes project. Docker Compose only on the free tier.
- Not enterprise security tooling. No Defender, no EDR — just the open source primitives.

## Contact / context

Solo project. The user is a security professional building a portfolio piece for SOC / detection engineering / AI security roles. Singapore-based (timezone matters for cron schedules — use SGT / `Asia/Singapore`).
