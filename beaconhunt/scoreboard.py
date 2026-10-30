"""Persistent scoreboard / history across rounds."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from .grader import GradeResult
from .scenario import STATE_DIR


@dataclass
class ScoreEntry:
    seed: int
    when: float
    final_points: int
    total_possible: int
    true_positives: int
    false_positives: int
    missed: int
    elapsed_seconds: float

    @property
    def detection_rate(self) -> float:
        found = self.true_positives
        total = self.true_positives + self.missed
        return (found / total) if total else 0.0


def _board_path(state_dir: Path) -> Path:
    return Path(state_dir) / "scoreboard.json"


def record(
    result: GradeResult,
    elapsed_seconds: float,
    state_dir: Path = STATE_DIR,
) -> ScoreEntry:
    entry = ScoreEntry(
        seed=result.seed,
        when=time.time(),
        final_points=result.final_points,
        total_possible=result.total_possible,
        true_positives=result.true_positives,
        false_positives=result.false_positives,
        missed=len(result.missed),
        elapsed_seconds=round(elapsed_seconds, 1),
    )
    entries = load(state_dir)
    entries.append(entry)
    Path(state_dir).mkdir(parents=True, exist_ok=True)
    _board_path(state_dir).write_text(
        json.dumps([asdict(e) for e in entries], indent=2), encoding="utf-8"
    )
    return entry


def load(state_dir: Path = STATE_DIR) -> list[ScoreEntry]:
    p = _board_path(state_dir)
    if not p.exists():
        return []
    return [ScoreEntry(**d) for d in json.loads(p.read_text(encoding="utf-8"))]
