"""BeaconHunt — a self-contained, defensive-security training range.

BeaconHunt plants a randomized set of intentionally-weak, *declawed* artifacts
(backdoors, beacons, persistence, misconfigs, weak creds, privesc) into
disposable containers it manages itself, then grades a defender's ability to
find them.

Hard scope rules (see beaconhunt.safety):
  * Everything runs against localhost or containers BeaconHunt spins up itself.
  * "Beacons" call back only to a local sink container, never the internet.
  * Planted artifacts are training stubs: realistic to hunt by signature,
    but neutered so they are not functioning weapons.

This is for authorized, defensive training on systems you own.
"""

__version__ = "0.1.0"
__all__ = ["__version__"]
