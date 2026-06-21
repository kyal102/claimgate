"""Theory scores."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List


@dataclass
class TheoryScore:
    name: str
    value: float
    n: int
    detail: str = ""
    def to_dict(self) -> dict:
        return {"name": self.name, "value": self.value, "n": self.n, "detail": self.detail}


THEORY_SCORE_NAMES = [
    "Theory Gate Score",
    "Theory Bench Score",
]


def theory_gate_score(results: List[dict]) -> TheoryScore:
    """Fraction of theory-gate cases where final status matches expected."""
    if not results:
        return TheoryScore("Theory Gate Score", 0.0, 0, "not_run")
    passed = sum(1 for r in results if r.get("self_consistent"))
    return TheoryScore("Theory Gate Score", passed / len(results), len(results),
                       f"{passed}/{len(results)} theories routed to correct final status")


def theory_bench_score(results: List[dict]) -> TheoryScore:
    """Same metric, distinct name for the bench-specific run."""
    if not results:
        return TheoryScore("Theory Bench Score", 0.0, 0, "not_run")
    passed = sum(1 for r in results if r.get("self_consistent"))
    return TheoryScore("Theory Bench Score", passed / len(results), len(results),
                       f"{passed}/{len(results)} bench categories correct")
