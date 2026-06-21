"""UnitGate bench: dimensional analysis verification with cert hashing."""
from __future__ import annotations
import hashlib
from ...core.physics import UnitGate, UNIT_CLAIMS, unit_gate_score, PUBLIC_WORDING

def run_physics_unitgate(seed: int = 20260624, model=None) -> dict:
    gate = UnitGate()
    results = []
    for claim in UNIT_CLAIMS:
        gr = gate.check_claim(claim.lhs_unit, claim.rhs_units)
        # cert hash: deterministic over (claim_id, lhs_dim, rhs_dim, verdict)
        cert_input = f"{claim.id}|{gr.lhs_dimension}|{gr.rhs_dimension}|{gr.verdict}"
        cert_hash = hashlib.sha256(cert_input.encode()).hexdigest()
        consistent = (gr.verdict == claim.expected_verdict)
        results.append({
            "id": claim.id, "statement": claim.statement,
            "verdict": gr.verdict, "expected": claim.expected_verdict,
            "self_consistent": consistent,
            "lhs_dimension": gr.lhs_dimension, "rhs_dimension": gr.rhs_dimension,
            "note": gr.note, "why": claim.why,
            "certificate_hash": cert_hash,
        })
    # determinism check: re-run and verify same hashes
    rerun_hashes = []
    for claim in UNIT_CLAIMS:
        gr = gate.check_claim(claim.lhs_unit, claim.rhs_units)
        cert_input = f"{claim.id}|{gr.lhs_dimension}|{gr.rhs_dimension}|{gr.verdict}"
        rerun_hashes.append(hashlib.sha256(cert_input.encode()).hexdigest())
    first_hashes = [r["certificate_hash"] for r in results]
    deterministic = (rerun_hashes == first_hashes)
    score = unit_gate_score(results)
    return {
        "bench": "physics_unitgate",
        "mode": "Dimensional analysis (exact rational exponents, no floats)",
        "public_wording": PUBLIC_WORDING,
        "seed": seed, "n_cases": len(results),
        "deterministic_cert_hashes": deterministic,
        "results": results, "score": score.to_dict(),
    }
