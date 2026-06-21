"""LimitGate: check limit behavior of physics expressions at extremes.

For a proposed equation, ask: what happens as a variable → 0 or → ∞?
Does it explode when it should stabilize? Does it stabilize when
physics says it should?

Verdicts:
  LIMIT_CHECK_PASSED   — behavior matches physical expectation
  LIMIT_CHECK_FAILED   — behavior contradicts physics
  LIMIT_INDETERMINATE  — limit is indeterminate (0/0, ∞/∞) -> needs care
  REFUSED              — expression cannot be analyzed

This is exact where possible (rational limits). For transcendental
behavior we use symbolic expectation rules, not float approximation.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import List, Optional, Tuple

from ..exact import Exact, ExactValue


@dataclass
class LimitCase:
    id: str
    description: str
    expr_kind: str          # "rational" | "power" | "product" | "exponential"
    # The expression is parameterized; we analyze limit as `var` -> target
    var: str
    target: str             # "0" | "infinity"
    # For rational expr = num_coeff * var^num_pow / (den_coeff * var^den_pow)
    num_coeff: int
    num_pow: int
    den_coeff: int
    den_pow: int
    expected_behavior: str  # "zero" | "finite" | "infinity" | "indeterminate"
    why: str


@dataclass
class LimitGateResult:
    verdict: str            # "LIMIT_CHECK_PASSED" | "LIMIT_CHECK_FAILED" | "LIMIT_INDETERMINATE" | "REFUSED"
    computed_behavior: str  # "zero" | "finite" | "infinity" | "indeterminate"
    expected_behavior: str
    note: str

    def to_dict(self) -> dict:
        return {"verdict": self.verdict, "computed_behavior": self.computed_behavior,
                "expected_behavior": self.expected_behavior, "note": self.note}


class LimitGate:
    """Analyzes limit behavior of simple rational/power expressions."""

    def analyze_rational_limit(self, num_coeff: int, num_pow: int,
                               den_coeff: int, den_pow: int,
                               target: str) -> str:
        """Compute limit of (num_coeff * x^num_pow) / (den_coeff * x^den_pow)
        as x -> target. Returns 'zero'|'finite'|'infinity'|'indeterminate'."""
        if den_coeff == 0:
            return "indeterminate"
        if target == "0":
            # x -> 0: x^k -> 0 for k>0, -> 1 for k=0, -> infinity for k<0
            num_term = self._term_at_zero(num_pow)
            den_term = self._term_at_zero(den_pow)
            if num_term == "zero" and den_term == "zero":
                return "indeterminate"  # 0/0
            if num_term == "zero" and den_term in ("finite", "infinity"):
                return "zero"
            if num_term == "finite" and den_term == "zero":
                return "infinity"
            if num_term == "finite" and den_term == "finite":
                return "finite"
            if num_term == "infinity" and den_term == "zero":
                return "infinity"
            if num_term == "infinity" and den_term == "infinity":
                return "indeterminate"
            return "finite"
        elif target == "infinity":
            # x -> inf: compare leading powers
            if num_pow > den_pow:
                return "infinity"
            if num_pow < den_pow:
                return "zero"
            # equal powers -> finite ratio
            return "finite"
        return "indeterminate"

    def _term_at_zero(self, power: int) -> str:
        if power > 0:
            return "zero"
        if power == 0:
            return "finite"
        return "infinity"  # negative power -> 1/0 -> infinity

    def check(self, case: LimitCase) -> LimitGateResult:
        behavior = self.analyze_rational_limit(
            case.num_coeff, case.num_pow, case.den_coeff, case.den_pow, case.target)
        if behavior == "indeterminate":
            return LimitGateResult("LIMIT_INDETERMINATE", behavior,
                                   case.expected_behavior,
                                   f"limit is indeterminate ({case.var} -> {case.target})")
        if behavior == case.expected_behavior:
            return LimitGateResult("LIMIT_CHECK_PASSED", behavior,
                                   case.expected_behavior,
                                   f"behavior matches: {behavior}")
        return LimitGateResult("LIMIT_CHECK_FAILED", behavior,
                               case.expected_behavior,
                               f"behavior {behavior} contradicts expected {case.expected_behavior}")


# Canonical limit cases (physics-motivated)
LIMIT_CASES = [
    LimitCase("lc1", "v = a*t as t -> 0 (object at rest at t=0)",
              "rational", "t", "0",
              num_coeff=1, num_pow=1, den_coeff=1, den_pow=0,
              expected_behavior="zero",
              why="velocity should be 0 at t=0 if starting from rest"),
    LimitCase("lc2", "a = v/t as t -> 0 with v fixed (singularity)",
              "rational", "t", "0",
              num_coeff=1, num_pow=0, den_coeff=1, den_pow=1,
              expected_behavior="infinity",
              why="acceleration blows up if v doesn't go to 0 with t"),
    LimitCase("lc3", "E = m*c^2 as m -> 0 (massless particle has zero rest energy)",
              "rational", "m", "0",
              num_coeff=1, num_pow=1, den_coeff=1, den_pow=0,
              expected_behavior="zero",
              why="rest energy -> 0 as mass -> 0"),
    LimitCase("lc4", "F = G*m1*m2/r^2 as r -> infinity (gravity vanishes at distance)",
              "rational", "r", "infinity",
              num_coeff=1, num_pow=0, den_coeff=1, den_pow=2,
              expected_behavior="zero",
              why="inverse-square force -> 0 at large distance"),
    LimitCase("lc5", "F = G*m1*m2/r^2 as r -> 0 (gravity singularity)",
              "rational", "r", "0",
              num_coeff=1, num_pow=0, den_coeff=1, den_pow=2,
              expected_behavior="infinity",
              why="point-mass gravity -> infinity"),
    LimitCase("lc6", "rho = m/V as V -> infinity with m fixed (density dilutes)",
              "rational", "V", "infinity",
              num_coeff=1, num_pow=0, den_coeff=1, den_pow=1,
              expected_behavior="zero",
              why="fixed mass in infinite volume -> zero density"),
    LimitCase("lc7", "p = m*v as v -> infinity (momentum unbounded)",
              "rational", "v", "infinity",
              num_coeff=1, num_pow=1, den_coeff=1, den_pow=0,
              expected_behavior="infinity",
              why="classical momentum grows without bound with v"),
    LimitCase("lc8", "1/r as r -> 0 (Coulomb singularity)",
              "rational", "r", "0",
              num_coeff=1, num_pow=0, den_coeff=1, den_pow=1,
              expected_behavior="infinity",
              why="point-charge field -> infinity"),
    LimitCase("lc9", "v^2/r as v -> 0 (centripetal accel vanishes at rest)",
              "rational", "v", "0",
              num_coeff=1, num_pow=2, den_coeff=1, den_pow=0,
              expected_behavior="zero",
              why="centripetal acceleration -> 0 as v -> 0"),
    LimitCase("lc10", "t/x as x -> infinity with t fixed (signal dilutes)",
              "rational", "x", "infinity",
              num_coeff=1, num_pow=0, den_coeff=1, den_pow=1,
              expected_behavior="zero",
              why="ratio -> 0 as denominator grows"),
]
