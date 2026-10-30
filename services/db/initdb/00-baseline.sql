-- BeaconHunt baseline schema (hardened). Loaded once on first container init.
-- The range becomes "vulnerable" only when BeaconHunt plants findings on top.

CREATE DATABASE IF NOT EXISTS acme;

USE acme;

CREATE TABLE IF NOT EXISTS orders (
  id   INT PRIMARY KEY AUTO_INCREMENT,
  item VARCHAR(64),
  qty  INT
);
INSERT INTO orders (item, qty) VALUES ('widget', 3), ('gadget', 1);

-- Least-privilege application account. Its password intentionally matches the
-- one leaked by the web service's exposed config backup (cross-service story).
CREATE USER IF NOT EXISTS 'webapp'@'%' IDENTIFIED BY 'Pa55w0rd!';
GRANT SELECT, INSERT, UPDATE, DELETE ON acme.* TO 'webapp'@'%';

FLUSH PRIVILEGES;
