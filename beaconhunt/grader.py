"""Grading: match free-form submissions against the scenario answer key.

Matching is intentionally forgiving (path-normalized + fuzzy keyword) because a
defender should get credit for pointing at the right thing even if they phrase
the evidence differently than the catalog author did.
"""

from __future__ import annotations

import posixpath
from dataclasses import asdict, dataclass, field
from difflib import SequenceMatcher

from .catalog import Catalog
from .scenario import Scenario
from .schema import AcceptEvidence, Artifact

# Hints cost a fraction of the finding's point value.
HINT_COST_FRACTION = 0.25
# A keyword-only (weak) match scores partial credit when the require mode allows.
WEAK_MATCH_FRACTION = 0.5
# Each false positive subtracts this many points (floored at zero overall).
FALSE_POSITIVE_PENALTY = 15


@dataclass
class Submission:
    type: str              # category the user claims (backdoor, beacon, ...)
    service: str           # service the user claims (ssh, web, ...)
    evidence: str          # free-form: path, PID, port, username, config line
    at: float = 0.0        # epoch seconds when submitted


@dataclass
class ScoredSubmission:
    submission: Submission
    matched_artifact_id: str | None
    awarded: int
    strength: str          # "strong" | "weak" | "none"
    note: str


@dataclass
class MissedFinding:
    artifact_id: str
    name: str
    service: str
    category: str
    points: int


@dataclass
class GradeResult:
    seed: int
    scored: list[ScoredSubmission] = field(default_factory=list)
    missed: list[MissedFinding] = field(default_factory=list)
    hints_used: dict[str, int] = field(default_factory=dict)  # artifact_id -> n hints
    total_possible: int = 0
    raw_points: int = 0
    hint_penalty: int = 0
    false_positive_penalty: int = 0

    @property
    def final_points(self) -> int:
        return max(0, self.raw_points - self.hint_penalty - self.false_positive_penalty)

    @property
    def true_positives(self) -> int:
        return sum(1 for s in self.scored if s.strength != "none")

    @property
    def false_positives(self) -> int:
        return sum(1 for s in self.scored if s.strength == "none")

    def to_dict(self) -> dict:
        return {
            "seed": self.seed,
            "total_possible": self.total_possible,
            "raw_points": self.raw_points,
            "hint_penalty": self.hint_penalty,
            "false_positive_penalty": self.false_positive_penalty,
            "final_points": self.final_points,
            "true_positives": self.true_positives,
            "false_positives": self.false_positives,
            "missed": [asdict(m) for m in self.missed],
            "scored": [
                {
                    "evidence": s.submission.evidence,
                    "claimed_type": s.submission.type,
                    "claimed_service": s.submission.service,
                    "matched_artifact_id": s.matched_artifact_id,
                    "awarded": s.awarded,
                    "strength": s.strength,
                    "note": s.note,
                }
                for s in self.scored
            ],
            "hints_used": self.hints_used,
        }


def _normalize_path(text: str) -> str:
    text = text.strip().strip("\"'")
    if "/" not in text:
        return text
    # Keep only the path-looking token. Prefer an absolute path (starts with
    # "/") so evidence like "open relay 0.0.0.0/0 in /etc/postfix/main.cf"
    # picks the file, not the CIDR; otherwise fall back to the first slash token.
    toks = text.split()
    token = next((t for t in toks if t.startswith("/")), None)
    if token is None:
        token = next((t for t in toks if "/" in t), text)
    token = token.split(":", 1)[0]  # drop ":line" suffixes like file:3
    norm = posixpath.normpath(token)
    return norm.rstrip("/") or "/"


def _path_hit(evidence: str, accept_paths: tuple[str, ...]) -> bool:
    ev_norm = _normalize_path(evidence)
    ev_base = posixpath.basename(ev_norm)
    for ap in accept_paths:
        ap_norm = _normalize_path(ap)
        if ev_norm == ap_norm:
            return True
        # Credit a pointer at the right file even if the dir prefix differs.
        if ev_base and ev_base == posixpath.basename(ap_norm):
            return True
        # Credit pointing inside the right directory tree.
        if ev_norm.startswith(ap_norm + "/") or ap_norm.startswith(ev_norm + "/"):
            return True
        # Fuzzy fallback for near-miss typos on the full path.
        if SequenceMatcher(None, ev_norm, ap_norm).ratio() >= 0.9:
            return True
    return False


def _keyword_hit(evidence: str, accept: AcceptEvidence) -> bool:
    ev = evidence.lower()
    for kw in accept.keywords:
        if kw.lower() in ev:
            return True
    for user in accept.users:
        if user.lower() in ev:
            return True
    for port in accept.ports:
        # match the port as a standalone token
        if str(port) in ev.split() or f":{port}" in ev or f" {port}" in f" {ev}":
            return True
    return False


def _match_strength(evidence: str, art: Artifact) -> str:
    accept = art.accept_evidence
    has_path = _path_hit(evidence, accept.paths) if accept.paths else False
    has_kw = _keyword_hit(evidence, accept)

    if accept.require == "path":
        return "strong" if has_path else "none"
    if accept.require == "keyword":
        return "strong" if has_kw else "none"
    # require == "any"
    if has_path:
        return "strong"
    if has_kw:
        return "weak"
    return "none"


def grade(
    scenario: Scenario,
    catalog: Catalog,
    submissions: list[Submission],
    hints_used: dict[str, int] | None = None,
) -> GradeResult:
    hints_used = dict(hints_used or {})
    planted_ids = [f.artifact_id for f in scenario.findings]
    planted_arts = {aid: catalog.get(aid) for aid in planted_ids}

    result = GradeResult(
        seed=scenario.seed,
        total_possible=scenario.total_points,
        hints_used=hints_used,
    )

    claimed: set[str] = set()  # artifact ids already credited

    for sub in submissions:
        best_id: str | None = None
        best_strength = "none"
        for aid, art in planted_arts.items():
            if aid in claimed:
                continue
            # Service mismatch disqualifies (user pointed at the wrong service).
            if sub.service and sub.service != art.service:
                continue
            strength = _match_strength(sub.evidence, art)
            if strength == "strong":
                best_id, best_strength = aid, "strong"
                break
            if strength == "weak" and best_strength == "none":
                best_id, best_strength = aid, "weak"

        if best_id is None:
            result.scored.append(
                ScoredSubmission(
                    submission=sub,
                    matched_artifact_id=None,
                    awarded=0,
                    strength="none",
                    note="No planted finding matches this evidence (false positive).",
                )
            )
            result.false_positive_penalty += FALSE_POSITIVE_PENALTY
            continue

        art = planted_arts[best_id]
        claimed.add(best_id)
        if best_strength == "strong":
            awarded = art.points
            note = f"Matched {art.name}."
        else:
            awarded = int(art.points * WEAK_MATCH_FRACTION)
            note = f"Partial match on {art.name} (keyword only — cite the exact location)."
        result.raw_points += awarded
        result.scored.append(
            ScoredSubmission(
                submission=sub,
                matched_artifact_id=best_id,
                awarded=awarded,
                strength=best_strength,
                note=note,
            )
        )

    # Missed findings = planted but never credited.
    for aid, art in planted_arts.items():
        if aid not in claimed:
            result.missed.append(
                MissedFinding(
                    artifact_id=aid,
                    name=art.name,
                    service=art.service,
                    category=art.category,
                    points=art.points,
                )
            )

    # Hint penalty.
    for aid, n in hints_used.items():
        if aid in planted_arts:
            result.hint_penalty += int(
                planted_arts[aid].points * HINT_COST_FRACTION * n
            )

    return result
