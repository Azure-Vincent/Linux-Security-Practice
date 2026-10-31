#!/usr/bin/env bash
# Declawed plant: a rogue A record hijacking an internal hostname to an
# attacker-controlled IP (a private, non-routable address here).
set -euo pipefail
ZONE=/etc/bind/db.acme.local
if ! grep -q 'beaconhunt-rogue' "$ZONE"; then
  echo 'vpn     IN      A       10.66.66.66     ; beaconhunt-rogue (hijacked record)' >> "$ZONE"
fi
echo "added rogue A record to $ZONE"
