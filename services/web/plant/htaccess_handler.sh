#!/usr/bin/env bash
# Declawed plant: a .htaccess that makes image files execute as PHP.
#
# Within this training container only. The file is the detectable condition;
# whether Apache honors it depends on AllowOverride, but the hunt is about
# finding the rogue handler override in a writable upload dir.
set -euo pipefail

DIR=/var/www/html/uploads
mkdir -p "$DIR"
cat > "$DIR/.htaccess" <<'HT'
# beaconhunt-htaccess (training) — makes uploaded images run as PHP
AddType application/x-httpd-php .jpg .png
HT
chmod 644 "$DIR/.htaccess"
echo "wrote $DIR/.htaccess"
