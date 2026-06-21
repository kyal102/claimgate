"""Dimensional analysis foundation: base dimensions, units, quantities.

Uses EXACT rational exponents (fractions.Fraction) — never floats — so
dimensional consistency checks are exact, not approximate.

Seven SI base dimensions:
  M  mass
  L  length
  T  time
  I  electric current
  Θ  temperature
  N  amount of substance
  J  luminous intensity

A Dimension is a mapping {base_dim: rational_exponent}. Dimensionless = {}.
Compound units (newton, joule, watt, etc.) are defined as named aliases.

This is the foundation of UnitGate: a physics equation is dimensionally
valid iff both sides have identical Dimension.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Dict, Optional, Tuple

# Base dimension symbols
BASE_DIMS = ("M", "L", "T", "I", "THETA", "N", "J")


@dataclass(frozen=True)
class Dimension:
    """A physical dimension as a mapping of base-dim -> rational exponent.

    Dimensionless quantities (pure numbers) have an empty mapping.
    """
    exponents: Dict[str, Fraction] = field(default_factory=dict)

    @classmethod
    def dimensionless(cls) -> "Dimension":
        return cls(exponents={})

    @classmethod
    def from_pairs(cls, *pairs: Tuple[str, object]) -> "Dimension":
        """Build from (base_dim, exponent) pairs. Exponent may be int or Fraction."""
        exps: Dict[str, Fraction] = {}
        for dim, exp in pairs:
            e = Fraction(exp)
            if e != 0:
                exps[dim] = exps.get(dim, Fraction(0)) + e
                if exps[dim] == 0:
                    del exps[dim]
        return cls(exponents=exps)

    def __mul__(self, other: "Dimension") -> "Dimension":
        out = dict(self.exponents)
        for d, e in other.exponents.items():
            out[d] = out.get(d, Fraction(0)) + e
            if out[d] == 0:
                del out[d]
        return Dimension(exponents=out)

    def __truediv__(self, other: "Dimension") -> "Dimension":
        out = dict(self.exponents)
        for d, e in other.exponents.items():
            out[d] = out.get(d, Fraction(0)) - e
            if out[d] == 0:
                del out[d]
        return Dimension(exponents=out)

    def __pow__(self, exp: object) -> "Dimension":
        e = Fraction(exp)
        if e == 0:
            return Dimension.dimensionless()
        return Dimension(exponents={d: v * e for d, v in self.exponents.items()})

    def __eq__(self, other) -> bool:
        if not isinstance(other, Dimension):
            return NotImplemented
        return self.exponents == other.exponents

    def __hash__(self) -> int:
        return hash(tuple(sorted(self.exponents.items())))

    def is_dimensionless(self) -> bool:
        return len(self.exponents) == 0

    def canonical_string(self) -> str:
        """Stable canonical string for hashing/comparison."""
        if not self.exponents:
            return "1"
        parts = []
        for d in BASE_DIMS:
            if d in self.exponents:
                e = self.exponents[d]
                if e == 1:
                    parts.append(d)
                else:
                    parts.append(f"{d}^{e}")
        # include any non-base dims (defensive)
        for d in sorted(self.exponents):
            if d not in BASE_DIMS:
                e = self.exponents[d]
                parts.append(f"{d}^{e}" if e != 1 else d)
        return "*".join(parts) if parts else "1"

    def display(self) -> str:
        return self.canonical_string()


# --- Named base dimensions -------------------------------------------------

MASS = Dimension.from_pairs(("M", 1))
LENGTH = Dimension.from_pairs(("L", 1))
TIME = Dimension.from_pairs(("T", 1))
CURRENT = Dimension.from_pairs(("I", 1))
TEMPERATURE = Dimension.from_pairs(("THETA", 1))
AMOUNT = Dimension.from_pairs(("N", 1))
LUMINOUS_INTENSITY = Dimension.from_pairs(("J", 1))
DIMENSIONLESS = Dimension.dimensionless()


# --- Named derived units (SI + common physics) -----------------------------
# Each maps a unit name to its Dimension. This is the table UnitGate consults.

UNIT_TABLE: Dict[str, Dimension] = {
    # base
    "kg": MASS, "g": MASS, "mass": MASS,
    "m": LENGTH, "cm": LENGTH, "mm": LENGTH, "km": LENGTH, "length": LENGTH, "distance": LENGTH,
    "s": TIME, "sec": TIME, "time": TIME,
    "A": CURRENT, "amp": CURRENT, "current": CURRENT,
    "K": TEMPERATURE, "temperature": TEMPERATURE,
    "mol": AMOUNT, "amount": AMOUNT,
    "cd": LUMINOUS_INTENSITY,

    # derived (mechanics)
    "velocity": LENGTH / TIME, "speed": LENGTH / TIME,
    "acceleration": LENGTH / (TIME ** 2),
    "force": MASS * LENGTH / (TIME ** 2),       # newton
    "energy": MASS * (LENGTH ** 2) / (TIME ** 2),  # joule
    "work": MASS * (LENGTH ** 2) / (TIME ** 2),
    "power": MASS * (LENGTH ** 2) / (TIME ** 3),    # watt
    "pressure": MASS / (LENGTH * (TIME ** 2)),      # pascal
    "momentum": MASS * LENGTH / TIME,
    "angular_momentum": MASS * (LENGTH ** 2) / TIME,
    "torque": MASS * (LENGTH ** 2) / (TIME ** 2),
    "frequency": DIMENSIONLESS / TIME,              # hertz
    "area": LENGTH ** 2,
    "volume": LENGTH ** 3,
    "density": MASS / (LENGTH ** 3),

    # derived (electromagnetic)
    "charge": CURRENT * TIME,                       # coulomb
    "voltage": MASS * (LENGTH ** 2) / (CURRENT * (TIME ** 3)),  # volt
    "resistance": MASS * (LENGTH ** 2) / (CURRENT ** 2 * (TIME ** 3)),  # ohm
    "capacitance": (CURRENT ** 2) * (TIME ** 4) / (MASS * (LENGTH ** 2)),  # farad
    "magnetic_field": MASS / (CURRENT * (TIME ** 2)),  # tesla
    "electric_field": MASS * LENGTH / (CURRENT * (TIME ** 3)),

    # derived (thermodynamic / other)
    "entropy": MASS * (LENGTH ** 2) / (TIME ** 2 * TEMPERATURE),
    "heat": MASS * (LENGTH ** 2) / (TIME ** 2),
    "specific_heat": (LENGTH ** 2) / (TIME ** 2 * TEMPERATURE),
}


def lookup_unit(name: str) -> Optional[Dimension]:
    """Look up a unit name (case-insensitive). Returns None if unknown."""
    return UNIT_TABLE.get(name.lower())


@dataclass(frozen=True)
class Quantity:
    """A physical quantity: a value (ExactValue) paired with a Dimension.

    For UnitGate we mostly care about the Dimension, but the value is
    carried for completeness and for downstream gates (uncertainty, etc.).
    """
    value_label: str   # symbolic label, e.g. "F", "m", "a" -- not a number
    dimension: Dimension

    def display(self) -> str:
        return f"{self.value_label} [{self.dimension.display()}]"
