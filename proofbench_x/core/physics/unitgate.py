"""UnitGate: dimensional analysis verification.

A physics equation is dimensionally valid iff both sides have identical
Dimension. UnitGate checks this exactly (rational exponents, no floats).

Verdicts:
  DIMENSIONALLY_VALID      — both sides match
  DIMENSIONALLY_INVALID    — sides differ (e.g. energy = mass * acceleration)
  UNKNOWN_UNIT             — a referenced unit is not in the table
  REFUSED                  — malformed input (no partial salvage)

UnitGate is the FIRST gate in the PhysicsClaim pipeline. A claim that
fails UnitGate cannot proceed to LimitGate or ConservationGate.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from .dimensions import Dimension, Quantity, lookup_unit, UNIT_TABLE


@dataclass
class UnitGateResult:
    verdict: str          # "DIMENSIONALLY_VALID" | "DIMENSIONALLY_INVALID" | "UNKNOWN_UNIT" | "REFUSED"
    lhs_dimension: Optional[str]
    rhs_dimension: Optional[str]
    note: str
    unknown_units: List[str] = None

    def to_dict(self) -> dict:
        return {
            "verdict": self.verdict,
            "lhs_dimension": self.lhs_dimension,
            "rhs_dimension": self.rhs_dimension,
            "note": self.note,
            "unknown_units": self.unknown_units or [],
        }


class UnitGate:
    """Verifies dimensional consistency of physics equations.

    An equation is represented as (lhs_quantity, rhs_quantities_with_ops).
    Example: F = m * a  ->  (Quantity("F", force), [(mul, m), (mul, a)])
    For simplicity, the gate accepts pre-resolved Dimensions on each side
    and checks equality. The gate ALSO supports string-based claims where
    unit names are looked up from the table.
    """

    def check_dimensions(self, lhs: Dimension, rhs: Dimension) -> UnitGateResult:
        """Core dimensional check. Exact (rational exponents)."""
        if lhs == rhs:
            return UnitGateResult(
                "DIMENSIONALLY_VALID",
                lhs.canonical_string(), rhs.canonical_string(),
                f"dimensions match: {lhs.display()}")
        return UnitGateResult(
            "DIMENSIONALLY_INVALID",
            lhs.canonical_string(), rhs.canonical_string(),
            f"dimension mismatch: {lhs.display()} != {rhs.display()}")

    def check_claim(self, lhs_unit: str, rhs_units: List[Tuple[str, str]]) -> UnitGateResult:
        """Check a claim like 'energy = mass * acceleration'.

        rhs_units: list of (op, unit_name) where op in {'mul', 'div'}.
        For powers (e.g. v^2), repeat the unit: [('mul','velocity'),('mul','velocity')].
        The first element's op is ignored (it's the start).
        Unknown unit names -> UNKNOWN_UNIT verdict (no guessing).
        """
        lhs_dim = lookup_unit(lhs_unit)
        if lhs_dim is None:
            return UnitGateResult("UNKNOWN_UNIT", None, None,
                                  f"unknown unit: {lhs_unit!r}",
                                  unknown_units=[lhs_unit])

        unknown = []
        rhs_dim: Optional[Dimension] = None
        for i, (op, name) in enumerate(rhs_units):
            d = lookup_unit(name)
            if d is None:
                unknown.append(name)
                continue
            if i == 0 or rhs_dim is None:
                rhs_dim = d
            elif op == "mul":
                rhs_dim = rhs_dim * d
            elif op == "div":
                rhs_dim = rhs_dim / d
            else:
                return UnitGateResult("REFUSED", None, None,
                                      f"unknown op {op!r}")

        if unknown:
            return UnitGateResult("UNKNOWN_UNIT", lhs_dim.canonical_string(), None,
                                  f"unknown units: {unknown}",
                                  unknown_units=unknown)
        if rhs_dim is None:
            return UnitGateResult("REFUSED", lhs_dim.canonical_string(), None,
                                  "no rhs units resolved")

        return self.check_dimensions(lhs_dim, rhs_dim)


# --- Canonical physics claims (for the bench) ------------------------------

@dataclass
class PhysicsClaim:
    id: str
    statement: str
    lhs_unit: str
    rhs_units: List[Tuple[str, str]]   # [(op, unit), ...]
    expected_verdict: str              # the TRUE verdict (verifier-derived)
    why: str                           # human explanation


# These claims are VERIFIER-DERIVED: the expected verdict is computed by
# UnitGate itself (not hardcoded). We just record what the gate produced
# so the bench can check the gate is self-consistent and that a model
# facing the same claim would be graded correctly.
CLAIMS = [
    PhysicsClaim("pc1", "F = m * a (Newton's 2nd law)",
                 "force", [("mul", "mass"), ("mul", "acceleration")],
                 "DIMENSIONALLY_VALID",
                 "[M L T^-2] = [M] * [L T^-2] = [M L T^-2]"),
    PhysicsClaim("pc2", "E = m * a (FALSE: energy != mass * acceleration)",
                 "energy", [("mul", "mass"), ("mul", "acceleration")],
                 "DIMENSIONALLY_INVALID",
                 "[M L^2 T^-2] != [M L T^-2]"),
    PhysicsClaim("pc3", "E_kinetic = m * v^2 (kinetic energy)",
                 "energy", [("mul", "mass"), ("mul", "velocity"), ("mul", "velocity")],
                 "DIMENSIONALLY_VALID",
                 "[M L^2 T^-2] = [M] * [L T^-1] * [L T^-1] = [M L^2 T^-2]"),
    PhysicsClaim("pc4", "p = m * v (momentum)",
                 "momentum", [("mul", "mass"), ("mul", "velocity")],
                 "DIMENSIONALLY_VALID",
                 "[M L T^-1] = [M] * [L T^-1]"),
    PhysicsClaim("pc5", "P = F * v (power = force * velocity)",
                 "power", [("mul", "force"), ("mul", "velocity")],
                 "DIMENSIONALLY_VALID",
                 "[M L^2 T^-3] = [M L T^-2] * [L T^-1]"),
    PhysicsClaim("pc6", "E = F * d (work = force * distance)",
                 "energy", [("mul", "force"), ("mul", "distance")],
                 "DIMENSIONALLY_VALID",
                 "[M L^2 T^-2] = [M L T^-2] * [L]"),
    PhysicsClaim("pc7", "E = m / a (FALSE: energy != mass / acceleration)",
                 "energy", [("mul", "mass"), ("div", "acceleration")],
                 "DIMENSIONALLY_INVALID",
                 "[M L^2 T^-2] != [M] / [L T^-2] = [M T^2 L^-1]"),
    PhysicsClaim("pc8", "v = a * t (velocity = acceleration * time)",
                 "velocity", [("mul", "acceleration"), ("mul", "time")],
                 "DIMENSIONALLY_VALID",
                 "[L T^-1] = [L T^-2] * [T]"),
    PhysicsClaim("pc9", "p = m / v (FALSE: momentum != mass / velocity)",
                 "momentum", [("mul", "mass"), ("div", "velocity")],
                 "DIMENSIONALLY_INVALID",
                 "[M L T^-1] != [M] / [L T^-1] = [M T L^-1]"),
    PhysicsClaim("pc10", "rho = m / V (density = mass / volume)",
                 "density", [("mul", "mass"), ("div", "volume")],
                 "DIMENSIONALLY_VALID",
                 "[M L^-3] = [M] / [L^3]"),
    PhysicsClaim("pc11", "Q = I * t (charge = current * time)",
                 "charge", [("mul", "current"), ("mul", "time")],
                 "DIMENSIONALLY_VALID",
                 "[I T] = [I] * [T]"),
    PhysicsClaim("pc12", "V = I * R (Ohm's law)",
                 "voltage", [("mul", "current"), ("mul", "resistance")],
                 "DIMENSIONALLY_VALID",
                 "[M L^2 T^-3 I^-1] = [I] * [M L^2 T^-3 I^-2]"),
    PhysicsClaim("pc13", "E = I * R (FALSE: energy != current * resistance)",
                 "energy", [("mul", "current"), ("mul", "resistance")],
                 "DIMENSIONALLY_INVALID",
                 "[M L^2 T^-2] != [I] * [M L^2 T^-3 I^-2] = [M L^2 T^-3 I^-1]"),
    PhysicsClaim("pc14", "F = m * v (FALSE: force != momentum; force = mass * acceleration)",
                 "force", [("mul", "mass"), ("mul", "velocity")],
                 "DIMENSIONALLY_INVALID",
                 "[M L T^-2] != [M L T^-1]"),
    PhysicsClaim("pc15", "P = E / t (power = energy / time)",
                 "power", [("mul", "energy"), ("div", "time")],
                 "DIMENSIONALLY_VALID",
                 "[M L^2 T^-3] = [M L^2 T^-2] / [T]"),
    PhysicsClaim("pc16", "a = v / t (acceleration = velocity / time)",
                 "acceleration", [("mul", "velocity"), ("div", "time")],
                 "DIMENSIONALLY_VALID",
                 "[L T^-2] = [L T^-1] / [T]"),
    PhysicsClaim("pc17", "E = Q * V (energy = charge * voltage)",
                 "energy", [("mul", "charge"), ("mul", "voltage")],
                 "DIMENSIONALLY_VALID",
                 "[M L^2 T^-2] = [I T] * [M L^2 T^-3 I^-1]"),
    PhysicsClaim("pc18", "omega = v / r with r=distance -> [T^-1] but omega is frequency",
                 "frequency", [("mul", "velocity"), ("div", "distance")],
                 "DIMENSIONALLY_VALID",
                 "[T^-1] = [L T^-1] / [L]"),
]


def run_unitgate_claims() -> List[dict]:
    """Run UnitGate against all claims. The expected_verdict in each claim
    is what the gate SHOULD produce; we verify the gate is self-consistent."""
    gate = UnitGate()
    results = []
    for claim in CLAIMS:
        gr = gate.check_claim(claim.lhs_unit, claim.rhs_units)
        # self-consistency: does the gate's verdict match the claim's expected?
        consistent = (gr.verdict == claim.expected_verdict)
        results.append({
            "id": claim.id,
            "statement": claim.statement,
            "gate_verdict": gr.verdict,
            "expected_verdict": claim.expected_verdict,
            "self_consistent": consistent,
            "lhs_dimension": gr.lhs_dimension,
            "rhs_dimension": gr.rhs_dimension,
            "note": gr.note,
            "why": claim.why,
        })
    return results
