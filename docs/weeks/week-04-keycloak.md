# Week 4 — Keycloak IdP

## Objectives

- Keycloak running, accessible at `https://auth.<your-domain>`
- Realm `halcyon-care` created
- A few realistic users (alice, bob, helpdesk) seeded
- OTP MFA required for at least one user — gives the MFA fatigue scenario something to spam
- Event logging enabled so Wazuh can consume Keycloak events

## Saturday — start Keycloak

```bash
cd infra
docker compose up -d keycloak-db
sleep 10  # let Postgres warm up
docker compose up -d keycloak
docker compose logs -f keycloak
```

Wait for "Keycloak X.Y.Z started in N ms." Then visit `https://auth.<your-domain>`.

Log in with `KEYCLOAK_ADMIN` / `KEYCLOAK_ADMIN_PASSWORD` from `.env`.

## Create the `halcyon-care` realm

In the master realm:
1. Top-left dropdown → Create realm
2. Name: `halcyon-care`
3. Enabled: yes

Switch into the new realm.

## Create users

For each of `alice`, `bob`, `helpdesk`:

1. Users → Add user
2. Email Verified: yes (don't want to wire up email)
3. After creation: Credentials tab → Set Password → uncheck "Temporary" → save

Required actions for alice: add "Configure OTP" so her next login forces MFA setup. Log in once as alice with the FreeOTP app to provision the OTP secret — now she's a realistic MFA-protected user.

## Create the `halcyon-portal` client

This is the client the red-team scenarios authenticate against.

1. Clients → Create client
2. Client ID: `halcyon-portal`
3. Client authentication: OFF (public client — direct access grants)
4. Authentication flow: enable Direct access grants (for the MFA fatigue scenario)
5. Standard flow + Direct access grants checked

## Enable event logging

Keycloak emits events to two places:
- **User events** (logins, logouts, code-to-token exchanges) — the spicy ones for detections
- **Admin events** (config changes) — important for the OAuth consent-grant scenario

In Realm settings → Events:
- Save events: ON
- Save admin events: ON
- Both: 30-day retention

These events feed into Loki via week 5's Promtail config, and into Wazuh via a Keycloak event decoder.

## Sunday — wire Keycloak events into Wazuh

Keycloak doesn't log to syslog by default; events live in the database. Two integration paths:

### Path A (simple): log file tailing

Configure Keycloak to also write events to a log file via the JBoss logging subsystem. Wazuh agent watches the file.

In `infra/keycloak/spi-events.json` (create this):

```json
{
  "providers": {
    "eventsListener": {
      "jboss-logging": {
        "success-level": "info",
        "error-level": "warn"
      }
    }
  }
}
```

Mount it into the container and restart Keycloak. Events will appear in container stdout, which Wazuh can ingest via docker log driver.

### Path B (better, week 12): admin-events API polling

Write a small Python sidecar that polls Keycloak's `/admin/realms/halcyon-care/events` and forwards to Wazuh syslog. We'll build this in Week 12.

For now, Path A is enough — we just need events to exist.

## Done conditions

- [ ] Keycloak accessible over HTTPS
- [ ] `halcyon-care` realm exists
- [ ] alice / bob / helpdesk users exist
- [ ] alice has OTP MFA configured
- [ ] `halcyon-portal` client exists with direct access grants enabled
- [ ] Event logging is on
- [ ] At least one auth event flows through to Wazuh

## Pitfalls

- **Keycloak hostname errors.** If `KC_HOSTNAME=auth.<your-domain>` and Caddy is forwarding correctly but Keycloak still complains, also set `KC_PROXY_HEADERS=xforwarded` and `KC_HTTP_ENABLED=true`.
- **Realm import on every restart.** Don't put `--import-realm` in the compose command without an `if` guard — it re-imports every restart and overwrites your manual changes.
