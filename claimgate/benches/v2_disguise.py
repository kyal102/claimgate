"""v2 ExpressionDisguise bench."""
from __future__ import annotations
from ..core.v2 import disguise_problem_set, verify_disguise_problem, expression_invariance_score

def run_v2_disguise(seed: int = 20260623, n: int = 8, model=None) -> dict:
    problems = disguise_problem_set(seed, n=n)
    results = [verify_disguise_problem(p) for p in problems]
    score = expression_invariance_score(results)
    return {"bench": "v2_disguise", "mode": "ExpressionDisguise (equivalent forms)",
            "seed": seed, "n_cases": len(results), "results": results,
            "score": score.to_dict()}
