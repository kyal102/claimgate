"""ConservationGate bench."""
from __future__ import annotations
from ...core.physics import ConservationGate, CONSERVATION_CASES, conservation_gate_score, PUBLIC_WORDING

def run_physics_conservationgate(seed: int = 20260624, model=None) -> dict:
    gate = ConservationGate()
    results = []
    for case in CONSERVATION_CASES:
        r = gate.check(case)
        d = r.to_dict(); d["id"] = case.id; d["description"] = case.description
        d["expected"] = case.expected; d["why"] = case.why
        results.append(d)
    score = conservation_gate_score(results)
    return {
        "bench": "physics_conservationgate",
        "mode": "Conservation checks (basic templates, NOT full conservation-law proof)",
        "public_wording": PUBLIC_WORDING,
        "seed": seed, "n_cases": len(results),
        "results": results, "score": score.to_dict(),
    }
