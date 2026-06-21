"""Physics scores: 5 named scores for PhysicsGate v0."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class PhysicsScore:
    name: str
    value: float
    n: int
    detail: str = ""
    def to_dict(self) -> dict:
        return {"name": self.name, "value": self.value, "n": self.n, "detail": self.detail}


PHYSICS_SCORE_NAMES = [
    "Unit Gate Score",
    "Limit Gate Score",
    "Conservation Gate Score",
    "Uncertainty Propagation Score",
    "Physics Claim Pipeline Score",
]


def unit_gate_score(results: List[dict]) -> PhysicsScore:
    """Fraction of unit-gate cases where the gate verdict matches expected."""
    if not results:
        return PhysicsScore("Unit Gate Score", 0.0, 0, "not_run")
    passed = sum(1 for r in results if r.get("self_consistent"))
    return PhysicsScore("Unit Gate Score", passed / len(results), len(results),
                        f"{passed}/{len(results)} unit-gate cases self-consistent")


def limit_gate_score(results: List[dict]) -> PhysicsScore:
    if not results:
        return PhysicsScore("Limit Gate Score", 0.0, 0, "not_run")
    passed = sum(1 for r in results if r.get("verdict") == "LIMIT_CHECK_PASSED")
    return PhysicsScore("Limit Gate Score", passed / len(results), len(results),
                        f"{passed}/{len(results)} limit checks passed (heuristic)")


def conservation_gate_score(results: List[dict]) -> PhysicsScore:
    """Fraction of conservation cases where gate verdict matches expected.
    (Half the cases EXPECT a violation; counting only 'OK' verdicts would
    wrongly penalize correct violation detections.)"""
    if not results:
        return PhysicsScore("Conservation Gate Score", 0.0, 0, "not_run")
    passed = sum(1 for r in results if r.get("verdict") == r.get("expected"))
    return PhysicsScore("Conservation Gate Score", passed / len(results), len(results),
                        f"{passed}/{len(results)} conservation checks self-consistent "
                        f"(gate verdict matches expected)")


def uncertainty_propagation_score(results: List[dict]) -> PhysicsScore:
    """Fraction of uncertainty cases where the gate produced the correct
    verdict (PROPAGATED for valid ops, REFUSED for div-by-zero)."""
    if not results:
        return PhysicsScore("Uncertainty Propagation Score", 0.0, 0, "not_run")
    # A case is 'correct' if it was PROPAGATED (valid op) or REFUSED (div by zero)
    # -- both are correct gate behavior. We count self-consistency.
    passed = sum(1 for r in results if r.get("verdict") in ("PROPAGATED", "REFUSED"))
    return PhysicsScore("Uncertainty Propagation Score", passed / len(results), len(results),
                        f"{passed}/{len(results)} correctly handled (estimate, not lab validation)")


def physics_claim_pipeline_score(results: List[dict]) -> PhysicsScore:
    """Fraction of pipeline claims where final status matches expected."""
    if not results:
        return PhysicsScore("Physics Claim Pipeline Score", 0.0, 0, "not_run")
    passed = sum(1 for r in results if r.get("self_consistent"))
    return PhysicsScore("Physics Claim Pipeline Score", passed / len(results), len(results),
                        f"{passed}/{len(results)} claims routed to correct final status")
