"""EvidencePack v0 + ReproGate v0: reproducibility and audit layer.

Public wording:
  "EvidencePack and ReproGate make verification results reproducible and
   auditable. They do not prove scientific truth; they preserve what was
   checked, how it was checked, and whether it can be reproduced."
"""
from .model import (
    ALL_EVIDENCE_STATUSES, PUBLIC_WORDING, PACK_SCHEMA_VERSION,
    MODEL_ROLES, CONTAMINATION_STATUSES,
    EvidencePack, now_iso,
)
from .builder import (
    build_from_unitgate_claim, build_from_physics_claim,
    build_from_theory_claim, build_all_evidence_packs,
    VERIFIER_VERSION, GATE_VERSION,
)
from .reprogate import ReproGate, ReproResult
from .reprobench import ReproCase, REPRO_CASES, run_reprobench
from .scores import (
    EVIDENCE_SCORE_NAMES, EvidenceScore,
    evidence_pack_score, repro_bench_score,
)

__all__ = [
    "ALL_EVIDENCE_STATUSES", "PUBLIC_WORDING", "PACK_SCHEMA_VERSION",
    "MODEL_ROLES", "CONTAMINATION_STATUSES",
    "EvidencePack", "now_iso",
    "build_from_unitgate_claim", "build_from_physics_claim",
    "build_from_theory_claim", "build_all_evidence_packs",
    "VERIFIER_VERSION", "GATE_VERSION",
    "ReproGate", "ReproResult",
    "ReproCase", "REPRO_CASES", "run_reprobench",
    "EVIDENCE_SCORE_NAMES", "EvidenceScore",
    "evidence_pack_score", "repro_bench_score",
]
