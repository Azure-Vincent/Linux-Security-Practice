#!/usr/bin/env bash
# Declawed plant: an /etc/aliases entry that pipes mail to a command on
# delivery (classic mail persistence). The hook is neutered (logs only).
set -euo pipefail
cat > /usr/local/bin/mailhook.sh <<'SH'
#!/bin/sh
# beaconhunt-mailhook (DECLAWED training hook — logs only, no payload)
cat >> /var/log/beaconhunt-mail.log 2>/dev/null || true
SH
chmod 0755 /usr/local/bin/mailhook.sh
if ! grep -q 'beaconhunt-alias' /etc/aliases 2>/dev/null; then
cat >> /etc/aliases <<'AL'
# beaconhunt-alias (training) — pipes mail to a command on delivery
support: "|/usr/local/bin/mailhook.sh"
AL
fi
newaliases >/dev/null 2>&1 || true
echo "added alias pipe backdoor to /etc/aliases"
