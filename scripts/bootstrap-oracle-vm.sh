#!/usr/bin/env bash
# Bootstrap a fresh Oracle Ubuntu 24.04 ARM VM for Project Healyx.
# Run as the default ubuntu user. Reboots once partway through.
#
# Usage:  curl ... | bash   OR   ./bootstrap-oracle-vm.sh

set -euo pipefail

echo "=== 1. system update ==="
sudo apt update && sudo apt upgrade -y

echo "=== 2. install deps ==="
sudo apt install -y \
  ca-certificates curl gnupg ufw \
  iptables-persistent jq pwgen git make

echo "=== 3. Docker via official convenience script ==="
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker "$USER"

echo "=== 4. firewall ==="
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# Clear Oracle's default-deny iptables that fight ufw
sudo iptables -F INPUT
sudo netfilter-persistent save

echo "=== 5. sysctl tweaks for Wazuh indexer ==="
echo "vm.max_map_count=262144" | sudo tee /etc/sysctl.d/99-healyx.conf
sudo sysctl --system

echo "=== 6. install yq (for YAML editing in shell) ==="
sudo snap install yq

echo
echo "=== DONE — please log out and back in (group membership) ==="
echo "Then:"
echo "  git clone https://github.com/justinkok28/Healyx.git"
echo "  cd Healyx && cp .env.example .env && nano .env"
echo "  make up"
