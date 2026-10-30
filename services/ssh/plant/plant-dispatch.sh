#!/usr/bin/env bash
# Plant dispatcher — runs inside the SSH training container.
#
# Usage: plant-dispatch.sh <artifact-id> [<artifact-id> ...]
#
# Maps a BeaconHunt catalog artifact id to the declawed planting script that
# installs its detectable (but neutered) training artifact. Idempotent: each
# planter can be run repeatedly without stacking duplicates.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

plant_one() {
  local id="$1"
  case "$id" in
    ssh-authorized-keys-backdoor) "$HERE/authorized_keys_backdoor.sh" ;;
    ssh-permit-root-login)        "$HERE/permit_root_login.sh" ;;
    ssh-weak-shared-cred)         "$HERE/weak_shared_cred.sh" ;;
    ssh-malicious-sshrc)          "$HERE/malicious_sshrc.sh" ;;
    ssh-beacon-cron)              "$HERE/beacon_cron.sh" ;;
    *)
      echo "plant-dispatch: unknown artifact id '$id'" >&2
      return 2
      ;;
  esac
  echo "planted: $id"
}

if [[ $# -eq 0 ]]; then
  echo "usage: plant-dispatch.sh <artifact-id> [...]" >&2
  exit 1
fi

for id in "$@"; do
  plant_one "$id"
done

# Reload sshd so config/drop-in changes take effect, if it is managed here.
if command -v service >/dev/null 2>&1; then
  service ssh reload 2>/dev/null || true
fi
