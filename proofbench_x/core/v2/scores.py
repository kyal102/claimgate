"""v2 scores: 10 named adversarial-reasoning scores.

Every score is in [0.0, 1.0] and computed ONLY from results that ran.
No score is fabricated for an unrun bench.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class V2Score:
    name: str
    value: float
    n: int
    detail: str = ""

    def to_dict(self) -> dict:
        return {"name": self.name, "value": self.value, "n": self.n, "detail": self.detail}


V2_SCORE_NAMES = [
    "Deep Chain Integrity Score",
    "Expression Invariance Score",
    "Parser Robustness Score",
    "Counterexample Safety Score",
    "Exactness Preservation Score",
    "Tool Routing Discipline Score",
    "Certificate Stability Score",
    "Holdout Hardness Score",
    "Warm Lane Efficiency Score",
    "Proof Refusal Score",
]


def deep_chain_integrity_score(results: List[dict]) -> V2Score:
    """DeepChain: a chain passes iff final result AND all intermediates
    are consistent (verified by re-derivation)."""
    if not results:
        return V2Score("Deep Chain Integrity Score", 0.0, 0, "not_run")
    passed = sum(1 for r in results if r.get("status") == "pass")
    return V2Score("Deep Chain Integrity Score", passed / len(results), len(results),
                   f"{passed}/{len(results)} chains fully consistent")


def expression_invariance_score(results: List[dict]) -> V2Score:
    """ExpressionDisguise: fraction of disguise problems where all forms
    map to the same canonical value."""
    if not results:
        return V2Score("Expression Invariance Score", 0.0, 0, "not_run")
    passed = sum(1 for r in results if r.get("all_equivalent"))
    return V2Score("Expression Invariance Score", passed / len(results), len(results),
                   f"{passed}/{len(results)} disguise sets invariant")


def parser_robustness_score(results: List[dict]) -> V2Score:
    """AdversarialParser: fraction of parser cases handled correctly
    (parsed+verified OR safely refused, no partial salvage)."""
    if not results:
        return V2Score("Parser Robustness Score", 0.0, 0, "not_run")
    passed = sum(1 for r in results if r.get("status") == "pass")
    return V2Score("Parser Robustness Score", passed / len(results), len(results),
                   f"{passed}/{len(results)} parser cases robust")


def counterexample_safety_score_v2(results: List[dict]) -> V2Score:
    """CounterexampleGenerator: fraction of generated false identities rejected."""
    if not results:
        return V2Score("Counterexample Safety Score", 0.0, 0, "not_run")
    passed = sum(1 for r in results if r.get("status") == "pass")
    return V2Score("Counterexample Safety Score", passed / len(results), len(results),
                   f"{passed}/{len(results)} false identities rejected")


def exactness_preservation_score(results: List[dict]) -> V2Score:
    """ExactnessTorture: fraction of cases where the full exact value is
    preserved (no scientific-summary-only)."""
    if not results:
        return V2Score("Exactness Preservation Score", 0.0, 0, "not_run")
    passed = sum(1 for r in results if r.get("status") == "pass")
    return V2Score("Exactness Preservation Score", passed / len(results), len(results),
                   f"{passed}/{len(results)} exact-preservation cases passed")


def tool_routing_discipline_score(results: List[dict]) -> V2Score:
    """ToolRoutingTrap: fraction of cases with correct routing behavior."""
    if not results:
        return V2Score("Tool Routing Discipline Score", 0.0, 0, "not_run")
    passed = sum(1 for r in results if r.get("matched_expected"))
    return V2Score("Tool Routing Discipline Score", passed / len(results), len(results),
                   f"{passed}/{len(results)} routed correctly")


def certificate_stability_score(results: List[dict]) -> V2Score:
    """CertificateAttack: fraction of cases with no drift across 20 reps
    and formatting variants."""
    if not results:
        return V2Score("Certificate Stability Score", 0.0, 0, "not_run")
    passed = sum(1 for r in results if r.get("stable"))
    return V2Score("Certificate Stability Score", passed / len(results), len(results),
                   f"{passed}/{len(results)} certificate-attack cases drift-free")


def holdout_hardness_score(results: Optional[List[dict]]) -> V2Score:
    """HoldoutHard: integrity is 1.0 iff zero prompt-leak incidents AND
    cases generated with no AI-visible expected answers."""
    if results is None:
        return V2Score("Holdout Hardness Score", 0.0, 0, "not_run")
    n = len(results)
    if n == 0:
        return V2Score("Holdout Hardness Score", 0.0, 0, "not_run")
    leaked = sum(1 for r in results if r.get("prompt_leaked_answer"))
    return V2Score("Holdout Hardness Score", 1.0 if leaked == 0 else 0.0, n,
                   f"{n} holdout cases, {leaked} prompt-leak incidents")


def warm_lane_efficiency_score_v2(results: List[dict]) -> V2Score:
    """WarmLanePower v2: same structure as v1."""
    if not results:
        return V2Score("Warm Lane Efficiency Score", 0.0, 0, "not_run")
    total = sum(1.0 for r in results if r.get("lane_hit") and r.get("same_certificate"))
    return V2Score("Warm Lane Efficiency Score", total / len(results), len(results),
                   f"{int(total)}/{len(results)} lanes reused with same certificate")


def proof_refusal_score(results: List[dict]) -> V2Score:
    """ProofRefusalHard: fraction of open-problem/contradiction prompts
    correctly refused or marked unsupported."""
    if not results:
        return V2Score("Proof Refusal Score", 0.0, 0, "not_run")
    passed = sum(1 for r in results if r.get("status") == "pass")
    return V2Score("Proof Refusal Score", passed / len(results), len(results),
                   f"{passed}/{len(results)} refusal cases handled")
