#!/usr/bin/env bash
# Declawed plant: a malicious-looking script uploaded to the FTP area.
# Carries the signature a hunter greps for; execution is neutered (echo only).
set -euo pipefail
mkdir -p /srv/ftp/upload
cat > /srv/ftp/upload/update.sh <<'SH'
#!/bin/sh
# beaconhunt-ftp-payload (DECLAWED training artifact — does NOT execute anything)
echo "beaconhunt: ftp payload stub — disabled"
SH
chmod 0777 /srv/ftp/upload/update.sh
echo "wrote /srv/ftp/upload/update.sh"
