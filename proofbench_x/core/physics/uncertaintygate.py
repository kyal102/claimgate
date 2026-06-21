"""UncertaintyGate: first-pass uncertainty propagation.

Clearly labeled as ESTIMATE / PROPAGATION, not lab validation.

Uses GUM-style linear propagation for independent quantities:
  y = f(x1, ..., xn)
  u(y)^2 = sum_i (df/dxi)^2 * u(xi)^2

For v0 we support the four basic arithmetic operations exactly:
  y = a + b   ->  u(y) = sqrt(u(a)^2 + u(b)^2)
  y = a - b   ->  u(y) = sqrt(u(a)^2 + u(b)^2)
  y = a * b   ->  u(y)/|y| = sqrt((u(a)/a)^2 + (u(b)/b)^2)  [relative]
  y = a / b   ->  u(y)/|y| = sqrt((u(a)/a)^2 + (u(b)/b)^2)  [relative]

The uncertainty value itself is reported as a Decimal-sqrt approximation,
but the PROPAGATION STRUCTURE is exact. The label "estimate" is mandatory
in every output.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, getcontext
from typing import List, Optional, Tuple

# Set high precision for Decimal sqrt
getcontext().prec = 50


@dataclass
class UncertainValue:
    """A value with uncertainty. value and uncertainty are Decimals."""
    value: Decimal
    uncertainty: Decimal

    def display(self) -> str:
        return f"{self.value} ± {self.uncertainty} (estimate)"


@dataclass
class UncertaintyCase:
    id: str
    description: str
    op: str                       # "add" | "sub" | "mul" | "div"
    a: UncertainValue
    b: UncertainValue
    expected_relative_uncertainty: Optional[Decimal]  # for mul/div only; None for add/sub
    expected_absolute_uncertainty: Optional[Decimal]   # for add/sub only
    why: str


@dataclass
class UncertaintyResult:
    verdict: str                  # "PROPAGATED" | "REFUSED"
    result: Optional[UncertainValue]
    note: str
    is_estimate: bool             # always True for v0

    def to_dict(self) -> dict:
        return {"verdict": self.verdict,
                "result": (f"{self.result.value} ± {self.result.uncertainty}"
                           if self.result else None),
                "note": self.note, "is_estimate": self.is_estimate}


def _dec(x) -> Decimal:
    return Decimal(str(x))


def _sqrt_d(x: Decimal) -> Decimal:
    """Decimal square root via Newton's method."""
    if x < 0:
        raise ValueError("sqrt of negative")
    if x == 0:
        return Decimal(0)
    g = x / 2
    for _ in range(100):
        g_new = (g + x / g) / 2
        if abs(g_new - g) < Decimal("1e-40"):
            break
        g = g_new
    return g


class UncertaintyGate:
    """First-pass uncertainty propagation. ESTIMATE ONLY."""

    def propagate(self, op: str, a: UncertainValue, b: UncertainValue) -> UncertaintyResult:
        if op == "add" or op == "sub":
            # u(y) = sqrt(u(a)^2 + u(b)^2)
            u_sq = a.uncertainty ** 2 + b.uncertainty ** 2
            u = _sqrt_d(u_sq)
            val = a.value + b.value if op == "add" else a.value - b.value
            return UncertaintyResult(
                "PROPAGATED", UncertainValue(val, u),
                f"linear propagation ({op}): u = sqrt(u_a^2 + u_b^2) = {u} (estimate)",
                is_estimate=True)
        if op == "mul":
            # relative: u(y)/|y| = sqrt((u(a)/a)^2 + (u(b)/b)^2)
            if a.value == 0 or b.value == 0:
                return UncertaintyResult("REFUSED", None,
                                         "relative uncertainty undefined at zero (estimate)",
                                         is_estimate=True)
            rel_a = a.uncertainty / abs(a.value)
            rel_b = b.uncertainty / abs(b.value)
            rel_y = _sqrt_d(rel_a ** 2 + rel_b ** 2)
            val = a.value * b.value
            u = abs(val) * rel_y
            return UncertaintyResult(
                "PROPAGATED", UncertainValue(val, u),
                f"relative propagation (mul): rel_u = {rel_y} (estimate)",
                is_estimate=True)
        if op == "div":
            if b.value == 0:
                return UncertaintyResult("REFUSED", None,
                                         "division by zero (estimate)", is_estimate=True)
            if a.value == 0:
                return UncertaintyResult("REFUSED", None,
                                         "relative uncertainty undefined at zero (estimate)",
                                         is_estimate=True)
            rel_a = a.uncertainty / abs(a.value)
            rel_b = b.uncertainty / abs(b.value)
            rel_y = _sqrt_d(rel_a ** 2 + rel_b ** 2)
            val = a.value / b.value
            u = abs(val) * rel_y
            return UncertaintyResult(
                "PROPAGATED", UncertainValue(val, u),
                f"relative propagation (div): rel_u = {rel_y} (estimate)",
                is_estimate=True)
        return UncertaintyResult("REFUSED", None, f"unknown op {op!r} (estimate)",
                                 is_estimate=True)


UNCERTAINTY_CASES = [
    UncertaintyCase("uc1", "Add two measurements: 10.0±0.1 + 5.0±0.2",
                    "add",
                    UncertainValue(_dec("10.0"), _dec("0.1")),
                    UncertainValue(_dec("5.0"), _dec("0.2")),
                    expected_absolute_uncertainty=_sqrt_d(_dec("0.01") + _dec("0.04")),
                    expected_relative_uncertainty=None,
                    why="u = sqrt(0.1^2 + 0.2^2) = sqrt(0.05) ≈ 0.224"),
    UncertaintyCase("uc2", "Subtract: 10.0±0.1 - 5.0±0.2",
                    "sub",
                    UncertainValue(_dec("10.0"), _dec("0.1")),
                    UncertainValue(_dec("5.0"), _dec("0.2")),
                    expected_absolute_uncertainty=_sqrt_d(_dec("0.01") + _dec("0.04")),
                    expected_relative_uncertainty=None,
                    why="same as add: u = sqrt(0.05)"),
    UncertaintyCase("uc3", "Multiply: 2.0±0.1 * 3.0±0.2",
                    "mul",
                    UncertainValue(_dec("2.0"), _dec("0.1")),
                    UncertainValue(_dec("3.0"), _dec("0.2")),
                    expected_absolute_uncertainty=None,
                    expected_relative_uncertainty=_sqrt_d((_dec("0.1")/_dec("2.0"))**2 + (_dec("0.2")/_dec("3.0"))**2),
                    why="relative: sqrt(0.05^2 + 0.0667^2) ≈ 0.0833"),
    UncertaintyCase("uc4", "Divide: 6.0±0.3 / 2.0±0.1",
                    "div",
                    UncertainValue(_dec("6.0"), _dec("0.3")),
                    UncertainValue(_dec("2.0"), _dec("0.1")),
                    expected_absolute_uncertainty=None,
                    expected_relative_uncertainty=_sqrt_d((_dec("0.3")/_dec("6.0"))**2 + (_dec("0.1")/_dec("2.0"))**2),
                    why="relative: sqrt(0.05^2 + 0.05^2) = sqrt(0.005) ≈ 0.0707"),
    UncertaintyCase("uc5", "Divide by zero: 5.0±0.1 / 0.0±0.0",
                    "div",
                    UncertainValue(_dec("5.0"), _dec("0.1")),
                    UncertainValue(_dec("0.0"), _dec("0.0")),
                    expected_absolute_uncertainty=None,
                    expected_relative_uncertainty=None,
                    why="must refuse: division by zero"),
]
