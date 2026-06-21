"""v2 ToolRoutingTrap bench."""
from __future__ import annotations
from ..core.v2 import ROUTING_TRAPS, tool_routing_discipline_score
from ..adapters import StubAdapter

def run_v2_routing(seed: int = 20260623, model=None) -> dict:
    model = model or StubAdapter(seed=seed)
    results = []
    for rt in ROUTING_TRAPS:
        resp = model.respond({"id": rt.id, "prompt": rt.prompt, "expected": rt.expected},
                             {"kind": "routing"})
        matched = (resp.action == rt.expected)
        results.append({"problem_id": rt.id, "prompt": rt.prompt,
                        "expected": rt.expected, "got": resp.action,
                        "matched_expected": matched, "note": resp.note,
                        "why": rt.why, "verifier_can_check": rt.verifier_can_check})
    score = tool_routing_discipline_score(results)
    return {"bench": "v2_routing", "mode": "ToolRoutingTrap",
            "seed": seed, "n_cases": len(results), "results": results,
            "score": score.to_dict()}
