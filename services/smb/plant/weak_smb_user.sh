#!/usr/bin/env bash
# Declawed plant: a Samba account with a weak password.
set -euo pipefail
USER_NAME="share"
WEAK="share123"
id "$USER_NAME" >/dev/null 2>&1 || useradd -M -s /usr/sbin/nologin "$USER_NAME"
printf '%s\n%s\n' "$WEAK" "$WEAK" | smbpasswd -s -a "$USER_NAME" >/dev/null 2>&1 || true
smbpasswd -e "$USER_NAME" >/dev/null 2>&1 || true
echo "created weak Samba user '$USER_NAME'"
