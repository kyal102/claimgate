"""Core engine: exact arithmetic, canonicalization, certificates, verifier, scores."""

from .exact import (
    Exact,
    ExactValue,
    exact_pow,
    exact_mod_pow,
    exact_gcd,
    exact_lcm,
    parse_int_strict,
    big_int_preserve,
    factorial,
)
from .canonical import canonicalize, canonical_value, normalize_input
from .certificate import Certificate, cert_hash
from .verifier import Verifier, VerificationResult, solve
from .scores import (
    Score,
    variant_consistency_score,
    metamorphic_stability_score,
    counterexample_safety_score,
    tool_routing_score,
    replay_stability_score,
    warm_lane_efficiency_score,
    holdout_integrity_score,
    v0_prototype_baseline_score,
    assemble_scores,
)
from .families import Family, FAMILY_REGISTRY, make_variants
from .metamorphic import metamorphic_forms
from .counterexamples import COUNTEREXAMPLES
from .routing import RoutingExpectation, ROUTING_CASES
from .v0_scores import (
    V0_SCORE_NAMES,
    math_trust_score,
    dtl_acceleration,
    proof_integrity,
    model_trap_resistance,
    all_v0_score_hooks,
)
from .duel import ModelDuel, DuelReport, LaneResult
from .schema import V1_SCORE_NAMES, RESULT_SCHEMA, SCORE_SCHEMA, CERTIFICATE_SCHEMA
from .report import export_research_report, export_json_report

__all__ = [
    "Exact", "ExactValue",
    "exact_pow", "exact_mod_pow", "exact_gcd", "exact_lcm",
    "parse_int_strict", "big_int_preserve", "factorial",
    "canonicalize", "canonical_value", "normalize_input",
    "Certificate", "cert_hash",
    "Verifier", "VerificationResult", "solve",
    "Score",
    "variant_consistency_score", "metamorphic_stability_score",
    "counterexample_safety_score", "tool_routing_score",
    "replay_stability_score", "warm_lane_efficiency_score",
    "holdout_integrity_score", "v0_prototype_baseline_score",
    "assemble_scores",
    "Family", "FAMILY_REGISTRY", "make_variants",
    "metamorphic_forms",
    "COUNTEREXAMPLES",
    "RoutingExpectation", "ROUTING_CASES",
    "V0_SCORE_NAMES", "math_trust_score", "dtl_acceleration",
    "proof_integrity", "model_trap_resistance", "all_v0_score_hooks",
    "ModelDuel", "DuelReport", "LaneResult",
    "V1_SCORE_NAMES", "RESULT_SCHEMA", "SCORE_SCHEMA", "CERTIFICATE_SCHEMA",
    "export_research_report", "export_json_report",
]
