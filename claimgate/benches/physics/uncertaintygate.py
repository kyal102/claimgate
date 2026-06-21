"""UncertaintyGate bench."""
from __future__ import annotations
from ...core.physics import UncertaintyGate, UNCERTAINTY_CASES, uncertainty_propagation_score, PUBLIC_WORDING

def run_physics_uncertaintygate(seed: int = 20260624, model=None) -> dict:
    gate = UncertaintyGate()
    results = []
    for case in UNCERTAINTY_CASES:
        r = gate.propagate(case.op, case.a, case.b)
        d = r.to_dict(); d["id"] = case.id; d["description"] = case.description
        d["why"] = case.why
        results.append(d)
    score = uncertainty_propagation_score(results)
    return {
        "bench": "physics_uncertaintygate",
        "mode": "Uncertainty propagation (first-pass ESTIMATE, NOT lab validation)",
        "public_wording": PUBLIC_WORDING,
        "seed": seed, "n_cases": len(results),
        "results": results, "score": score.to_dict(),
    }
