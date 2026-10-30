"""Top-level entry point for the launcher GUI (and the PyInstaller build).

Kept at the repo root so it imports the `beaconhunt` package normally; this is
what BeaconHunt.exe is built from.
"""

from beaconhunt.launcher import main

if __name__ == "__main__":
    raise SystemExit(main())
