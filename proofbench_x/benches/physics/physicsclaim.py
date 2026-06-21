"""PhysicsClaimBench: the multi-gate pipeline with 10 conservative statuses."""
from __future__ import annotations
from ...core.physics import PhysicsClaimBench, BENCH_CLAIMS, physics_claim_pipeline_score, PUBLIC_WORDING, ALL_STATUSES

def run_physics_claimbench(seed: int = 20260624, model=None) -> dict:
    bench = PhysicsClaimBench()
    results = []
    for claim in BENCH_CLAIMS:
        r = bench.evaluate(claim)
        results.append(r.to_dict())
    score = physics_claim_pipeline_score(results)
    # tally statuses
    status_tally = {}
    for r in results:
        s = r["final_status"]
        status_tally[s] = status_tally.get(s, 0) + 1
    return {
        "bench": "physics_claimbench",
        "mode": "Multi-gate pipeline (6 categories, 10 conservative statuses)",
        "public_wording": PUBLIC_WORDING,
        "allowed_statuses": ALL_STATUSES,
        "seed": seed, "n_cases": len(results),
        "status_tally": status_tally,
        "results": results, "score": score.to_dict(),
        "discipline_note": "v0 does NOT claim experimental truth. CANDIDATE_PREDICTION means 'passed all gates; worth investigating', NOT 'proven true'.",
    }
