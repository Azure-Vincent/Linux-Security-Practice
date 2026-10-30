#!/usr/bin/env bash
# Declawed plant: a share whose 'root preexec' runs a script as root on connect.
# The script is neutered (logs a marker); the detectable condition is the
# root-preexec directive plus an unexpected root-run script.
set -euo pipefail
mkdir -p /etc/samba/scripts /srv/backup
cat > /etc/samba/scripts/onconnect.sh <<'SH'
#!/bin/sh
# beaconhunt-preexec (DECLAWED training hook — logs only, runs as root on connect)
echo "$(date -u +%FT%TZ) onconnect $USER" >> /var/log/beaconhunt-smb.log 2>/dev/null || true
SH
chmod 0755 /etc/samba/scripts/onconnect.sh
if ! grep -q "beaconhunt-preexec-share" /etc/samba/smb.conf; then
cat >> /etc/samba/smb.conf <<'CONF'

# beaconhunt-preexec-share (training) — runs a script as root on every connect
[backup]
   path = /srv/backup
   guest ok = yes
   root preexec = /etc/samba/scripts/onconnect.sh
CONF
fi
echo "added [backup] share with root preexec backdoor"
