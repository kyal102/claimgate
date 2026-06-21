"""DomainGate v0: check whether a math claim has the domain assumptions
needed for safe verification.

Supported domains:
  real, integer, rational, positive, nonzero, matrix, invertible_matrix,
  modular, mod_prime, finite_set

Statuses:
  DOMAIN_VALID, DOMAIN_INVALID, MISSING_DOMAIN_ASSUMPTION,
  UNSUPPORTED_DOMAIN, CONDITIONAL_VALIDITY_REQUIRED
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Any

SUPPORTED_DOMAINS = [
    "real", "integer", "rational", "positive", "nonzero",
    "matrix", "invertible_matrix", "modular", "mod_prime", "finite_set",
]

DOMAIN_STATUSES = [
    "DOMAIN_VALID",
    "DOMAIN_INVALID",
    "MISSING_DOMAIN_ASSUMPTION",
    "UNSUPPORTED_DOMAIN",
    "CONDITIONAL_VALIDITY_REQUIRED",
]


@dataclass
class DomainClaim:
    """A mathematical claim with a declared domain."""
    claim_id: str
    expression: str           # e.g. "x/x = 1"
    declared_domain: str      # one of SUPPORTED_DOMAINS, or "" if missing
    required_domain: str      # the domain the claim actually needs
    variables: List[str] = field(default_factory=list)
    why: str = ""


@dataclass
class DomainGateResult:
    verdict: str
    declared_domain: str
    required_domain: str
    note: str
    missing: bool = False

    def to_dict(self) -> dict:
        return {"verdict": self.verdict, "declared_domain": self.declared_domain,
                "required_domain": self.required_domain, "note": self.note,
                "missing": self.missing}


class DomainGate:
    """Checks domain assumptions for mathematical claims."""

    # Map required domain -> compatible declared domains
    DOMAIN_COMPATIBILITY = {
        "real": {"real", "positive", "nonzero", "integer", "rational"},
        "integer": {"integer"},
        "rational": {"rational", "integer", "real", "positive", "nonzero"},
        "positive": {"positive"},
        "nonzero": {"nonzero", "positive", "real", "integer", "rational"},
        "matrix": {"matrix", "invertible_matrix"},
        "invertible_matrix": {"invertible_matrix"},
        "modular": {"modular", "mod_prime"},
        "mod_prime": {"mod_prime", "modular"},
        "finite_set": {"finite_set"},
    }

    def check(self, claim: DomainClaim) -> DomainGateResult:
        # 1. Check if domain is declared
        if not claim.declared_domain:
            return DomainGateResult(
                "MISSING_DOMAIN_ASSUMPTION", "", claim.required_domain,
                f"no domain declared; required domain is '{claim.required_domain}'",
                missing=True)

        # 2. Check if domain is supported
        if claim.declared_domain not in SUPPORTED_DOMAINS:
            return DomainGateResult(
                "UNSUPPORTED_DOMAIN", claim.declared_domain, claim.required_domain,
                f"domain '{claim.declared_domain}' is not supported")

        # 3. Check if required domain is supported
        if claim.required_domain not in SUPPORTED_DOMAINS:
            return DomainGateResult(
                "UNSUPPORTED_DOMAIN", claim.declared_domain, claim.required_domain,
                f"required domain '{claim.required_domain}' is not supported")

        # 4. Check compatibility
        compatible = self.DOMAIN_COMPATIBILITY.get(claim.required_domain, set())
        if claim.declared_domain in compatible:
            # check if conditional validity is needed:
            # - if declared is a SUBSET of required (more restrictive, e.g. positive for nonzero)
            #   -> DOMAIN_VALID (the claim is safe)
            # - if declared is a SUPERSET of required (more general, e.g. real for nonzero)
            #   -> CONDITIONAL_VALIDITY_REQUIRED (the claim needs the narrower domain)
            declared_subsets_of_required = self._is_subset(claim.declared_domain, claim.required_domain)
            if declared_subsets_of_required:
                return DomainGateResult(
                    "DOMAIN_VALID", claim.declared_domain, claim.required_domain,
                    f"domain '{claim.declared_domain}' is a subset of required '{claim.required_domain}' -> valid")
            # check if declared is a superset of required
            declared_superset_of_required = self._is_subset(claim.required_domain, claim.declared_domain)
            if declared_superset_of_required and claim.required_domain in ("nonzero", "positive", "invertible_matrix", "mod_prime"):
                return DomainGateResult(
                    "CONDITIONAL_VALIDITY_REQUIRED", claim.declared_domain, claim.required_domain,
                    f"domain '{claim.declared_domain}' is a superset of required '{claim.required_domain}' -> conditionally valid")
            return DomainGateResult(
                "DOMAIN_VALID", claim.declared_domain, claim.required_domain,
                f"domain '{claim.declared_domain}' satisfies required '{claim.required_domain}'")

        # 5. Domain mismatch
        return DomainGateResult(
            "DOMAIN_INVALID", claim.declared_domain, claim.required_domain,
            f"domain '{claim.declared_domain}' does not satisfy required '{claim.required_domain}'")

    # Subset relationships: key is a SUBSET of value (key is more restrictive)
    SUBSET_RELATIONS = {
        ("positive", "nonzero"): True,      # positive ⊂ nonzero
        ("positive", "real"): True,         # positive ⊂ real
        ("positive", "rational"): True,     # positive ⊂ rational
        ("positive", "integer"): True,      # positive ⊂ integer
        ("nonzero", "real"): True,          # nonzero ⊂ real
        ("nonzero", "rational"): True,      # nonzero ⊂ rational
        ("nonzero", "integer"): True,       # nonzero ⊂ integer (nonzero integers are a subset of integers)
        ("integer", "real"): True,          # integer ⊂ real
        ("integer", "rational"): True,      # integer ⊂ rational
        ("mod_prime", "modular"): True,     # mod_prime ⊂ modular
        ("invertible_matrix", "matrix"): True,  # invertible ⊂ matrix
    }

    def _is_subset(self, a: str, b: str) -> bool:
        """Returns True if domain a is a SUBSET of domain b (a is more restrictive)."""
        if a == b:
            return True
        return self.SUBSET_RELATIONS.get((a, b), False)


__all__ = ["SUPPORTED_DOMAINS", "DOMAIN_STATUSES", "DomainClaim",
           "DomainGateResult", "DomainGate"]
