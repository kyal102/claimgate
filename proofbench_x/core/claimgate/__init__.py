"""ClaimGate v0: extract, classify, and route scientific claims to verification gates.

Public wording:
  "ClaimGate extracts and routes scientific claims to verification gates.
   It does not prove scientific truth; it records which claims were
   checked, which failed, which need evidence, and which require
   simulation or experiment."
"""
from .model import (
    CLAIM_TYPES, CLAIM_STATUSES, PUBLIC_WORDING,
    ExtractedClaim, ClaimReport,
)
from .extractor import extract_claims, detect_claim_hints
from .classifier import classify_claim, classify_claims
from .router import ClaimRouter
from .report import generate_report
from .claimbench import ClaimBenchCase, BENCH_CASES, run_claimbench

__all__ = [
    "CLAIM_TYPES", "CLAIM_STATUSES", "PUBLIC_WORDING",
    "ExtractedClaim", "ClaimReport",
    "extract_claims", "detect_claim_hints",
    "classify_claim", "classify_claims",
    "ClaimRouter", "generate_report",
    "ClaimBenchCase", "BENCH_CASES", "run_claimbench",
]
