#!/usr/bin/env bash
# Declawed plant: a mailbox account with a weak password.
set -euo pipefail
U=mailtest; P=welcome1
id "$U" >/dev/null 2>&1 || useradd -m -s /usr/sbin/nologin "$U"
echo "${U}:${P}" | chpasswd
maildirmake.dovecot "/home/$U/Maildir" >/dev/null 2>&1 || true
chown -R "$U:$U" "/home/$U" 2>/dev/null || true
echo "created weak mailbox user '$U'"
