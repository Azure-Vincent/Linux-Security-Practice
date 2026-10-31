#!/usr/bin/env bash
# Declawed plant: reconfigure Postfix as an open relay (within this container).
set -euo pipefail
MAIN=/etc/postfix/main.cf
touch "$MAIN"
if ! grep -q 'beaconhunt-relay' "$MAIN"; then
cat >> "$MAIN" <<'CONF'

# beaconhunt-relay (training) — turns Postfix into an OPEN RELAY
mynetworks = 0.0.0.0/0
smtpd_relay_restrictions = permit_mynetworks
CONF
fi
postfix reload >/dev/null 2>&1 || service postfix reload >/dev/null 2>&1 || true
echo "configured open relay in $MAIN"
