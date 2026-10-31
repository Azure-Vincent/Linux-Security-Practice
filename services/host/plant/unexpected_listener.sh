#!/usr/bin/env bash
# Declawed plant: an unexpected listening service on tcp/4444.
# A real finding here might be a bind shell; this listener just accepts and
# discards connections (no shell), so it is the detectable condition only.
set -euo pipefail
if ! ss -tlnp 2>/dev/null | grep -q ':4444'; then
  setsid sh -c 'socat TCP-LISTEN:4444,fork,reuseaddr /dev/null' >/dev/null 2>&1 &
fi
sleep 0.3
echo "started benign listener on tcp/4444 (declawed)"
