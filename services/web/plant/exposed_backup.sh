#!/usr/bin/env bash
# Declawed plant: a stale config backup left in the webroot.
#
# config.php.bak is served as plaintext (the .bak extension isn't parsed by
# PHP), leaking database credentials. The credentials are training-only and
# used by the planted DB service account if present.
set -euo pipefail

cat > /var/www/html/config.php.bak <<'BAK'
<?php
// beaconhunt-exposed (training) — stale backup, served as plaintext
define('DB_HOST', 'db');
define('DB_USER', 'webapp');
define('DB_PASS', 'Pa55w0rd!');   // leaked via an exposed .bak file
BAK
chmod 644 /var/www/html/config.php.bak
echo "wrote /var/www/html/config.php.bak"
