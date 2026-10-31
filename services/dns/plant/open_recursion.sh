#!/usr/bin/env bash
# Declawed plant: turn the server into an open resolver.
set -euo pipefail
OPT=/etc/bind/named.conf.options
sed -i 's/recursion no;/recursion yes;  \/\/ beaconhunt-recursion/' "$OPT"
grep -q 'allow-recursion' "$OPT" || sed -i 's/\(recursion yes;.*\)/\1\n    allow-recursion { any; };/' "$OPT"
echo "enabled open recursion in $OPT"
