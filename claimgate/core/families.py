"""Math families and seeded VAR-Lane variant generation.

A Family is a closed, verifiable math problem template. Each family:
  * has a stable id and name
  * generates a base case + N seeded numeric-remap variants
  * exposes a `verify(problem_dict) -> ExactValue` solver that computes
    the exact answer from the problem's parameters (no answer lookup)

VAR-Lane remapping: same reasoning structure, different numbers. The
family only "passes" if ALL its variants pass. This is the basis of the
Variant Consistency Score.

All families use only closed, elementary, verifiable math. No open
problems. No unsolved conjectures. No proof fabrication.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable, Dict, List

from .exact import ExactValue, Exact, exact_pow, exact_mod_pow, factorial, exact_gcd, exact_lcm


@dataclass
class Family:
    id: str
    name: str
    structure: str   # human description of the reasoning structure
    base: Dict       # base-case parameters
    gen_variant: Callable[[random.Random], Dict]   # seeded remap
    render: Callable[[Dict], str]                   # problem -> string
    verify: Callable[[Dict], ExactValue]            # problem -> exact answer (solver)
    lane_id: Callable[[Dict], str]                  # warm-lane cache key


# ---- helpers --------------------------------------------------------------

def _rr(rng, lo, hi):
    return rng.randint(lo, hi)


# ---- F1: integer sum chain ------------------------------------------------

def _f1_gen(rng):
    n = _rr(rng, 3, 6)
    return {"terms": [_rr(rng, -50, 200) for _ in range(n)]}

def _f1_render(p):
    return " + ".join(str(t) for t in p["terms"])

def _f1_verify(p):
    acc = Exact.i(0)
    for t in p["terms"]:
        acc = Exact.add(acc, Exact.i(t))
    return acc

def _f1_lane(p):
    return "f1:sumchain:n=%d" % len(p["terms"])


# ---- F2: rational arithmetic ----------------------------------------------

def _f2_gen(rng):
    return {
        "a": (_rr(rng, 1, 99), _rr(rng, 2, 99)),
        "b": (_rr(rng, 1, 99), _rr(rng, 2, 99)),
        "op": rng.choice(["+", "-", "*", "/"]),
    }

def _f2_render(p):
    (an, ad), (bn, bd) = p["a"], p["b"]
    # Parenthesize rational operands to avoid ambiguous a/b/c parses
    # when op is '/' (e.g. "3/4 / 5/6" is ambiguous; "(3/4)/(5/6)" is not)
    a_str = f"({an}/{ad})" if p["op"] == "/" else f"{an}/{ad}"
    b_str = f"({bn}/{bd})" if p["op"] == "/" else f"{bn}/{bd}"
    return f"{a_str} {p['op']} {b_str}"

def _f2_verify(p):
    (an, ad), (bn, bd) = p["a"], p["b"]
    a = Exact.frac(an, ad)
    b = Exact.frac(bn, bd)
    op = p["op"]
    if op == "+":
        return Exact.add(a, b)
    if op == "-":
        return Exact.add(a, Exact.mul(b, Exact.i(-1)))
    if op == "*":
        return Exact.mul(a, b)
    if op == "/":
        if bn == 0:
            raise ZeroDivisionError("division by zero fraction")
        inv = Exact.frac(bd, bn)
        return Exact.mul(a, inv)
    raise ValueError(op)

def _f2_lane(p):
    return f"f2:ratarith:op={p['op']}"


# ---- F3: modular exponentiation ------------------------------------------

def _f3_gen(rng):
    return {
        "base": _rr(rng, 2, 999),
        "exp": _rr(rng, 10, 2000),
        "mod": rng.choice([997, 1009, 1013, 1000000007, 7919, 65537]),
    }

def _f3_render(p):
    return f"{p['base']}^{p['exp']} mod {p['mod']}"

def _f3_verify(p):
    return Exact.mod(exact_mod_pow(p["base"], p["exp"], p["mod"]), p["mod"])

def _f3_lane(p):
    return f"f3:modexp:mod={p['mod']}"


# ---- F4: exact power (big integer) ---------------------------------------

def _f4_gen(rng):
    return {"base": _rr(rng, 2, 99), "exp": _rr(rng, 20, 400)}

def _f4_render(p):
    return f"{p['base']}^{p['exp']}"

def _f4_verify(p):
    return Exact.i(exact_pow(p["base"], p["exp"]))

def _f4_lane(p):
    return f"f4:bigpow:base={p['base']}"


# ---- F5: factorial -------------------------------------------------------

def _f5_gen(rng):
    return {"n": _rr(rng, 10, 500)}

def _f5_render(p):
    return f"{p['n']}!"

def _f5_verify(p):
    return Exact.i(factorial(p["n"]))

def _f5_lane(p):
    return "f5:factorial"


# ---- F6: gcd/lcm ---------------------------------------------------------

def _f6_gen(rng):
    a = _rr(rng, 1, 10**6)
    b = _rr(rng, 1, 10**6)
    return {"a": a, "b": b, "op": rng.choice(["gcd", "lcm"])}

def _f6_render(p):
    return f"{p['op']}({p['a']}, {p['b']})"

def _f6_verify(p):
    if p["op"] == "gcd":
        return Exact.i(exact_gcd(p["a"], p["b"]))
    return Exact.i(exact_lcm(p["a"], p["b"]))

def _f6_lane(p):
    return f"f6:{p['op']}"


FAMILY_REGISTRY: Dict[str, Family] = {}


def _register(f: Family):
    FAMILY_REGISTRY[f.id] = f
    return f


_register(Family(
    id="f1_sum_chain", name="Integer sum chain",
    structure="Left-to-right exact integer summation.",
    base=_f1_gen(random.Random(1)),
    gen_variant=_f1_gen, render=_f1_render, verify=_f1_verify, lane_id=_f1_lane,
))
_register(Family(
    id="f2_rational", name="Rational arithmetic",
    structure="Exact fraction add/sub/mul/div.",
    base=_f2_gen(random.Random(2)),
    gen_variant=_f2_gen, render=_f2_render, verify=_f2_verify, lane_id=_f2_lane,
))
_register(Family(
    id="f3_modexp", name="Modular exponentiation",
    structure="Repeated-squaring modular power.",
    base=_f3_gen(random.Random(3)),
    gen_variant=_f3_gen, render=_f3_render, verify=_f3_verify, lane_id=_f3_lane,
))
_register(Family(
    id="f4_bigpow", name="Exact big-integer power",
    structure="Exact exponentiation preserving all digits.",
    base=_f4_gen(random.Random(4)),
    gen_variant=_f4_gen, render=_f4_render, verify=_f4_verify, lane_id=_f4_lane,
))
_register(Family(
    id="f5_factorial", name="Exact factorial",
    structure="Exact product 1..n preserving all digits.",
    base=_f5_gen(random.Random(5)),
    gen_variant=_f5_gen, render=_f5_render, verify=_f5_verify, lane_id=_f5_lane,
))
_register(Family(
    id="f6_gcd_lcm", name="GCD / LCM",
    structure="Euclidean gcd and lcm.",
    base=_f6_gen(random.Random(6)),
    gen_variant=_f6_gen, render=_f6_render, verify=_f6_verify, lane_id=_f6_lane,
))


def make_variants(family: Family, count: int, master_seed: int) -> List[Dict]:
    """Generate `count` seeded numeric-remap variants of a family.

    Deterministic: same (family, count, master_seed) -> same variants, always.
    """
    rng = random.Random((master_seed * 1_000_003) ^ hash(family.id))
    out = []
    seen = set()
    safety = 0
    while len(out) < count and safety < count * 50:
        safety += 1
        v = family.gen_variant(rng)
        key = family.render(v)
        if key in seen:
            continue
        seen.add(key)
        out.append(v)
    if len(out) < count:
        # degenerate fallback: pad with re-seeded distinct params
        while len(out) < count:
            rng2 = random.Random((master_seed * 7) ^ len(out) ^ hash(family.id))
            out.append(family.gen_variant(rng2))
    return out
