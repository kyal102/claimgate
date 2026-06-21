"""v2 AdversarialParser bench."""
from __future__ import annotations
from ..core.v2 import parser_problem_set, grade_parser_case, parser_robustness_score

def run_v2_parser(seed: int = 20260623, n_each: int = 2, model=None) -> dict:
    problems = parser_problem_set(seed, n_each=n_each)
    results = [grade_parser_case(p) for p in problems]
    score = parser_robustness_score(results)
    return {"bench": "v2_parser", "mode": "AdversarialParser (unicode/malformed/refuse)",
            "seed": seed, "n_cases": len(results), "results": results,
            "score": score.to_dict()}
