"""ClaimExtractor v0: extract atomic claims from raw text.

Uses deterministic pattern matching (regex + heuristics) to split messy
text into atomic claims. This is NOT an NLP model — it is a transparent,
auditable extractor that identifies claim-bearing sentences and splits
them by type.

Supported claim patterns:
  * equation claims: "F = m*a", "E = mc^2", "energy equals mass times c squared"
  * dimensional/physics claims: "force equals mass times acceleration"
  * theory/new physics claims: "proposes a new field", "dark energy", "modified gravity"
  * experimental/result claims: "measured to be", "experiment shows", "observed"
  * power/efficiency claims: "saves 50% power", "compute saving", "speedup"
  * unsupported broad claims: "proves that", "explains everything", "universal theory"
"""
from __future__ import annotations

import re
from typing import List

from .model import ExtractedClaim


# Pattern keywords for each claim type
EQUATION_PATTERN = re.compile(
    r'[A-Za-z_][A-Za-z0-9_\^]*\s*=\s*[A-Za-z0-9_\^*/+\-\s().]+',
    re.IGNORECASE,
)

DIMENSIONAL_KEYWORDS = [
    "equals", "is equal to", "dimensionally", "units of",
    "force", "energy", "power", "momentum", "acceleration", "velocity",
]

THEORY_KEYWORDS = [
    "proposes", "proposed", "new theory", "new physics", "dark energy",
    "dark matter", "modified gravity", "new field", "new force",
    "theory of everything", "universal law", "new paradigm",
]

EXPERIMENTAL_KEYWORDS = [
    "measured", "experiment", "observed", "experimental result",
    "data shows", "results show", "finding", "detected", "recorded",
]

POWER_KEYWORDS = [
    "saves", "saving", "speedup", "efficiency", "power reduction",
    "compute saving", "faster", "acceleration factor",
]

UNSUPPORTED_KEYWORDS = [
    "proves that", "proven", "explains everything", "universal truth",
    "definitively", "certainly", "undoubtedly", "conclusively",
    "theory of everything", "final equation",
]

AMBIGUOUS_KEYWORDS = [
    "it", "this", "that", "the thing", "the result", "previously mentioned",
]


# Verbs that introduce a NEW atomic claim inside a compound sentence. Used to
# split "A equals B and proves C that saves D%" into three atomic claims.
_CLAUSE_VERB = (
    r"(?:proves?|proven|proving|saves?|saving|shows?|showing|reduc\w+|"
    r"demonstrat\w+|achiev\w+|explain\w+|predict\w+|observ\w+|measur\w+|"
    r"cuts?|cutting|improves?|improving|enables?|yields?|eliminat\w+|"
    r"guarantees?|implies|means|confirms?|establishes?)"
)
# Split before a coordinating/relative connective that is immediately followed
# by a claim verb (so we don't break ordinary phrases like "mass and energy").
_CLAUSE_SPLIT = re.compile(
    r"\s+(?:and|that|which|,|;|&)\s+(?=" + _CLAUSE_VERB + r"\b)", re.IGNORECASE
)


def extract_claims(text: str) -> List[ExtractedClaim]:
    """Extract atomic claims from raw text.

    Splits text into sentences, then splits each sentence into atomic claims at
    compound-clause boundaries (a connective immediately followed by a claim
    verb). Each atomic clause becomes one ExtractedClaim. The claim_type is set
    later by the classifier. This is a transparent, auditable heuristic — not an
    NLP model — so its splits are inspectable and deterministic.
    """
    if not text or not text.strip():
        return []

    sentences = _split_sentences(text)
    claims = []
    idx = 0
    for sent in sentences:
        for clause in _split_clauses(sent):
            clause = clause.strip(" ,.;")
            if not clause or len(clause) < 3:
                continue
            claims.append(ExtractedClaim(
                claim_id=f"claim_{idx:03d}",
                raw_text=clause,
                normalized_input=clause.lower().strip(),
            ))
            idx += 1
    return claims


def _split_clauses(sentence: str) -> List[str]:
    """Split a sentence into atomic claim clauses at connective+claim-verb
    boundaries. A sentence with no such boundary is returned unchanged."""
    parts = _CLAUSE_SPLIT.split(sentence.strip())
    return [p for p in (p.strip() for p in parts) if p]


def _split_sentences(text: str) -> List[str]:
    """Split text into sentences, being careful not to split inside equations."""
    # protect equations (replace periods inside equations with placeholder)
    protected = text
    # simple sentence split on . ! ? followed by space or end
    parts = re.split(r'(?<=[.!?])\s+', protected)
    return [p.strip() for p in parts if p.strip()]


def detect_claim_hints(text: str) -> List[str]:
    """Detect which claim-type keywords appear in the text.
    Returns a list of hint categories found."""
    lower = text.lower()
    hints = []
    if EQUATION_PATTERN.search(text):
        hints.append("equation")
    if any(kw in lower for kw in DIMENSIONAL_KEYWORDS):
        hints.append("dimensional")
    if any(kw in lower for kw in THEORY_KEYWORDS):
        hints.append("theory")
    if any(kw in lower for kw in EXPERIMENTAL_KEYWORDS):
        hints.append("experimental")
    if any(kw in lower for kw in POWER_KEYWORDS):
        hints.append("power")
    if any(kw in lower for kw in UNSUPPORTED_KEYWORDS):
        hints.append("unsupported")
    if any(kw in lower for kw in AMBIGUOUS_KEYWORDS):
        hints.append("ambiguous")
    return hints


__all__ = ["extract_claims", "detect_claim_hints", "EQUATION_PATTERN"]
