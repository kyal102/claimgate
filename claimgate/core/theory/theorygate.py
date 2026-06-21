"""TheoryGate pipeline: composes all gates, produces evidence pack + status.

Pipeline order (conservative, short-circuit on first failure):
  1. Structural completeness  -> THEORY_INCOMPLETE (if core fields missing)
  2. VariableGate             -> VARIABLES_UNDEFINED / UNITS_UNDEFINED
  3. UnitGate (via PhysicsGate) -> DIMENSIONALLY_INVALID (preserve NEEDS_EXPERIMENT)
  4. KnownLawGate             -> KNOWN_LIMIT_CONFLICT
  5. FalsifiabilityGate       -> NOT_FALSIFIABLE
  6. PredictionGate           -> NO_TESTABLE_PREDICTION
  7. Final routing:
     - requires_simulation True  -> NEEDS_SIMULATION
     - requires_experiment True  -> NEEDS_EXPERIMENT
     - otherwise                 -> CANDIDATE_THEORY (NEVER "proven true")

CANDIDATE_THEORY means "passed all structural gates; worth simulating/
experimenting." It does NOT mean the theory is correct.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import List, Optional

from .model import (
    TheoryClaim, ALL_THEORY_STATUSES, PUBLIC_WORDING,
)
from .gates import (
    VariableGate, KnownLawGate, FalsifiabilityGate, PredictionGate,
)
from ..physics.unitgate import UnitGate
from ..physics.claimbench import PhysicsClaimBench, PhysicsBenchClaim


@dataclass
class EvidencePack:
    """The full evidence pack for a theory claim."""
    theory_name: str
    raw_claim: str
    category: str
    parsed_variables: List[dict]
    units_dimensions: List[dict]
    equations_checked: List[dict]
    physics_gate_result: dict
    known_law_checklist_result: dict
    falsifiability_result: dict
    prediction_result: dict
    final_status: str
    certificate_hash: str
    limitations: List[str]
    next_required_validation: str

    def to_dict(self) -> dict:
        return {
            "theory_name": self.theory_name,
            "raw_claim": self.raw_claim,
            "category": self.category,
            "parsed_variables": self.parsed_variables,
            "units_dimensions": self.units_dimensions,
            "equations_checked": self.equations_checked,
            "physics_gate_result": self.physics_gate_result,
            "known_law_checklist_result": self.known_law_checklist_result,
            "falsifiability_result": self.falsifiability_result,
            "prediction_result": self.prediction_result,
            "final_status": self.final_status,
            "certificate_hash": self.certificate_hash,
            "limitations": self.limitations,
            "next_required_validation": self.next_required_validation,
        }


class TheoryGate:
    """The main pipeline. Stateless; all methods are pure functions."""

    def __init__(self):
        self.var_gate = VariableGate()
        self.known_law_gate = KnownLawGate()
        self.fals_gate = FalsifiabilityGate()
        self.pred_gate = PredictionGate()
        self.unit_gate = UnitGate()

    def evaluate(self, theory: TheoryClaim) -> EvidencePack:
        # 1. Structural completeness
        if not theory.theory_name.strip() or not theory.raw_claim.strip():
            return self._pack(theory, "THEORY_INCOMPLETE",
                              {}, {}, [], {}, {}, {}, {},
                              next_validation="provide theory name and raw claim")

        # 2. VariableGate
        vr = self.var_gate.check(theory)
        if vr.verdict == "VARIABLES_UNDEFINED":
            return self._pack(theory, "VARIABLES_UNDEFINED",
                              vr.to_dict(), {}, [], {}, {}, {}, {},
                              next_validation="define all variables with name and meaning")
        if vr.verdict == "UNITS_UNDEFINED":
            return self._pack(theory, "UNITS_UNDEFINED",
                              vr.to_dict(), {}, [], {}, {}, {}, {},
                              next_validation="assign valid units to all variables")

        # 3. UnitGate (route each equation through dimensional analysis)
        eq_results = []
        any_invalid = False
        any_needs_experiment = False
        for eq in theory.equations:
            ur = self.unit_gate.check_claim(eq.lhs_unit, eq.rhs_units)
            eq_results.append({
                "id": eq.id, "statement": eq.statement,
                "verdict": ur.verdict,
                "lhs_dimension": ur.lhs_dimension,
                "rhs_dimension": ur.rhs_dimension,
                "note": ur.note,
            })
            if ur.verdict == "DIMENSIONALLY_INVALID":
                any_invalid = True
            # preserve NEEDS_EXPERIMENT-style routing from PhysicsGate context
            # (UnitGate itself only returns dimensional verdicts; the experiment
            # flag comes from the theory's category + requires_experiment)
        physics_result = {
            "equations_checked": len(eq_results),
            "any_dimensionally_invalid": any_invalid,
            "equations": eq_results,
        }
        if any_invalid:
            return self._pack(theory, "DIMENSIONALLY_INVALID",
                              vr.to_dict(), self._units_dim(theory), eq_results,
                              physics_result, {}, {}, {},
                              next_validation="fix dimensional inconsistencies")

        # 4. KnownLawGate
        kr = self.known_law_gate.check(theory)
        if kr.verdict == "KNOWN_LIMIT_CONFLICT":
            return self._pack(theory, "KNOWN_LIMIT_CONFLICT",
                              vr.to_dict(), self._units_dim(theory), eq_results,
                              physics_result, kr.to_dict(), {}, {},
                              next_validation="resolve known-law limit conflicts")

        # 5. FalsifiabilityGate
        fr = self.fals_gate.check(theory)
        if fr.verdict == "NOT_FALSIFIABLE":
            return self._pack(theory, "NOT_FALSIFIABLE",
                              vr.to_dict(), self._units_dim(theory), eq_results,
                              physics_result, kr.to_dict(), fr.to_dict(), {},
                              next_validation="state falsifiable conditions")

        # 6. PredictionGate
        pr = self.pred_gate.check(theory)
        if pr.verdict == "NO_TESTABLE_PREDICTION":
            return self._pack(theory, "NO_TESTABLE_PREDICTION",
                              vr.to_dict(), self._units_dim(theory), eq_results,
                              physics_result, kr.to_dict(), fr.to_dict(), pr.to_dict(),
                              next_validation="provide complete measurable predictions")

        # 7. Final routing
        if theory.requires_simulation:
            final = "NEEDS_SIMULATION"
            next_val = "run simulation to test predictions"
        elif theory.requires_experiment:
            final = "NEEDS_EXPERIMENT"
            next_val = "run experiment to test predictions"
        else:
            final = "CANDIDATE_THEORY"
            next_val = ("passed all structural gates; requires simulation, "
                        "experiment, and peer review (NOT proven true)")

        return self._pack(theory, final,
                          vr.to_dict(), self._units_dim(theory), eq_results,
                          physics_result, kr.to_dict(), fr.to_dict(), pr.to_dict(),
                          next_validation=next_val)

    def _units_dim(self, theory: TheoryClaim) -> dict:
        from ..physics.dimensions import lookup_unit
        out = {}
        for v in theory.variables:
            d = lookup_unit(v.unit_name)
            out[v.name] = {
                "unit_name": v.unit_name,
                "dimension": d.canonical_string() if d else None,
            }
        return out

    def _pack(self, theory: TheoryClaim, status: str,
              var_result: dict, units_dim: dict, eq_results: list,
              physics_result: dict, known_law_result: dict,
              fals_result: dict, pred_result: dict,
              next_validation: str) -> EvidencePack:
        # certificate hash: deterministic over (theory_name, status, key gate verdicts)
        cert_input = "|".join([
            theory.theory_name, status,
            str(var_result.get("verdict", "")),
            str(physics_result.get("any_dimensionally_invalid", "")),
            str(known_law_result.get("verdict", "")),
            str(fals_result.get("verdict", "")),
            str(pred_result.get("verdict", "")),
        ])
        cert_hash = hashlib.sha256(cert_input.encode("utf-8")).hexdigest()
        limitations = [
            "TheoryGate is a structural check; it does not prove new physics.",
            "Known-law checklist is declarative; TheoryGate does not re-derive physics.",
            "CANDIDATE_THEORY means 'worth investigating', never 'proven true'.",
            "Final validation requires simulation, experiment, or peer review.",
        ]
        return EvidencePack(
            theory_name=theory.theory_name,
            raw_claim=theory.raw_claim,
            category=theory.category,
            parsed_variables=[v.to_dict() for v in theory.variables],
            units_dimensions=units_dim,
            equations_checked=eq_results,
            physics_gate_result=physics_result,
            known_law_checklist_result=known_law_result,
            falsifiability_result=fals_result,
            prediction_result=pred_result,
            final_status=status,
            certificate_hash=cert_hash,
            limitations=limitations,
            next_required_validation=next_validation,
        )


__all__ = ["TheoryGate", "EvidencePack"]
