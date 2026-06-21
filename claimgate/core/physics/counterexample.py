"""PhysicsCounterexample: bounded search for values where an equation breaks.

BOUNDED SEARCH ONLY. If no counterexample is found, the verdict is
"NO_COUNTEREXAMPLE_FOUND_IN_RANGE" — NEVER "proven true".

The search is over a finite grid of rational test points. For each
candidate equation lhs(var) =?= rhs(var), we sample N points and check
exact equality. If any point disagrees, we have a counterexample
(REFUTED_BY_COUNTEREXAMPLE). If all agree in the sampled range, we
report NO_COUNTEREXAMPLE_FOUND_IN_RANGE.

This does NOT prove the equation is true everywhere — only that it held
in the tested range.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from fractions import Fraction
from typing import Callable, List, Optional, Tuple

from ..exact import Exact, ExactValue


@dataclass
class CounterexampleCase:
    id: str
    description: str
    # The proposed identity: lhs(var) == rhs(var)
    # Each side is a callable taking a Fraction -> ExactValue
    lhs: Callable[[Fraction], ExactValue]
    rhs: Callable[[Fraction], ExactValue]
    var_name: str
    sample_range: Tuple[int, int]   # integer range to sample
    n_samples: int
    expected: str   # "REFUTED_BY_COUNTEREXAMPLE" | "NO_COUNTEREXAMPLE_FOUND_IN_RANGE"
    why: str


@dataclass
class CounterexampleResult:
    verdict: str
    n_tested: int
    counterexample_value: Optional[str]   # the var value that broke it, if any
    lhs_at_ce: Optional[str]
    rhs_at_ce: Optional[str]
    note: str

    def to_dict(self) -> dict:
        return {"verdict": self.verdict, "n_tested": self.n_tested,
                "counterexample_value": self.counterexample_value,
                "lhs_at_ce": self.lhs_at_ce, "rhs_at_ce": self.rhs_at_ce,
                "note": self.note}


class PhysicsCounterexample:
    """Bounded grid search. Never claims 'proven true'."""

    def search(self, case: CounterexampleCase, seed: int = 20260624) -> CounterexampleResult:
        rng = random.Random(seed ^ hash(case.id))
        lo, hi = case.sample_range
        tested = 0
        # deterministic sample: evenly spaced + a few random rationals
        step = max(1, (hi - lo) // case.n_samples)
        test_points = list(range(lo, hi + 1, step))[:case.n_samples]
        # add some fractions
        for _ in range(min(5, case.n_samples // 3)):
            num = rng.randint(lo * 10, hi * 10)
            test_points.append(Fraction(num, 10))
        for v in test_points:
            tested += 1
            try:
                lhs_val = case.lhs(v)
                rhs_val = case.rhs(v)
            except Exception:
                continue
            if not Exact.eq(lhs_val, rhs_val):
                return CounterexampleResult(
                    "REFUTED_BY_COUNTEREXAMPLE", tested,
                    counterexample_value=str(v),
                    lhs_at_ce=lhs_val.display(),
                    rhs_at_ce=rhs_val.display(),
                    note=f"counterexample found at {case.var_name}={v}: "
                         f"lhs={lhs_val.display()} != rhs={rhs_val.display()}")
        return CounterexampleResult(
            "NO_COUNTEREXAMPLE_FOUND_IN_RANGE", tested,
            counterexample_value=None, lhs_at_ce=None, rhs_at_ce=None,
            note=f"no counterexample found in tested range [{lo},{hi}] over {tested} points "
                 f"(NOT a proof of truth)")


# Helper builders for common expression shapes
def _lin(a, b):
    """Returns f(x) = a*x + b as ExactValue."""
    def f(x):
        return Exact.add(Exact.mul(Exact.i(a), Exact.frac(x.numerator, x.denominator)),
                         Exact.i(b))
    return f

def _const(c):
    def f(x):
        return Exact.i(c)
    return f

def _identity():
    def f(x):
        return Exact.frac(x.numerator, x.denominator)
    return f


COUNTEREXAMPLE_CASES = [
    CounterexampleCase(
        "pec1", "True identity: 2*x = x + x (should NOT be refuted)",
        lhs=lambda x: Exact.mul(Exact.i(2), Exact.frac(x.numerator, x.denominator)),
        rhs=lambda x: Exact.add(Exact.frac(x.numerator, x.denominator),
                                Exact.frac(x.numerator, x.denominator)),
        var_name="x", sample_range=(-10, 10), n_samples=20,
        expected="NO_COUNTEREXAMPLE_FOUND_IN_RANGE",
        why="2x = x+x is a true algebraic identity; no counterexample exists"),
    CounterexampleCase(
        "pec2", "FALSE identity: (a+b)^2 = a^2 + b^2 (should be refuted)",
        lhs=lambda x: Exact.mul(Exact.add(Exact.frac(x.numerator, x.denominator), Exact.i(3)),
                                Exact.add(Exact.frac(x.numerator, x.denominator), Exact.i(3))),
        rhs=lambda x: Exact.add(
            Exact.mul(Exact.frac(x.numerator, x.denominator),
                      Exact.frac(x.numerator, x.denominator)),
            Exact.i(9)),
        var_name="x", sample_range=(-5, 5), n_samples=20,
        expected="REFUTED_BY_COUNTEREXAMPLE",
        why="(x+3)^2 = x^2+6x+9, not x^2+9; counterexample at any x!=0"),
    CounterexampleCase(
        "pec3", "True identity: F = m*a with a=2, so F = 2*m",
        lhs=lambda m: Exact.mul(Exact.i(2), Exact.frac(m.numerator, m.denominator)),
        rhs=lambda m: Exact.mul(Exact.frac(m.numerator, m.denominator), Exact.i(2)),
        var_name="m", sample_range=(1, 100), n_samples=20,
        expected="NO_COUNTEREXAMPLE_FOUND_IN_RANGE",
        why="2m = m*2 by commutativity; no counterexample"),
    CounterexampleCase(
        "pec4", "FALSE claim: E_kinetic = m*v (should be m*v^2/2)",
        lhs=lambda v: Exact.mul(Exact.frac(v.numerator, v.denominator),
                                Exact.frac(v.numerator, v.denominator)),
        rhs=lambda v: Exact.frac(v.numerator, v.denominator),
        var_name="v", sample_range=(-5, 5), n_samples=20,
        expected="REFUTED_BY_COUNTEREXAMPLE",
        why="v^2 != v except at v=0,1; counterexample at v=2"),
]
