"""TheoryGate v0: structural check for proposed physics theories.

TheoryGate does NOT prove new physics or a universal theory. It checks
whether a proposed theory is structured enough to be TESTED:

  * are all variables defined with units?
  * do the equations pass dimensional analysis (via PhysicsGate/UnitGate)?
  * does it reduce to known physics in supported limits (checklist, not proof)?
  * is it falsifiable?
  * does it make a measurable prediction?

Public wording:
  "TheoryGate checks whether a proposed physics theory is mathematically
   structured, dimensionally coherent, falsifiable, and prediction-bearing.
   It does not prove new physics or replace simulation, experiment, or
   peer review."

This module defines the data model. The pipeline lives in theorygate.py.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from ..physics.dimensions import Dimension, lookup_unit
from ..physics.unitgate import PhysicsClaim


# The 10 canonical TheoryGate statuses (no others may be emitted)
ALL_THEORY_STATUSES = [
    "THEORY_INCOMPLETE",
    "VARIABLES_UNDEFINED",
    "UNITS_UNDEFINED",
    "DIMENSIONALLY_INVALID",
    "KNOWN_LIMIT_CONFLICT",
    "NOT_FALSIFIABLE",
    "NO_TESTABLE_PREDICTION",
    "NEEDS_SIMULATION",
    "NEEDS_EXPERIMENT",
    "CANDIDATE_THEORY",
]

PUBLIC_WORDING = (
    "TheoryGate checks whether a proposed physics theory is mathematically "
    "structured, dimensionally coherent, falsifiable, and prediction-bearing. "
    "It does not prove new physics or replace simulation, experiment, or peer review."
)


@dataclass
class Variable:
    """A variable in a proposed theory."""
    name: str              # e.g. "F", "m", "a"
    meaning: str           # e.g. "force", "mass", "acceleration"
    unit_name: str         # e.g. "force", "mass", "acceleration" (looked up in UNIT_TABLE)

    def is_named(self) -> bool:
        return bool(self.name and self.name.strip())

    def has_meaning(self) -> bool:
        return bool(self.meaning and self.meaning.strip())

    def has_valid_unit(self) -> bool:
        return lookup_unit(self.unit_name) is not None

    def to_dict(self) -> dict:
        return {"name": self.name, "meaning": self.meaning, "unit_name": self.unit_name}


@dataclass
class KnownLawCheck:
    """One item in the known-law reduction checklist.

    The theory DECLARES which limits it claims to satisfy, and whether the
    check passes. TheoryGate does NOT re-derive physics; it verifies the
    checklist is structurally complete and flags declared failures.
    """
    limit_type: str        # "newtonian" | "conservation_energy" | "inverse_square" | "limit_zero" | "limit_infinity"
    description: str
    passes: Optional[bool] # True=passes, False=fails (conflict), None=not checked
    note: str = ""


@dataclass
class Prediction:
    """A measurable prediction made by the theory."""
    observable: str        # what to measure (e.g. "orbital precession")
    condition: str         # setup (e.g. "Mercury perihelion")
    expected_value: str    # expected deviation/value (symbolic or numeric)
    unit_name: str         # unit (looked up)
    required_measurement: str  # "simulation" or "experiment" or specific instrument

    def is_complete(self) -> bool:
        return all([self.observable.strip(), self.condition.strip(),
                    self.expected_value.strip(), self.unit_name.strip(),
                    self.required_measurement.strip()])

    def has_valid_unit(self) -> bool:
        return lookup_unit(self.unit_name) is not None

    def to_dict(self) -> dict:
        return {"observable": self.observable, "condition": self.condition,
                "expected_value": self.expected_value, "unit_name": self.unit_name,
                "required_measurement": self.required_measurement,
                "complete": self.is_complete(), "valid_unit": self.has_valid_unit()}


@dataclass
class TheoryClaim:
    """A proposed physics theory, structured for TheoryGate evaluation."""
    theory_name: str
    raw_claim: str
    category: str          # for TheoryBench routing (see bench_claims.py)
    variables: List[Variable] = field(default_factory=list)
    equations: List[PhysicsClaim] = field(default_factory=list)  # for UnitGate routing
    known_law_checks: List[KnownLawCheck] = field(default_factory=list)
    falsifiable_conditions: List[str] = field(default_factory=list)
    predictions: List[Prediction] = field(default_factory=list)
    # routing hints (set by the bench; pipeline respects them when all gates pass)
    requires_simulation: bool = False
    requires_experiment: bool = False
    expected_final_status: str = ""   # for self-consistency check
    why: str = ""

    def is_structurally_complete(self) -> bool:
        """A theory is structurally complete if it has at least: variables,
        at least one equation, at least one known-law check, at least one
        falsifiable condition, and at least one prediction."""
        return bool(self.variables and self.equations and self.known_law_checks
                    and self.falsifiable_conditions and self.predictions)


__all__ = [
    "ALL_THEORY_STATUSES", "PUBLIC_WORDING",
    "Variable", "KnownLawCheck", "Prediction", "TheoryClaim",
]
