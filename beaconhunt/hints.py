"""Shared tiered-hint logic used by both the CLI and the web UI."""

from __future__ import annotations

from .catalog import Catalog
from .scenario import Scenario
from .schema import Artifact
from .session import RoundState

HINT_COST_FRACTION = 0.25


def hint_tiers(art: Artifact) -> list[str]:
    return [
        f"There is a {art.category} finding in the {art.service} service "
        f"({art.difficulty}).",
        (f"Technique: {art.learn.strip()}" if art.learn
         else f"Look for: {art.description}"),
        (f"Try: {art.hunt_commands[0]}" if art.hunt_commands
         else f"Check: {art.description}"),
    ]


def choose_hint(
    catalog: Catalog,
    scenario: Scenario,
    state: RoundState,
    service: str | None = None,
) -> dict | None:
    """Pick the least-hinted finding (optionally filtered by service).

    Returns a dict describing the hint, or None if nothing matches. The caller
    is responsible for incrementing state.hints_used and persisting it.
    """
    candidates = [
        f for f in scenario.findings if (not service or f.service == service)
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda f: state.hints_used.get(f.artifact_id, 0))
    target = candidates[0]
    art = catalog.get(target.artifact_id)
    n = state.hints_used.get(art.id, 0)
    tiers = hint_tiers(art)
    tier = min(n, len(tiers) - 1)
    return {
        "artifact_id": art.id,
        "service": art.service,
        "category": art.category,
        "n": n,
        "text": tiers[tier],
        "cost": int(art.points * HINT_COST_FRACTION),
    }
