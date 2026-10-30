#!/usr/bin/env bash
# Declawed plant: create a service account with a weak password.
#
# Within this disposable training container only. The account is a hunting
# target; the weak password is intentional and never reused anywhere real.
set -euo pipefail

USER_NAME="svc-backup"
WEAK_PASS="Summer2024"   # intentionally weak, training-only

if id "$USER_NAME" >/dev/null 2>&1; then
  echo "account $USER_NAME already present"
else
  useradd -m -s /bin/bash -c "backup service (planted)" "$USER_NAME"
  echo "created account $USER_NAME"
fi

echo "${USER_NAME}:${WEAK_PASS}" | chpasswd
# Make the hash non-expiring to mimic a neglected service account.
chage -M -1 "$USER_NAME" 2>/dev/null || true
echo "set weak password on $USER_NAME"
