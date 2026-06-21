"""v2 ExactnessTorture bench."""
from __future__ import annotations
from ..core.v2 import exactness_torture_set, exactness_preservation_score
from ..core.verifier import Verifier
from ..core.exact import Exact, parse_int_strict
from ..adapters import StubAdapter

def run_v2_exactness(seed: int = 20260623, model=None) -> dict:
    model = model or StubAdapter(seed=seed)
    v = Verifier()
    cases = exactness_torture_set(seed)
    results = []
    for i, c in enumerate(cases):
        pid = f"extort_{c['subkind']}_{i}"
        val = c["value"]
        if isinstance(val, int):
            resp = model.respond({"value": val}, {"kind": "exactness"})
            vr = v.check_exact_preservation(val, resp.answer_str)
            d = vr.to_dict(); d["subkind"] = c["subkind"]; d["digits"] = c.get("digits", 0)
            results.append(d)
        elif isinstance(val, __import__("fractions").Fraction):
            true_str = f"{val.numerator}/{val.denominator}"
            resp = model.respond({"value": val}, {"kind": "exactness"})
            got = resp.answer_str.strip()
            ok = (got == true_str)
            results.append({"problem_id": pid, "family": "exactness",
                            "status": "pass" if ok else "fail",
                            "expected": true_str, "got": got,
                            "certificate": None, "subkind": c["subkind"],
                            "note": resp.note})
        else:
            results.append({"problem_id": pid, "status": "unverified",
                            "note": "unsupported value type", "subkind": c["subkind"]})
    score = exactness_preservation_score(results)
    return {"bench": "v2_exactness", "mode": "ExactnessTorture (10k+ digits, determinants)",
            "seed": seed, "n_cases": len(results), "results": results,
            "score": score.to_dict()}
