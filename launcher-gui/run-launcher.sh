#!/usr/bin/env bash
# BeaconHunt Launcher — Linux/macOS entry point. Opens the GUI with no terminal
# (when started from a .desktop entry or the installer) and gives a clear
# message if a prerequisite is missing.
set -euo pipefail

HERE="$(cd "$(dirname "$(readlink -f "$0" 2>/dev/null || echo "$0")")" && pwd)"

notify() {  # best-effort graphical message, falls back to stderr
  local msg="$1"
  if command -v zenity >/dev/null 2>&1; then
    zenity --error --no-wrap --title="BeaconHunt Launcher" --text="$msg" 2>/dev/null
  elif command -v kdialog >/dev/null 2>&1; then
    kdialog --error "$msg" 2>/dev/null
  elif command -v notify-send >/dev/null 2>&1; then
    notify-send "BeaconHunt Launcher" "$msg"
  fi
  echo "$msg" >&2
}

PY="$(command -v python3 || command -v python || true)"
if [ -z "$PY" ]; then
  notify "Python 3.10+ is required but was not found. Please install Python 3."
  exit 1
fi

if ! "$PY" -c 'import tkinter' >/dev/null 2>&1; then
  notify "The launcher GUI needs Tk, which isn't installed.

Install it:
  Debian/Ubuntu:  sudo apt install python3-tk
  Fedora:         sudo dnf install python3-tkinter
  Arch:           sudo pacman -S tk

Then run the launcher again."
  exit 1
fi

cd "$HERE"
exec "$PY" "$HERE/beaconhunt_launcher.py" "$@"
