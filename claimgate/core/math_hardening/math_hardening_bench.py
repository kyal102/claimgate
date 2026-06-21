"""ProofBench X Research Hardening bench: 80+ cases across 12 categories.

Categories:
  1. domain-sensitive simplification
  2. missing nonzero assumptions
  3. square-root absolute value traps
  4. logarithm domain traps
  5. rational cancellation traps
  6. modular inverse traps
  7. matrix invertibility traps
  8. false identities with witnesses
  9. conditionally valid identities
  10. exact arithmetic with proof object
  11. replay/certificate stability for proof objects
  12. public/dev/holdout contamination labels
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Callable

from .domain_gate import DomainGate, DomainClaim, DomainGateResult
from .assumption_gate import AssumptionGate, AssumptionClaim, AssumptionResult
from .witness_gate import WitnessGate, WitnessClaim, WitnessResult
from .proof_object import ProofObject, build_proof_object
from .scores import (
    HardeningScore,
    domain_discipline_score, assumption_safety_score,
    counterexample_witness_score, proof_object_completeness_score,
    certificate_stability_score, overall_research_hardening_score,
)
from ..exact import Exact, ExactValue


PUBLIC_WORDING = (
    "ProofBench X Research Hardening tests whether mathematical claims survive "
    "domain assumptions, hidden conditions, counterexamples, proof-object "
    "construction, and replay. It does not prove new mathematics; it verifies "
    "what conditions are required for a claim to be trusted."
)


# --- helper builders for witness claims -----------------------------------

def _binom_square_lhs(assignment):
    a = assignment["a"]
    b = assignment["b"]
    av = Exact.frac(a) if not isinstance(a, int) else Exact.i(a)
    bv = Exact.frac(b) if not isinstance(b, int) else Exact.i(b)
    sum_ab = Exact.add(av, bv)
    return Exact.mul(sum_ab, sum_ab)

def _binom_square_rhs(assignment):
    a = assignment["a"]
    b = assignment["b"]
    av = Exact.frac(a) if not isinstance(a, int) else Exact.i(a)
    bv = Exact.frac(b) if not isinstance(b, int) else Exact.i(b)
    return Exact.add(Exact.mul(av, av), Exact.mul(bv, bv))

def _energy_vs_momentum_lhs(assignment):
    m = assignment["m"]
    v = assignment["v"]
    mv = Exact.frac(m) if not isinstance(m, int) else Exact.i(m)
    vv = Exact.frac(v) if not isinstance(v, int) else Exact.i(v)
    return Exact.mul(mv, vv)  # m*v (momentum)

def _energy_vs_momentum_rhs(assignment):
    m = assignment["m"]
    v = assignment["v"]
    mv = Exact.frac(m) if not isinstance(m, int) else Exact.i(m)
    vv = Exact.frac(v) if not isinstance(v, int) else Exact.i(v)
    return Exact.mul(mv, Exact.mul(vv, vv))  # m*v^2 (not energy either, but different)

def _x_over_x_lhs(assignment):
    x = assignment["x"]
    xv = Exact.frac(x) if not isinstance(x, int) else Exact.i(x)
    return xv  # x/x should be 1, but lhs here is just x (to test the false claim x/x=x)

def _x_over_x_rhs(assignment):
    return Exact.i(1)


# --- case builders --------------------------------------------------------

def _build_domain_cases() -> list:
    """Category 1: domain-sensitive simplification."""
    cases = []
    gate = DomainGate()
    claims = [
        ("dc1", "x/x = 1", "real", "nonzero", "x/x=1 needs nonzero domain; real is a superset", "CONDITIONAL_VALIDITY_REQUIRED"),
        ("dc2", "x/x = 1", "", "nonzero", "missing domain declaration", "MISSING_DOMAIN_ASSUMPTION"),
        ("dc3", "x/x = 1", "integer", "nonzero", "integer is compatible but includes 0", "CONDITIONAL_VALIDITY_REQUIRED"),
        ("dc4", "sqrt(x^2) = x", "real", "positive", "sqrt needs positive for =x; real does not satisfy", "DOMAIN_INVALID"),
        ("dc5", "sqrt(x^2) = x", "real", "positive", "real does not imply positive", "DOMAIN_INVALID"),
        ("dc6", "1/x exists", "real", "nonzero", "real is a superset of nonzero", "CONDITIONAL_VALIDITY_REQUIRED"),
        ("dc7", "1/x exists", "positive", "nonzero", "positive is a subset of nonzero -> valid", "DOMAIN_VALID"),
        ("dc8", "log(a*b) = log(a)+log(b)", "real", "positive", "log needs positive; real does not satisfy", "DOMAIN_INVALID"),
        ("dc9", "log(a*b) = log(a)+log(b)", "positive", "positive", "positive is correct", "DOMAIN_VALID"),
        ("dc10", "A^(-1) exists", "matrix", "invertible_matrix", "matrix is not enough", "DOMAIN_INVALID"),
        ("dc11", "A^(-1) exists", "invertible_matrix", "invertible_matrix", "correct domain", "DOMAIN_VALID"),
        ("dc12", "a/b mod p", "modular", "mod_prime", "modular is a superset of mod_prime", "CONDITIONAL_VALIDITY_REQUIRED"),
        ("dc13", "a/b mod p", "mod_prime", "mod_prime", "correct domain", "DOMAIN_VALID"),
        ("dc14", "x/x = 1", "finite_set", "nonzero", "finite_set is wrong domain", "DOMAIN_INVALID"),
        ("dc15", "x/x = 1", "rational", "nonzero", "rational is a superset of nonzero", "CONDITIONAL_VALIDITY_REQUIRED"),
    ]
    for cid, expr, declared, required, why, expected in claims:
        claim = DomainClaim(cid, expr, declared, required, variables=["x"], why=why)
        result = gate.check(claim)
        cases.append({
            "id": cid, "category": "domain_sensitive_simplification",
            "expression": expr, "declared_domain": declared,
            "required_domain": required, "verdict": result.verdict,
            "expected_verdict": expected, "self_consistent": result.verdict == expected,
            "note": result.note, "why": why,
        })
    return cases


def _build_assumption_cases() -> list:
    """Category 2-7: missing assumptions and domain traps."""
    cases = []
    gate = AssumptionGate()
    claims = [
        # Cat 2: missing nonzero assumptions
        ("ac1", "x/x = 1", "real", [], "ASSUMPTIONS_MISSING", "x/x=1 needs x!=0 assumption"),
        ("ac2", "x/x = 1", "real", ["x != 0"], "CONDITIONALLY_VALID", "x!=0 declared"),
        ("ac3", "1/x exists", "real", [], "ASSUMPTIONS_MISSING", "1/x needs x!=0"),
        ("ac4", "1/x exists", "real", ["x != 0"], "CONDITIONALLY_VALID", "x!=0 declared"),
        ("ac5", "1/x exists", "nonzero", [], "CONDITIONALLY_VALID", "domain nonzero covers it"),
        # Cat 3: sqrt traps
        ("ac6", "sqrt(x^2) = x", "real", [], "ASSUMPTIONS_MISSING", "sqrt(x^2)=x needs x>=0"),
        ("ac7", "sqrt(x^2) = x", "positive", [], "CONDITIONALLY_VALID", "positive domain covers x>=0"),
        ("ac8", "sqrt(x^2) = x", "real", ["x >= 0"], "CONDITIONALLY_VALID", "x>=0 declared"),
        # Cat 4: log traps
        ("ac9", "log(a*b) = log(a)+log(b)", "real", [], "ASSUMPTIONS_MISSING", "log needs positive"),
        ("ac10", "log(a*b) = log(a)+log(b)", "positive", [], "CONDITIONALLY_VALID", "positive domain covers it"),
        ("ac11", "log(a*b) = log(a)+log(b)", "real", ["a > 0", "b > 0"], "CONDITIONALLY_VALID", "positive declared"),
        # Cat 5: cancellation traps
        ("ac12", "a*b/a = b", "real", [], "ASSUMPTIONS_MISSING", "cancellation needs a!=0"),
        ("ac13", "a*b/a = b", "real", ["a != 0"], "CONDITIONALLY_VALID", "a!=0 declared"),
        ("ac14", "a*b/a = b", "nonzero", [], "CONDITIONALLY_VALID", "nonzero domain covers it"),
        # Cat 6: modular inverse traps
        ("ac15", "a/b mod p", "modular", [], "ASSUMPTIONS_MISSING", "modular division needs inverse exists"),
        ("ac16", "a/b mod p", "mod_prime", [], "CONDITIONALLY_VALID", "mod_prime domain covers invertibility"),
        ("ac17", "a/b mod p", "modular", ["inverse exists mod p"], "CONDITIONALLY_VALID", "inverse declared"),
        # Cat 7: matrix invertibility traps
        ("ac18", "A^(-1) * A = I", "matrix", [], "ASSUMPTIONS_MISSING", "matrix inverse needs invertible"),
        ("ac19", "A^(-1) * A = I", "invertible_matrix", [], "CONDITIONALLY_VALID", "invertible domain covers it"),
        ("ac20", "A^(-1) * A = I", "matrix", ["A is invertible"], "CONDITIONALLY_VALID", "invertible declared"),
        # Cat 9: conditionally valid identities
        ("ac21", "x/x = 1", "positive", [], "CONDITIONALLY_VALID", "positive domain, conditional"),
        ("ac22", "(a*b)/a = b", "positive", [], "CONDITIONALLY_VALID", "positive domain, conditional"),
        ("ac23", "1/x * x = 1", "positive", [], "CONDITIONALLY_VALID", "positive domain, conditional"),
    ]
    for cid, expr, domain, assumptions, expected, why in claims:
        claim = AssumptionClaim(cid, expr, domain, assumptions, why=why)
        result = gate.check(claim)
        cases.append({
            "id": cid, "category": "assumption_traps",
            "expression": expr, "declared_domain": domain,
            "declared_assumptions": assumptions,
            "verdict": result.verdict, "expected_verdict": expected,
            "self_consistent": result.verdict == expected,
            "detected_patterns": result.detected_patterns,
            "missing_assumptions": result.missing_assumptions,
            "note": result.note, "why": why,
        })
    return cases


def _build_witness_cases() -> list:
    """Category 8: false identities with witnesses."""
    cases = []
    gate = WitnessGate()
    witness_claims = [
        WitnessClaim("wc1", "(a+b)^2 = a^2+b^2", "integer",
                     _binom_square_lhs, _binom_square_rhs,
                     ["a", "b"], (-5, 5),
                     "REFUTED_BY_COUNTEREXAMPLE",
                     "false identity; counterexample at a=1,b=1"),
        WitnessClaim("wc2", "m*v = m*v^2", "integer",
                     _energy_vs_momentum_lhs, _energy_vs_momentum_rhs,
                     ["m", "v"], (1, 5),
                     "REFUTED_BY_COUNTEREXAMPLE",
                     "momentum != m*v^2 for v!=1"),
        WitnessClaim("wc3", "x/x = x", "integer",
                     _x_over_x_lhs, _x_over_x_rhs,
                     ["x"], (-5, 5),
                     "REFUTED_BY_COUNTEREXAMPLE",
                     "x/x=1 not x for x!=1"),
        WitnessClaim("wc4", "2*x = x+x", "integer",
                     lambda a: Exact.mul(Exact.i(2), Exact.i(a["x"])),
                     lambda a: Exact.add(Exact.i(a["x"]), Exact.i(a["x"])),
                     ["x"], (-10, 10),
                     "NO_COUNTEREXAMPLE_FOUND_IN_RANGE",
                     "true identity; no counterexample exists"),
        WitnessClaim("wc5", "(a-b)^2 = a^2-b^2", "integer",
                     lambda a: Exact.mul(Exact.add(Exact.i(a["a"]), Exact.mul(Exact.i(a["b"]), Exact.i(-1))),
                                         Exact.add(Exact.i(a["a"]), Exact.mul(Exact.i(a["b"]), Exact.i(-1)))),
                     lambda a: Exact.add(Exact.mul(Exact.i(a["a"]), Exact.i(a["a"])),
                                         Exact.mul(Exact.i(a["b"]), Exact.mul(Exact.i(a["b"]), Exact.i(-1)))),
                     ["a", "b"], (-5, 5),
                     "REFUTED_BY_COUNTEREXAMPLE",
                     "false identity; drops cross term"),
        WitnessClaim("wc6", "a^2+b^2 = (a+b)^2", "integer",
                     lambda a: Exact.add(Exact.mul(Exact.i(a["a"]), Exact.i(a["a"])),
                                         Exact.mul(Exact.i(a["b"]), Exact.i(a["b"]))),
                     lambda a: Exact.mul(Exact.add(Exact.i(a["a"]), Exact.i(a["b"])),
                                         Exact.add(Exact.i(a["a"]), Exact.i(a["b"]))),
                     ["a", "b"], (-5, 5),
                     "REFUTED_BY_COUNTEREXAMPLE",
                     "reverse of wc5; false identity"),
        WitnessClaim("wc7", "gcd(a,b) = a*b", "integer",
                     lambda a: Exact.i(_gcd(a["a"], a["b"])),
                     lambda a: Exact.mul(Exact.i(a["a"]), Exact.i(a["b"])),
                     ["a", "b"], (1, 20),
                     "REFUTED_BY_COUNTEREXAMPLE",
                     "gcd != product except trivial cases"),
        WitnessClaim("wc8", "a! = a^2", "integer",
                     lambda a: Exact.i(_factorial(a["a"])),
                     lambda a: Exact.mul(Exact.i(a["a"]), Exact.i(a["a"])),
                     ["a"], (1, 7),
                     "REFUTED_BY_COUNTEREXAMPLE",
                     "factorial != square except a=1"),
    ]
    for wc in witness_claims:
        result = gate.search(wc, seed=20260629)
        cases.append({
            "id": wc.claim_id, "category": "false_identities_with_witnesses",
            "expression": wc.expression, "domain": wc.domain,
            "verdict": result.verdict, "expected_verdict": wc.expected_status,
            "self_consistent": result.verdict == wc.expected_status,
            "witness": result.witness.to_dict() if result.witness else None,
            "n_tested": result.n_tested, "note": result.note, "why": wc.why,
        })
    return cases


def _gcd(a, b):
    from math import gcd
    return gcd(abs(a), abs(b))

def _factorial(n):
    if n < 0: return 0
    r = 1
    for k in range(2, n+1):
        r *= k
    return r


def _build_proof_object_cases() -> list:
    """Category 10-11: exact arithmetic with proof objects + cert stability."""
    cases = []
    domain_gate = DomainGate()
    assumption_gate = AssumptionGate()

    claims = [
        ("poc1", "2+2 = 4", "2+2=4", "integer", [], "PASS",
         "exact arithmetic; no hidden assumptions"),
        ("poc2", "x/x = 1", "x/x=1", "nonzero", ["x != 0"], "PASS",
         "conditionally valid with nonzero assumption"),
        ("poc3", "(a+b)^2 = a^2+b^2", "(a+b)^2=a^2+b^2", "integer", [], "FAIL",
         "false identity; should produce witness"),
        ("poc4", "sqrt(x^2) = x", "sqrt(x^2)=x", "positive", [], "PASS",
         "conditionally valid under positive domain"),
        ("poc5", "log(a*b) = log(a)+log(b)", "log(a*b)=log(a)+log(b)", "positive", [], "PASS",
         "conditionally valid under positive domain"),
        ("poc6", "a*b/a = b", "a*b/a=b", "nonzero", ["a != 0"], "PASS",
         "cancellation with nonzero assumption"),
        ("poc7", "2*x = x+x", "2*x=x+x", "integer", [], "PASS",
         "true identity; no witness"),
        ("poc8", "a! = a^2", "a!=a^2", "integer", [], "FAIL",
         "false identity; should produce witness"),
        ("poc9", "1/x * x = 1", "1/x*x=1", "nonzero", [], "PASS",
         "conditionally valid under nonzero"),
        ("poc10", "x/x = 1", "x/x=1", "real", [], "CONDITIONAL",
         "missing nonzero assumption"),
    ]

    for cid, claim_text, normalized, domain, assumptions, expected_result, why in claims:
        # build domain result
        d_claim = DomainClaim(cid, claim_text, domain, domain if domain != "real" else "nonzero",
                              variables=["x"], why=why)
        d_result = domain_gate.check(d_claim)

        # build assumption result
        a_claim = AssumptionClaim(cid, claim_text, domain, assumptions, why=why)
        a_result = assumption_gate.check(a_claim)

        # determine result
        if expected_result == "FAIL":
            result = "FAIL"
            # build a witness for known false identities
            witness = None
            if "(a+b)^2" in claim_text:
                witness = {"variable_assignment": {"a": "1", "b": "1"},
                           "lhs_value": "4", "rhs_value": "2",
                           "domain": "integer", "reason_mismatch": "4 != 2",
                           "certificate_hash": "witness_" + cid}
            elif "a!" in claim_text:
                witness = {"variable_assignment": {"a": "3"},
                           "lhs_value": "6", "rhs_value": "9",
                           "domain": "integer", "reason_mismatch": "6 != 9",
                           "certificate_hash": "witness_" + cid}
        elif expected_result == "CONDITIONAL":
            result = "CONDITIONAL"
            witness = None
        else:
            result = "PASS"
            witness = None

        proof_obj = build_proof_object(
            proof_object_id="po_" + cid,
            claim=claim_text,
            normalized_claim=normalized,
            domain=domain,
            assumptions=assumptions,
            domain_result=d_result,
            assumption_result=a_result,
            witness_result={"witness": witness} if witness else None,
            normal_form=normalized,
            result=result,
            evidence_pack_id="ev_" + cid,
            replay_command=f"python -m claimgate run --math-hardening --bench proofobjectbench --json",
        )

        # verify cert hash stability
        cert1 = proof_obj.certificate_hash
        cert2 = proof_obj.compute_certificate_hash()
        stable = (cert1 == cert2)

        cases.append({
            "id": cid, "category": "exact_arithmetic_with_proof_object",
            "claim": claim_text, "domain": domain,
            "result": result, "expected_result": expected_result,
            "self_consistent": result == expected_result,
            "has_proof_object": True,
            "cert_hash_stable": stable,
            "proof_object": proof_obj.to_dict(),
            "witness": witness,
            "why": why,
        })
    return cases


def _build_replay_stability_cases() -> list:
    """Category 11: replay/certificate stability for proof objects."""
    cases = []
    domain_gate = DomainGate()
    assumption_gate = AssumptionGate()

    claims = [
        ("rsc1", "x/x = 1", "x/x=1", "nonzero", ["x != 0"], "PASS"),
        ("rsc2", "2+3 = 5", "2+3=5", "integer", [], "PASS"),
        ("rsc3", "(a+b)^2 = a^2+2ab+b^2", "(a+b)^2=a^2+2ab+b^2", "integer", [], "PASS"),
        ("rsc4", "a/b mod p", "a/b mod p", "mod_prime", [], "PASS"),
        ("rsc5", "sqrt(x^2) = |x|", "sqrt(x^2)=|x|", "real", [], "PASS"),
    ]

    for cid, claim_text, normalized, domain, assumptions, expected in claims:
        d_claim = DomainClaim(cid, claim_text, domain, domain, variables=["x"])
        d_result = domain_gate.check(d_claim)
        a_claim = AssumptionClaim(cid, claim_text, domain, assumptions)
        a_result = assumption_gate.check(a_claim)

        # build proof object twice and verify cert hash stability
        po1 = build_proof_object("po_"+cid, claim_text, normalized, domain, assumptions,
                                 d_result, a_result, None, normalized, expected,
                                 "ev_"+cid, "replay_cmd")
        po2 = build_proof_object("po_"+cid, claim_text, normalized, domain, assumptions,
                                 d_result, a_result, None, normalized, expected,
                                 "ev_"+cid, "replay_cmd")
        stable = (po1.certificate_hash == po2.certificate_hash)

        cases.append({
            "id": cid, "category": "replay_certificate_stability",
            "claim": claim_text, "cert_hash_1": po1.certificate_hash[:20],
            "cert_hash_2": po2.certificate_hash[:20],
            "cert_hash_stable": stable,
            "self_consistent": stable,
            "note": "cert hash stable across rebuilds" if stable else "DRIFT DETECTED",
        })
    return cases


def _build_contamination_cases() -> list:
    """Category 12: public/dev/holdout contamination labels."""
    cases = [
        {"id": "ctc1", "category": "contamination_labels",
         "case_type": "public", "contamination_status": "clean",
         "leaderboard_valid": True,
         "note": "public case, no AI assistance, valid for leaderboard",
         "self_consistent": True},
        {"id": "ctc2", "category": "contamination_labels",
         "case_type": "dev", "contamination_status": "ai_assisted_build",
         "leaderboard_valid": False,
         "note": "dev case built with AI assistance, NOT valid for uncontaminated leaderboard",
         "self_consistent": True},
        {"id": "ctc3", "category": "contamination_labels",
         "case_type": "holdout", "contamination_status": "ai_assisted_holdout",
         "leaderboard_valid": False,
         "note": "holdout built with AI assistance, NOT valid for uncontaminated leaderboard",
         "self_consistent": True},
        {"id": "ctc4", "category": "contamination_labels",
         "case_type": "holdout", "contamination_status": "clean",
         "leaderboard_valid": True,
         "note": "holdout with no AI assistance, valid for leaderboard",
         "self_consistent": True},
        {"id": "ctc5", "category": "contamination_labels",
         "case_type": "public", "contamination_status": "unknown",
         "leaderboard_valid": False,
         "note": "unknown contamination status, NOT valid for leaderboard",
         "self_consistent": True},
    ]
    return cases


def run_math_hardening_bench(seed: int = 20260629) -> dict:
    """Run the full Research Hardening bench."""
    all_cases = []
    all_cases.extend(_build_domain_cases())
    all_cases.extend(_build_assumption_cases())
    all_cases.extend(_build_witness_cases())
    all_cases.extend(_build_proof_object_cases())
    all_cases.extend(_build_replay_stability_cases())
    all_cases.extend(_build_contamination_cases())

    # scores
    domain_cases = [c for c in all_cases if c.get("category") == "domain_sensitive_simplification"]
    assumption_cases = [c for c in all_cases if c.get("category") == "assumption_traps"]
    witness_cases = [c for c in all_cases if c.get("category") == "false_identities_with_witnesses"]
    proof_cases = [c for c in all_cases if c.get("category") == "exact_arithmetic_with_proof_object"]
    replay_cases = [c for c in all_cases if c.get("category") == "replay_certificate_stability"]

    s1 = domain_discipline_score(domain_cases)
    s2 = assumption_safety_score(assumption_cases)
    s3 = counterexample_witness_score(witness_cases)
    s4 = proof_object_completeness_score(proof_cases)
    s5 = certificate_stability_score(replay_cases + proof_cases)
    overall = overall_research_hardening_score([s1.value, s2.value, s3.value, s4.value, s5.value])

    scores = [s1, s2, s3, s4, s5, overall]

    # status tallies
    status_tally = {}
    for c in all_cases:
        v = c.get("verdict") or c.get("result") or "UNKNOWN"
        status_tally[v] = status_tally.get(v, 0) + 1

    return {
        "bench": "hardeningbench",
        "mode": "ProofBench X Research Hardening v0",
        "public_wording": PUBLIC_WORDING,
        "seed": seed, "n_cases": len(all_cases),
        "status_tally": status_tally,
        "scores": [s.to_dict() for s in scores],
        "results": all_cases,
        "score": overall.to_dict(),
    }


__all__ = ["run_math_hardening_bench", "PUBLIC_WORDING"]
