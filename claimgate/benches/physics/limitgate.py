"""LimitGate bench."""
from __future__ import annotations
from ...core.physics import LimitGate, LIMIT_CASES, limit_gate_score, PUBLIC_WORDING

def run_physics_limitgate(seed: int = 20260624, model=None) -> dict:
    gate = LimitGate()
    results = []
    for case in LIMIT_CASES:
        r = gate.check(case)
        d = r.to_dict(); d["id"] = case.id; d["description"] = case.description
        d["why"] = case.why
        results.append(d)
    score = limit_gate_score(results)
    return {
        "bench": "physics_limitgate",
        "mode": "Limit behavior (bounded heuristic check, NOT proof of physical truth)",
        "public_wording": PUBLIC_WORDING,
        "seed": seed, "n_cases": len(results),
        "results": results, "score": score.to_dict(),
    }
