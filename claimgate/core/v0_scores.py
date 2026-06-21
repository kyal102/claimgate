"""v0 score interface hooks.

A full v0 benchmark defines these four scores. This module provides a STABLE
INTERFACE for them so that:

  * v1 code can reference v0 scores by name without depending on v0 internals
  * a downstream integration can wire these hooks to its actual v0 computation
  * the prototype can emit v0-shaped score records (clearly labeled as
    prototype placeholders) so the report format is complete

*** These are HOOKS, not reimplementations of real v0 scoring. ***
When integrating, replace the placeholder logic with calls to the actual v0
score functions. Do NOT keep the placeholder logic in production.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


# Canonical v0 score names (do not rename -- the real v0 REPORT and
# Packages.html scoreboard card use these exact labels).
V0_SCORE_NAMES = [
    "Math Trust Score",
    "DTL Acceleration",
    "Proof Integrity",
    "Model Trap Resistance",
]


@dataclass
class V0ScoreHook:
    name: str
    value: float
    n: int
    detail: str
    is_real_v0: bool   # False in prototype; True once wired to real v0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "value": self.value,
            "n": self.n,
            "detail": self.detail,
            "is_real_v0": self.is_real_v0,
        }


def math_trust_score(v0_results: list) -> V0ScoreHook:
    """Math Trust Score: fraction of v0 cases where the verifier trusted
    the (re-derived) result and issued a verified certificate.

    PROTOTYPE PLACEHOLDER. Wire to real v0 in production.
    """
    if not v0_results:
        return V0ScoreHook("Math Trust Score", 0.0, 0, "not_run (prototype hook)", False)
    trusted = sum(1 for r in v0_results
                  if r.get("certificate") and r["certificate"].get("verified"))
    return V0ScoreHook("Math Trust Score", trusted / len(v0_results), len(v0_results),
                       f"{trusted}/{len(v0_results)} (PROTOTYPE hook -- wire to real v0)", False)


def dtl_acceleration(v0_results: list, warm_results: Optional[list] = None) -> V0ScoreHook:
    """DTL Acceleration: speedup ratio from warm-lane reuse.

    PROTOTYPE PLACEHOLDER. Uses warm_power bench numbers if available.
    """
    if not warm_results:
        return V0ScoreHook("DTL Acceleration", 0.0, 0, "not_run (prototype hook)", False)
    speedups = [r.get("speedup", 0.0) for r in warm_results]
    avg = sum(speedups) / len(speedups) if speedups else 0.0
    return V0ScoreHook("DTL Acceleration", avg, len(speedups),
                       f"avg speedup {avg:.2f}x (PROTOTYPE hook -- wire to real v0)", False)


def proof_integrity(v0_results: list) -> V0ScoreHook:
    """Proof Integrity: fraction of cases with a valid (non-faked) certificate.

    PROTOTYPE PLACEHOLDER. Wire to real v0 in production.
    """
    if not v0_results:
        return V0ScoreHook("Proof Integrity", 0.0, 0, "not_run (prototype hook)", False)
    valid = sum(1 for r in v0_results
                if r.get("certificate") and r["certificate"].get("verified")
                and r.get("status") != "unverified")
    return V0ScoreHook("Proof Integrity", valid / len(v0_results), len(v0_results),
                       f"{valid}/{len(v0_results)} valid certificates (PROTOTYPE hook)", False)


def model_trap_resistance(counterexample_results: list,
                          routing_results: Optional[list] = None) -> V0ScoreHook:
    """Model Trap Resistance: fraction of trap cases (counterexamples +
    routing traps) the system correctly refused/rejected.

    PROTOTYPE PLACEHOLDER. Wire to real v0 in production.
    """
    total = 0
    resisted = 0
    for r in counterexample_results:
        total += 1
        if r.get("status") == "pass":
            resisted += 1
    if routing_results:
        for r in routing_results:
            total += 1
            if r.get("matched_expected"):
                resisted += 1
    if total == 0:
        return V0ScoreHook("Model Trap Resistance", 0.0, 0, "not_run (prototype hook)", False)
    return V0ScoreHook("Model Trap Resistance", resisted / total, total,
                       f"{resisted}/{total} traps resisted (PROTOTYPE hook)", False)


def all_v0_score_hooks(v0_results: list,
                       warm_results: Optional[list] = None,
                       counterexample_results: Optional[list] = None,
                       routing_results: Optional[list] = None) -> dict:
    """Assemble all four v0 score hooks."""
    return {
        h.name: h.to_dict() for h in [
            math_trust_score(v0_results),
            dtl_acceleration(v0_results, warm_results),
            proof_integrity(v0_results),
            model_trap_resistance(counterexample_results or [], routing_results or []),
        ]
    }
