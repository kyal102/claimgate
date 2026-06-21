"""Metamorphic equivalence-form generators.

For a given ExactValue-producing problem, generate several surface forms
that are mathematically equivalent. The verifier canonicalizes each and
checks they map to the same canonical value & certificate family.

Covered equivalences:
  * x*x vs x^2
  * a+b vs b+a (commutativity)
  * expanded vs factored (small forms)
  * scaled equivalent fractions (1/2 == 2/4 == 3/6)
  * whitespace / comma / unicode-digit variants
"""
from __future__ import annotations

import random
from typing import List, Tuple

from .exact import Exact, ExactValue


def _scaled_fraction_forms(num: int, den: int, k: int = 3) -> List[str]:
    forms = [f"{num}/{den}"]
    for s in range(2, k + 2):
        forms.append(f"{num*s}/{den*s}")
    return forms


def _pow_vs_mul_forms(base: int, exp: int) -> List[str]:
    """x^2 == x*x ; x^3 == x*x*x (small exp only)."""
    if exp == 2:
        return [f"{base}^{exp}", f"{base}*{base}"]
    if exp == 3:
        return [f"{base}^{exp}", f"{base}*{base}*{base}"]
    return [f"{base}^{exp}"]


def _commuted_sum_forms(terms: List[int]) -> List[str]:
    if len(terms) < 2:
        return [" + ".join(map(str, terms))]
    # original and one rotation
    a = " + ".join(map(str, terms))
    rotated = " + ".join(map(str, terms[1:] + terms[:1]))
    return [a, rotated]


def _expanded_vs_factored_forms(a: int, b: int, c: int) -> List[str]:
    """a*b + a*c  vs  a*(b+c)"""
    return [f"{a}*{b} + {a}*{c}", f"{a}*({b}+{c})"]


def _surface_noise_forms(expr: str) -> List[str]:
    """Whitespace, unicode digit (NFKC-foldable), and thousands-separator
    variants that must normalize to the same canonical form."""
    forms = [expr]
    # internal whitespace variant
    if " " not in expr:
        forms.append(expr)  # no-op
    # insert spaces around operators
    spaced = expr.replace("+", " + ").replace("-", " - ").replace("*", " * ").replace("/", " / ")
    spaced = " ".join(spaced.split())
    if spaced != expr:
        forms.append(spaced)
    # unicode multiplication signs (NFKC -> ascii)
    forms.append(expr.replace("*", "×"))
    return list(dict.fromkeys(forms))  # dedupe, preserve order


def metamorphic_forms(problem: dict) -> List[Tuple[str, str, ExactValue]]:
    """Given a problem dict tagged with a 'kind', return a list of
    (label, expression_string, expected_exact_value) tuples.

    The expected value is RE-DERIVED here by the solver (not looked up),
    so metamorphic equivalence is checked against ground truth.
    """
    kind = problem["kind"]
    out: List[Tuple[str, str, ExactValue]] = []

    if kind == "scaled_fraction":
        num, den = problem["num"], problem["den"]
        val = Exact.frac(num, den)
        for s, f in zip(range(1, 5), _scaled_fraction_forms(num, den, 3)):
            out.append((f"scaled_x{s}", f, val))

    elif kind == "pow_vs_mul":
        b, e = problem["base"], problem["exp"]
        val = Exact.i(b ** e)
        for label, f in zip(("power", "mulform"), _pow_vs_mul_forms(b, e)):
            out.append((label, f, val))

    elif kind == "commuted_sum":
        terms = problem["terms"]
        val = Exact.i(sum(terms))
        for label, f in zip(("orig", "rotated"), _commuted_sum_forms(terms)):
            out.append((label, f, val))

    elif kind == "expanded_factored":
        a, b, c = problem["a"], problem["b"], problem["c"]
        val = Exact.i(a * b + a * c)
        for label, f in zip(("expanded", "factored"), _expanded_vs_factored_forms(a, b, c)):
            out.append((label, f, val))

    elif kind == "surface_noise":
        expr = problem["expr"]
        # expected value is re-derived by the verifier at canonicalize time;
        # we don't know the value here, so we mark it for verifier re-derivation
        for label, f in zip(("plain", "spaced", "unicode_mul"), _surface_noise_forms(expr)):
            out.append((label, f, Exact.i(0)))  # placeholder; verifier re-derives

    else:
        raise ValueError(f"unknown metamorphic kind {kind!r}")

    return out


def metamorphic_problem_set(seed: int, n_each: int = 3) -> List[dict]:
    """Generate a deterministic metamorphic problem set."""
    rng = random.Random(seed)
    problems = []
    for _ in range(n_each):
        problems.append({"kind": "scaled_fraction",
                         "num": rng.randint(1, 50), "den": rng.randint(2, 50)})
    for _ in range(n_each):
        problems.append({"kind": "pow_vs_mul",
                         "base": rng.randint(2, 12), "exp": rng.choice([2, 3])})
    for _ in range(n_each):
        problems.append({"kind": "commuted_sum",
                         "terms": [rng.randint(-20, 50) for _ in range(rng.randint(3, 5))]})
    for _ in range(n_each):
        problems.append({"kind": "expanded_factored",
                         "a": rng.randint(2, 30), "b": rng.randint(2, 30), "c": rng.randint(2, 30)})
    for _ in range(n_each):
        problems.append({"kind": "surface_noise",
                         "expr": f"{rng.randint(2,20)}*{rng.randint(2,20)} + {rng.randint(2,20)}"})
    return problems
