# Week 14 — APT41 secondary actor

## Objectives

- Two new scenarios emulating APT41 TTPs (less identity-focused, more tooling-led)
- Triage agent's actor attribution correctly distinguishes UNC3944 vs APT41
- A CTI profile at `docs/cti/apt41.md` mirroring the Scattered Spider format

## Why APT41

UNC3944 is identity-led, social-engineering-heavy, financially motivated. APT41 is dual-purpose (state + criminal), supply-chain-led, malware-tooling-heavy. Adding it as a second actor:

- Tests whether your detections generalize beyond one playbook
- Tests whether triage attribution is real or just guessing "UNC3944" by default
- Adds richness to the portfolio (two threat actors, not one)

## Two scenarios to implement

### `apt41_web_shell_drop`

Drops a web shell into Sage's static assets directory (simulating a web app compromise). Wazuh syscheck should fire on the new file. MITRE T1505.003.

### `apt41_living_off_the_land`

Uses built-in OS tools (curl, python3, base64) to exfiltrate `/etc/passwd` over DNS. Tests whether your host detections look for behavior (suspicious DNS volumes) vs binaries (file hashes). MITRE T1071.004.

## Saturday — implement and detect

Build the scenarios. Author two new Sigma rules:

- `healyx-host-web-shell-drop-v1.yml` (file creation in a webroot with shell-like content)
- `healyx-host-dns-exfil-v1.yml` (anomalous DNS query length / volume)

## Sunday — CTI profile + attribution test

Write `docs/cti/apt41.md` using the same structure as `scattered-spider.md`.

Run a mixed-actor session: 2 rounds of UNC3944, 2 rounds of APT41. Check the triage incidents log — did the agent correctly attribute each? Adjust the prompt if not.

## Done conditions

- [ ] Two APT41 scenarios in `agent/redteam/scenarios/`
- [ ] Two new Sigma rules
- [ ] CTI doc at `docs/cti/apt41.md`
- [ ] Triage agent correctly attributes APT41 vs UNC3944 in mixed sessions
