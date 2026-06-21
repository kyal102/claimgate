"""Research-grade anti-cheat tests for the ported verified-claim infrastructure
(claimgate).

These prove the ported stack does NOT cheat:
  * the verifier RE-DERIVES truth (it is not an answer lookup),
  * a model answer can never override the verifier,
  * open problems are refused, never "proved",
  * certificates are deterministic (stable hash; drift is detectable),
  * exact preservation rejects lossy scientific summaries,
  * the replay audit loop is fully green with NO shell execution,
  * the stub is a simulated participant, never the verifier.

No full-app import; imports only the additive claim_infra package.
"""

import random
from pathlib import Path

from claimgate.core.families import FAMILY_REGISTRY
from claimgate.core.verifier import Verifier
from claimgate.core.counterexamples import COUNTEREXAMPLES
from claimgate.core.certificate import cert_hash
from claimgate.core.replay.replaybench import run_replaybench
from claimgate.core.claimgate import generate_report
from claimgate.core.report import _check_wording

PKG = Path("claimgate")
V = Verifier()


def test_verifier_grades_against_rederived_truth_not_the_model():
    fam = FAMILY_REGISTRY["f1_sum_chain"]
    prob = fam.gen_variant(random.Random(1234))
    truth = fam.verify(prob)                      # re-derived by the solver
    correct = truth.display()
    r_ok = V.grade_family_case(fam, prob, correct, "ac1")
    assert r_ok.status == "pass"
    # A deliberately WRONG model answer is graded fail — the model is never trusted.
    r_bad = V.grade_family_case(fam, prob, str(int(correct) + 1), "ac2")
    assert r_bad.status == "fail"
    # The certificate carries the verifier's truth, not the model's answer.
    assert r_ok.certificate.result_canonical == truth.canonical_string()


def test_truth_matches_an_independent_oracle_no_hardcoding():
    # f1_sum_chain renders "a + b + c + ..."; an independent Python sum must
    # match the verifier's re-derived truth (so it is computed, not looked up).
    fam = FAMILY_REGISTRY["f1_sum_chain"]
    for s in range(5):
        prob = fam.gen_variant(random.Random(s))
        rendered = fam.render(prob)
        independent = sum(int(x) for x in rendered.split("+"))
        assert fam.verify(prob).display() == str(independent)


def test_all_counterexamples_are_genuinely_false():
    # The verifier computes real lhs/rhs; every counterexample must be truly
    # false (no "VERIFIER BUG" path where a claimed-false identity is true).
    for ce in COUNTEREXAMPLES:
        is_false, detail = V.check_counterexample(ce)
        assert is_false, f"{ce.id} must be genuinely false: {detail}"


def test_model_cannot_override_verifier_on_false_identity():
    ce = COUNTEREXAMPLES[0]
    assert V.grade_counterexample(ce, "accept").status == "fail"   # accepting a lie -> fail
    assert V.grade_counterexample(ce, "reject").status == "pass"   # rejecting it -> pass


def test_certificate_hash_is_deterministic_and_drift_sensitive():
    a = cert_hash("2 + 2", "int:4", "lane1")
    b = cert_hash("2 + 2", "int:4", "lane1")
    assert a == b and len(a) == 64
    assert cert_hash("2 + 2", "int:5", "lane1") != a   # changed result -> different hash (drift)


def test_exact_preservation_rejects_scientific_summary():
    big = 10 ** 2000 + 7   # 2001 digits (under Python's default int->str cap)
    assert V.check_exact_preservation(big, str(big)).status == "pass"
    assert V.check_exact_preservation(big, "1.0e2000").status == "fail"   # lossy summary refused


def test_replay_audit_loop_is_fully_green():
    res = run_replaybench()
    assert res["n_cases"] == 7
    assert res["score"]["value"] == 1.0


def test_no_shell_true_anywhere_in_claim_infra():
    offenders = [str(p) for p in PKG.rglob("*.py")
                 if "shell=True" in p.read_text(encoding="utf-8", errors="ignore")]
    assert offenders == [], f"shell=True found in: {offenders}"


def test_claimgate_refuses_proven_open_problem():
    rep = generate_report("I have proven the Riemann Hypothesis.")
    statuses = [c.gate_status for c in rep.extracted_claims]
    assert "UNSUPPORTED_CLAIM" in statuses
    # never reports an open problem as proved/passed/verified
    assert not any(s in ("PASS", "VERIFIED", "PROVED", "PROVEN") for s in statuses)


def test_stub_is_a_simulated_participant_not_the_verifier():
    from claimgate.adapters import stub
    doc = (stub.__doc__ or "").lower()
    assert "simulated" in doc or "weakness" in doc          # labeled simulated model
    # the verifier must not depend on the stub/model at all
    vsrc = (PKG / "core" / "verifier.py").read_text(encoding="utf-8").lower()
    assert "stub" not in vsrc and "adapter" not in vsrc


def test_report_wording_guard_blocks_forbidden_phrases():
    assert _check_wording("this is the world's hardest math benchmark") != []
    assert _check_wording("proof-aware mathematical verification benchmark") == []
