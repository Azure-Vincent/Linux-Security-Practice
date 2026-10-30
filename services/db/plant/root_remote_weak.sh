#!/usr/bin/env bash
# Declawed plant: root reachable from any host with a weak password.
set -euo pipefail
mariadb -uroot -p"${MARIADB_ROOT_PASSWORD:-beaconhunt-root}" <<'SQL'
CREATE USER IF NOT EXISTS 'root'@'%' IDENTIFIED BY 'toor';
GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION;
FLUSH PRIVILEGES;
SQL
echo "created weak remote 'root'@'%'"
