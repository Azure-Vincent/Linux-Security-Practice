#!/usr/bin/env bash
# Start cron (for beacon-style artifacts) and Apache in the foreground.
set -euo pipefail

service cron start 2>/dev/null || cron || true

echo "beaconhunt web target up (hardened; awaiting plant)"
exec apache2-foreground
