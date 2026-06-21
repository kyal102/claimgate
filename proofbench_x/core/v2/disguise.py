"""ExpressionDisguise Mode: many equivalent forms of the same expression.

Includes expanded, factored, reordered, whitespace, unicode, and
alternate operator forms. Scored by canonical equivalence and linked
certificate family.
"""
from __future__ import annotations

import random
from typing import List, Tuple

from ..exact import Exact, ExactValue
from ..canonical import canonicalize, parse_expression, _eval_node


def _disguise_forms(base: str) -> List[Tuple[str, str]]:
    """Given a base expression, return (label, disguised_form) pairs."""
    forms = [("base", base)]
    # whitespace variant
    spaced = base.replace("+", " + ").replace("-", " - ").replace("*", " * ").replace("/", " / ")
    spaced = " ".join(spaced.split())
    if spaced != base:
        forms.append(("spaced", spaced))
    # unicode operators
    u = base.replace("*", "×").replace("/", "÷")
    forms.append(("unicode_ops", u))
    # unicode minus on negatives is handled by NFKC
    # alternate: a+a -> 2*a (only for simple cases)
    # expanded vs factored: a*(b+c) vs a*b+a*c
    return forms


def disguise_problem_set(seed: int, n: int = 8) -> List[dict]:
    """Generate a set of disguise problems. Each has a base expression and
    a list of disguised forms; the verifier checks all map to the same
    canonical value."""
    rng = random.Random(seed)
    problems = []
    for i in range(n):
        kind = rng.choice(["poly2", "poly3", "frac_prod", "gcd_pair", "modpow"])
        if kind == "poly2":
            a, b, c = rng.randint(2, 20), rng.randint(2, 20), rng.randint(2, 20)
            # expanded: a*b + a*c ; factored: a*(b+c)
            problems.append({
                "kind": kind,
                "forms": [
                    ("expanded", f"{a}*{b} + {a}*{c}"),
                    ("factored", f"{a}*({b}+{c})"),
                    ("reordered", f"{a}*{c} + {a}*{b}"),
                ],
            })
        elif kind == "poly3":
            a, x = rng.randint(2, 12), rng.randint(2, 8)
            # a*x^2 vs a*x*x vs a*(x*x)
            problems.append({
                "kind": kind,
                "forms": [
                    ("pow2", f"{a}*{x}^2"),
                    ("mulmul", f"{a}*{x}*{x}"),
                    ("grouped", f"{a}*({x}*{x})"),
                ],
            })
        elif kind == "frac_prod":
            a, b, c, d = (rng.randint(1, 30) for _ in range(4))
            problems.append({
                "kind": kind,
                "forms": [
                    ("standard", f"{a}/{b} * {c}/{d}"),
                    ("reordered", f"{c}/{d} * {a}/{b}"),
                    # unambiguous: explicit parens around numerator and denominator
                    ("combined_parens", f"({a}*{c})/({b}*{d})"),
                ],
            })
        elif kind == "gcd_pair":
            a, b = rng.randint(1, 10**5), rng.randint(1, 10**5)
            problems.append({
                "kind": kind,
                "forms": [
                    ("gcd_ab", f"gcd({a},{b})"),
                    ("gcd_ba", f"gcd({b},{a})"),
                ],
            })
        elif kind == "modpow":
            base, exp, m = rng.randint(2, 50), rng.randint(10, 100), rng.choice([97, 101, 997])
            problems.append({
                "kind": kind,
                "forms": [
                    ("standard", f"{base}^{exp} mod {m}"),
                    ("spaced", f"{base} ^ {exp} mod {m}"),
                ],
            })
    return problems


def verify_disguise_problem(problem: dict) -> dict:
    """Verify all forms in a disguise problem map to the same canonical value.
    Returns a per-form result + overall equivalence flag."""
    forms = problem["forms"]
    results = []
    canonicals = []
    for label, expr in forms:
        try:
            node = parse_expression(expr)
            val = _eval_node(node)
            can = val.canonical_string()
            results.append({"label": label, "expr": expr, "canonical": can,
                            "value": val.display(), "ok": True})
            canonicals.append(can)
        except Exception as e:
            results.append({"label": label, "expr": expr, "canonical": None,
                            "value": None, "ok": False, "error": str(e)})
            canonicals.append(None)
    # all equivalent iff all canonicals are non-None and equal
    all_equiv = (len(canonicals) > 1 and all(c is not None for c in canonicals)
                 and len(set(canonicals)) == 1)
    return {
        "kind": problem["kind"],
        "forms": results,
        "all_equivalent": all_equiv,
        "canonical": canonicals[0] if canonicals and canonicals[0] else None,
    }
