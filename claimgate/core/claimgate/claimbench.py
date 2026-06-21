"""ClaimBench v0: 20 messy text cases for ClaimGate.

Cases 1-10: base categories
Cases 11-20: variations with formatting, unicode, equations, mixed claims
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .report import generate_report
from .model import ClaimReport, PUBLIC_WORDING


@dataclass
class ClaimBenchCase:
    id: str
    text: str
    expected_claim_types: List[str]   # at least one of these should appear
    expected_statuses: List[str]      # at least one of these should appear
    why: str


BENCH_CASES = [
    # 1-10: base categories
    ClaimBenchCase("cb1",
        "The equation F = m*a describes Newton's second law of motion.",
        ["unit_claim", "math_claim"], ["DIMENSIONALLY_VALID"],
        "valid physics equation in prose"),
    ClaimBenchCase("cb2",
        "Energy equals mass times acceleration.",
        ["unit_claim", "physics_claim"], ["DIMENSIONALLY_INVALID"],
        "invalid dimensional claim (energy != mass * acceleration)"),
    ClaimBenchCase("cb3",
        "This proves that (a+b)^2 = a^2 + b^2 for all values.",
        ["unsupported_claim", "math_claim"], ["UNSUPPORTED_CLAIM", "REFUTED_BY_COUNTEREXAMPLE"],
        "fake proof claim (overclaim + false identity)"),
    ClaimBenchCase("cb4",
        "We propose a new dark energy field that explains everything in the universe.",
        ["theory_claim", "unsupported_claim"], ["UNSUPPORTED_OPEN_CLAIM", "UNSUPPORTED_CLAIM"],
        "unsupported new physics claim"),
    ClaimBenchCase("cb5",
        "The modified gravity theory F = G*m/r^2.1 predicts testable deviations but requires experiment.",
        ["theory_claim", "unit_claim"], ["NEEDS_EXPERIMENT", "UNSUPPORTED_OPEN_CLAIM"],
        "testable but unproven theory claim"),
    ClaimBenchCase("cb6",
        "Our system saves 50% power compared to the baseline.",
        ["experimental_claim"], ["NEEDS_DATA", "NEEDS_EXPERIMENT"],
        "power saving claim with no measurement data"),
    ClaimBenchCase("cb7",
        "The result reproduces with the same certificate hash but the data hash is missing.",
        ["reproducibility_claim"], ["MISSING_DATA_HASH"],
        "reproducibility claim with missing data hash"),
    ClaimBenchCase("cb8",
        "The force F = m*a is valid. However, E = m*a is also claimed. The experiment shows results.",
        ["unit_claim", "experimental_claim"], ["DIMENSIONALLY_VALID", "DIMENSIONALLY_INVALID", "NEEDS_DATA"],
        "multiple claims in one paragraph"),
    ClaimBenchCase("cb9",
        "It equals the thing we mentioned earlier.",
        ["unsupported_claim"], ["UNSUPPORTED_CLAIM", "AMBIGUOUS_NEEDS_CLARIFICATION"],
        "ambiguous claim requiring clarification"),
    ClaimBenchCase("cb10",
        "This definitively proves the universal theory of everything.",
        ["unsupported_claim"], ["UNSUPPORTED_CLAIM"],
        "AI-generated overclaim"),
    # 11-20: variations
    ClaimBenchCase("cb11",
        "F=m*a (no spaces, unicode minus test).",
        ["unit_claim", "math_claim"], ["DIMENSIONALLY_VALID"],
        "valid equation, minimal formatting"),
    ClaimBenchCase("cb12",
        "The claim E = m*c^2 is dimensionally valid and experimentally verified.",
        ["unit_claim", "experimental_claim"], ["DIMENSIONALLY_VALID", "NEEDS_DATA"],
        "valid equation + experimental reference"),
    ClaimBenchCase("cb13",
        "Energy = mass × acceleration is wrong dimensionally.",
        ["unit_claim"], ["DIMENSIONALLY_INVALID"],
        "invalid dimensional claim with unicode multiplication sign"),
    ClaimBenchCase("cb14",
        "We measured the orbital precession to be 0.01 arcsec/century in our experiment.",
        ["experimental_claim"], ["NEEDS_DATA"],
        "experimental result claim"),
    ClaimBenchCase("cb15",
        "This proposes a new modified gravity theory. The data shows deviations at sub-mm scales.",
        ["theory_claim", "experimental_claim"], ["UNSUPPORTED_OPEN_CLAIM", "NEEDS_DATA"],
        "theory + experimental mixed claim"),
    ClaimBenchCase("cb16",
        "The replay produced drift: the certificate hash changed between runs.",
        ["reproducibility_claim"], ["DRIFT_DETECTED"],
        "reproducibility drift claim"),
    ClaimBenchCase("cb17",
        "p = m*v is the momentum equation.",
        ["unit_claim", "math_claim"], ["DIMENSIONALLY_VALID"],
        "valid momentum equation"),
    ClaimBenchCase("cb18",
        "Undoubtedly this conclusively explains everything.",
        ["unsupported_claim"], ["UNSUPPORTED_CLAIM"],
        "unsupported broad overclaim"),
    ClaimBenchCase("cb19",
        "F = m*v proves that force equals momentum.",
        ["unit_claim", "unsupported_claim"], ["DIMENSIONALLY_INVALID", "UNSUPPORTED_CLAIM"],
        "invalid equation + overclaim"),
    ClaimBenchCase("cb20",
        "The equation v = a*t gives velocity from acceleration and time. The experiment observed the result.",
        ["unit_claim", "experimental_claim"], ["DIMENSIONALLY_VALID", "NEEDS_DATA"],
        "valid equation + experimental observation"),
]


def run_claimbench(seed: int = 20260628, model=None) -> dict:
    results = []
    for case in BENCH_CASES:
        report = generate_report(case.text, seed=seed)
        d = report.to_dict()
        d["id"] = case.id
        d["expected_claim_types"] = case.expected_claim_types
        d["expected_statuses"] = case.expected_statuses
        d["why"] = case.why
        # check: at least one expected type appeared
        actual_types = [c["claim_type"] for c in d["extracted_claims"]]
        actual_statuses = [c["gate_status"] for c in d["extracted_claims"]]
        type_match = any(t in actual_types for t in case.expected_claim_types)
        status_match = any(s in actual_statuses for s in case.expected_statuses)
        d["self_consistent"] = type_match and status_match
        d["actual_claim_types"] = actual_types
        d["actual_statuses"] = actual_statuses
        results.append(d)
    passed = sum(1 for r in results if r["self_consistent"])
    score = {
        "name": "Claim Bench Score",
        "value": passed / len(results) if results else 0.0,
        "n": len(results),
        "detail": f"{passed}/{len(results)} claimbench cases correct",
    }
    # aggregate tallies
    type_tally = {}
    status_tally = {}
    total_claims = 0
    total_packs = 0
    for r in results:
        for c in r["extracted_claims"]:
            total_claims += 1
            if c["evidence_pack_id"]:
                total_packs += 1
            type_tally[c["claim_type"]] = type_tally.get(c["claim_type"], 0) + 1
            status_tally[c["gate_status"]] = status_tally.get(c["gate_status"], 0) + 1
    return {
        "bench": "claimbench",
        "mode": "ClaimBench v0 (messy text -> extracted claims -> routed gates -> evidence packs)",
        "public_wording": PUBLIC_WORDING,
        "seed": seed, "n_cases": len(results),
        "total_claims_extracted": total_claims,
        "total_evidence_packs_created": total_packs,
        "claim_type_tally": type_tally,
        "status_tally": status_tally,
        "results": results, "score": score,
    }


__all__ = ["ClaimBenchCase", "BENCH_CASES", "run_claimbench"]
