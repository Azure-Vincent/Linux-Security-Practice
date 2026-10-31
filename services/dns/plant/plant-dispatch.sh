#!/usr/bin/env bash
# Plant dispatcher — runs inside the DNS training container.
# Usage: plant-dispatch.sh <artifact-id> [<artifact-id> ...]
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
plant_one() {
  case "$1" in
    dns-zone-transfer-any) "$HERE/zone_transfer_any.sh" ;;
    dns-open-recursion)    "$HERE/open_recursion.sh" ;;
    dns-rogue-record)      "$HERE/rogue_record.sh" ;;
    dns-weak-rndc-key)     "$HERE/weak_rndc_key.sh" ;;
    dns-cron-beacon)       "$HERE/beacon_cron.sh" ;;
    *) echo "plant-dispatch: unknown artifact id '$1'" >&2; return 2 ;;
  esac
  echo "planted: $1"
}
[[ $# -eq 0 ]] && { echo "usage: plant-dispatch.sh <artifact-id> [...]" >&2; exit 1; }
for id in "$@"; do plant_one "$id"; done
# Reload named (best-effort) to pick up config/zone changes.
rndc reload >/dev/null 2>&1 || { pkill -x named >/dev/null 2>&1 || true; (/usr/sbin/named -u bind -c /etc/bind/named.conf 2>/dev/null &) || true; }
