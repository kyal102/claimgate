"""TheoryBench: run the pipeline, grouped by category."""
from __future__ import annotations
from collections import defaultdict
from ...core.theory import TheoryGate, THEORY_CLAIMS, theory_bench_score, PUBLIC_WORDING

def run_theory_bench(seed: int = 20260625, model=None) -> dict:
    gate = TheoryGate()
    results = []
    by_category = defaultdict(list)
    for theory in THEORY_CLAIMS:
        pack = gate.evaluate(theory)
        d = pack.to_dict()
        d["expected_final_status"] = theory.expected_final_status
        d["self_consistent"] = (pack.final_status == theory.expected_final_status)
        d["why"] = theory.why
        results.append(d)
        by_category[theory.category].append({
            "theory_name": pack.theory_name,
            "final_status": pack.final_status,
            "expected": theory.expected_final_status,
            "self_consistent": d["self_consistent"],
        })
    score = theory_bench_score(results)
    return {
        "bench": "theorybench",
        "mode": "TheoryBench (10 categories of theory claims)",
        "public_wording": PUBLIC_WORDING,
        "seed": seed, "n_cases": len(results),
        "categories": dict(by_category),
        "results": results, "score": score.to_dict(),
    }
