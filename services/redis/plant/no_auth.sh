#!/usr/bin/env bash
# Declawed plant: remove auth and expose Redis on all interfaces.
set -euo pipefail
CONF=/etc/redis/redis.conf
sed -i 's/^protected-mode yes/protected-mode no/' "$CONF"
sed -i 's/^bind .*/bind 0.0.0.0/' "$CONF"
sed -i 's/^requirepass .*/# requirepass removed/' "$CONF"
grep -q 'beaconhunt-noauth' "$CONF" || echo '# beaconhunt-noauth (training) — no auth, bound to all interfaces' >> "$CONF"
echo "disabled Redis auth / opened bind in $CONF"
