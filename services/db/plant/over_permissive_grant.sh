#!/usr/bin/env bash
# Declawed plant: the least-privilege app user is over-granted to *.* ALL.
set -euo pipefail
mariadb -uroot -p"${MARIADB_ROOT_PASSWORD:-beaconhunt-root}" <<'SQL'
GRANT ALL PRIVILEGES ON *.* TO 'webapp'@'%';
FLUSH PRIVILEGES;
SQL
echo "over-granted 'webapp'@'%' to ALL PRIVILEGES on *.*"
