"""Tool-Routing Mode.

Score model behavior separately: answer_directly / call_supermath /
refuse / ask_clarification. The model loses points if it answers when
it should verify. The verifier remains the final authority.
"""
from __future__ import annotations

from typing import List

from ..core.routing import ROUTING_CASES
from ..core.scores import tool_routing_score
from ..adapters import StubAdapter


def run_tool_routing(seed: int = 20260622, model=None) -> dict:
    model = model or StubAdapter(seed=seed)
    results: List[dict] = []
    for rt in ROUTING_CASES:
        resp = model.respond(
            {"id": rt.id, "prompt": rt.prompt, "expected": rt.expected},
            {"kind": "routing"},
        )
        matched = (resp.action == rt.expected)
        results.append({
            "problem_id": rt.id,
            "prompt": rt.prompt,
            "expected": rt.expected,
            "got": resp.action,
            "matched_expected": matched,
            "note": resp.note,
            "verifier_can_check": rt.verifier_can_check,
            "why": rt.why,
        })
    score = tool_routing_score(results)
    return {
        "bench": "tool_routing",
        "mode": "Tool-routing correctness",
        "n_cases": len(results),
        "results": results,
        "score": score.to_dict(),
    }
