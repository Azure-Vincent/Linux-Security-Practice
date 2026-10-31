#!/usr/bin/env bash
# Plant dispatcher — runs inside the mail training container.
#
# Usage: plant-dispatch.sh <artifact-id> [<artifact-id> ...]
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

plant_one() {
  case "$1" in
    mail-open-relay)         "$HERE/open_relay.sh" ;;
    mail-weak-mailbox-cred)  "$HERE/weak_mailbox_cred.sh" ;;
    mail-alias-backdoor)     "$HERE/alias_backdoor.sh" ;;
    mail-forward-exfil)      "$HERE/forward_exfil.sh" ;;
    mail-cron-beacon)        "$HERE/beacon_cron.sh" ;;
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
