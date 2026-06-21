"""AssumptionBench: run only the assumption-trap cases."""
from __future__ import annotations
from ...core.math_hardening.math_hardening_bench import _build_assumption_cases
from ...core.math_hardening.scores import assumption_safety_score
from ...core.math_hardening import PUBLIC_WORDING

def run_assumptionbench(seed: int = 20260629, model=None) -> dict:
    cases = _build_assumption_cases()
    score = assumption_safety_score(cases)
    return {
        "bench": "assumptionbench",
        "mode": "AssumptionGate v0 (hidden assumption detection)",
        "public_wording": PUBLIC_WORDING,
        "seed": seed, "n_cases": len(cases),
        "results": cases, "score": score.to_dict(),
    }
