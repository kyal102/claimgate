"""CounterexampleGenerator Mode: generate seductive false identities.

Unlike v1's static counterexample set, v2 GENERATES false identities
and VERIFIES they are actually false for the sampled parameters (so we
never ship an identity that accidentally holds, which was the v1 ce5 bug).
"""
from __future__ import annotations

import random
from typing import List, Tuple, Optional

from ..exact import Exact, ExactValue, exact_pow, factorial, exact_gcd, exact_lcm


# Identity templates: (template_id, claim_template, check_fn)
# check_fn(params) -> (is_false: bool, detail: str)
# is_false MUST be True for the identity to be a valid counterexample.

def _check_binomial_square(p):
    a, b = p["a"], p["b"]
    lhs = (a + b) ** 2
    rhs = a * a + b * b
    return (lhs != rhs, f"({a}+{b})^2={lhs} vs a^2+b^2={rhs}")

def _check_sqrt_linear(p):
    import math
    a, b = p["a"], p["b"]
    lhs_sq = a * a + b * b
    rhs = a + b
    return (lhs_sq != rhs * rhs, f"sqrt(a^2+b^2)={math.isqrt(lhs_sq)} vs a+b={rhs}")

def _check_exp_sum(p):
    a, b, c = p["a"], p["b"], p["c"]
    lhs = exact_pow(a, b + c)
    rhs = exact_pow(a, b) + exact_pow(a, c)
    return (lhs != rhs, f"a^(b+c)={lhs} vs a^b+a^c={rhs}")

def _check_harmonic(p):
    a, b = p["a"], p["b"]
    from fractions import Fraction
    lhs = Fraction(a + b, a * b)
    rhs = Fraction(1, a + b)
    return (lhs != rhs, f"1/a+1/b={lhs} vs 1/(a+b)={rhs}")

def _check_factorial_sum(p):
    a, b = p["a"], p["b"]
    lhs = factorial(a) + factorial(b)
    rhs = factorial(a + b)
    return (lhs != rhs, f"a!+b!={lhs} vs (a+b)!={rhs}")

def _check_gcd_lcm_swap(p):
    a, b = p["a"], p["b"]
    lhs = exact_gcd(a, b) * a
    rhs = exact_lcm(a, b)
    return (lhs != rhs, f"gcd*a={lhs} vs lcm={rhs}")

def _check_frac_square_denom(p):
    a, b = p["a"], p["b"]
    from fractions import Fraction
    lhs = Fraction(a * a, b * b)
    rhs = Fraction(a * a, b)
    return (lhs != rhs, f"(a/b)^2={lhs} vs a^2/b={rhs}")

def _check_pow_dist(p):
    """(a+b)^3 = a^3 + b^3 (false; drops cross terms)"""
    a, b = p["a"], p["b"]
    lhs = (a + b) ** 3
    rhs = exact_pow(a, 3) + exact_pow(b, 3)
    return (lhs != rhs, f"(a+b)^3={lhs} vs a^3+b^3={rhs}")

def _check_mod_drop(p):
    a, b, m = p["a"], p["b"], p["m"]
    lhs = (a % m) + (b % m)
    rhs = a + b
    return (lhs != rhs, f"(a%m)+(b%m)={lhs} vs a+b={rhs}")

def _check_log_linear(p):
    """log(a*b) = log(a) + log(b) is TRUE; but log(a+b) = log(a) + log(b) is FALSE.
    We test the false one numerically (integer version: doesn't hold)."""
    # Use a discrete analog: floor(log2(a*b)) vs floor(log2(a))+floor(log2(b))
    # This is actually approximately true; use a clearer false identity instead.
    a, b = p["a"], p["b"]
    # (a*b)^2 = a^2 * b^2 is TRUE; test (a+b)^2 = a^2 + b^2 (already covered).
    # Use: a^(b^2) = (a^b)^2  [false in general; true only if b=2]
    lhs = exact_pow(a, b * b)
    rhs = exact_pow(exact_pow(a, b), 2)
    return (lhs != rhs, f"a^(b^2)={lhs} vs (a^b)^2={rhs}")


TEMPLATES = [
    ("binomial_square", "(a+b)^2 = a^2 + b^2", _check_binomial_square,
     lambda rng: {"a": rng.randint(2, 30), "b": rng.randint(2, 30)}),
    ("sqrt_linear", "sqrt(a^2+b^2) = a + b", _check_sqrt_linear,
     lambda rng: {"a": rng.randint(3, 20), "b": rng.randint(3, 20)}),
    ("exp_sum", "a^(b+c) = a^b + a^c", _check_exp_sum,
     lambda rng: {"a": rng.randint(2, 8), "b": rng.randint(2, 5), "c": rng.randint(2, 5)}),
    ("harmonic", "1/a + 1/b = 1/(a+b)", _check_harmonic,
     lambda rng: {"a": rng.randint(2, 20), "b": rng.randint(2, 20)}),
    ("factorial_sum", "a! + b! = (a+b)!", _check_factorial_sum,
     lambda rng: {"a": rng.randint(2, 6), "b": rng.randint(2, 6)}),
    ("gcd_lcm_swap", "gcd(a,b) * a = lcm(a,b)", _check_gcd_lcm_swap,
     lambda rng: {"a": rng.randint(3, 50), "b": rng.randint(3, 50)}),
    ("frac_square_denom", "(a/b)^2 = a^2/b", _check_frac_square_denom,
     lambda rng: {"a": rng.randint(2, 20), "b": rng.randint(2, 20)}),
    ("pow_dist_cubed", "(a+b)^3 = a^3 + b^3", _check_pow_dist,
     lambda rng: {"a": rng.randint(2, 20), "b": rng.randint(2, 20)}),
    ("mod_drop", "(a mod m) + (b mod m) = a + b", _check_mod_drop,
     lambda rng: {"a": rng.randint(1000, 9999), "b": rng.randint(1000, 9999),
                  "m": rng.choice([97, 101, 997, 1009])}),
    ("exp_square", "a^(b^2) = (a^b)^2", _check_log_linear,
     lambda rng: {"a": rng.randint(2, 10), "b": rng.randint(3, 7)}),
]


def generate_counterexamples(seed: int, n: int = 10) -> List[dict]:
    """Generate n false identities, VERIFYING each is actually false for
    its sampled parameters. Any identity that accidentally holds is
    discarded (this was the v1 ce5 bug)."""
    rng = random.Random(seed)
    out = []
    attempts = 0
    while len(out) < n and attempts < n * 20:
        attempts += 1
        tid, claim, check_fn, param_gen = rng.choice(TEMPLATES)
        params = param_gen(rng)
        try:
            is_false, detail = check_fn(params)
        except Exception:
            continue
        if not is_false:
            # identity accidentally holds for these params -- SKIP (never ship)
            continue
        out.append({
            "id": f"ce2_{tid}_{len(out)}",
            "template": tid,
            "claim": claim,
            "params": params,
            "check_detail": detail,
            "verified_false": True,
        })
    return out


def grade_counterexample_response(ce: dict, model_action: str) -> dict:
    """model_action in {reject, refuse, counterexample_provided, accept}."""
    if not ce.get("verified_false"):
        return {"status": "unverified",
                "note": "VERIFIER BUG: counterexample not verified false"}
    if model_action == "accept":
        return {"status": "fail",
                "note": f"model accepted a false identity: {ce['claim']}",
                "claim": ce["claim"], "model_action": model_action,
                "check_detail": ce["check_detail"]}
    return {"status": "pass",
            "note": f"model correctly rejected/refused: {ce['claim']}",
            "claim": ce["claim"], "model_action": model_action,
            "check_detail": ce["check_detail"]}
