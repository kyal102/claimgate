"""TheoryGate bench: run the pipeline on all theory claims."""
from __future__ import annotations
from ...core.theory import TheoryGate, THEORY_CLAIMS, theory_gate_score, PUBLIC_WORDING

def run_theory_gate(seed: int = 20260625, model=None) -> dict:
    gate = TheoryGate()
    results = []
    for theory in THEORY_CLAIMS:
        pack = gate.evaluate(theory)
        d = pack.to_dict()
        d["expected_final_status"] = theory.expected_final_status
        d["self_consistent"] = (pack.final_status == theory.expected_final_status)
        d["why"] = theory.why
        results.append(d)
    # determinism: re-run and verify same cert hashes
    rerun_hashes = []
    for theory in THEORY_CLAIMS:
        pack = gate.evaluate(theory)
        rerun_hashes.append(pack.certificate_hash)
    first_hashes = [r["certificate_hash"] for r in results]
    deterministic = (rerun_hashes == first_hashes)
    score = theory_gate_score(results)
    # status tally
    status_tally = {}
    for r in results:
        s = r["final_status"]
        status_tally[s] = status_tally.get(s, 0) + 1
    return {
        "bench": "theorygate",
        "mode": "TheoryGate pipeline (10 conservative statuses, evidence packs)",
        "public_wording": PUBLIC_WORDING,
        "seed": seed, "n_cases": len(results),
        "deterministic_cert_hashes": deterministic,
        "status_tally": status_tally,
        "results": results, "score": score.to_dict(),
    }
