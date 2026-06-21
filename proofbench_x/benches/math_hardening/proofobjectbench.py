"""ProofObjectBench: run only the proof-object cases."""
from __future__ import annotations
from ...core.math_hardening.math_hardening_bench import _build_proof_object_cases
from ...core.math_hardening.scores import proof_object_completeness_score
from ...core.math_hardening import PUBLIC_WORDING

def run_proofobjectbench(seed: int = 20260629, model=None) -> dict:
    cases = _build_proof_object_cases()
    score = proof_object_completeness_score(cases)
    return {
        "bench": "proofobjectbench",
        "mode": "ProofObject v0 (structured proof/certificate objects)",
        "public_wording": PUBLIC_WORDING,
        "seed": seed, "n_cases": len(cases),
        "results": cases, "score": score.to_dict(),
    }
