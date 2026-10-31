#!/usr/bin/env bash
# Declawed plant: the classic Redis -> SSH key persistence outcome. A real
# attack uses CONFIG SET dir/dbfilename + SET + SAVE to drop an authorized_keys.
# Here we write the resulting (fake, non-usable) key file directly.
set -euo pipefail
mkdir -p /root/.ssh
chmod 700 /root/.ssh
cat > /root/.ssh/authorized_keys <<'K'
# beaconhunt-redis-persist (training) — key written via Redis CONFIG SET dir/dbfilename
ssh-ed25519 AAAATRAINING-NOT-A-REAL-KEY beaconhunt-redis-persist
K
chmod 600 /root/.ssh/authorized_keys
echo "wrote /root/.ssh/authorized_keys (redis persistence)"
