"""ClaimClassifier v0: classify each extracted claim into one of 7 types.

Classification rules (deterministic, priority-ordered):
  1. unsupported_claim  -- contains "proves", "universal truth", "explains everything", etc.
  2. theory_claim       -- contains "proposes", "new theory", "dark energy", etc.
  3. experimental_claim -- contains "measured", "experiment", "observed", etc.
  4. reproducibility_claim -- contains "reproduce", "replay", "drift", "certificate", etc.
  5. unit_claim         -- contains dimensional keywords + an equation
  6. physics_claim      -- contains physics keywords without a clear equation
  7. math_claim         -- contains an equation but no physics keywords

If a claim matches none, it defaults to unsupported_claim.
"""
from __future__ import annotations

from typing import List

from .model import ExtractedClaim, CLAIM_TYPES
from .extractor import detect_claim_hints, EQUATION_PATTERN


# Keywords for reproducibility claims (separate from experimental)
REPRO_KEYWORDS = [
    "reproduce", "replay", "drift", "certificate", "evidence pack",
    "reproducibility", "reproducible", "hash mismatch",
]


def classify_claim(claim: ExtractedClaim) -> str:
    """Classify a single claim. Returns one of CLAIM_TYPES."""
    text = claim.raw_text
    lower = text.lower()
    hints = detect_claim_hints(text)
    has_equation = bool(EQUATION_PATTERN.search(text))

    # Priority 1: unsupported broad claims
    if "unsupported" in hints:
        return "unsupported_claim"

    # Priority 2: ambiguous claims with deictic references (it/this/that/the thing)
    # but only if there's no concrete equation or specific quantity
    if "ambiguous" in hints and not has_equation:
        # check if the claim has a concrete subject (not just "it equals the thing")
        # if the text is mostly deictic + "equals", it's unsupported
        deictic_count = sum(1 for kw in ["it ", "this ", "that ", "the thing", "the result", "previously"] if kw in lower)
        if deictic_count >= 2 and "dimensional" in hints:
            return "unsupported_claim"

    # Priority 3: reproducibility claims
    if any(kw in lower for kw in REPRO_KEYWORDS):
        return "reproducibility_claim"

    # Priority 4: theory/new physics claims
    if "theory" in hints:
        return "theory_claim"

    # Priority 5: experimental claims
    if "experimental" in hints:
        return "experimental_claim"

    # Priority 6: power/efficiency claims
    if "power" in hints:
        return "experimental_claim"  # power claims need measurement data

    # Priority 7: unit/dimensional claims (equation + dimensional keywords)
    if has_equation and "dimensional" in hints:
        return "unit_claim"

    # Priority 8: physics claims (physics keywords, may or may not have equation)
    if "dimensional" in hints:
        return "physics_claim"

    # Priority 9: math claims (equation, no physics keywords)
    if has_equation:
        return "math_claim"

    # Priority 10: ambiguous claims (fallback)
    if "ambiguous" in hints:
        return "unsupported_claim"  # ambiguous -> unsupported until clarified

    # Default: unsupported
    return "unsupported_claim"


def classify_claims(claims: List[ExtractedClaim]) -> List[ExtractedClaim]:
    """Classify all claims in place. Returns the same list (modified)."""
    for claim in claims:
        claim.claim_type = classify_claim(claim)
    return claims


__all__ = ["classify_claim", "classify_claims"]
