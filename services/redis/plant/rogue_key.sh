#!/usr/bin/env bash
# Declawed plant: a rogue key holding attacker-controlled data, persisted to RDB.
set -euo pipefail
PASS="${REDIS_PASSWORD:-beaconhunt-redis}"
rc() { redis-cli -a "$PASS" --no-auth-warning "$@" 2>/dev/null || redis-cli --no-auth-warning "$@" 2>/dev/null || true; }
rc SET beaconhunt:backdoor "attacker-note: planted rogue key (training)" >/dev/null
rc SAVE >/dev/null
echo "set rogue key 'beaconhunt:backdoor'"
