# Week 15 — Incident writeups (the portfolio centerpiece)

## Objectives

- Five full incident investigation writeups, one per category, in `docs/writeups/`
- Each writeup follows a consistent template
- Each is publishable as a standalone artifact for the portfolio

## The template

Each writeup uses this structure (also saved as `docs/writeups/_template.md`):

```markdown
# Incident <NN> — <short title>

**Category:** Identity / Host / Network / Cloud / LLM-app
**Date:** ...
**Actor emulated:** UNC3944 (or APT41)
**MITRE techniques:** Txxxx.yyy, ...

## TL;DR
Three sentences. What happened, what blue saw, what was tuned.

## Timeline
- 14:02 SGT — initial access via vishing-driven password reset
- 14:08 SGT — first Keycloak login from new IP
- 14:14 SGT — MFA device added on attacker session
- ...

## What red did
Step-by-step what the scenario executed. Include exact commands and API calls. Reproducibility is the point.

## What blue saw
Which Sigma rules fired, in what order, what the triage agent concluded. Include the actual TriageResult JSON for at least one alert.

## What was missed
Honest assessment: where coverage failed. This section is what separates a real writeup from a marketing piece.

## Tuning applied
What changed in detections/sigma/ as a result. Link to the PR.

## MITRE mapping
Table of techniques observed → rules that caught them.

## References
Public CTI links, related MITRE pages.
```

## Saturday — write 3 of 5

Pick the easiest first. You'll have the most data for:

1. **Identity** — MFA fatigue → successful login → role escalation
2. **LLM-app** — Prompt injection bypassing some defenses, caught by others
3. **Network** — SSH brute force from external IP

## Sunday — write the remaining 2

4. **Host** — SUID binary creation outside expected paths
5. **Cloud** — Keycloak admin manipulation (new client + secret added)

## Length and quality

Aim for 1000–1500 words each. Long enough to be substantive, short enough to read in a coffee break. Recruiters and hiring managers do not have time for 5000-word essays. Make every paragraph do work.

## What makes a writeup excellent

- **Specific commands.** "Attacker ran `nmap -Pn -p 22 ...`" beats "attacker performed reconnaissance."
- **Honest gaps.** A writeup that admits "rule X had a 30-second window that the attacker beat by pacing slower" reads as more credible than one that claims perfect detection.
- **Numbers.** Time-to-detect, alerts fired, false positives in that period. Even rough numbers beat vague claims.
- **A link to the PR that fixed the gap.** That's the chef's kiss — closes the loop visibly.

## Done conditions

- [ ] Five writeups in `docs/writeups/`
- [ ] Each one 1000–1500 words, each with timeline + MITRE mapping + tuning section
- [ ] All five linked from `docs/index.md`
- [ ] At least one writeup has a PR-link footer showing the tuning that resulted
