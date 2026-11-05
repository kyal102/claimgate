"""ClaimLint CL006 — certification and compliance claims are unroutable.

ClaimLint rule CL006 (https://github.com/kyal102/claimlint) flags wording that
asserts a certification, accreditation, authorization, or compliance status.
No deterministic gate can establish that status: this stack does not look up
a certificate registry, an auditor's report, or a scope statement.

Verdict mapping
---------------
ClaimLint CL006 (unroutable)  ->  ClaimGate ``ABSTAIN``

``ABSTAIN`` refuses to confirm or deny the attestation. It is not a pass.

It is not ``VALID_FORMULA``. That verdict only means a chemical formula
parsed (ElementGate). Standard designators parse as formulas by accident —
``ISO`` is I+S+O, ``SOC`` / ``SOC2`` is S+O+C — and a well-formed formula is
not evidence that anyone is certified or compliant.

It is not ``REPRODUCIBLE``. The word "certificate" in "ISO 27001 certificate"
is the attestation, not an evidence-pack certificate hash.

It is not ``DIMENSIONALLY_VALID`` or ``ALGEBRAICALLY_VALID``. An equation
sharing the sentence must not launder the attestation into a pass.

``UNSUPPORTED_CLAIM`` stays the refusal for other uncheckable claims (open
problems, "proves new physics"). CL006 is the narrower case: there is no
route, so the decision is abstain.
"""
from __future__ import annotations

import re

# Named frameworks. A bare "ISO" / "SOC" still counts: "ISO certified" is the
# same kind of attestation as "ISO 27001 certified". Digits and "Type II"
# stay optional so both forms match. Word boundaries keep "isolation",
# "isotope", and "socket" out.
_FRAMEWORK = re.compile(
    r"""(?ix)
    \b(?:
        iso(?:\s*/\s*iec)?(?:\s*/\s*ieee)?(?:[\s-]*\d{4,5}(?:\s*[:\-]\s*\d{2,4})?)?
      | soc(?:[\s-]*[123](?:\s*type\s*(?:i{1,3}|[1-3]))?)?
      | pci(?:\s*-?\s*dss)?
      | hipaa
      | hitech
      | gdpr
      | ccpa
      | fedramp
      | cmmc
      | hitrust
      | fisma
      | tisax
      | irap
      | nist(?:\s*(?:csf|800\s*-\s*\d+|ai\s*rmf))?
      | cyber\s+essentials
    )\b
    """
)

# Attestation predicates. "certificate" is handled separately so an
# evidence-pack "certificate hash" is not an attestation.
_ATTESTATION = re.compile(
    r"""(?ix)
    \b(?:
        certifi(?:ed|cation)
      | complian(?:t|ce)
      | accredit(?:ed|ation)
      | attest(?:ed|ation)
      | authori[sz](?:ed|ation)
    )\b
    """
)

_CERT_WORD = re.compile(r"\bcertificates?\b", re.IGNORECASE)
_CERT_HASH = re.compile(r"\bcertificates?[_\s]+hash(?:es)?\b", re.IGNORECASE)

# Coordinators used only to peel a certification clause off a checkable one.
_COORD = re.compile(r"\s*(?:,|;|\band\b|\bbut\b)\s*", re.IGNORECASE)
# A clause ClaimGate can actually route (equation or "X equals Y"). Prose
# leftovers ("and is the best") are not checkable and stay with the attestation.
_CHECKABLE = re.compile(
    r"[A-Za-z_][A-Za-z0-9_^]*\s*=\s*[A-Za-z0-9_^*/+\-\s().]+|\b(?:equals|equal to)\b",
    re.IGNORECASE,
)

CL006_RULE = "CL006"
CL006_VERDICT = "ABSTAIN"


def _scrub_evidence_certificate(text: str) -> str:
    """Drop evidence-pack 'certificate hash' so it is not read as an attestation."""
    return _CERT_HASH.sub(" ", text)


def is_certification_or_compliance_claim(text: str) -> bool:
    """True when ``text`` asserts a certification or compliance status (CL006).

    Requires a named framework and an attestation. A bare formula, a bare
    "SOC 2", or an evidence-pack certificate hash does not match.
    """
    if not text or not _FRAMEWORK.search(text):
        return False
    scrubbed = _scrub_evidence_certificate(text)
    if _ATTESTATION.search(scrubbed):
        return True
    return _CERT_WORD.search(scrubbed) is not None


def peel_certification_clauses(sentence: str) -> list[str]:
    """Split a certification clause off a co-occurring checkable clause.

    "We are HIPAA certified and F = m*a" must not inherit the equation's
    verdict, and the equation must still be checked on its own. A sentence
    stays intact when it has no certification clause, when every piece is
    one, or when the other piece is prose ClaimGate cannot check.
    """
    pieces = [p.strip(" ,.;") for p in _COORD.split(sentence) if p and p.strip(" ,.;")]
    if len(pieces) < 2:
        return [sentence.strip()] if sentence.strip() else []
    has_cert = any(is_certification_or_compliance_claim(p) for p in pieces)
    has_checkable = any(
        _CHECKABLE.search(p) and not is_certification_or_compliance_claim(p)
        for p in pieces
    )
    if has_cert and has_checkable:
        return pieces
    return [sentence.strip()] if sentence.strip() else []


__all__ = [
    "CL006_RULE",
    "CL006_VERDICT",
    "is_certification_or_compliance_claim",
    "peel_certification_clauses",
]
