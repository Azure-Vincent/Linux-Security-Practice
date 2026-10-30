#!/usr/bin/env bash
# Start cron (for beacon-style artifacts) and sshd in the foreground.
set -euo pipefail

ssh-keygen -A >/dev/null 2>&1 || true
service cron start 2>/dev/null || cron || true

echo "beaconhunt ssh target up (hardened; awaiting plant)"
exec /usr/sbin/sshd -D -e
