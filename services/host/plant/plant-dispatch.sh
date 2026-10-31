#!/usr/bin/env bash
# Plant dispatcher — runs inside the host training container.
#
# Usage: plant-dispatch.sh <artifact-id> [<artifact-id> ...]
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

plant_one() {
  case "$1" in
    host-uid0-account)        "$HERE/uid0_account.sh" ;;
    host-sudoers-nopasswd)    "$HERE/sudoers_nopasswd.sh" ;;
    host-rogue-systemd-timer) "$HERE/systemd_timer.sh" ;;
    host-history-tamper)      "$HERE/history_tamper.sh" ;;
    host-unexpected-listener) "$HERE/unexpected_listener.sh" ;;
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
