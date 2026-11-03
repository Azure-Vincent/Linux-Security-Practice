#!/usr/bin/env bash
# Install a desktop entry so BeaconHunt Launcher appears in the app menu and on
# the Desktop, launching with no terminal. Safe to re-run.
set -euo pipefail

HERE="$(cd "$(dirname "$(readlink -f "$0" 2>/dev/null || echo "$0")")" && pwd)"
chmod +x "$HERE/run-launcher.sh"

APPS="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
mkdir -p "$APPS"
DESK="$APPS/beaconhunt-launcher.desktop"

cat > "$DESK" <<DESKTOP
[Desktop Entry]
Type=Application
Version=1.0
Name=BeaconHunt Launcher
Comment=Launch a BeaconHunt training range — no terminal needed
Exec=$HERE/run-launcher.sh
Icon=security-high
Terminal=false
Categories=Security;Education;System;
DESKTOP
chmod 644 "$DESK"
update-desktop-database "$APPS" >/dev/null 2>&1 || true

# Also place a launcher on the Desktop, if there is one.
DESKTOP_DIR="$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")"
if [ -d "$DESKTOP_DIR" ]; then
  cp "$DESK" "$DESKTOP_DIR/beaconhunt-launcher.desktop"
  chmod +x "$DESKTOP_DIR/beaconhunt-launcher.desktop" 2>/dev/null || true
  # GNOME: mark as trusted so it runs on double-click.
  gio set "$DESKTOP_DIR/beaconhunt-launcher.desktop" metadata::trusted true 2>/dev/null || true
fi

echo "Installed. Look for 'BeaconHunt Launcher' in your applications menu"
echo "(and on your Desktop). It launches with no terminal window."
