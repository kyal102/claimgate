"""ClaimGate v0: extract, classify, and route scientific claims to verification gates.

ClaimGate sits at the TOP of the stack. It takes messy human/AI science
text, extracts atomic claims, classifies each, routes it to the correct
gate (SuperMath, UnitGate, PhysicsGate, TheoryGate, EvidencePack,
ReproGate), and produces an EvidencePack for every claim.

Public wording:
  "ClaimGate extracts and routes scientific claims to verification gates.
   It does not prove scientific truth; it records which claims were
   checked, which failed, which need evidence, and which require
   simulation or experiment."

ClaimGate ROUTES claims; GATES decide verdicts. ClaimGate never overrides
a gate result, never claims scientific truth, and never upgrades an
unsupported claim to truth.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Any


# 7 claim types (classification targets)
CLAIM_TYPES = [
    "math_claim",
    "unit_claim",
    "physics_claim",
    "theory_claim",
    "experimental_claim",
    "reproducibility_claim",
    "unsupported_claim",
]

# Claim statuses (produced by the routed gate, NOT by ClaimGate itself)
CLAIM_STATUSES = [
    "DIMENSIONALLY_VALID",
    "DIMENSIONALLY_INVALID",
    "ALGEBRAICALLY_VALID",
    "REFUTED_BY_COUNTEREXAMPLE",
    "LIMIT_CHECK_PASSED",
    "KNOWN_LAW_CONFLICT",
    "NEEDS_SIMULATION",
    "NEEDS_EXPERIMENT",
    "NEEDS_DATA",
    "UNSUPPORTED_OPEN_CLAIM",
    "UNSUPPORTED_CLAIM",
    "NOT_FALSIFIABLE",
    "NO_TESTABLE_PREDICTION",
    "THEORY_INCOMPLETE",
    "REPRODUCIBLE",
    "DRIFT_DETECTED",
    "MISSING_DATA_HASH",
    "CONTAMINATED_BY_MODEL",
    "AMBIGUOUS_NEEDS_CLARIFICATION",
]

PUBLIC_WORDING = (
    "ClaimGate extracts and routes scientific claims to verification gates. "
    "It does not prove scientific truth; it records which claims were "
    "checked, which failed, which need evidence, and which require "
    "simulation or experiment."
)


@dataclass
class ExtractedClaim:
    """A single atomic claim extracted from raw text."""
    claim_id: str
    raw_text: str              # the exact substring from the source
    claim_type: str = ""       # set by classifier (one of CLAIM_TYPES)
    normalized_input: str = "" # normalized form for routing/hashing
    # routing metadata
    routed_gate: str = ""      # "UnitGate" | "PhysicsClaimBench" | "TheoryGate" | ...
    gate_status: str = ""      # the gate's verdict
    evidence_pack_id: str = ""
    certificate_hash: str = ""
    limitation: str = ""
    next_required_validation: str = ""

    def to_dict(self) -> dict:
        return {
            "claim_id": self.claim_id,
            "raw_text": self.raw_text,
            "claim_type": self.claim_type,
            "normalized_input": self.normalized_input,
            "routed_gate": self.routed_gate,
            "gate_status": self.gate_status,
            "evidence_pack_id": self.evidence_pack_id,
            "certificate_hash": self.certificate_hash,
            "limitation": self.limitation,
            "next_required_validation": self.next_required_validation,
        }


@dataclass
class ClaimReport:
    """The full report for one input text."""
    original_text: str
    extracted_claims: List[ExtractedClaim] = field(default_factory=list)
    summary: str = ""
    n_claims: int = 0
    n_evidence_packs: int = 0
    status_tally: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "original_text": self.original_text,
            "extracted_claims": [c.to_dict() for c in self.extracted_claims],
            "summary": self.summary,
            "n_claims": self.n_claims,
            "n_evidence_packs": self.n_evidence_packs,
            "status_tally": self.status_tally,
        }


__all__ = [
    "CLAIM_TYPES", "CLAIM_STATUSES", "PUBLIC_WORDING",
    "ExtractedClaim", "ClaimReport",
]
