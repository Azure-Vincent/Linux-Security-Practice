#!/usr/bin/env bash
# Declawed plant: a rogue superuser account (contained to this training DB).
set -euo pipefail
mariadb -uroot -p"${MARIADB_ROOT_PASSWORD:-beaconhunt-root}" <<'SQL'
CREATE USER IF NOT EXISTS 'dbsupport'@'%' IDENTIFIED BY 'S3rvice!';
GRANT ALL PRIVILEGES ON *.* TO 'dbsupport'@'%' WITH GRANT OPTION;
FLUSH PRIVILEGES;
SQL
echo "created rogue admin 'dbsupport'@'%'"
