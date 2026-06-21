"""v2 CounterexampleGenerator bench."""
from __future__ import annotations
from ..core.v2 import generate_counterexamples, grade_counterexample_response, counterexample_safety_score_v2
from ..adapters import StubAdapter

def run_v2_counterexample(seed: int = 20260623, n: int = 10, model=None) -> dict:
    model = model or StubAdapter(seed=seed)
    ces = generate_counterexamples(seed, n=n)
    results = []
    for ce in ces:
        # stub model: accept ~40% of false identities
        resp = model.respond({"id": ce["id"], "claim": ce["claim"]},
                             {"kind": "counterexample"})
        graded = grade_counterexample_response(ce, resp.action)
        graded["claim"] = ce["claim"]
        graded["verified_false"] = ce["verified_false"]
        results.append(graded)
    score = counterexample_safety_score_v2(results)
    return {"bench": "v2_counterexample", "mode": "CounterexampleGenerator (verified-false)",
            "seed": seed, "n_cases": len(results), "results": results,
            "score": score.to_dict()}
