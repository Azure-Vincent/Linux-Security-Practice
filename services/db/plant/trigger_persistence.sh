#!/usr/bin/env bash
# Declawed plant: a persistence trigger. A real one can't run GRANT/DDL in
# MySQL/MariaDB, so attackers use triggers to re-seed rows; this one writes a
# marker into a shadow table on every insert — the detectable condition is an
# unexpected trigger, which is exactly what a hunter looks for.
set -euo pipefail
mariadb -uroot -p"${MARIADB_ROOT_PASSWORD:-beaconhunt-root}" <<'SQL'
USE acme;
CREATE TABLE IF NOT EXISTS audit_shadow (
  id INT AUTO_INCREMENT PRIMARY KEY,
  note VARCHAR(128),
  ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
DROP TRIGGER IF EXISTS beaconhunt_persist;
DELIMITER $$
CREATE TRIGGER beaconhunt_persist AFTER INSERT ON orders
FOR EACH ROW
BEGIN
  INSERT INTO audit_shadow(note) VALUES ('beaconhunt-trigger-persist');
END$$
DELIMITER ;
SQL
echo "installed trigger 'beaconhunt_persist' on acme.orders"
