#!/usr/bin/env bash
# Declawed plant: a rogue login account added out-of-band (baseline deviation).
#
# A regular, login-capable user that is NOT part of the box's provisioned
# population — the tell a defender catches by diffing /etc/passwd + /etc/shadow
# against a baseline (odd UID, latest last-change date, mismatched hash algo).
# The GECOS field carries a training marker; the password is training-only.
set -euo pipefail

U="iris.wood"
if ! id "$U" >/dev/null 2>&1; then
  useradd -m -s /bin/bash -u 1337 -c "beaconhunt-rogue-acct" "$U" 2>/dev/null \
    || useradd -m -s /bin/bash -c "beaconhunt-rogue-acct" "$U"
fi
echo "${U}:Autumn2026!" | chpasswd
chage -M -1 "$U" 2>/dev/null || true   # no expiry, like a neglected account
echo "added rogue login account $U"
