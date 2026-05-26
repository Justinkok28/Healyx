# Week 5 — Grafana + Loki

## Objectives

- Loki running and accepting log writes
- Grafana running, accessible at `https://grafana.<your-domain>`, Loki datasource configured
- Promtail (or alloy) installed on the VM, shipping Docker container logs to Loki
- At least one Grafana dashboard showing recent auth events from Keycloak

## Why two log systems

You'll occasionally wonder why we have *both* Wazuh and Loki. Different purposes:

- **Wazuh** — security-relevant events, rule-engine alerting, the SIEM you actually triage from
- **Loki** — high-volume application logs, easy LogQL ad-hoc queries, the Grafana dashboards a developer would use

Both ingest from the same Docker containers but the *consumers* are different. The triage agent reads Loki for context around an alert.

## Saturday — bring up Loki + Grafana

```bash
cd infra
docker compose up -d loki grafana
docker compose logs -f loki grafana
```

Wait for both to settle. Visit `https://grafana.<your-domain>`. Log in with `GRAFANA_ADMIN_USER` / `GRAFANA_ADMIN_PASSWORD`.

The Loki datasource should already be configured via the provisioning file in `infra/grafana/provisioning/datasources/`. Confirm under Connections → Data sources.

## Ship logs into Loki — Promtail or Grafana Alloy

Both work. Alloy is the newer, recommended approach. Install Alloy as a Docker service:

Add to `infra/docker-compose.yml` (next to `loki`):

```yaml
  alloy:
    image: grafana/alloy:latest
    container_name: alloy
    restart: unless-stopped
    volumes:
      - ./alloy/config.alloy:/etc/alloy/config.alloy:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
    command: run --server.http.listen-addr=0.0.0.0:12345 /etc/alloy/config.alloy
    networks: [healyx]
    depends_on: [loki]
```

Create `infra/alloy/config.alloy`:

```hcl
discovery.docker "containers" {
  host = "unix:///var/run/docker.sock"
}

discovery.relabel "containers" {
  targets = discovery.docker.containers.targets
  rule {
    source_labels = ["__meta_docker_container_name"]
    target_label  = "container"
    regex         = "/(.+)"
    replacement   = "$1"
  }
}

loki.source.docker "default" {
  host       = "unix:///var/run/docker.sock"
  targets    = discovery.relabel.containers.output
  forward_to = [loki.write.default.receiver]
}

loki.write "default" {
  endpoint {
    url = "http://loki:3100/loki/api/v1/push"
  }
}
```

`docker compose up -d alloy`. Within a minute, logs from every container should be in Loki.

## Sunday — first Grafana dashboard

In Grafana:

1. New Dashboard → Add visualization → Datasource: Loki
2. Query: `{container="keycloak"} |= "LOGIN"`
3. Save as "Halcyon Care — Keycloak Auth Events"

Add panels:

- `count_over_time({container="keycloak"} |= "LOGIN_ERROR" [5m])` — failed auth rate
- `{container="sage"} |~ "(?i)injection|jailbreak"` — Sage prompt-injection attempts
- `{container=~"wazuh-.+"} |= "ERROR"` — Wazuh internal errors

## Done conditions

- [ ] Loki receives container logs
- [ ] Grafana datasource works, ad-hoc LogQL queries return data
- [ ] At least one saved dashboard with three panels
- [ ] Grafana accessible over HTTPS via Caddy

## Pitfalls

- **Alloy can't read Docker socket.** Make sure your user inside the Alloy container can access the socket (the bind mount mode matters on some kernels).
- **Loki rejects logs as "too far behind."** Default `reject_old_samples_max_age` is 24h. If you replay old logs it will reject; bump the limit or accept the loss.
