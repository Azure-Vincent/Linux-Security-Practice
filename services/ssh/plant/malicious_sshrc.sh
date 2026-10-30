#!/usr/bin/env bash
# Declawed plant: /etc/ssh/sshrc persistence hook.
#
# A real sshrc backdoor would execute a payload or log keystrokes on every
# login. This training version only appends a timestamped marker to a local
# training log, so it carries the exact signature a hunter looks for without
# doing anything harmful.
set -euo pipefail

SSHRC="/etc/ssh/sshrc"
cat > "$SSHRC" <<'EOF'
#!/bin/sh
# beaconhunt-sshrc-marker  (declawed training hook — logs only, no payload)
echo "$(date -u +%FT%TZ) sshrc fired for ${USER:-unknown}" \
    >> /var/log/beaconhunt-sshrc.log 2>/dev/null || true
EOF
chmod 755 "$SSHRC"
echo "wrote $SSHRC"
