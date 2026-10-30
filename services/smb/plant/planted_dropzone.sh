#!/usr/bin/env bash
# Declawed plant: a malicious-looking script left in the writable share.
# Carries the signature a hunter greps for; execution is neutered (echo only).
set -euo pipefail
mkdir -p /srv/public
cat > /srv/public/update.sh <<'SH'
#!/bin/sh
# beaconhunt-smb-payload (DECLAWED training artifact — does NOT execute anything)
# A real dropped payload would fetch and run a stage here.
echo "beaconhunt: smb payload stub — disabled"
SH
chmod 0777 /srv/public/update.sh
echo "wrote /srv/public/update.sh"
