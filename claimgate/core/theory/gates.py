"""TheoryGate sub-gates: variable, known-law, falsifiability, prediction.

Each gate returns a structured result. The main TheoryGate pipeline
(theorygate.py) composes these and produces the final conservative status.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .model import Variable, KnownLawCheck, Prediction, TheoryClaim


# === VariableGate ========================================================

@dataclass
class VariableGateResult:
    verdict: str   # "VARIABLES_OK" | "VARIABLES_UNDEFINED" | "UNITS_UNDEFINED"
    undefined_variables: List[str] = field(default_factory=list)
    undefined_units: List[str] = field(default_factory=list)
    note: str = ""

    def to_dict(self) -> dict:
        return {"verdict": self.verdict,
                "undefined_variables": self.undefined_variables,
                "undefined_units": self.undefined_units,
                "note": self.note}


class VariableGate:
    """Checks that all variables are named, have meaning, and have valid units."""

    def check(self, theory: TheoryClaim) -> VariableGateResult:
        if not theory.variables:
            return VariableGateResult("VARIABLES_UNDEFINED",
                                      note="no variables declared")
        undef_vars = []
        undef_units = []
        for v in theory.variables:
            if not v.is_named() or not v.has_meaning():
                undef_vars.append(v.name or "<unnamed>")
            if not v.has_valid_unit():
                undef_units.append(v.unit_name or "<no unit>")
        if undef_vars:
            return VariableGateResult("VARIABLES_UNDEFINED",
                                      undefined_variables=undef_vars,
                                      note=f"variables undefined: {undef_vars}")
        if undef_units:
            return VariableGateResult("UNITS_UNDEFINED",
                                      undefined_units=undef_units,
                                      note=f"units undefined: {undef_units}")
        return VariableGateResult("VARIABLES_OK",
                                  note=f"all {len(theory.variables)} variables defined with units")


# === KnownLawGate ========================================================

@dataclass
class KnownLawGateResult:
    verdict: str   # "KNOWN_LAW_OK" | "KNOWN_LIMIT_CONFLICT" | "KNOWN_LAW_INCOMPLETE"
    failing_checks: List[str] = field(default_factory=list)
    unchecked: List[str] = field(default_factory=list)
    note: str = ""

    def to_dict(self) -> dict:
        return {"verdict": self.verdict, "failing_checks": self.failing_checks,
                "unchecked": self.unchecked, "note": self.note}


class KnownLawGate:
    """Checks the known-law reduction checklist.

    This is a CHECKLIST, not proof of physical truth. A theory must DECLARE
    which limits it claims to satisfy. If a declared check FAILS, that's a
    KNOWN_LIMIT_CONFLICT. If essential checks are missing entirely, the
    theory is incomplete (but we don't force a specific conflict status).
    """

    def check(self, theory: TheoryClaim) -> KnownLawGateResult:
        if not theory.known_law_checks:
            return KnownLawGateResult("KNOWN_LAW_INCOMPLETE",
                                      note="no known-law checks declared (checklist empty)")
        failing = []
        unchecked = []
        for c in theory.known_law_checks:
            if c.passes is False:
                failing.append(c.limit_type)
            elif c.passes is None:
                unchecked.append(c.limit_type)
        if failing:
            return KnownLawGateResult("KNOWN_LIMIT_CONFLICT",
                                      failing_checks=failing, unchecked=unchecked,
                                      note=f"failing limits: {failing}")
        if unchecked:
            return KnownLawGateResult("KNOWN_LAW_INCOMPLETE",
                                      unchecked=unchecked,
                                      note=f"unchecked limits: {unchecked} (not a conflict, but incomplete)")
        return KnownLawGateResult("KNOWN_LAW_OK",
                                  note=f"all {len(theory.known_law_checks)} declared checks pass (checklist, not proof)")


# === FalsifiabilityGate ==================================================

@dataclass
class FalsifiabilityResult:
    verdict: str   # "FALSIFIABLE" | "NOT_FALSIFIABLE"
    conditions: List[str] = field(default_factory=list)
    note: str = ""

    def to_dict(self) -> dict:
        return {"verdict": self.verdict, "conditions": self.conditions, "note": self.note}


class FalsifiabilityGate:
    """Requires the theory to state what would prove it wrong."""

    def check(self, theory: TheoryClaim) -> FalsifiabilityResult:
        valid = [c.strip() for c in theory.falsifiable_conditions if c and c.strip()]
        if not valid:
            return FalsifiabilityResult("NOT_FALSIFIABLE",
                                        note="no falsifiable conditions stated")
        return FalsifiabilityResult("FALSIFIABLE", conditions=valid,
                                    note=f"{len(valid)} falsifiable condition(s) stated")


# === PredictionGate ======================================================

@dataclass
class PredictionResult:
    verdict: str   # "HAS_TESTABLE_PREDICTION" | "NO_TESTABLE_PREDICTION"
    predictions: List[dict] = field(default_factory=list)
    note: str = ""

    def to_dict(self) -> dict:
        return {"verdict": self.verdict, "predictions": self.predictions, "note": self.note}


class PredictionGate:
    """Requires at least one measurable prediction with all required fields."""

    def check(self, theory: TheoryClaim) -> PredictionResult:
        if not theory.predictions:
            return PredictionResult("NO_TESTABLE_PREDICTION",
                                    note="no predictions declared")
        valid_preds = []
        incomplete = []
        for p in theory.predictions:
            if not p.is_complete():
                incomplete.append(p.observable or "<incomplete>")
                continue
            if not p.has_valid_unit():
                incomplete.append(f"{p.observable} (invalid unit: {p.unit_name})")
                continue
            valid_preds.append(p.to_dict())
        if not valid_preds:
            return PredictionResult("NO_TESTABLE_PREDICTION",
                                    predictions=[],
                                    note=f"all predictions incomplete: {incomplete}")
        return PredictionResult("HAS_TESTABLE_PREDICTION",
                                predictions=valid_preds,
                                note=f"{len(valid_preds)} testable prediction(s)")


__all__ = [
    "VariableGate", "VariableGateResult",
    "KnownLawGate", "KnownLawGateResult",
    "FalsifiabilityGate", "FalsifiabilityResult",
    "PredictionGate", "PredictionResult",
]
