"""Counterexample Mode.

Present plausible-but-FALSE identities. The system must reject, refuse,
or produce a counterexample. Never accept seductive false identities.
"""
from __future__ import annotations

from typing import List

from ..core.counterexamples import COUNTEREXAMPLES
from ..core.verifier import Verifier
from ..core.scores import counterexample_safety_score
from ..adapters import StubAdapter


def run_counterexample(seed: int = 20260622, model=None) -> dict:
    model = model or StubAdapter(seed=seed)
    v = Verifier()
    results: List[dict] = []
    for ce in COUNTEREXAMPLES:
        resp = model.respond({"id": ce.id, "claim": ce.claim}, {"kind": "counterexample"})
        vr = v.grade_counterexample(ce, resp.action)
        d = vr.to_dict()
        d["claim"] = ce.claim
        d["why_plausible"] = ce.why_plausible
        d["model_action"] = resp.action
        results.append(d)
    score = counterexample_safety_score(results)
    return {
        "bench": "counterexample",
        "mode": "Counterexample safety",
        "n_cases": len(results),
        "results": results,
        "score": score.to_dict(),
    }
