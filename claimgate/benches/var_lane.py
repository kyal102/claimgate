"""VAR-Lane Mode: numeric remapping.

For each base family, generate 50-500 seeded variants (same reasoning
structure, different numbers). A family passes ONLY if all its variants
pass. Outputs a per-family consistency score.
"""
from __future__ import annotations

from typing import Dict, List

from ..core.families import FAMILY_REGISTRY, make_variants
from ..core.verifier import Verifier
from ..core.scores import variant_consistency_score
from ..adapters import StubAdapter


def run_var_lane(seed: int = 20260622, variants_per_family: int = 50, model=None) -> dict:
    model = model or StubAdapter(seed=seed)
    v = Verifier()
    per_family: Dict[str, List[dict]] = {}
    per_family_detail = {}
    for fid, fam in sorted(FAMILY_REGISTRY.items()):
        variants = make_variants(fam, variants_per_family, seed)
        fam_results = []
        for j, problem in enumerate(variants):
            pid = f"varlane:{fid}:{j}"
            resp = model.respond(problem, {"kind": "family", "family_id": fid})
            vr = v.grade_family_case(fam, problem, resp.answer_str, pid)
            fam_results.append(vr.to_dict())
        per_family[fid] = fam_results
        passed = sum(1 for r in fam_results if r["status"] == "pass")
        per_family_detail[fid] = {
            "n": len(fam_results),
            "passed": passed,
            "fully_consistent": passed == len(fam_results),
            "consistency": passed / len(fam_results) if fam_results else 0.0,
        }
    score = variant_consistency_score(per_family)
    total = sum(len(r) for r in per_family.values())
    return {
        "bench": "var_lane",
        "mode": "VAR-Lane numeric remapping",
        "seed": seed,
        "variants_per_family": variants_per_family,
        "n_cases": total,
        "per_family": per_family_detail,
        "results": {k: v for k, v in per_family.items()},
        "score": score.to_dict(),
    }
