#!/usr/bin/env bash
# Plant dispatcher — runs inside the FTP training container.
#
# Usage: plant-dispatch.sh <artifact-id> [<artifact-id> ...]
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

plant_one() {
  case "$1" in
    ftp-anonymous-writable) "$HERE/anonymous_writable.sh" ;;
    ftp-weak-cred)          "$HERE/weak_cred.sh" ;;
    ftp-planted-backdoor)   "$HERE/planted_backdoor.sh" ;;
    ftp-no-chroot)          "$HERE/no_chroot.sh" ;;
    ftp-cron-beacon)        "$HERE/beacon_cron.sh" ;;
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

# Restart vsftpd to pick up config changes (best-effort).
pkill -x vsftpd >/dev/null 2>&1 || true
( vsftpd /etc/vsftpd.conf & ) >/dev/null 2>&1 || true
