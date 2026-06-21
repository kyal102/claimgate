"""JSON schema for ProofBench X results.

Defines the shape of `run --json` output so researchers can parse it
programmatically. The schema is intentionally permissive (additional
properties allowed) so v0 and v1 outputs both validate.
"""
from __future__ import annotations

# Top-level result envelope
RESULT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "SuperMathProofBenchXResult",
    "type": "object",
    "required": ["benchmark", "descriptor", "version"],
    "properties": {
        "benchmark": {"type": "string"},
        "descriptor": {
            "type": "string",
            "const": "proof-aware mathematical verification benchmark"
        },
        "version": {"type": "string"},
        "is_prototype": {"type": "boolean"},
        "mode": {"type": "string"},
        "seed": {"type": "integer"},
        "total_v1_cases": {"type": "integer"},
        "n_cases": {"type": "integer"},
        "n_benches": {"type": "integer"},
        "benches": {"type": "object"},
        "scores": {"type": "object"},
        "result": {"type": "object"},
        "score": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "value": {"type": ["number", "null"]},
                "n": {"type": "integer"},
                "detail": {"type": "string"}
            }
        },
    },
    "additionalProperties": True,
}

# Per-bench score object
SCORE_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "ProofBenchScore",
    "type": "object",
    "required": ["name", "value", "n", "detail"],
    "properties": {
        "name": {"type": "string"},
        "value": {"type": ["number", "null"]},
        "n": {"type": "integer"},
        "detail": {"type": "string"},
    },
    "additionalProperties": False,
}

# Certificate object
CERTIFICATE_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "ProofBenchCertificate",
    "type": "object",
    "required": ["problem_id", "family", "problem_canonical", "result_kind",
                 "result_canonical", "lane_id", "verified", "hash"],
    "properties": {
        "problem_id": {"type": "string"},
        "family": {"type": "string"},
        "problem_canonical": {"type": "string"},
        "result_kind": {"type": "string"},
        "result_canonical": {"type": "string"},
        "lane_id": {"type": "string"},
        "verified": {"type": "boolean"},
        "note": {"type": "string"},
        "hash": {"type": "string"},
    },
    "additionalProperties": False,
}

# All v1 score names (canonical)
V1_SCORE_NAMES = [
    "Variant Consistency Score",
    "Metamorphic Stability Score",
    "Counterexample Safety Score",
    "Tool Routing Score",
    "Replay Stability Score",
    "Warm Lane Efficiency Score",
    "Holdout Integrity Score",
    "Exactness Stress Score",
]

# All v0 score names (canonical, preserved)
V0_SCORE_NAMES = [
    "Math Trust Score",
    "DTL Acceleration",
    "Proof Integrity",
    "Model Trap Resistance",
]


def validate_score(score_dict: dict) -> bool:
    """Lightweight structural validation of a score dict."""
    return all(k in score_dict for k in ("name", "value", "n", "detail"))
