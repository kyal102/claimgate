"""v2 subpackage: Invariance & Adversarial Reasoning Mode."""

from .deepchain import generate_chain, verify_chain, ChainProblem, ChainStep
from .disguise import disguise_problem_set, verify_disguise_problem
from .parser import parser_problem_set, attempt_parse, grade_parser_case
from .counterexamples import generate_counterexamples, grade_counterexample_response
from .exactness import exactness_torture_set, _bareiss_determinant
from .traps import ROUTING_TRAPS, REFUSAL_CASES, certificate_attack_cases, grade_certificate_attack
from .scores import (
    V2_SCORE_NAMES, V2Score,
    deep_chain_integrity_score, expression_invariance_score,
    parser_robustness_score, counterexample_safety_score_v2,
    exactness_preservation_score, tool_routing_discipline_score,
    certificate_stability_score, holdout_hardness_score,
    warm_lane_efficiency_score_v2, proof_refusal_score,
)

__all__ = [
    "generate_chain", "verify_chain", "ChainProblem", "ChainStep",
    "disguise_problem_set", "verify_disguise_problem",
    "parser_problem_set", "attempt_parse", "grade_parser_case",
    "generate_counterexamples", "grade_counterexample_response",
    "exactness_torture_set", "_bareiss_determinant",
    "ROUTING_TRAPS", "REFUSAL_CASES", "certificate_attack_cases", "grade_certificate_attack",
    "V2_SCORE_NAMES", "V2Score",
    "deep_chain_integrity_score", "expression_invariance_score",
    "parser_robustness_score", "counterexample_safety_score_v2",
    "exactness_preservation_score", "tool_routing_discipline_score",
    "certificate_stability_score", "holdout_hardness_score",
    "warm_lane_efficiency_score_v2", "proof_refusal_score",
]
