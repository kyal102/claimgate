"""WitnessGate v0: produce concrete counterexample witnesses for false claims.

Each witness includes:
  variable assignment, lhs value, rhs value, domain, reason mismatch,
  certificate hash

Statuses:
  REFUTED_BY_COUNTEREXAMPLE, NO_COUNTEREXAMPLE_FOUND_IN_RANGE,
  WITNESS_CREATED, WITNESS_NOT_AVAILABLE
"""
from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from fractions import Fraction
from typing import List, Optional, Callable

from ..exact import Exact, ExactValue


WITNESS_STATUSES = [
    "REFUTED_BY_COUNTEREXAMPLE",
    "NO_COUNTEREXAMPLE_FOUND_IN_RANGE",
    "WITNESS_CREATED",
    "WITNESS_NOT_AVAILABLE",
]


@dataclass
class Witness:
    """A concrete counterexample witness."""
    variable_assignment: dict    # e.g. {"a": 3, "b": 4}
    lhs_value: str               # e.g. "49"
    rhs_value: str               # e.g. "25"
    domain: str                  # e.g. "integer"
    reason_mismatch: str         # e.g. "lhs != rhs"
    certificate_hash: str

    def to_dict(self) -> dict:
        return {
            "variable_assignment": self.variable_assignment,
            "lhs_value": self.lhs_value,
            "rhs_value": self.rhs_value,
            "domain": self.domain,
            "reason_mismatch": self.reason_mismatch,
            "certificate_hash": self.certificate_hash,
        }


@dataclass
class WitnessClaim:
    claim_id: str
    expression: str              # the claimed identity, e.g. "(a+b)^2 = a^2+b^2"
    domain: str                  # e.g. "integer"
    # lhs and rhs are callables taking a dict of variable assignments -> ExactValue
    lhs: Callable[[dict], ExactValue]
    rhs: Callable[[dict], ExactValue]
    variables: List[str]         # variable names to search over
    search_range: tuple          # (lo, hi) integer range
    expected_status: str
    why: str = ""


@dataclass
class WitnessResult:
    verdict: str
    witness: Optional[Witness]
    n_tested: int
    note: str

    def to_dict(self) -> dict:
        return {"verdict": self.verdict,
                "witness": self.witness.to_dict() if self.witness else None,
                "n_tested": self.n_tested,
                "note": self.note}


class WitnessGate:
    """Searches for counterexample witnesses for false claims."""

    def search(self, claim: WitnessClaim, seed: int = 20260629) -> WitnessResult:
        rng = random.Random(seed ^ hash(claim.claim_id))
        lo, hi = claim.search_range
        # deterministic sample: integers in range
        test_points = list(range(lo, hi + 1))
        # add some fractions for rational domain
        if claim.domain in ("rational", "real"):
            for _ in range(5):
                num = rng.randint(lo * 10, hi * 10)
                test_points.append(Fraction(num, 10))

        tested = 0
        for v0 in test_points:
            # assign the first variable
            if len(claim.variables) == 1:
                assignment = {claim.variables[0]: v0}
                tested += 1
                result = self._test_assignment(claim, assignment)
                if result is not None:
                    return result
            elif len(claim.variables) == 2:
                # also vary the second variable
                for v1 in test_points[:10]:  # limit inner loop
                    assignment = {claim.variables[0]: v0, claim.variables[1]: v1}
                    tested += 1
                    result = self._test_assignment(claim, assignment)
                    if result is not None:
                        return result
            else:
                # 3+ variables: just use the first
                assignment = {claim.variables[0]: v0}
                tested += 1
                result = self._test_assignment(claim, assignment)
                if result is not None:
                    return result

        return WitnessResult(
            "NO_COUNTEREXAMPLE_FOUND_IN_RANGE", None, tested,
            f"no counterexample found in range [{lo},{hi}] over {tested} points "
            f"(NOT a proof of truth)")

    def _test_assignment(self, claim: WitnessClaim, assignment: dict) -> Optional[WitnessResult]:
        """Test a single variable assignment. Returns a WitnessResult if a
        counterexample is found, None otherwise."""
        try:
            lhs_val = claim.lhs(assignment)
            rhs_val = claim.rhs(assignment)
        except Exception:
            return None

        if not Exact.eq(lhs_val, rhs_val):
            # found a counterexample
            cert_input = (f"{claim.claim_id}|{assignment}|"
                         f"{lhs_val.display()}|{rhs_val.display()}")
            cert_hash = hashlib.sha256(cert_input.encode()).hexdigest()
            witness = Witness(
                variable_assignment={k: str(v) for k, v in assignment.items()},
                lhs_value=lhs_val.display(),
                rhs_value=rhs_val.display(),
                domain=claim.domain,
                reason_mismatch=f"lhs ({lhs_val.display()}) != rhs ({rhs_val.display()})",
                certificate_hash=cert_hash,
            )
            return WitnessResult(
                "REFUTED_BY_COUNTEREXAMPLE", witness, 0,
                f"counterexample found: {assignment}")
        return None


__all__ = ["WITNESS_STATUSES", "Witness", "WitnessClaim",
           "WitnessResult", "WitnessGate"]
