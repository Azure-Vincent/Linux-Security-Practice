"""Active-round state: tracks submissions, hints, and timing for a scenario.

Kept as a small JSON file in the state dir so `submit`, `hint`, and `grade`
can be separate CLI invocations against the same round.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .grader import Submission
from .scenario import STATE_DIR


@dataclass
class RoundState:
    seed: int
    started_at: float = field(default_factory=time.time)
    finished_at: float | None = None
    submissions: list[Submission] = field(default_factory=list)
    hints_used: dict[str, int] = field(default_factory=dict)

    @property
    def elapsed(self) -> float:
        end = self.finished_at or time.time()
        return end - self.started_at

    def to_dict(self) -> dict:
        return {
            "seed": self.seed,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "submissions": [asdict(s) for s in self.submissions],
            "hints_used": self.hints_used,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "RoundState":
        return cls(
            seed=d["seed"],
            started_at=d.get("started_at", time.time()),
            finished_at=d.get("finished_at"),
            submissions=[Submission(**s) for s in d.get("submissions", [])],
            hints_used=dict(d.get("hints_used", {})),
        )


def _path(seed: int, state_dir: Path) -> Path:
    return Path(state_dir) / f"round-{seed}.json"


def load_round(seed: int, state_dir: Path = STATE_DIR) -> RoundState:
    p = _path(seed, state_dir)
    if p.exists():
        return RoundState.from_dict(json.loads(p.read_text(encoding="utf-8")))
    return RoundState(seed=seed)


def save_round(state: RoundState, state_dir: Path = STATE_DIR) -> Path:
    state_dir = Path(state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    p = _path(state.seed, state_dir)
    p.write_text(json.dumps(state.to_dict(), indent=2), encoding="utf-8")
    return p
