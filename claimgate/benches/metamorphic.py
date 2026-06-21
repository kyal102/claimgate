"""Metamorphic Consistency Mode.

Generate equivalent forms of the same expression and verify they map to
the same canonical result / linked certificate family.
"""
from __future__ import annotations

from typing import List

from ..core.metamorphic import metamorphic_problem_set, metamorphic_forms
from ..core.verifier import Verifier
from ..core.canonical import canonicalize
from ..core.scores import metamorphic_stability_score
from ..adapters import StubAdapter


def run_metamorphic(seed: int = 20260622, n_each: int = 3, model=None) -> dict:
    model = model or StubAdapter(seed=seed)
    v = Verifier()
    problems = metamorphic_problem_set(seed, n_each=n_each)
    pair_results: List[dict] = []
    detail = []
    for i, prob in enumerate(problems):
        forms = metamorphic_forms(prob)
        if len(forms) < 2:
            continue
        # compare form[0] to every other form
        base_label, base_expr, _ = forms[0]
        for label, expr, _ in forms[1:]:
            try:
                equiv, ca, cb, va, vb = v.verify_metamorphic_pair(base_expr, expr)
            except Exception as e:
                equiv = False
                ca = cb = f"ERR:{e}"
                va = vb = None
            rec = {
                "problem_index": i,
                "kind": prob["kind"],
                "form_a": base_expr,
                "form_b": expr,
                "canonical_a": ca,
                "canonical_b": cb,
                "value_a": va.canonical_string() if va else None,
                "value_b": vb.canonical_string() if vb else None,
                "equivalent": bool(equiv),
            }
            pair_results.append(rec)
            detail.append(rec)
    score = metamorphic_stability_score(pair_results)
    return {
        "bench": "metamorphic",
        "mode": "Metamorphic consistency",
        "seed": seed,
        "n_problems": len(problems),
        "n_pairs": len(pair_results),
        "n_cases": len(pair_results),
        "results": detail,
        "score": score.to_dict(),
    }
