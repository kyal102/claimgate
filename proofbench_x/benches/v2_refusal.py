"""v2 ProofRefusalHard bench: open problems + contradictions."""
from __future__ import annotations
from ..core.v2 import REFUSAL_CASES, proof_refusal_score
from ..adapters import StubAdapter

def run_v2_refusal(seed: int = 20260623, model=None) -> dict:
    model = model or StubAdapter(seed=seed)
    results = []
    for rc in REFUSAL_CASES:
        # stub: refuse correctly ~85% of the time; sometimes "proves" (fail)
        action = "refuse" if model.rng.random() < 0.85 else "prove"
        matched = (action in ("refuse", "mark_unsupported"))
        results.append({"problem_id": rc.id, "prompt": rc.prompt, "kind": rc.kind,
                        "expected": rc.expected, "got": action,
                        "status": "pass" if matched else "fail",
                        "note": "correctly refused" if matched else "faked a proof (forbidden)"})
    score = proof_refusal_score(results)
    return {"bench": "v2_refusal", "mode": "ProofRefusalHard (open problems + contradictions)",
            "seed": seed, "n_cases": len(results), "results": results,
            "score": score.to_dict()}
