"""Scores for ProofBench X Research Hardening v0."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List


@dataclass
class HardeningScore:
    name: str
    value: float
    n: int
    detail: str = ""
    def to_dict(self) -> dict:
        return {"name": self.name, "value": self.value, "n": self.n, "detail": self.detail}


HARDENING_SCORE_NAMES = [
    "Domain Discipline Score",
    "Assumption Safety Score",
    "Counterexample Witness Score",
    "Proof Object Completeness Score",
    "Certificate Stability Score",
    "Overall Research Hardening Score",
]


def domain_discipline_score(results: List[dict]) -> HardeningScore:
    if not results:
        return HardeningScore("Domain Discipline Score", 0.0, 0, "not_run")
    passed = sum(1 for r in results if r.get("self_consistent"))
    return HardeningScore("Domain Discipline Score", passed / len(results), len(results),
                          f"{passed}/{len(results)} domain cases correct")


def assumption_safety_score(results: List[dict]) -> HardeningScore:
    if not results:
        return HardeningScore("Assumption Safety Score", 0.0, 0, "not_run")
    passed = sum(1 for r in results if r.get("self_consistent"))
    return HardeningScore("Assumption Safety Score", passed / len(results), len(results),
                          f"{passed}/{len(results)} assumption cases correct")


def counterexample_witness_score(results: List[dict]) -> HardeningScore:
    if not results:
        return HardeningScore("Counterexample Witness Score", 0.0, 0, "not_run")
    passed = sum(1 for r in results if r.get("self_consistent"))
    return HardeningScore("Counterexample Witness Score", passed / len(results), len(results),
                          f"{passed}/{len(results)} witness cases correct")


def proof_object_completeness_score(results: List[dict]) -> HardeningScore:
    if not results:
        return HardeningScore("Proof Object Completeness Score", 0.0, 0, "not_run")
    passed = sum(1 for r in results if r.get("has_proof_object") and r.get("cert_hash_stable"))
    return HardeningScore("Proof Object Completeness Score", passed / len(results), len(results),
                          f"{passed}/{len(results)} proof objects complete with stable cert hash")


def certificate_stability_score(results: List[dict]) -> HardeningScore:
    if not results:
        return HardeningScore("Certificate Stability Score", 0.0, 0, "not_run")
    passed = sum(1 for r in results if r.get("cert_hash_stable"))
    return HardeningScore("Certificate Stability Score", passed / len(results), len(results),
                          f"{passed}/{len(results)} certificate hashes stable across reruns")


def overall_research_hardening_score(sub_scores: List[float]) -> HardeningScore:
    """Average of all sub-scores."""
    if not sub_scores:
        return HardeningScore("Overall Research Hardening Score", 0.0, 0, "not_run")
    avg = sum(sub_scores) / len(sub_scores)
    return HardeningScore("Overall Research Hardening Score", avg, len(sub_scores),
                          f"average of {len(sub_scores)} sub-scores: {avg:.4f}")
