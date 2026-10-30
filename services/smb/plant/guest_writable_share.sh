#!/usr/bin/env bash
# Declawed plant: an anonymous, world-writable share (classic bad smb.conf).
set -euo pipefail
mkdir -p /srv/public
chmod 0777 /srv/public
if ! grep -q "beaconhunt-public" /etc/samba/smb.conf; then
cat >> /etc/samba/smb.conf <<'CONF'

# beaconhunt-public (training) — anonymous, world-writable drop share
[public]
   path = /srv/public
   guest ok = yes
   browseable = yes
   writable = yes
   force user = root
CONF
fi
echo "added world-writable guest share [public] -> /srv/public"
