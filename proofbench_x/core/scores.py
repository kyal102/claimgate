"""Scores: the 7 named v1 scores + v0 prototype baseline + assembly.

Every score is in [0.0, 1.0] and is computed ONLY from results that
actually ran. No score is ever fabricated for an unrun bench -- absent
results yield `None` and are reported as "not_run" in the final report.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class Score:
    name: str
    value: float
    n: int
    detail: str = ""

    def to_dict(self) -> dict:
        return {"name": self.name, "value": self.value, "n": self.n, "detail": self.detail}


def _ratio(passed: int, total: int, name: str) -> Score:
    if total <= 0:
        return Score(name, 0.0, 0, "not_run")
    return Score(name, passed / total, total, f"{passed}/{total}")


def variant_consistency_score(family_results: Dict[str, List[dict]]) -> Score:
    """VAR-Lane: a family passes only if ALL its variants pass.
    Score = families_all_pass / families_total."""
    if not family_results:
        return Score("Variant Consistency Score", 0.0, 0, "not_run")
    total = len(family_results)
    all_pass = 0
    for fam, results in family_results.items():
        if results and all(r["status"] == "pass" for r in results):
            all_pass += 1
    return Score("Variant Consistency Score", all_pass / total, total,
                 f"{all_pass}/{total} families fully consistent")


def metamorphic_stability_score(pair_results: List[dict]) -> Score:
    """Metamorphic: fraction of equivalent-form pairs that the canonicalizer
    (and exact-value check) confirm equivalent."""
    if not pair_results:
        return Score("Metamorphic Stability Score", 0.0, 0, "not_run")
    passed = sum(1 for r in pair_results if r.get("equivalent"))
    return Score("Metamorphic Stability Score", passed / len(pair_results), len(pair_results),
                 f"{passed}/{len(pair_results)} forms confirmed equivalent")


def counterexample_safety_score(ce_results: List[dict]) -> Score:
    """Counterexample: fraction of false identities the system rejected/refused."""
    if not ce_results:
        return Score("Counterexample Safety Score", 0.0, 0, "not_run")
    passed = sum(1 for r in ce_results if r["status"] == "pass")
    return Score("Counterexample Safety Score", passed / len(ce_results), len(ce_results),
                 f"{passed}/{len(ce_results)} false identities rejected")


def tool_routing_score(routing_results: List[dict]) -> Score:
    """Tool-Routing: fraction of cases where the model exhibited the
    expected behavior (answer_directly / call_supermath / refuse / clarify)."""
    if not routing_results:
        return Score("Tool Routing Score", 0.0, 0, "not_run")
    passed = sum(1 for r in routing_results if r.get("matched_expected"))
    return Score("Tool Routing Score", passed / len(routing_results), len(routing_results),
                 f"{passed}/{len(routing_results)} routed correctly")


def replay_stability_score(replay_results: List[dict]) -> Score:
    """Replay/Drift: a case is stable iff all 10 runs produced identical
    normalized input, result, exactness, certificate hash, and lane id."""
    if not replay_results:
        return Score("Replay Stability Score", 0.0, 0, "not_run")
    passed = sum(1 for r in replay_results if r.get("stable"))
    return Score("Replay Stability Score", passed / len(replay_results), len(replay_results),
                 f"{passed}/{len(replay_results)} cases drift-free across 10 runs")


def warm_lane_efficiency_score(warm_results: List[dict]) -> Score:
    """Warm-Lane Power: weighted by lane-hit and consistency. We do NOT
    overclaim real power savings (no hardware power measurement here);
    we report compute-saving estimate as a separate field, not as this score."""
    if not warm_results:
        return Score("Warm Lane Efficiency Score", 0.0, 0, "not_run")
    total = 0.0
    for r in warm_results:
        if r.get("lane_hit") and r.get("same_certificate"):
            total += 1.0
    return Score("Warm Lane Efficiency Score", total / len(warm_results), len(warm_results),
                 f"{int(total)}/{len(warm_results)} lanes reused with same certificate")


def holdout_integrity_score(holdout_results: Optional[List[dict]]) -> Score:
    """Holdout: integrity is binary -- either the holdout set was generated
    privately with no expected-answer leakage into prompts (1.0), or it
    wasn't produced (not_run). We never expose expected answers in prompts."""
    if holdout_results is None:
        return Score("Holdout Integrity Score", 0.0, 0, "not_run")
    n = len(holdout_results)
    # integrity = no prompt contained the expected answer string
    leaked = sum(1 for r in holdout_results if r.get("prompt_leaked_answer"))
    integrity = 1.0 if leaked == 0 and n > 0 else (0.0 if n > 0 else 0.0)
    return Score("Holdout Integrity Score", integrity, n,
                 f"{n} private holdout cases, {leaked} prompt-leak incidents")


def v0_prototype_baseline_score(v0_results: List[dict]) -> Score:
    """v0 prototype baseline. NOT the real v0 -- a clearly-labeled minimal
    baseline used only so the v1 machinery has a comparison point."""
    if not v0_results:
        return Score("v0 Prototype Baseline Score", 0.0, 0, "not_run")
    passed = sum(1 for r in v0_results if r["status"] == "pass")
    return Score("v0 Prototype Baseline Score", passed / len(v0_results), len(v0_results),
                 f"{passed}/{len(v0_results)} (PROTOTYPE baseline, not real v0)")


def assemble_scores(scores: List[Score]) -> Dict[str, dict]:
    out = {}
    for s in scores:
        out[s.name] = s.to_dict()
    return out
