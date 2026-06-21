"""WitnessBench: run only the false-identity witness cases."""
from __future__ import annotations
from ...core.math_hardening.math_hardening_bench import _build_witness_cases
from ...core.math_hardening.scores import counterexample_witness_score
from ...core.math_hardening import PUBLIC_WORDING

def run_witnessbench(seed: int = 20260629, model=None) -> dict:
    cases = _build_witness_cases()
    score = counterexample_witness_score(cases)
    return {
        "bench": "witnessbench",
        "mode": "WitnessGate v0 (counterexample witness generation)",
        "public_wording": PUBLIC_WORDING,
        "seed": seed, "n_cases": len(cases),
        "results": cases, "score": score.to_dict(),
    }
