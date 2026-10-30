#!/usr/bin/env bash
# Declawed plant: an unexpected SUID-root binary.
#
# A real SUID backdoor would be a shell or GTFOBins-abusable binary that grants
# instant root. This training version is a copy of /bin/true with the SUID bit
# set — it is detectable exactly like the real thing (`find / -perm -4000`) but
# does nothing when run, so it is not an actual privilege-escalation path.
set -euo pipefail

BIN=/usr/local/bin/sysdiag
cp /bin/true "$BIN"
chown root:root "$BIN"
chmod 4755 "$BIN"          # SUID root — the detectable condition
echo "installed SUID-root $BIN (declawed copy of /bin/true)"
