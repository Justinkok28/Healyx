# Week 3 — Wazuh SIEM

## Objectives

- Wazuh indexer + manager + dashboard running
- Wazuh dashboard reachable at `https://wazuh.<your-domain>`
- Wazuh agent installed on the VM itself (host-monitoring its own host)
- A test alert visible in the dashboard

## Saturday — bring up Wazuh

The indexer is memory-hungry (1.5 GB). Bring services up one at a time so failures are obvious:

```bash
cd infra
docker compose up -d wazuh-indexer
# Wait for it to become healthy — first start does data dir init
docker compose logs -f wazuh-indexer
# When you see "started" + indices loading, ctrl-c and continue:
docker compose up -d wazuh-manager
docker compose logs -f wazuh-manager
docker compose up -d wazuh-dashboard
docker compose logs -f wazuh-dashboard
```

Visit `https://wazuh.<your-domain>`. Log in with the `kibanaserver` user and the `WAZUH_DASHBOARD_PASSWORD` from `.env`.

### Important: change default certs and passwords

Wazuh images ship with default internal certs. For a lab this is acceptable, but flag in your portfolio writeup that production deployment would require running `wazuh-certs-tool.sh` to regenerate.

## Sunday — install the Wazuh agent on the VM

The manager monitors itself only via syscheck on its container. Real value comes from a Wazuh agent on the host watching files, processes, and syscalls.

```bash
# On the VM, NOT inside the container:
curl -so wazuh-agent.deb https://packages.wazuh.com/4.x/apt/pool/main/w/wazuh-agent/wazuh-agent_4.9.2-1_arm64.deb
sudo WAZUH_MANAGER="127.0.0.1" dpkg -i wazuh-agent.deb
sudo systemctl daemon-reload
sudo systemctl enable wazuh-agent
sudo systemctl start wazuh-agent
```

The agent reports to the manager on port 1514. In the dashboard → Agents, you should see one agent enrolled within 30 seconds.

### Generate a test alert

```bash
# Touch a file inside a monitored directory — default syscheck watches /etc
sudo touch /etc/ouroboros-test-file
# Wait ~30s — Wazuh's syscheck scans periodically
```

In the dashboard, navigate to Security events. You should see a 5000-series rule alert for a new file in `/etc`.

## Done conditions

- [ ] Wazuh indexer / manager / dashboard all running
- [ ] Dashboard accessible over HTTPS via Caddy
- [ ] One Wazuh agent enrolled (the VM itself)
- [ ] At least one test alert visible

## Pitfalls

- **Out of memory during indexer start.** Lower `OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m` if you're on a 12 GB VM.
- **Indexer fails on `vm.max_map_count`.** Run `sudo sysctl -w vm.max_map_count=262144` and persist in `/etc/sysctl.d/99-wazuh.conf`.
- **Dashboard 503 behind Caddy.** Dashboard takes 60–90 seconds to be fully ready after the container starts. Be patient.
