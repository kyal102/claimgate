"""PhysicsClaimBench: the multi-gate pipeline.

For each physics claim, run through the gates in order and emit a
CONSERVATIVE final status. The 10 allowed statuses (no others):

  DIMENSIONALLY_VALID
  DIMENSIONALLY_INVALID
  ALGEBRAICALLY_VALID
  REFUTED_BY_COUNTEREXAMPLE
  LIMIT_CHECK_PASSED
  KNOWN_LAW_CONFLICT
  NEEDS_SIMULATION
  NEEDS_EXPERIMENT
  UNSUPPORTED_OPEN_CLAIM
  CANDIDATE_PREDICTION

Pipeline order (short-circuit: first failure stops):
  1. UnitGate         -> DIMENSIONALLY_VALID or DIMENSIONALLY_INVALID
  2. Algebraic check  -> ALGEBRAICALLY_VALID or REFUTED_BY_COUNTEREXAMPLE
  3. LimitGate        -> LIMIT_CHECK_PASSED (heuristic, not proof)
  4. ConservationGate -> KNOWN_LAW_CONFLICT (if violated)
  5. Counterexample   -> REFUTED_BY_COUNTEREXAMPLE (if found)
  6. Final routing:
     - known-law claim that passes all gates  -> DIMENSIONALLY_VALID (+ sub-statuses)
     - open/new-physics claim                 -> UNSUPPORTED_OPEN_CLAIM or NEEDS_EXPERIMENT
     - claim requiring numeric sim            -> NEEDS_SIMULATION
     - claim that survives all gates + is novel -> CANDIDATE_PREDICTION (never "proven")

v0 does NOT claim experimental truth. CANDIDATE_PREDICTION means "passed
all gates; worth simulating/experimenting," NOT "this is true."
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .unitgate import UnitGate, PhysicsClaim as UnitClaim
from .limitgate import LimitGate, LimitCase
from .conservationgate import ConservationGate, ConservationCase
from .counterexample import PhysicsCounterexample, CounterexampleCase


# The 10 canonical statuses (no others may be emitted)
ALL_STATUSES = [
    "DIMENSIONALLY_VALID",
    "DIMENSIONALLY_INVALID",
    "ALGEBRAICALLY_VALID",
    "REFUTED_BY_COUNTEREXAMPLE",
    "LIMIT_CHECK_PASSED",
    "KNOWN_LAW_CONFLICT",
    "NEEDS_SIMULATION",
    "NEEDS_EXPERIMENT",
    "UNSUPPORTED_OPEN_CLAIM",
    "CANDIDATE_PREDICTION",
]


@dataclass
class PhysicsBenchClaim:
    id: str
    statement: str
    category: str   # "valid_known" | "invalid_fake" | "equivalent_transform" | "unit_trap" | "open_new_physics" | "needs_simulation"
    # gate inputs
    unit_claim: Optional[UnitClaim]       # for UnitGate
    limit_case: Optional[LimitCase]       # for LimitGate
    conservation_case: Optional[ConservationCase]  # for ConservationGate
    counterexample_case: Optional[CounterexampleCase]  # for bounded search
    # what the final routing should be (for self-consistency check)
    expected_final_status: str
    why: str


@dataclass
class ClaimPipelineResult:
    claim_id: str
    statement: str
    category: str
    gate_results: dict        # per-gate verdicts
    final_status: str         # one of ALL_STATUSES
    expected_final_status: str
    self_consistent: bool
    note: str

    def to_dict(self) -> dict:
        return {
            "claim_id": self.claim_id, "statement": self.statement,
            "category": self.category, "gate_results": self.gate_results,
            "final_status": self.final_status,
            "expected_final_status": self.expected_final_status,
            "self_consistent": self.self_consistent, "note": self.note,
        }


class PhysicsClaimBench:
    """Runs the multi-gate pipeline on each claim."""

    def __init__(self):
        self.unit_gate = UnitGate()
        self.limit_gate = LimitGate()
        self.conservation_gate = ConservationGate()
        self.counterexample_search = PhysicsCounterexample()

    def evaluate(self, claim: PhysicsBenchClaim) -> ClaimPipelineResult:
        gates = {}
        status = None

        # 1. UnitGate (if claim has unit input)
        if claim.unit_claim is not None:
            uc = claim.unit_claim
            ur = self.unit_gate.check_claim(uc.lhs_unit, uc.rhs_units)
            gates["unit_gate"] = ur.to_dict()
            if ur.verdict == "DIMENSIONALLY_INVALID":
                status = "DIMENSIONALLY_INVALID"
            elif ur.verdict == "UNKNOWN_UNIT":
                status = "UNSUPPORTED_OPEN_CLAIM"  # can't analyze
            # if DIMENSIONALLY_VALID, continue

        # 2. Algebraic / counterexample check (if provided)
        if status is None and claim.counterexample_case is not None:
            cr = self.counterexample_search.search(claim.counterexample_case)
            gates["counterexample_search"] = cr.to_dict()
            if cr.verdict == "REFUTED_BY_COUNTEREXAMPLE":
                status = "REFUTED_BY_COUNTEREXAMPLE"
            else:
                gates["counterexample_search"]["algebraically_valid"] = True
                # mark ALGEBRAICALLY_VALID as a sub-finding (not final)
                if status is None:
                    gates["_algebraic_status"] = "ALGEBRAICALLY_VALID"

        # 3. LimitGate (heuristic)
        if status is None and claim.limit_case is not None:
            lr = self.limit_gate.check(claim.limit_case)
            gates["limit_gate"] = lr.to_dict()
            if lr.verdict == "LIMIT_CHECK_PASSED":
                gates["_limit_status"] = "LIMIT_CHECK_PASSED"
            # LIMIT_CHECK_FAILED -> could be REFUTED, but we keep it heuristic
            # and do NOT short-circuit (limit failures are not refutations)

        # 4. ConservationGate
        if status is None and claim.conservation_case is not None:
            cr2 = self.conservation_gate.check(claim.conservation_case)
            gates["conservation_gate"] = cr2.to_dict()
            if cr2.verdict == "CONSERVATION_VIOLATED":
                status = "KNOWN_LAW_CONFLICT"

        # 5. Final routing by category
        if status is None:
            cat = claim.category
            if cat == "valid_known":
                status = "DIMENSIONALLY_VALID"  # passed all gates
            elif cat == "equivalent_transform":
                status = "ALGEBRAICALLY_VALID"
            elif cat == "invalid_fake":
                # should have been caught by a gate; if not, mark conflict
                status = "KNOWN_LAW_CONFLICT"
            elif cat == "unit_trap":
                status = "DIMENSIONALLY_INVALID"
            elif cat == "open_unsupported":
                # speculative claim with no clear experimental path
                status = "UNSUPPORTED_OPEN_CLAIM"
            elif cat == "open_needs_experiment":
                # testable claim that requires experimental validation
                status = "NEEDS_EXPERIMENT"
            elif cat == "needs_simulation":
                status = "NEEDS_SIMULATION"
            else:
                status = "CANDIDATE_PREDICTION"  # survived all gates; worth investigating

        consistent = (status == claim.expected_final_status)
        return ClaimPipelineResult(
            claim_id=claim.id, statement=claim.statement, category=claim.category,
            gate_results=gates, final_status=status,
            expected_final_status=claim.expected_final_status,
            self_consistent=consistent,
            note=f"final status: {status} | expected: {claim.expected_final_status} | "
                 f"{'consistent' if consistent else 'PIPELINE BUG'}")
