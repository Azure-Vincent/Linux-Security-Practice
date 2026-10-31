"""Scope enforcement for BeaconHunt.

BeaconHunt is only ever allowed to operate against:
  * the local loopback interface (127.0.0.0/8, ::1), or
  * Docker containers that BeaconHunt itself manages via its compose project.

Any attempt to point a BeaconHunt operation at an external / routable host is
refused here. This module is the single chokepoint every network-touching
operation must call. It is deliberately conservative: when in doubt, refuse.
"""

from __future__ import annotations

import ipaddress
import os
import socket
from dataclasses import dataclass

# The docker-compose project name. Containers BeaconHunt manages share this
# prefix; we never operate on a container outside it.
COMPOSE_PROJECT = os.environ.get("BEACONHUNT_PROJECT", "beaconhunt")

# Hostnames that always resolve to the local range / managed containers.
_ALLOWED_HOSTNAMES = {
    "localhost",
    "ip6-localhost",
    "ip6-loopback",
}


class ScopeViolation(RuntimeError):
    """Raised when an operation would touch something outside the allowed scope."""


@dataclass(frozen=True)
class ScopeDecision:
    allowed: bool
    target: str
    reason: str

    def enforce(self) -> "ScopeDecision":
        if not self.allowed:
            raise ScopeViolation(
                f"Refusing to target {self.target!r}: {self.reason}. "
                "BeaconHunt only operates against localhost and the containers "
                "it manages itself."
            )
        return self


def _is_loopback(ip: str) -> bool:
    try:
        return ipaddress.ip_address(ip).is_loopback
    except ValueError:
        return False


def _is_managed_container(host: str) -> bool:
    """A service name within the compose project (e.g. 'beaconhunt-ssh').

    Compose service DNS names are single labels or carry the project prefix.
    We only trust names that begin with the project prefix; a bare service
    name is accepted only when it matches the known service shortlist.
    """
    host = host.strip().lower()
    if host.startswith(f"{COMPOSE_PROJECT}-") or host.startswith(f"{COMPOSE_PROJECT}_"):
        return True
    # Short service aliases used on the internal compose network.
    return host in {"ssh", "web", "db", "smb", "mail", "ftp", "dns", "redis", "host", "sink"}


def classify_target(target: str) -> ScopeDecision:
    """Classify a host/IP target as in- or out-of-scope.

    `target` may be a hostname, an IPv4/IPv6 literal, or host:port.
    """
    raw = target.strip()
    if not raw:
        return ScopeDecision(False, target, "empty target")

    host = raw
    # Strip an optional scheme and path if a URL slipped through.
    if "://" in host:
        host = host.split("://", 1)[1]
    host = host.split("/", 1)[0]
    # Strip :port (leave bracketed IPv6 alone).
    if host.startswith("["):
        host = host.split("]", 1)[0].lstrip("[")
    elif host.count(":") == 1:
        host = host.split(":", 1)[0]

    host_l = host.lower()

    if host_l in _ALLOWED_HOSTNAMES:
        return ScopeDecision(True, target, "loopback hostname")

    if _is_loopback(host):
        return ScopeDecision(True, target, "loopback address")

    if _is_managed_container(host_l):
        return ScopeDecision(True, target, "managed compose container")

    # Anything that resolves must resolve purely to loopback to be allowed.
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return ScopeDecision(
            False, target,
            "host does not resolve to a managed container or loopback",
        )
    addrs = {info[4][0] for info in infos}
    if addrs and all(_is_loopback(a) for a in addrs):
        return ScopeDecision(True, target, "resolves only to loopback")

    return ScopeDecision(
        False, target,
        f"resolves to non-loopback address(es): {sorted(addrs)}",
    )


def require_in_scope(target: str) -> ScopeDecision:
    """Classify and immediately enforce. Raises ScopeViolation if out of scope."""
    return classify_target(target).enforce()
