#!/usr/bin/env bash
# Declawed plant: append a training public key to root's authorized_keys.
#
# The key is a throwaway generated in-container purely so the authorized_keys
# line looks real to a hunter. Its comment carries an obvious training marker,
# and no corresponding private key is retained, so it is not a usable
# credential outside this disposable container.
set -euo pipefail

MARKER="beaconhunt-trainingkey"
AK="/root/.ssh/authorized_keys"

mkdir -p /root/.ssh
chmod 700 /root/.ssh
touch "$AK"
chmod 600 "$AK"

if grep -q "$MARKER" "$AK" 2>/dev/null; then
  echo "authorized_keys backdoor already present"
  exit 0
fi

# Generate a disposable key just to obtain a syntactically real public key,
# then discard the private half immediately.
tmp="$(mktemp -d)"
ssh-keygen -t ed25519 -N '' -C "$MARKER" -f "$tmp/k" >/dev/null
cat "$tmp/k.pub" >> "$AK"
shred -u "$tmp/k" 2>/dev/null || rm -f "$tmp/k"
rm -rf "$tmp"

echo "appended training key to $AK"
