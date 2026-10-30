"""Scenario generator: pick a reproducible set of findings from the catalog.

A scenario is fully determined by (seed, selection constraints, catalog state),
so sharing a seed reproduces the same range. Scenarios are persisted to the
state dir so the grader and report can refer back to the answer key.
"""

from __future__ import annotations

import json
import random
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .catalog import Catalog
from .schema import Artifact

STATE_DIR = Path(__file__).resolve().parent.parent / "state"


@dataclass
class PlantedFinding:
    """One artifact selected for a scenario (a line in the answer key)."""

    artifact_id: str
    service: str
    category: str
    difficulty: str
    points: int
    name: str


@dataclass
class Scenario:
    seed: int
    created_at: float
    findings: list[PlantedFinding] = field(default_factory=list)
    constraints: dict = field(default_factory=dict)

    @property
    def total_points(self) -> int:
        return sum(f.points for f in self.findings)

    def to_dict(self) -> dict:
        return {
            "seed": self.seed,
            "created_at": self.created_at,
            "constraints": self.constraints,
            "findings": [asdict(f) for f in self.findings],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Scenario":
        return cls(
            seed=d["seed"],
            created_at=d["created_at"],
            constraints=d.get("constraints", {}),
            findings=[PlantedFinding(**f) for f in d.get("findings", [])],
        )

    def path(self, state_dir: Path = STATE_DIR) -> Path:
        return Path(state_dir) / f"scenario-{self.seed}.json"

    def save(self, state_dir: Path = STATE_DIR) -> Path:
        state_dir = Path(state_dir)
        state_dir.mkdir(parents=True, exist_ok=True)
        p = self.path(state_dir)
        p.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        # Record the current scenario pointer for convenience.
        (state_dir / "current.json").write_text(
            json.dumps({"seed": self.seed}), encoding="utf-8"
        )
        return p


def _artifact_to_finding(a: Artifact) -> PlantedFinding:
    return PlantedFinding(
        artifact_id=a.id,
        service=a.service,
        category=a.category,
        difficulty=a.difficulty,
        points=a.points,
        name=a.name,
    )


def generate_scenario(
    catalog: Catalog,
    seed: int | None = None,
    count: int = 5,
    services: list[str] | None = None,
    categories: list[str] | None = None,
    difficulties: list[str] | None = None,
) -> Scenario:
    """Deterministically select `count` artifacts under the given constraints.

    The same seed + constraints + catalog yields the same selection.
    """
    if seed is None:
        seed = random.randrange(1, 2**31)
    rng = random.Random(seed)

    pool: list[Artifact] = []
    for art in sorted(catalog.all(), key=lambda a: a.id):  # stable order for RNG
        if services and art.service not in services:
            continue
        if categories and art.category not in categories:
            continue
        if difficulties and art.difficulty not in difficulties:
            continue
        pool.append(art)

    if not pool:
        raise ValueError("no catalog artifacts match the given constraints")

    count = min(count, len(pool))
    chosen = rng.sample(pool, count)
    # Sort chosen for a stable, readable answer key (does not affect selection).
    chosen.sort(key=lambda a: (a.service, a.category, a.id))

    return Scenario(
        seed=seed,
        created_at=time.time(),
        findings=[_artifact_to_finding(a) for a in chosen],
        constraints={
            "count": count,
            "services": services or [],
            "categories": categories or [],
            "difficulties": difficulties or [],
        },
    )


def load_scenario(seed: int, state_dir: Path = STATE_DIR) -> Scenario:
    p = Path(state_dir) / f"scenario-{seed}.json"
    if not p.exists():
        raise FileNotFoundError(f"no saved scenario for seed {seed} at {p}")
    return Scenario.from_dict(json.loads(p.read_text(encoding="utf-8")))


def current_seed(state_dir: Path = STATE_DIR) -> int | None:
    p = Path(state_dir) / "current.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8")).get("seed")
