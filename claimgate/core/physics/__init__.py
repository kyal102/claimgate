"""PhysicsGate v0: mathematical and dimensional coherence of physics claims.

Public wording:
  "PhysicsGate checks mathematical and dimensional coherence of physics
   claims. It does not prove new physics or replace experiment."
"""
from .dimensions import (
    Dimension, Quantity, UNIT_TABLE, lookup_unit,
    MASS, LENGTH, TIME, CURRENT, TEMPERATURE, AMOUNT, LUMINOUS_INTENSITY,
    DIMENSIONLESS, BASE_DIMS,
)
from .unitgate import UnitGate, UnitGateResult, PhysicsClaim, CLAIMS as UNIT_CLAIMS, run_unitgate_claims
from .limitgate import LimitGate, LimitGateResult, LimitCase, LIMIT_CASES
from .conservationgate import ConservationGate, ConservationResult, ConservationCase, CONSERVATION_CASES
from .uncertaintygate import UncertaintyGate, UncertaintyResult, UncertainValue, UncertaintyCase, UNCERTAINTY_CASES
from .counterexample import PhysicsCounterexample, CounterexampleResult, CounterexampleCase, COUNTEREXAMPLE_CASES
from .claimbench import PhysicsClaimBench, PhysicsBenchClaim, ClaimPipelineResult, ALL_STATUSES
from .bench_claims import BENCH_CLAIMS
from .scores import (
    PHYSICS_SCORE_NAMES, PhysicsScore,
    unit_gate_score, limit_gate_score, conservation_gate_score,
    uncertainty_propagation_score, physics_claim_pipeline_score,
)

PUBLIC_WORDING = ("PhysicsGate checks mathematical and dimensional coherence of "
                  "physics claims. It does not prove new physics or replace experiment.")

__all__ = [
    "PUBLIC_WORDING",
    "Dimension", "Quantity", "UNIT_TABLE", "lookup_unit",
    "MASS", "LENGTH", "TIME", "CURRENT", "TEMPERATURE", "AMOUNT",
    "LUMINOUS_INTENSITY", "DIMENSIONLESS", "BASE_DIMS",
    "UnitGate", "UnitGateResult", "PhysicsClaim", "UNIT_CLAIMS", "run_unitgate_claims",
    "LimitGate", "LimitGateResult", "LimitCase", "LIMIT_CASES",
    "ConservationGate", "ConservationResult", "ConservationCase", "CONSERVATION_CASES",
    "UncertaintyGate", "UncertaintyResult", "UncertainValue", "UncertaintyCase", "UNCERTAINTY_CASES",
    "PhysicsCounterexample", "CounterexampleResult", "CounterexampleCase", "COUNTEREXAMPLE_CASES",
    "PhysicsClaimBench", "PhysicsBenchClaim", "ClaimPipelineResult", "ALL_STATUSES",
    "BENCH_CLAIMS",
    "PHYSICS_SCORE_NAMES", "PhysicsScore",
    "unit_gate_score", "limit_gate_score", "conservation_gate_score",
    "uncertainty_propagation_score", "physics_claim_pipeline_score",
]
