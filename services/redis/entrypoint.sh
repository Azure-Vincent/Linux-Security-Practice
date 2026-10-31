#!/usr/bin/env bash
# Start cron and redis-server best-effort, then keep PID 1 alive. Not -e so a
# bad config can't abort the container (findings are file/command-detected).
set -uo pipefail
service cron start 2>/dev/null || cron || true
(redis-server /etc/redis/redis.conf 2>/dev/null &) || true
echo "beaconhunt redis target up (hardened; awaiting plant)"
exec tail -f /dev/null
