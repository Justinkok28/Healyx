# Scattered Spider (UNC3944)

> Primary anchor threat actor for Project Ouroboros. All eight red-team scenarios emulate TTPs from this group.

## At a glance

- **Aliases:** Scattered Spider, UNC3944, Octo Tempest (Microsoft), 0ktapus, Scatter Swine, Muddled Libra
- **MITRE ATT&CK Group:** [G1015](https://attack.mitre.org/groups/G1015/)
- **First reported:** 2022
- **Composition:** Loosely affiliated English-speaking operators, suspected ties to "The Com" criminal ecosystem
- **Targeting:** Initially telco/BPO/SaaS for SIM swaps; expanded into hospitality, retail, financial services, and **healthcare** (2023+)
- **Motivation:** Financial — extortion, ransomware-as-a-service affiliations (BlackCat/ALPHV, RansomHub)

## Why this group anchors the project

Three reasons:

1. **Identity-first playbook.** Their access vector is almost always identity — vishing the help desk, MFA fatigue, SIM swap, OAuth abuse. Halcyon Care's SSO via Keycloak is exactly the surface they target.
2. **Healthcare activity on record.** CISA + HHS HC3 advisories specifically call out hospital and healthcare-SaaS victims, giving the Halcyon scenario realistic basis.
3. **Public reporting is dense.** Mandiant, Microsoft, CrowdStrike, Trellix, Trustwave, and CISA have all published technical detail. The TTPs are not guesswork.

## TTP summary mapped to MITRE

| Tactic | Technique | Sub-technique | UNC3944 specifics |
|---|---|---|---|
| Reconnaissance | T1591 | Gather Victim Org Info | LinkedIn for help-desk staff names |
| Resource Development | T1585.001 | Establish Accounts: Social Media | Fake LinkedIn / impersonation |
| Initial Access | T1566 | Phishing | SMS smishing, vishing the help desk |
| Initial Access | T1078.004 | Valid Accounts: Cloud Accounts | Post-vishing credential use |
| Credential Access | T1621 | MFA Request Generation | Push spam after password capture |
| Credential Access | T1111 | MFA Interception | SIM swap or push approval |
| Credential Access | T1556.006 | Modify Auth Process: MFA | Adding attacker MFA device |
| Persistence | T1098.001 | Account Manipulation: Cloud Credentials | New service principal secret |
| Persistence | T1136.003 | Create Account: Cloud Account | Net-new admin account |
| Privilege Escalation | T1078.004 | Valid Accounts: Cloud Accounts | Targeting privileged users |
| Defense Evasion | T1562 | Impair Defenses | Disabling Defender / Wazuh agent |
| Discovery | T1087.004 | Account Discovery: Cloud | Enumerating Entra/Keycloak |
| Lateral Movement | T1021.007 | Remote Services: Cloud Services | Federated movement |
| Collection | T1530 | Data from Cloud Storage | Mass-download from SaaS |
| Exfiltration | T1567 | Exfiltration to Cloud Storage | mega.nz, transfer.sh |
| Impact | T1486 | Data Encrypted for Impact | BlackCat/RansomHub deployment |

## Scenarios mapped to TTPs

| Project scenario | Primary TTP(s) | Plays out as |
|---|---|---|
| `mfa_fatigue` | T1621, T1078.004 | Spam Keycloak `/token` endpoint until user approves |
| `helpdesk_password_reset` | T1078.004, T1556 | Simulated phishing call; reset attacker-controlled |
| `oauth_consent_grant` | T1550.001, T1078.004 | Malicious OAuth client + consent phishing |
| `priv_role_burst` | T1098.003 | Assign + revoke admin in rapid bursts |
| `sp_credential_addition` | T1098.001 | Add second client secret to a SP / service account |
| `port_scan_then_ssh_bf` | T1595, T1110 | nmap + rockyou-lite SSH brute-force |
| `cloud_storage_exfil` | T1530, T1567 | Bulk pull of "patient records" via Sage data endpoint |
| `chatbot_prompt_injection` | T0051 (MITRE ATLAS) | Extract Sage system prompt + pivot to enumerate bookings |

## What detection actually needs to catch

Behavior, not signatures. UNC3944 operators rotate tooling, but the *shape* of their playbook is consistent:

- Many failed → one successful auth from the same identity in a short window
- Help-desk-initiated password reset followed by MFA device change followed by privileged action
- New OAuth client + new consent grant + first use, all within minutes
- Service principal credential addition without a corresponding change ticket
- Privileged role assignment that's revoked within hours (covers tracks)

These behaviors are the basis for the Sigma rules in `detections/sigma/`.

## References (all public)

- [MITRE ATT&CK G1015](https://attack.mitre.org/groups/G1015/)
- [CISA AA23-320A](https://www.cisa.gov/news-events/cybersecurity-advisories/aa23-320a) — Scattered Spider advisory
- [HHS HC3 Threat Brief — Scattered Spider](https://www.hhs.gov/sites/default/files/scattered-spider.pdf)
- Microsoft Threat Intelligence: Octo Tempest writeups
- Mandiant blog: UNC3944 publications (2022–2024)

No private reporting or non-public material is used in this project.
