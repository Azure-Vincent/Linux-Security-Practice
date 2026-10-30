#!/usr/bin/env bash
# Plant dispatcher — runs inside the DB training container.
#
# Usage: plant-dispatch.sh <artifact-id> [<artifact-id> ...]
# Waits for MariaDB to accept connections, then applies the declawed SQL for
# each selected finding.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export MARIADB_ROOT_PASSWORD="${MARIADB_ROOT_PASSWORD:-beaconhunt-root}"

# Wait until the server is up (first boot runs initdb and can take a while).
echo "waiting for MariaDB…"
for _ in $(seq 1 60); do
  if mariadb -uroot -p"$MARIADB_ROOT_PASSWORD" -e 'SELECT 1' >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

plant_one() {
  case "$1" in
    db-rogue-admin-user)      "$HERE/rogue_admin.sh" ;;
    db-root-remote-weak)      "$HERE/root_remote_weak.sh" ;;
    db-over-permissive-grant) "$HERE/over_permissive_grant.sh" ;;
    db-file-privilege)        "$HERE/file_privilege.sh" ;;
    db-trigger-persistence)   "$HERE/trigger_persistence.sh" ;;
    *)
      echo "plant-dispatch: unknown artifact id '$1'" >&2
      return 2
      ;;
  esac
  echo "planted: $1"
}

if [[ $# -eq 0 ]]; then
  echo "usage: plant-dispatch.sh <artifact-id> [...]" >&2
  exit 1
fi

for id in "$@"; do
  plant_one "$id"
done
