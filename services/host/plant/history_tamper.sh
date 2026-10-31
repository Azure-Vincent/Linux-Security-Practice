#!/usr/bin/env bash
# Declawed plant: shell-history / anti-forensics tampering.
set -euo pipefail
mkdir -p /etc/profile.d
cat > /etc/profile.d/00-history.sh <<'SH'
# beaconhunt-histoff (training) — disables shell history (anti-forensics)
unset HISTFILE
export HISTSIZE=0
export HISTFILESIZE=0
SH
chmod 644 /etc/profile.d/00-history.sh
ln -sf /dev/null /root/.bash_history
echo "disabled shell history and nulled /root/.bash_history"
