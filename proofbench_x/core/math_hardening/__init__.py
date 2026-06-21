"""ProofBench X Research Hardening v0.

Public wording:
  "ProofBench X Research Hardening tests whether mathematical claims survive
   domain assumptions, hidden conditions, counterexamples, proof-object
   construction, and replay. It does not prove new mathematics; it verifies
   what conditions are required for a claim to be trusted."
"""
from .domain_gate import DomainGate, DomainClaim, DomainGateResult, SUPPORTED_DOMAINS, DOMAIN_STATUSES
from .assumption_gate import AssumptionGate, AssumptionClaim, AssumptionResult, ASSUMPTION_STATUSES
from .witness_gate import WitnessGate, WitnessClaim, WitnessResult, Witness, WITNESS_STATUSES
from .proof_object import ProofObject, build_proof_object
from .scores import (
    HARDENING_SCORE_NAMES, HardeningScore,
    domain_discipline_score, assumption_safety_score,
    counterexample_witness_score, proof_object_completeness_score,
    certificate_stability_score, overall_research_hardening_score,
)
from .math_hardening_bench import run_math_hardening_bench, PUBLIC_WORDING

__all__ = [
    "DomainGate", "DomainClaim", "DomainGateResult", "SUPPORTED_DOMAINS", "DOMAIN_STATUSES",
    "AssumptionGate", "AssumptionClaim", "AssumptionResult", "ASSUMPTION_STATUSES",
    "WitnessGate", "WitnessClaim", "WitnessResult", "Witness", "WITNESS_STATUSES",
    "ProofObject", "build_proof_object",
    "HARDENING_SCORE_NAMES", "HardeningScore",
    "domain_discipline_score", "assumption_safety_score",
    "counterexample_witness_score", "proof_object_completeness_score",
    "certificate_stability_score", "overall_research_hardening_score",
    "run_math_hardening_bench", "PUBLIC_WORDING",
]
