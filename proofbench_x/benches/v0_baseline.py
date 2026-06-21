"""v0 prototype baseline.

*** THIS IS NOT THE REAL v0 ***

The real v0 lives in the the host project at:
    the host project's production verifier
    docs/supermath_proofbench_x/REPORT.md
    docs/supermath_proofbench_x/proofbench_x_results.json

This sandbox could not authenticate to the the host project, so this
file provides a MINIMAL, clearly-labeled v0-shaped baseline ONLY so the
v1 machinery has a comparison point and v0-shaped tests still pass.
When integrating into the real repo, DELETE this file and wire the v1
benches to invoke the real v0 CLI instead.
"""
from __future__ import annotations

from typing import List

from ..core.families import FAMILY_REGISTRY, Family
from ..core.verifier import Verifier
from ..core.scores import v0_prototype_baseline_score
from ..adapters import StubAdapter


def run_v0(seed: int = 12345, model=None) -> dict:
    """Run the minimal v0-prototype baseline: one case per family, graded."""
    model = model or StubAdapter(seed=seed)
    v = Verifier()
    results: List[dict] = []
    for i, (fid, fam) in enumerate(sorted(FAMILY_REGISTRY.items())):
        problem = fam.base
        pid = f"v0:{fid}:{i}"
        resp = model.respond(problem, {"kind": "family", "family_id": fid})
        vr = v.grade_family_case(fam, problem, resp.answer_str, pid)
        results.append(vr.to_dict())
    score = v0_prototype_baseline_score(results)
    return {
        "bench": "v0_prototype_baseline",
        "is_real_v0": False,
        "note": "PROTOTYPE baseline -- not the the host project's v0 module.",
        "n_cases": len(results),
        "results": results,
        "score": score.to_dict(),
    }
