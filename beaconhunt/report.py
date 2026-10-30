"""End-of-round report rendering (plain text + machine-readable dict)."""

from __future__ import annotations

from .catalog import Catalog
from .grader import GradeResult
from .scenario import Scenario


def _fmt_duration(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m}m{s:02d}s"


def category_breakdown(result: GradeResult, catalog: Catalog, scenario: Scenario):
    """Detection rate per category and per service."""
    by_cat: dict[str, list[int]] = {}   # cat -> [found, total]
    by_svc: dict[str, list[int]] = {}
    found_ids = {s.matched_artifact_id for s in result.scored if s.strength != "none"}
    for finding in scenario.findings:
        art = catalog.get(finding.artifact_id)
        hit = 1 if finding.artifact_id in found_ids else 0
        by_cat.setdefault(art.category, [0, 0])
        by_cat[art.category][0] += hit
        by_cat[art.category][1] += 1
        by_svc.setdefault(art.service, [0, 0])
        by_svc[art.service][0] += hit
        by_svc[art.service][1] += 1
    return by_cat, by_svc


def render_text(
    result: GradeResult,
    catalog: Catalog,
    scenario: Scenario,
    elapsed_seconds: float,
) -> str:
    lines: list[str] = []
    w = lines.append

    w("=" * 64)
    w(f"  BeaconHunt — Round Report  (seed {result.seed})")
    w("=" * 64)
    w("")
    w(f"  Time:            {_fmt_duration(elapsed_seconds)}")
    w(f"  Score:           {result.final_points} / {result.total_possible}")
    w(f"  True positives:  {result.true_positives}")
    w(f"  False positives: {result.false_positives}"
      f"  (-{result.false_positive_penalty} pts)")
    w(f"  Missed:          {len(result.missed)}")
    if result.hint_penalty:
        w(f"  Hint penalty:    -{result.hint_penalty} pts")
    w("")

    by_cat, by_svc = category_breakdown(result, catalog, scenario)
    w("  Detection rate by category:")
    for cat, (found, total) in sorted(by_cat.items()):
        pct = int(100 * found / total) if total else 0
        w(f"    {cat:<12} {found}/{total}  ({pct}%)")
    w("")
    w("  Detection rate by service:")
    for svc, (found, total) in sorted(by_svc.items()):
        pct = int(100 * found / total) if total else 0
        w(f"    {svc:<12} {found}/{total}  ({pct}%)")
    w("")

    if result.scored:
        w("  Your submissions:")
        for s in result.scored:
            mark = "✓" if s.strength == "strong" else ("~" if s.strength == "weak" else "✗")
            w(f"    [{mark}] +{s.awarded:<4} {s.submission.evidence}")
            w(f"         {s.note}")
        w("")

    if result.missed:
        w("  MISSED FINDINGS (what was there and how to fix it):")
        w("  " + "-" * 60)
        for m in result.missed:
            art = catalog.get(m.artifact_id)
            sig_locs = [s.path for s in art.signatures if s.path]
            where = sig_locs[0] if sig_locs else "(see signatures)"
            w(f"    • {art.name}  [{art.service}/{art.category}, {art.points} pts]")
            w(f"        Where:  {where}")
            w(f"        What:   {art.description}")
            if art.remediation:
                w(f"        Fix:    {art.remediation.strip()}")
            if art.hunt_commands:
                w(f"        Hunt:   {art.hunt_commands[0]}")
            w("")
    else:
        w("  No missed findings — clean sweep. 🎯")
        w("")

    w("=" * 64)
    return "\n".join(lines)
