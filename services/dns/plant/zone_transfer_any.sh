#!/usr/bin/env bash
# Declawed plant: allow zone transfer (AXFR) from anyone.
set -euo pipefail
OPT=/etc/bind/named.conf.options
sed -i 's/allow-transfer { none; };/allow-transfer { any; };  \/\/ beaconhunt-axfr/' "$OPT"
grep -q 'beaconhunt-axfr' "$OPT" || echo '    allow-transfer { any; };  // beaconhunt-axfr' >> "$OPT"
echo "enabled AXFR from any in $OPT"
