"""v2 CertificateAttack bench: 20x repeats + formatting variants.

The certificate hash must be computed over the CANONICAL form of the
expression, not the raw input string -- otherwise formatting variants
(spaces, unicode operators) produce different hashes for the same value.
This bench verifies that invariant.
"""
from __future__ import annotations
from ..core.v2 import certificate_attack_cases, grade_certificate_attack, certificate_stability_score
from ..core.canonical import parse_expression, _eval_node, canonicalize
from ..core.certificate import cert_hash

def run_v2_certificate(seed: int = 20260623, n_base: int = 3, reps: int = 20, model=None) -> dict:
    cases = certificate_attack_cases(seed, n_base=n_base, reps=reps)
    results = []
    for case in cases:
        per_variant = []
        for v in case["variants"]:
            try:
                node = parse_expression(v["expr"])
                val = _eval_node(node)
                canon = val.canonical_string()
                # cert hash over CANONICAL problem form, not raw input --
                # formatting variants of the same expression must hash alike
                problem_canon = canonicalize(v["expr"])
                h = cert_hash(problem_canon, canon, "certattack")
                per_variant.append({"rep": v["rep"], "variant": v["variant"],
                                    "expr": v["expr"], "parsed_ok": True,
                                    "value_canonical": canon, "cert_hash": h,
                                    "problem_canonical": problem_canon})
            except Exception as e:
                per_variant.append({"rep": v["rep"], "variant": v["variant"],
                                    "expr": v["expr"], "parsed_ok": False,
                                    "value_canonical": None, "cert_hash": None,
                                    "error": str(e)})
        graded = grade_certificate_attack(case, per_variant)
        graded["per_variant"] = per_variant
        results.append(graded)
    score = certificate_stability_score(results)
    return {"bench": "v2_certificate", "mode": "CertificateAttack (20x + formatting, canonical hash)",
            "seed": seed, "n_cases": len(results), "reps_per_case": reps,
            "results": results, "score": score.to_dict()}
