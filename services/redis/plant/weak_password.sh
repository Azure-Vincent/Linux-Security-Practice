#!/usr/bin/env bash
# Declawed plant: set a weak Redis password.
set -euo pipefail
CONF=/etc/redis/redis.conf
if grep -q '^requirepass' "$CONF"; then
  sed -i 's/^requirepass .*/requirepass foobared  # beaconhunt-weakpass/' "$CONF"
else
  echo 'requirepass foobared  # beaconhunt-weakpass' >> "$CONF"
fi
echo "set weak Redis password in $CONF"
