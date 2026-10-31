#!/usr/bin/env bash
# Start cron and sshd in the foreground. (systemd is not PID 1 in a container,
# so planted systemd units are inspected on disk rather than via systemctl.)
set -euo pipefail

ssh-keygen -A >/dev/null 2>&1 || true
service cron start 2>/dev/null || cron || true

echo "beaconhunt host target up (hardened; awaiting plant)"
exec /usr/sbin/sshd -D -e
