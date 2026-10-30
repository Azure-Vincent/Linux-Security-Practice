#!/usr/bin/env bash
# Declawed plant: a PHP "web shell" dropped in the uploads directory.
#
# This carries the signatures a hunter greps for (an uploaded .php in a writable
# dir, the classic $_GET['cmd'] shape, a system() token) but the command
# execution is NEUTERED — it echoes a notice instead of running anything. It is
# a detection target, not a usable RCE.
set -euo pipefail

DIR=/var/www/html/uploads
mkdir -p "$DIR"
cat > "$DIR/up_8842.php" <<'PHP'
<?php
// beaconhunt-webshell (DECLAWED training artifact — does NOT execute input)
// A real uploaded web shell would run attacker-supplied commands, e.g.:
//     system($_GET['cmd']);     // <- intentionally neutered below
if (isset($_GET['cmd'])) {
    echo "beaconhunt: webshell stub — command execution is disabled\n";
}
echo "ok";
PHP
chmod 644 "$DIR/up_8842.php"
echo "wrote $DIR/up_8842.php"
