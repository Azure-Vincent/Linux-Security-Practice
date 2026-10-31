#!/usr/bin/env bash
# Declawed plant: a weak/known TSIG key usable for unauthorized dynamic updates.
set -euo pipefail
cat > /etc/bind/ddns.key <<'KEY'
# beaconhunt-weakkey (training) — weak, publicly-known TSIG key
key "ddns-key" {
    algorithm hmac-sha256;
    secret "MDAwMDAwMDAwMDAwMDAwMA==";
};
KEY
chmod 644 /etc/bind/ddns.key
echo "wrote weak TSIG key /etc/bind/ddns.key"
