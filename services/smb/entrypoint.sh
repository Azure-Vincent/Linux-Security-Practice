#!/usr/bin/env bash
# Start cron (for beacon-style artifacts) and smbd in the foreground.
set -euo pipefail

mkdir -p /srv/docs /var/log/samba
service cron start 2>/dev/null || cron || true

echo "beaconhunt smb target up (hardened; awaiting plant)"
exec smbd --foreground --no-process-group
