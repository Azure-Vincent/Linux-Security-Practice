#!/usr/bin/env bash
# Declawed plant: a user with the FILE privilege (server-side file read/write).
set -euo pipefail
mariadb -uroot -p"${MARIADB_ROOT_PASSWORD:-beaconhunt-root}" <<'SQL'
CREATE USER IF NOT EXISTS 'report'@'%' IDENTIFIED BY 'Rep0rt!';
GRANT FILE ON *.* TO 'report'@'%';
GRANT SELECT ON acme.* TO 'report'@'%';
FLUSH PRIVILEGES;
SQL
echo "granted FILE privilege to 'report'@'%'"
