"""ClaimReport v0: generate the full claim verification report for an input text."""
from __future__ import annotations

from typing import List

from .model import ClaimReport, ExtractedClaim
from .extractor import extract_claims
from .classifier import classify_claims
from .router import ClaimRouter


def generate_report(text: str, seed: int = 20260628) -> ClaimReport:
    """Generate a full ClaimReport for the input text.

    Steps:
      1. Extract atomic claims from the text.
      2. Classify each claim.
      3. Route each claim to the correct gate (produces an EvidencePack).
      4. Populate the report with results.
    """
    # 1. extract
    claims = extract_claims(text)
    # 2. classify
    claims = classify_claims(claims)
    # 3. route
    router = ClaimRouter()
    status_tally = {}
    for claim in claims:
        pack = router.route(claim)
        claim.routed_gate = pack.gate_name
        claim.gate_status = pack.status
        claim.evidence_pack_id = pack.pack_id
        claim.certificate_hash = pack.certificate_hash
        claim.limitation = pack.limitations[0] if pack.limitations else ""
        claim.next_required_validation = pack.next_required_validation
        status_tally[pack.status] = status_tally.get(pack.status, 0) + 1
    # 4. build report
    n_pass = sum(1 for c in claims if c.gate_status in ("DIMENSIONALLY_VALID", "ALGEBRAICALLY_VALID", "REPRODUCIBLE"))
    n_fail = sum(1 for c in claims if c.gate_status in ("DIMENSIONALLY_INVALID", "REFUTED_BY_COUNTEREXAMPLE", "DRIFT_DETECTED", "KNOWN_LAW_CONFLICT"))
    n_needs = sum(1 for c in claims if c.gate_status.startswith("NEEDS_") or c.gate_status in ("UNSUPPORTED_CLAIM", "UNSUPPORTED_OPEN_CLAIM", "MISSING_DATA_HASH", "AMBIGUOUS_NEEDS_CLARIFICATION"))
    summary = (f"Extracted {len(claims)} claim(s): {n_pass} passed, {n_fail} failed, "
               f"{n_needs} need evidence/clarification. ClaimGate routes claims; "
               f"gates decide verdicts.")
    return ClaimReport(
        original_text=text,
        extracted_claims=claims,
        summary=summary,
        n_claims=len(claims),
        n_evidence_packs=len(claims),
        status_tally=status_tally,
    )


__all__ = ["generate_report"]
