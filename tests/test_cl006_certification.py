"""Regression: ClaimLint CL006 certification and compliance claims.

ClaimGate must abstain. It must not report VALID_FORMULA (a chemical formula
parse of a designator such as ISO or SOC), and it must not count the claim
as a pass via REPRODUCIBLE or DIMENSIONALLY_VALID.

Verdict mapping: ClaimLint CL006 (unroutable) -> ClaimGate ABSTAIN.
"""

import re

from claimgate.core.claimgate import generate_report
from claimgate.core.claimgate.compliance import is_certification_or_compliance_claim

# The cases ClaimLint CL006 refuses, including the reported false passes.
CL006_CASES = [
    "ISO 27001 certified",
    "SOC 2 compliant",
    "EcoKure is ISO 27001 certified",
    "EcoKure has ISO 27001 certification and is the best, fully secure platform",
    "We are SOC 2 Type II compliant",
    "ISO/IEC 27001 certified",
    "ISO/IEC 27001:2022 certified",
    "certified to ISO 27001:2022",
    "HIPAA compliant",
    "GDPR compliant",
    "PCI DSS compliant",
    "PCI-DSS compliant",
    "FedRAMP authorized",
    "ISO 42001 certified",
    "ISO certified",
    "We hold an ISO 27001 certificate",
    "ISO 27001 certificate",
    "compliant with SOC 2",
    "The platform is SOC 2 Type II certified",
    "SOC2 certified",
    "ISO27001 certification",
]

# Statuses that would show up as a pass. VALID_FORMULA is the reported bug:
# ISO (I+S+O) and SOC/SOC2 (S+O+C) are well-formed formulas, not certificates.
PASS_STATUSES = {
    "VALID_FORMULA",
    "DIMENSIONALLY_VALID",
    "ALGEBRAICALLY_VALID",
    "REPRODUCIBLE",
    "BALANCED",
    "PASS",
    "VERIFIED",
    "PROVED",
    "PROVEN",
}


def _statuses(text):
    report = generate_report(text)
    return report, [c.gate_status for c in report.extracted_claims]


def test_cl006_cases_abstain_and_are_not_valid_formula():
    for text in CL006_CASES:
        assert is_certification_or_compliance_claim(text), text
        report, statuses = _statuses(text)
        assert statuses, text
        assert statuses == ["ABSTAIN"] * len(statuses), (text, statuses)
        assert "VALID_FORMULA" not in statuses
        assert not any(s in PASS_STATUSES for s in statuses), (text, statuses)
        assert all(c.routed_gate == "ClaimGate" for c in report.extracted_claims), text
        assert all(c.gate_status == "ABSTAIN" for c in report.extracted_claims), text
        assert re.search(r"\b0 passed\b", report.summary), (text, report.summary)


def test_cl006_pack_records_the_verdict_mapping():
    from claimgate.core.claimgate.classifier import classify_claims
    from claimgate.core.claimgate.extractor import extract_claims
    from claimgate.core.claimgate.router import ClaimRouter

    router = ClaimRouter()
    for text in ("ISO 27001 certified", "SOC 2 compliant", "We hold an ISO 27001 certificate"):
        claims = classify_claims(extract_claims(text))
        assert len(claims) == 1, text
        pack = router.route(claims[0])
        assert pack.status == "ABSTAIN", text
        assert pack.gate_name == "ClaimGate"
        assert pack.sub_statuses == ["CL006"]
        assert pack.result_body["claimlint_rule"] == "CL006"
        assert pack.result_body["mapped_verdict"] == "ABSTAIN"
        assert "VALID_FORMULA" in pack.result_body["refused_verdicts"]
        assert "VALID_FORMULA" not in pack.status


def test_certificate_word_does_not_become_reproducible():
    """'ISO 27001 certificate' used to route to ReproGate as REPRODUCIBLE."""
    report, statuses = _statuses("We hold an ISO 27001 certificate")
    assert statuses == ["ABSTAIN"]
    assert report.extracted_claims[0].routed_gate == "ClaimGate"
    report, statuses = _statuses("ISO 27001 certificate")
    assert statuses == ["ABSTAIN"]
    assert "1 passed" not in report.summary


def test_equation_cannot_launder_a_certification_claim():
    """'HIPAA certified and F = m*a' used to return DIMENSIONALLY_VALID for the whole sentence."""
    report, statuses = _statuses("We are HIPAA certified and F = m*a")
    assert "ABSTAIN" in statuses
    assert "VALID_FORMULA" not in statuses
    certs = [c for c in report.extracted_claims if "HIPAA" in c.raw_text or "certified" in c.raw_text.lower()]
    assert certs and all(c.gate_status == "ABSTAIN" for c in certs)
    # The equation is a separate checkable claim and may still be dimensionally valid.
    equations = [c for c in report.extracted_claims if "F = m*a" in c.raw_text or "f = m*a" in c.raw_text.lower()]
    assert equations
    assert all(c.gate_status != "VALID_FORMULA" for c in equations)
    assert any(c.gate_status == "DIMENSIONALLY_VALID" for c in equations)


def test_certification_clause_does_not_hide_a_dimensional_failure():
    report, statuses = _statuses(
        "Energy equals mass times acceleration and the company is ISO 27001 certified."
    )
    assert "ABSTAIN" in statuses
    assert "DIMENSIONALLY_INVALID" in statuses
    assert "VALID_FORMULA" not in statuses
    assert not any(s in PASS_STATUSES for s in statuses)


def test_evidence_pack_certificate_hash_is_not_cl006():
    text = "The result reproduces with the same certificate hash but the data hash is missing."
    assert not is_certification_or_compliance_claim(text)
    _, statuses = _statuses(text)
    assert "MISSING_DATA_HASH" in statuses
    assert "ABSTAIN" not in statuses

    drift = "The replay produced drift: the certificate hash changed between runs."
    assert not is_certification_or_compliance_claim(drift)
    _, statuses = _statuses(drift)
    assert "DRIFT_DETECTED" in statuses
    assert "ABSTAIN" not in statuses


def test_open_problem_stays_unsupported_not_abstain():
    _, statuses = _statuses("I have proven the Riemann Hypothesis.")
    assert "UNSUPPORTED_CLAIM" in statuses
    assert "ABSTAIN" not in statuses
    assert "VALID_FORMULA" not in statuses


def test_formulas_and_bare_designators_are_not_certification_claims():
    # These are not attestations. A formula parser may accept some of them;
    # ClaimGate must still not call that a certification pass.
    for text in ("H2O", "Ca(OH)2", "ISO", "SOC 2", "SOC2", "isolation 27001", "socket 2"):
        assert not is_certification_or_compliance_claim(text), text
        _, statuses = _statuses(text)
        assert "ABSTAIN" not in statuses, (text, statuses)
        assert "VALID_FORMULA" not in statuses, (text, statuses)


def test_real_equation_still_passes():
    _, statuses = _statuses("The equation F = m*a describes Newton's second law of motion.")
    assert "DIMENSIONALLY_VALID" in statuses
    assert "ABSTAIN" not in statuses
