# Scope

## Fictional company: Halcyon Care Pte Ltd

- Singapore-incorporated healthcare-SaaS, 25 employees
- Offers an appointment-booking and patient-records platform to small clinics
- Stores PHI (protected health information); subject to Singapore's PDPA + (aspirationally) HIPAA-style controls
- Customer-facing web app at `booking.halcyon.care.example` includes an AI assistant called Sage
- Internal SSO via Keycloak realm `halcyon-care`

## On the names

- **Ouroboros** — the serpent eating its own tail. Names the project because the architecture *is* the loop: red attacks → blue detects → triage proposes tuning → detections sharpen → red adapts. The cycle is the deliverable.
- **Halcyon Care** — Halcyon is a mythological bird that calms the seas. Fitting for a healthtech maintaining peaceful operations for its clinics.

## Anchor threat actor

**UNC3944 / Scattered Spider** (MITRE G1015) — well-documented across MITRE, CISA, Mandiant, Microsoft, and HHS HC3. Picked because:

- Identity-first playbook fits Halcyon's profile (SSO is the crown jewel)
- Healthcare-sector activity is on record
- Heavy social engineering means scenarios are interesting beyond pure technical exploitation
- Public reporting gives detailed TTPs to emulate without speculation

Secondary actor (week 14): **APT41** — gives variety in technique style, less identity-led, more tooling-led.

## The four centerpieces

1. **Threat-informed identity detection** — Sigma rules mapped to specific UNC3944 TTPs against Keycloak
2. **Cloud incident investigation** — five full writeups across the categories below
3. **Two AI agents** — red-team adversary emulator and triage agent
4. **AI chatbot security** — Sage with layered defenses + the four Wazuh detections that fire when defenses fail

## The five-category incident writeup matrix

| Category | Example incident |
|---|---|
| Identity | MFA fatigue → successful Keycloak push approval → role escalation |
| Host | Wazuh agent on the VM detects suspicious cron + new SUID binary |
| Network | nmap fingerprint + SSH brute-force from external IP, caught by Caddy + Wazuh |
| Cloud | New Keycloak client created with broad scopes, secret added (T1098.001 analog) |
| LLM-app | Prompt injection extracts Sage system prompt and pivots to enumerating bookings |

## Out of scope

- Real PHI of any kind
- Active attacks against any system not owned by the operator
- Anything that requires a license (Splunk, CrowdStrike, paid Wazuh tiers, etc.)
- Multi-tenant operation
- High availability / disaster recovery
- Long-term log retention beyond seven days

## Done conditions for the 16-week build

- [ ] All eight red-team scenarios implemented and runnable
- [ ] At least 12 Sigma detections written, with Wazuh-rule compile output committed
- [ ] Triage agent receives Wazuh webhook calls and persists structured verdicts
- [ ] Red-team LLM planner runs autonomously for a multi-round session under spend cap
- [ ] Sage chatbot deployed with at least four layered defenses
- [ ] Five full incident writeups committed to `docs/writeups/`
- [ ] A/B evaluation comparing at least three models (one Hermes, one Claude, one open) with metrics CSV + Grafana panel
- [ ] Docs site builds green and is public on GitHub Pages
- [ ] CI green on every commit on `main`
