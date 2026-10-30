<?php
// Benign status endpoint (part of the baseline app).
header('Content-Type: text/plain');
echo "acme-intranet ok\n";
echo "time: " . date('c') . "\n";
