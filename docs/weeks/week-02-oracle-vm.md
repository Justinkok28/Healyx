# Week 2 — Oracle VM + Docker + Caddy

> 4–6 hours. The first weekend you stand up real infrastructure.

## Objectives

- Oracle Ampere A1 VM provisioned and SSH-accessible
- Hardened: non-root user, key auth only, ufw + Oracle security list configured
- Docker + Docker Compose installed
- Domain or subdomain resolving to the VM's public IP
- `make up` runs on the VM, Caddy serves a placeholder over HTTPS with a real Let's Encrypt cert

## Saturday — provision the VM (1–4 hours, depending on Oracle's mood)

### Provision

1. Oracle Cloud Console → Compute → Instances → Create
2. Shape: `VM.Standard.A1.Flex`, 4 OCPU / 24 GB RAM
3. Image: Canonical Ubuntu 24.04 (Minimal is fine)
4. Networking: place in your default VCN's public subnet; assign a public IPv4
5. SSH keys: upload your laptop's public key

If you hit **Out of host capacity**:

- Try a different region (you can change your home region once for free)
- Retry at off-peak times (00:00–06:00 region-local often works)
- Downscale to 2 OCPU / 12 GB and retry
- Try `VM.Standard.E2.1.Micro` × 2 (x86, also free) and split services
- Fall back to Hetzner CAX11 ($5/mo, ARM, no oversubscription)

### Connect + harden

```bash
# From your laptop:
ssh ubuntu@<your-vm-ip>

# Create your work user
sudo adduser ouroboros
sudo usermod -aG sudo ouroboros
sudo mkdir /home/ouroboros/.ssh
sudo cp /home/ubuntu/.ssh/authorized_keys /home/ouroboros/.ssh/
sudo chown -R ouroboros:ouroboros /home/ouroboros/.ssh
sudo chmod 700 /home/ouroboros/.ssh
sudo chmod 600 /home/ouroboros/.ssh/authorized_keys

# Disable root + password SSH (already disabled by default on Oracle images; verify)
sudo sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo sed -i 's/^#*PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl restart ssh

# Test the new user works, then disconnect:
exit
ssh ouroboros@<your-vm-ip>
```

### Open ports — Oracle security list + ufw

Oracle Ubuntu images come with iptables rules that block everything except SSH. Two layers to fix:

```bash
# Layer 1: Linux firewall (ufw)
sudo apt update && sudo apt install -y ufw
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Also clear the default iptables that Oracle puts in (often fights ufw):
sudo iptables -F INPUT
sudo iptables-save | sudo tee /etc/iptables/rules.v4
```

Layer 2: in Oracle console, find your VCN's Security List and add ingress rules for 80/tcp and 443/tcp from 0.0.0.0/0.

## Sunday — Docker, Compose, domain, `make up`

### Install Docker + Compose

```bash
# Official Docker convenience installer (fine for a single-host lab)
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker ouroboros
# Re-login or `newgrp docker` to pick up the group
exit
ssh ouroboros@<your-vm-ip>

docker --version
docker compose version  # should be v2 (plugin-based)
```

### Domain

Pick one:

- **You have a domain.** Add an A record for the apex *and* a wildcard `*.<your-domain>` pointing at the VM's public IP.
- **No domain.** Cloudflare Registrar sells `.dev` for ~$10/year, free wildcard DNS. Or use Duck DNS for a free subdomain.

Verify:

```bash
dig +short auth.your-domain.example
# should return your VM IP
```

### Clone the repo and bring up

```bash
cd ~
git clone https://github.com/justinkok28/Ouroboros.git
cd Ouroboros
cp .env.example .env

# Edit .env — at minimum: PUBLIC_DOMAIN, ACME_EMAIL, OPENROUTER_API_KEY,
# and all the *_PASSWORD values. Use `pwgen 32 1` for each.
nano .env

# Bring up just the edge for now (Wazuh + Keycloak come in weeks 3–4):
cd infra
docker compose --env-file ../.env up -d caddy
docker compose logs -f caddy
```

Caddy will hit Let's Encrypt and provision certs on the fly. The first request can take 30–60 seconds while ACME runs.

Visit `https://<your-domain>` — should respond with "Project Ouroboros — lab is up..."

## Done conditions

- [ ] VM provisioned, SSH key-only, non-root user
- [ ] ufw allowing only 22/80/443
- [ ] Oracle security list updated to allow 80/443
- [ ] Docker + Compose installed, non-root user runs `docker ps` without sudo
- [ ] Domain resolves to the VM
- [ ] `make up` brings up Caddy successfully
- [ ] Visiting `https://<your-domain>` returns the placeholder over a valid TLS cert

## Common pitfalls

- **Caddy gets a Let's Encrypt rate-limit lockout.** Don't repeatedly bring it up/down while debugging — Let's Encrypt rate-limits failures per domain per week. If you hit it, switch to LE staging while debugging by adding `acme_ca https://acme-staging-v02.api.letsencrypt.org/directory` to the Caddyfile globals.
- **ufw enabled with no SSH rule.** Always `sudo ufw allow 22/tcp` *before* `sudo ufw enable`. Otherwise you lock yourself out and need the console serial port to recover.
- **Oracle's `iptables-persistent` reloads on reboot and undoes ufw.** Save rules after configuring ufw: `sudo netfilter-persistent save`.

## Next week

Week 3 stands up Wazuh — the largest single component. Read ahead.
