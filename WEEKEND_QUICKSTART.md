# Weekend Quickstart

Two-day plan to finish the pivot and get to a working position on Week 2.

## Saturday (4–6 hours)

### Morning block — repo migration (2 hr)

Follow `PIVOT_CHECKLIST.md` Steps 1–5. End state: new GitHub repo with the OSS skeleton pushed, CI green, GitHub Pages building.

### Mid-day — account provisioning (1 hr)

`PIVOT_CHECKLIST.md` Steps 6–7. Open Oracle Cloud signup *first* because it sometimes takes hours to fully verify. While it processes:

- Sign up for OpenRouter
- Fund $10, set $20/month spend cap
- Create API key

### Afternoon — local dev environment (1–2 hr)

`PIVOT_CHECKLIST.md` Steps 8–9. Get `pytest` and `make lint` passing on your laptop.

### Evening — read ahead (45 min)

Read these three files cover to cover. They're your spec.

1. `CLAUDE.md` — the project's bible
2. `docs/architecture.md` — the system diagram
3. `docs/weeks/week-02-oracle-vm.md` — tomorrow's playbook

Do **not** start Week 2 today. The Oracle VM provisioning often blocks on capacity issues; you want a full day's window to retry.

## Sunday (4–6 hours)

### Morning — VM provisioning (1–3 hr depending on Oracle's mood)

Follow `docs/weeks/week-02-oracle-vm.md` through "VM provisioned + SSH works."

If you hit "Out of host capacity":

- Try a different home region (you can change once)
- Try at off-peak times for that region
- Try Ampere A1 with 2 OCPU / 12 GB instead of the full 4 OCPU / 24 GB
- Fall back to x86 micro × 2 (split services across both)
- Fall back to Hetzner CAX11 ($5/month, ARM, no oversubscription)

### Mid-day — VM hardening + Docker (1–2 hr)

Continue Week 2 playbook through "Docker + Docker Compose installed, non-root user can run docker."

### Afternoon — first compose up (1 hr)

Continue through "`make up` succeeds, Caddy is serving the placeholder page over HTTPS at your domain."

You'll need a domain (or a subdomain). Cheap options: a `.dev` from Cloudflare Registrar (~$10/yr, free DNS), or a free subdomain from DuckDNS / Cloudflare (if you have a domain already).

### Evening — commit progress, breathe (30 min)

- Commit the docker-compose tweaks you made for your environment
- Push, watch CI pass
- Read `docs/weeks/week-03-wazuh.md` so you know what's coming next weekend

## Done conditions for the weekend

By Sunday evening, you should have:

- [ ] OSS repo on GitHub with green CI and a published docs site
- [ ] OpenRouter account + key + spend cap
- [ ] Oracle (or Hetzner fallback) VM provisioned, SSH-accessible
- [ ] Docker + Docker Compose installed on the VM
- [ ] `make up` working on the VM, Caddy serving a placeholder page over HTTPS
- [ ] Domain or subdomain pointing at the VM

If you finished all of those, you are **ahead** of where the Azure plan would have put you, because you've already done real Linux ops instead of clicking through portals.
