#!/usr/bin/env bash
# Declawed plant: enable anonymous login with writable upload (within container).
set -euo pipefail
CONF=/etc/vsftpd.conf
mkdir -p /srv/ftp/upload
chmod 0777 /srv/ftp/upload
if ! grep -q 'beaconhunt-ftp-anon' "$CONF"; then
cat >> "$CONF" <<'CFG'

# beaconhunt-ftp-anon (training) — anonymous login + world-writable upload
anonymous_enable=YES
anon_upload_enable=YES
anon_mkdir_write_enable=YES
write_enable=YES
anon_root=/srv/ftp
allow_writeable_chroot=YES
CFG
fi
echo "enabled anonymous writable FTP in $CONF"
