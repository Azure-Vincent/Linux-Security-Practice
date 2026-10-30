#!/usr/bin/env bash
# Declawed plant: drop-in that re-enables PermitRootLogin.
#
# Within this disposable training container only. The hardened image default is
# PermitRootLogin no; this drop-in overrides it so a hunter can catch the
# effective-vs-file-config discrepancy with `sshd -T`.
set -euo pipefail

DROPIN_DIR="/etc/ssh/sshd_config.d"
DROPIN="$DROPIN_DIR/99-beaconhunt.conf"

mkdir -p "$DROPIN_DIR"
cat > "$DROPIN" <<'EOF'
# planted by BeaconHunt (training) — overrides hardened default
PermitRootLogin yes
EOF
chmod 644 "$DROPIN"
echo "wrote $DROPIN"
