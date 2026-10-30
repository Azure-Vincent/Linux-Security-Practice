#!/usr/bin/env bash
# Plant dispatcher — runs inside the SMB training container.
#
# Usage: plant-dispatch.sh <artifact-id> [<artifact-id> ...]
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

plant_one() {
  case "$1" in
    smb-guest-writable-share)   "$HERE/guest_writable_share.sh" ;;
    smb-planted-dropzone)       "$HERE/planted_dropzone.sh" ;;
    smb-weak-smb-user)          "$HERE/weak_smb_user.sh" ;;
    smb-root-preexec)           "$HERE/root_preexec.sh" ;;
    smb-cron-beacon)            "$HERE/beacon_cron.sh" ;;
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

# Pick up any smb.conf changes.
smbcontrol all reload-config >/dev/null 2>&1 || true
