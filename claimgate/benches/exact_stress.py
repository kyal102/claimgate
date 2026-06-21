"""Exactness Stress Mode.

Long exact arithmetic chains, rational chains, modular arithmetic, and
10k+ digit exact-preservation tests. A scientific-summary-only result
does NOT count as exact unless the full exact value is preserved in the
certificate/result object.
"""
from __future__ import annotations

import random
from typing import List

from ..core.exact import exact_pow, exact_mod_pow, factorial
from ..core.verifier import Verifier
from ..core.scores import Score
from ..adapters import StubAdapter


def _big_pow_chain(rng):
    # 10k+ digit preservation: 2^33222 has 10000+ digits
    return {"value": exact_pow(2, rng.choice([33222, 33223, 40000]))}

def _factorial_chain(rng):
    # 1000! has 2568 digits; 3000! has ~9131 digits
    return {"value": factorial(rng.choice([1000, 1500, 3000]))}

def _mod_chain(rng):
    m = 10**9 + 7
    base = rng.randint(2, 10**6)
    exp = rng.randint(10**5, 10**6)
    return {"value": exact_mod_pow(base, exp, m)}

def _rational_chain(rng):
    # exact product of many fractions
    from fractions import Fraction
    acc = Fraction(1)
    for _ in range(50):
        acc *= Fraction(rng.randint(1, 99), rng.randint(1, 99))
    return {"value": acc}


def run_exact_stress(seed: int = 20260622, n_big=4, n_fac=3, n_mod=5, n_rat=4, model=None) -> dict:
    model = model or StubAdapter(seed=seed)
    v = Verifier()
    rng = random.Random(seed)
    cases = []
    results: List[dict] = []

    for i in range(n_big):
        c = _big_pow_chain(rng); c["subkind"] = "bigint_10k_plus"
        cases.append((f"es_big_{i}", c))
    for i in range(n_fac):
        c = _factorial_chain(rng); c["subkind"] = "factorial_chain"
        cases.append((f"es_fac_{i}", c))
    for i in range(n_mod):
        c = _mod_chain(rng); c["subkind"] = "modular_chain"
        cases.append((f"es_mod_{i}", c))
    for i in range(n_rat):
        c = _rational_chain(rng); c["subkind"] = "rational_chain"
        cases.append((f"es_rat_{i}", c))

    for pid, c in cases:
        val = c["value"]
        # For int-valued cases, use the exactness preservation check.
        # For rational, convert to a canonical "num/den" string and check.
        if isinstance(val, int):
            resp = model.respond({"value": val}, {"kind": "exactness"})
            vr = v.check_exact_preservation(val, resp.answer_str)
            d = vr.to_dict(); d["subkind"] = c["subkind"]; d["digits"] = len(str(abs(val)))
            results.append(d)
        else:
            # rational: ask model to produce exact num/den
            from fractions import Fraction
            true_str = f"{val.numerator}/{val.denominator}"
            # stub: produce exact half the time, garbled otherwise
            resp = model.respond({"value": val}, {"kind": "exactness"})
            got = resp.answer_str.strip()
            ok = (got == true_str)
            results.append({
                "problem_id": pid, "family": "exactness",
                "status": "pass" if ok else "fail",
                "expected": true_str, "got": got,
                "certificate": None,
                "subkind": c["subkind"], "digits_num": len(str(abs(val.numerator))),
                "note": resp.note,
            })

    passed = sum(1 for r in results if r["status"] == "pass")
    score = Score("Exactness Stress Score", passed / len(results) if results else 0.0,
                  len(results), f"{passed}/{len(results)} exact-preservation cases passed")
    return {
        "bench": "exact_stress",
        "mode": "Exactness stress (10k+ digit preservation)",
        "n_cases": len(results),
        "results": results,
        "score": score.to_dict(),
    }
