#!/usr/bin/env bash
# Declawed plant: an FTP account with a weak password.
set -euo pipefail
U=ftpuser; P=ftpuser123
id "$U" >/dev/null 2>&1 || useradd -m -d /srv/ftp/ftpuser -s /usr/sbin/nologin "$U"
echo "${U}:${P}" | chpasswd
echo "created weak FTP user '$U'"
