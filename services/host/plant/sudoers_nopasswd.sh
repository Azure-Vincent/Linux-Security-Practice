#!/usr/bin/env bash
# Declawed plant: a sudoers.d drop-in granting passwordless root to an account.
set -euo pipefail
id svcops >/dev/null 2>&1 || useradd -M -s /bin/bash svcops
cat > /etc/sudoers.d/99-beaconhunt <<'CONF'
# beaconhunt-sudoers (training) — passwordless root for a planted account
svcops ALL=(ALL) NOPASSWD:ALL
CONF
chmod 440 /etc/sudoers.d/99-beaconhunt
echo "wrote /etc/sudoers.d/99-beaconhunt (svcops NOPASSWD:ALL)"
