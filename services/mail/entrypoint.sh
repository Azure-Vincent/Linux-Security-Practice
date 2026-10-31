#!/usr/bin/env bash
# Start syslog, Postfix, Dovecot and cron best-effort, then keep PID 1 alive.
# Not -e: one service failing to start must not abort the whole container, so
# the range (whose findings are detected from files) still stands up.
set -uo pipefail

service rsyslog start 2>/dev/null || true
service postfix start 2>/dev/null || postfix start 2>/dev/null || true
service dovecot start 2>/dev/null || dovecot 2>/dev/null || true
service cron start 2>/dev/null || cron || true

echo "beaconhunt mail target up (hardened; awaiting plant)"
exec tail -f /dev/null
