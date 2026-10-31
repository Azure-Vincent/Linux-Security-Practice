#!/usr/bin/env bash
# Plant dispatcher — runs inside the Redis training container.
# Usage: plant-dispatch.sh <artifact-id> [<artifact-id> ...]
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
plant_one() {
  case "$1" in
    redis-no-auth)              "$HERE/no_auth.sh" ;;
    redis-weak-password)        "$HERE/weak_password.sh" ;;
    redis-rogue-key)            "$HERE/rogue_key.sh" ;;
    redis-ssh-key-persistence)  "$HERE/ssh_key_persistence.sh" ;;
    redis-cron-beacon)          "$HERE/beacon_cron.sh" ;;
    *) echo "plant-dispatch: unknown artifact id '$1'" >&2; return 2 ;;
  esac
  echo "planted: $1"
}
[[ $# -eq 0 ]] && { echo "usage: plant-dispatch.sh <artifact-id> [...]" >&2; exit 1; }
for id in "$@"; do plant_one "$id"; done
# Restart redis to apply config changes (best-effort).
pkill -x redis-server >/dev/null 2>&1 || true
(redis-server /etc/redis/redis.conf 2>/dev/null &) || true
