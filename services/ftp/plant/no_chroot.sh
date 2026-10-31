#!/usr/bin/env bash
# Declawed plant: disable chroot so local users can browse the whole filesystem.
set -euo pipefail
CONF=/etc/vsftpd.conf
if ! grep -q 'beaconhunt-nochroot' "$CONF"; then
cat >> "$CONF" <<'CFG'

# beaconhunt-nochroot (training) — users escape their home to the whole FS
chroot_local_user=NO
CFG
fi
echo "disabled chroot_local_user in $CONF"
