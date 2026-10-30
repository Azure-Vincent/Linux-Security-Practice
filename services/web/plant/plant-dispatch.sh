#!/usr/bin/env bash
# Plant dispatcher — runs inside the web training container.
#
# Usage: plant-dispatch.sh <artifact-id> [<artifact-id> ...]
# Maps a BeaconHunt web catalog artifact id to its declawed planting script.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

plant_one() {
  case "$1" in
    web-php-webshell)         "$HERE/php_webshell.sh" ;;
    web-htaccess-handler)     "$HERE/htaccess_handler.sh" ;;
    web-exposed-backup-creds) "$HERE/exposed_backup.sh" ;;
    web-cron-beacon)          "$HERE/beacon_cron.sh" ;;
    web-suid-backdoor)        "$HERE/suid_backdoor.sh" ;;
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
