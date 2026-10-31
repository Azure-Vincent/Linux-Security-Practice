#!/usr/bin/env bash
# Start cron and vsftpd best-effort, then keep PID 1 alive. Not -e: if vsftpd
# refuses a config the container still stays up (findings are file-detected).
set -uo pipefail

mkdir -p /var/run/vsftpd/empty /srv/ftp
service cron start 2>/dev/null || cron || true
vsftpd /etc/vsftpd.conf &

echo "beaconhunt ftp target up (hardened; awaiting plant)"
exec tail -f /dev/null
