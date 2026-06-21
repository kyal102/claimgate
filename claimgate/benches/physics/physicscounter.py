"""PhysicsCounterexample bench (bounded search)."""
from __future__ import annotations
from ...core.physics import PhysicsCounterexample, COUNTEREXAMPLE_CASES, PUBLIC_WORDING
from ...core.physics.scores import PhysicsScore

def run_physics_counterexample(seed: int = 20260624, model=None) -> dict:
    search = PhysicsCounterexample()
    results = []
    for case in COUNTEREXAMPLE_CASES:
        r = search.search(case, seed=seed)
        d = r.to_dict(); d["id"] = case.id; d["description"] = case.description
        d["expected"] = case.expected; d["why"] = case.why
        d["self_consistent"] = (r.verdict == case.expected)
        results.append(d)
    passed = sum(1 for r in results if r.get("self_consistent"))
    score = PhysicsScore("Physics Counterexample Score", passed / len(results) if results else 0.0,
                         len(results), f"{passed}/{len(results)} bounded searches correct (NOT proof of truth)")
    return {
        "bench": "physics_counterexample",
        "mode": "Bounded counterexample search (no counterexample found != proven true)",
        "public_wording": PUBLIC_WORDING,
        "seed": seed, "n_cases": len(results),
        "results": results, "score": score.to_dict(),
    }
