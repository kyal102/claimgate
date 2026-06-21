"""TheoryGate v0: structural check for proposed physics theories.

Public wording:
  "TheoryGate checks whether a proposed physics theory is mathematically
   structured, dimensionally coherent, falsifiable, and prediction-bearing.
   It does not prove new physics or replace simulation, experiment, or
   peer review."
"""
from .model import (
    ALL_THEORY_STATUSES, PUBLIC_WORDING,
    Variable, KnownLawCheck, Prediction, TheoryClaim,
)
from .gates import (
    VariableGate, VariableGateResult,
    KnownLawGate, KnownLawGateResult,
    FalsifiabilityGate, FalsifiabilityResult,
    PredictionGate, PredictionResult,
)
from .theorygate import TheoryGate, EvidencePack
from .bench_claims import THEORY_CLAIMS
from .scores import THEORY_SCORE_NAMES, TheoryScore, theory_gate_score, theory_bench_score

__all__ = [
    "ALL_THEORY_STATUSES", "PUBLIC_WORDING",
    "Variable", "KnownLawCheck", "Prediction", "TheoryClaim",
    "VariableGate", "VariableGateResult",
    "KnownLawGate", "KnownLawGateResult",
    "FalsifiabilityGate", "FalsifiabilityResult",
    "PredictionGate", "PredictionResult",
    "TheoryGate", "EvidencePack",
    "THEORY_CLAIMS",
    "THEORY_SCORE_NAMES", "TheoryScore", "theory_gate_score", "theory_bench_score",
]
