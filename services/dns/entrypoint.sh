#!/usr/bin/env bash
# Start cron and named best-effort, then keep PID 1 alive. Not -e: if named
# refuses a config the container still stays up (findings are file-detected).
set -uo pipefail
service cron start 2>/dev/null || cron || true
(/usr/sbin/named -u bind -c /etc/bind/named.conf 2>/dev/null &) || true
echo "beaconhunt dns target up (hardened; awaiting plant)"
exec tail -f /dev/null
