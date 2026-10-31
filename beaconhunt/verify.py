"""Live verification: confirm planted signatures are actually present in the
running range.

For each finding in a scenario, `verify` turns its detection signatures into a
shell check and runs it *inside the relevant container* via
`docker compose exec`. This is both a range self-test (did planting work?) and
an integration test of the service images and plant scripts.

Each signature check reports one of:
  * present — the condition is live (plant succeeded),
  * absent  — the check ran and the condition is NOT there (plant missing/broken),
  * skip    — the check could not run (container down, docker missing, tool absent).

A finding is PASS if any signature is present and none is absent, FAIL if any is
absent, else SKIP.
"""

from __future__ import annotations

import shlex
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from . import safety
from .catalog import Catalog
from .scenario import Scenario
from .schema import Signature

REPO_ROOT = Path(__file__).resolve().parent.parent
COMPOSE_FILE = REPO_ROOT / "docker-compose.yml"

PRESENT, ABSENT, SKIP = "present", "absent", "skip"


def check_snippet(sig: Signature) -> str | None:
    """Build a /bin/sh snippet that prints BH_PRESENT / BH_ABSENT / BH_SKIP."""
    q = shlex.quote
    t = sig.type

    if t in ("file_line", "config", "cron", "timer", "user"):
        path = sig.path or ("/etc/passwd" if t == "user" else None)
        if not path or sig.match is None:
            return None
        flag = "-Eq" if sig.regex else "-Fq"
        check = f"grep {flag} -- {q(sig.match)} {q(path)}"
        return f"if {check}; then echo BH_PRESENT; else echo BH_ABSENT; fi"

    if t == "file_exists":
        if not sig.path:
            return None
        return f"if test -e {q(sig.path)}; then echo BH_PRESENT; else echo BH_ABSENT; fi"

    if t == "process":
        if sig.match is None:
            return None
        check = f"ps -eo args 2>/dev/null | grep -Fq -- {q(sig.match)}"
        return f"if {check}; then echo BH_PRESENT; else echo BH_ABSENT; fi"

    if t == "port":
        if sig.match is None:
            return None
        check = f"ss -tln 2>/dev/null | grep -Fq {q(':' + str(sig.match))}"
        return f"if {check}; then echo BH_PRESENT; else echo BH_ABSENT; fi"

    if t == "sql":
        query = sig.extra.get("query")
        if not query or sig.match is None:
            return None
        inner = f'mariadb -uroot -p"$MARIADB_ROOT_PASSWORD" -N -B -e {q(query)}'
        return _dynamic_snippet(inner, sig.match)

    if t == "command":
        command = sig.extra.get("command")
        if not command or sig.match is None:
            return None
        return _dynamic_snippet(command, sig.match)

    return None


def _dynamic_snippet(inner: str, match: str) -> str:
    """For sql/command checks: distinguish a run error (SKIP) from a real miss."""
    q = shlex.quote
    return (
        f'out=$({inner} 2>/dev/null); rc=$?; '
        f'if [ "$rc" -ne 0 ]; then echo BH_SKIP; '
        f'elif printf "%s" "$out" | grep -Fq -- {q(match)}; then echo BH_PRESENT; '
        f'else echo BH_ABSENT; fi'
    )


@dataclass
class SignatureResult:
    signature: Signature
    status: str  # present | absent | skip


@dataclass
class FindingResult:
    artifact_id: str
    service: str
    name: str
    verdict: str = "SKIP"  # PASS | FAIL | SKIP
    signatures: list[SignatureResult] = field(default_factory=list)
    note: str = ""


def _compose_exec(service: str, snippet: str, timeout: float = 30.0) -> str:
    cmd = ["docker", "compose", "-p", safety.COMPOSE_PROJECT,
           "-f", str(COMPOSE_FILE), "exec", "-T", service, "sh", "-c", snippet]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        return SKIP  # docker not installed
    except subprocess.TimeoutExpired:
        return SKIP
    out = res.stdout or ""
    if "BH_PRESENT" in out:
        return PRESENT
    if "BH_ABSENT" in out:
        return ABSENT
    # BH_SKIP, or exec failed (container down / not built yet)
    return SKIP


def verify(scenario: Scenario, catalog: Catalog) -> list[FindingResult]:
    results: list[FindingResult] = []
    for finding in scenario.findings:
        art = catalog.get(finding.artifact_id)
        fr = FindingResult(artifact_id=art.id, service=art.service, name=art.name)
        for sig in art.signatures:
            snippet = check_snippet(sig)
            status = _compose_exec(art.service, snippet) if snippet else SKIP
            fr.signatures.append(SignatureResult(sig, status))
        statuses = [s.status for s in fr.signatures]
        if ABSENT in statuses:
            fr.verdict = "FAIL"
            fr.note = "a planted signature is not present in the container"
        elif PRESENT in statuses:
            fr.verdict = "PASS"
        else:
            fr.verdict = "SKIP"
            fr.note = "could not check (is the range up? `beaconhunt deploy`)"
        results.append(fr)
    return results


def render(results: list[FindingResult]) -> str:
    lines = ["", "  BeaconHunt — live verification", "  " + "-" * 56]
    mark = {"PASS": "✓", "FAIL": "✗", "SKIP": "·"}
    for r in results:
        lines.append(f"    [{mark[r.verdict]}] {r.verdict:<4} {r.service}/{r.artifact_id}")
        if r.verdict != "PASS" and r.note:
            lines.append(f"              {r.note}")
    npass = sum(1 for r in results if r.verdict == "PASS")
    nfail = sum(1 for r in results if r.verdict == "FAIL")
    nskip = sum(1 for r in results if r.verdict == "SKIP")
    lines.append("  " + "-" * 56)
    lines.append(f"  {npass} live · {nfail} missing · {nskip} unchecked "
                 f"(of {len(results)})")
    return "\n".join(lines)
