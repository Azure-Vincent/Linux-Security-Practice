"""Declarative schema for a planted artifact.

A planted artifact is defined entirely in YAML so the catalog is easy to
extend. This module loads, validates, and normalizes those definitions into
typed objects the rest of BeaconHunt consumes.

Schema (all keys unless noted as optional):

    id:          unique slug, e.g. "ssh-authorized-keys-backdoor"
    name:        human-readable title
    service:     one of the known services (ssh, web, db, smb, host)
    category:    backdoor | beacon | persistence | misconfig | weak-cred | privesc
    difficulty:  easy | medium | hard
    points:      positive integer awarded for a true positive
    description: one-line summary of the planted condition

    install:                       # how the artifact is planted in the container
      script: plant/foo.sh         # path relative to the service dir, run in-container
      args:   ["optional", "argv"] # optional extra argv passed to the script

    detection:                     # the answer key used for grading
      signatures:                  # machine checks that verify the plant is live
        - type: file_line          # file_line|file_exists|process|port|user|config|cron|timer
          path: /root/.ssh/authorized_keys
          match: "beaconhunt-trainingkey"   # substring (or regex: true)
      accept_evidence:             # what a user submission must look like to score
        paths:     ["/root/.ssh/authorized_keys"]   # path(s), matched normalized
        keywords:  ["authorized_keys", "ssh-ed25519"]  # any keyword is a weak hit
        ports:     [2222]          # optional
        users:     ["svc-backup"]  # optional
        require:   path            # path|keyword|any  (what is sufficient to score)

    remediation:  how a defender fixes it
    hunt_commands: [ "cat ...", "find ..." ]   # commands that surface it
    learn:        longer explainer of the technique
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

KNOWN_SERVICES = {"ssh", "web", "db", "smb", "mail", "ftp", "dns", "redis", "host"}
KNOWN_CATEGORIES = {
    "backdoor", "beacon", "persistence", "misconfig", "weak-cred", "privesc",
}
KNOWN_DIFFICULTIES = {"easy", "medium", "hard"}
KNOWN_SIGNATURE_TYPES = {
    "file_line", "file_exists", "process", "port", "user", "config", "cron", "timer",
    "sql", "command",
}
REQUIRE_MODES = {"path", "keyword", "any"}


class SchemaError(ValueError):
    """Raised when an artifact YAML definition is malformed."""


@dataclass(frozen=True)
class Signature:
    type: str
    path: str | None = None
    match: str | None = None
    regex: bool = False
    # free-form extra fields (port number, user name, process name, ...)
    extra: dict[str, Any] = field(default_factory=dict)

    def compiled(self) -> re.Pattern[str] | None:
        if self.match is None:
            return None
        pattern = self.match if self.regex else re.escape(self.match)
        return re.compile(pattern)


@dataclass(frozen=True)
class AcceptEvidence:
    paths: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()
    ports: tuple[int, ...] = ()
    users: tuple[str, ...] = ()
    require: str = "any"  # path | keyword | any


@dataclass(frozen=True)
class Install:
    script: str | None = None
    args: tuple[str, ...] = ()


@dataclass(frozen=True)
class Artifact:
    id: str
    name: str
    service: str
    category: str
    difficulty: str
    points: int
    description: str
    install: Install
    signatures: tuple[Signature, ...]
    accept_evidence: AcceptEvidence
    remediation: str
    hunt_commands: tuple[str, ...]
    learn: str
    source_path: Path | None = None


def _require(d: dict[str, Any], key: str, where: str) -> Any:
    if key not in d:
        raise SchemaError(f"{where}: missing required key {key!r}")
    return d[key]


def _parse_signature(raw: dict[str, Any], where: str) -> Signature:
    if not isinstance(raw, dict):
        raise SchemaError(f"{where}: each signature must be a mapping")
    stype = _require(raw, "type", where)
    if stype not in KNOWN_SIGNATURE_TYPES:
        raise SchemaError(
            f"{where}: unknown signature type {stype!r} "
            f"(known: {sorted(KNOWN_SIGNATURE_TYPES)})"
        )
    known = {"type", "path", "match", "regex"}
    extra = {k: v for k, v in raw.items() if k not in known}
    return Signature(
        type=stype,
        path=raw.get("path"),
        match=raw.get("match"),
        regex=bool(raw.get("regex", False)),
        extra=extra,
    )


def _parse_accept(raw: dict[str, Any] | None, where: str) -> AcceptEvidence:
    raw = raw or {}
    require = raw.get("require", "any")
    if require not in REQUIRE_MODES:
        raise SchemaError(
            f"{where}: accept_evidence.require must be one of {sorted(REQUIRE_MODES)}"
        )
    ports = tuple(int(p) for p in raw.get("ports", []))
    return AcceptEvidence(
        paths=tuple(str(p) for p in raw.get("paths", [])),
        keywords=tuple(str(k) for k in raw.get("keywords", [])),
        ports=ports,
        users=tuple(str(u) for u in raw.get("users", [])),
        require=require,
    )


def parse_artifact(data: dict[str, Any], source_path: Path | None = None) -> Artifact:
    where = str(source_path or data.get("id", "<artifact>"))
    if not isinstance(data, dict):
        raise SchemaError(f"{where}: artifact definition must be a mapping")

    service = _require(data, "service", where)
    if service not in KNOWN_SERVICES:
        raise SchemaError(f"{where}: unknown service {service!r}")
    category = _require(data, "category", where)
    if category not in KNOWN_CATEGORIES:
        raise SchemaError(f"{where}: unknown category {category!r}")
    difficulty = _require(data, "difficulty", where)
    if difficulty not in KNOWN_DIFFICULTIES:
        raise SchemaError(f"{where}: unknown difficulty {difficulty!r}")

    points = _require(data, "points", where)
    if not isinstance(points, int) or points <= 0:
        raise SchemaError(f"{where}: points must be a positive integer")

    detection = _require(data, "detection", where)
    sig_raw = detection.get("signatures", []) if isinstance(detection, dict) else []
    if not sig_raw:
        raise SchemaError(f"{where}: detection.signatures must not be empty")
    signatures = tuple(
        _parse_signature(s, f"{where} signature[{i}]") for i, s in enumerate(sig_raw)
    )

    install_raw = data.get("install", {}) or {}
    install = Install(
        script=install_raw.get("script"),
        args=tuple(str(a) for a in install_raw.get("args", [])),
    )

    return Artifact(
        id=_require(data, "id", where),
        name=_require(data, "name", where),
        service=service,
        category=category,
        difficulty=difficulty,
        points=points,
        description=_require(data, "description", where),
        install=install,
        signatures=signatures,
        accept_evidence=_parse_accept(detection.get("accept_evidence"), where),
        remediation=data.get("remediation", ""),
        hunt_commands=tuple(str(c) for c in data.get("hunt_commands", [])),
        learn=data.get("learn", ""),
        source_path=source_path,
    )


def load_artifact_file(path: Path) -> Artifact:
    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return parse_artifact(data, source_path=path)
