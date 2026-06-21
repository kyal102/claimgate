"""AssumptionGate v0: detect hidden assumptions required for common
transformations.

Patterns:
  x/x = 1            requires x != 0
  1/x exists         requires x != 0
  sqrt(x^2) = x      requires x >= 0
  log(a*b)=log(a)+log(b)  requires positive domain
  matrix inverse     requires invertible matrix
  modular division   requires inverse exists
  cancellation       requires nonzero factor

Statuses:
  ASSUMPTIONS_SATISFIED, ASSUMPTIONS_MISSING, CONDITIONALLY_VALID, INVALID_UNDER_DOMAIN
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .domain_gate import DomainGate, DomainClaim

ASSUMPTION_STATUSES = [
    "ASSUMPTIONS_SATISFIED",
    "ASSUMPTIONS_MISSING",
    "CONDITIONALLY_VALID",
    "INVALID_UNDER_DOMAIN",
]

# Hidden assumption patterns: (pattern_name, regex, required_condition, description)
ASSUMPTION_PATTERNS = [
    ("division_by_variable",
     r'(\w+)\s*/\s*\1\s*=\s*1',
     "x != 0",
     "x/x = 1 requires x != 0"),
    ("reciprocal_exists",
     r'1\s*/\s*[\(\s]*(\w+)',
     "x != 0",
     "1/x exists requires x != 0"),
    ("sqrt_square",
     r'sqrt\s*\(\s*(\w+)\s*\^\s*2\s*\)\s*=\s*\1',
     "x >= 0",
     "sqrt(x^2) = x requires x >= 0"),
    ("log_product",
     r'log\s*\(\s*(\w+)\s*\*\s*(\w+)\s*\)\s*=\s*log\s*\(\s*\1\s*\)\s*\+\s*log\s*\(\s*\2\s*\)',
     "positive domain",
     "log(a*b)=log(a)+log(b) requires positive a, b"),
    ("matrix_inverse",
     r'(\w+)\s*\^\s*\(?\s*-\s*1\s*\)?',
     "invertible matrix",
     "matrix inverse requires invertible matrix"),
    ("modular_division",
     r'(\w+)\s*/\s*(\w+)\s*mod\s*(\w+)',
     "inverse exists mod p",
     "modular division requires inverse exists mod p"),
    ("cancellation",
     r'[\(\s]*(\w+)\s*\*\s*(\w+)\s*[\)]?\s*/\s*\1\s*=\s*\2',
     "nonzero factor",
     "cancellation requires nonzero factor"),
]


@dataclass
class AssumptionClaim:
    claim_id: str
    expression: str
    declared_domain: str
    declared_assumptions: List[str] = field(default_factory=list)
    why: str = ""


@dataclass
class AssumptionResult:
    verdict: str
    detected_patterns: List[str] = field(default_factory=list)
    required_assumptions: List[str] = field(default_factory=list)
    missing_assumptions: List[str] = field(default_factory=list)
    note: str = ""

    def to_dict(self) -> dict:
        return {"verdict": self.verdict,
                "detected_patterns": self.detected_patterns,
                "required_assumptions": self.required_assumptions,
                "missing_assumptions": self.missing_assumptions,
                "note": self.note}


class AssumptionGate:
    """Detects hidden assumptions in mathematical expressions."""

    def __init__(self):
        import re
        self._re = re
        self._compiled = [(name, self._re.compile(pat, self._re.IGNORECASE), cond, desc)
                          for name, pat, cond, desc in ASSUMPTION_PATTERNS]

    def check(self, claim: AssumptionClaim) -> AssumptionResult:
        detected = []
        required = []
        for name, regex, cond, desc in self._compiled:
            if regex.search(claim.expression):
                detected.append(name)
                required.append(cond)

        if not detected:
            return AssumptionResult(
                "ASSUMPTIONS_SATISFIED",
                note="no hidden assumptions detected in expression")

        # check which required assumptions are declared
        missing = []
        for req in required:
            req_lower = req.lower().strip()
            # check if the domain itself covers this requirement
            if self._domain_covers(claim.declared_domain, req_lower):
                continue
            # check if any declared assumption covers this requirement
            covered = False
            for decl in claim.declared_assumptions:
                if self._covers(decl, req, claim.declared_domain):
                    covered = True
                    break
            if not covered:
                missing.append(req)

        if missing:
            return AssumptionResult(
                "ASSUMPTIONS_MISSING",
                detected_patterns=detected,
                required_assumptions=required,
                missing_assumptions=missing,
                note=f"missing assumptions: {missing}")

        # all satisfied but there were hidden patterns -> conditionally valid
        return AssumptionResult(
            "CONDITIONALLY_VALID",
            detected_patterns=detected,
            required_assumptions=required,
            note=f"all required assumptions satisfied; claim is conditionally valid")

    def _covers(self, declared: str, required: str, domain: str) -> bool:
        """Check if a declared assumption covers a required one.
        Also checks if the domain itself covers the requirement."""
        declared_lower = declared.lower().strip()
        required_lower = required.lower().strip()

        # direct match
        if declared_lower == required_lower:
            return True

        # domain-based coverage: if the domain itself covers the requirement
        if self._domain_covers(domain, required_lower):
            return True

        # semantic coverage: check if the declared assumption implies the requirement
        # "a > 0" / "b > 0" / "x > 0" covers "positive domain"
        if required_lower == "positive domain" and ">" in declared_lower and "0" in declared_lower:
            return True
        # "a != 0" / "x != 0" covers "nonzero factor"
        if required_lower == "nonzero factor" and "!=" in declared_lower and "0" in declared_lower:
            return True
        # "A is invertible" / "invertible" covers "invertible matrix"
        if required_lower == "invertible matrix" and "invertible" in declared_lower:
            return True
        # "inverse exists" covers "inverse exists mod p"
        if required_lower == "inverse exists mod p" and "inverse" in declared_lower:
            return True

        # declared assumption mentions the required condition
        if required_lower in declared_lower:
            return True
        if declared_lower in required_lower:
            return True

        return False

    def _domain_covers(self, domain: str, required_lower: str) -> bool:
        """Check if the domain itself covers the required assumption."""
        if domain == "positive":
            if required_lower in ("x != 0", "x >= 0", "positive domain", "nonzero factor"):
                return True
        if domain == "nonzero":
            if required_lower in ("x != 0", "nonzero factor"):
                return True
        if domain == "invertible_matrix":
            if required_lower in ("invertible matrix",):
                return True
        if domain == "mod_prime":
            if required_lower in ("inverse exists mod p",):
                return True
        return False


__all__ = ["ASSUMPTION_STATUSES", "ASSUMPTION_PATTERNS",
           "AssumptionClaim", "AssumptionResult", "AssumptionGate"]
