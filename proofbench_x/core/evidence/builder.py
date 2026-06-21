"""Evidence builder: turn gate results into EvidencePacks.

Creates evidence packs from:
  - UnitGate results (physics/unitgate)
  - PhysicsClaimBench results (physics/claimbench)
  - TheoryGate results (theory/theorygate)
  - ProofBench v1 results (var_lane, counterexample, etc.)

Each pack is sealed (certificate_hash + evidence_pack_hash computed) and
carries a repro_command so ReproGate can attempt reproduction.
"""
from __future__ import annotations

from typing import Optional

from .model import EvidencePack, now_iso, PACK_SCHEMA_VERSION
from ..physics.dimensions import lookup_unit
from ..physics.unitgate import UnitGate, CLAIMS as UNIT_CLAIMS
from ..physics.claimbench import PhysicsClaimBench
from ..physics.bench_claims import BENCH_CLAIMS as PHYSICS_BENCH_CLAIMS
from ..theory.theorygate import TheoryGate
from ..theory.bench_claims import THEORY_CLAIMS


VERIFIER_VERSION = "supermath.prototype.v0"
GATE_VERSION = "v0"


def _normalize_unitgate_input(lhs_unit: str, rhs_units: list) -> str:
    """Produce a stable normalized input string for a UnitGate claim."""
    parts = [lhs_unit]
    for op, name in rhs_units:
        parts.append(f"{op}:{name}")
    return "|".join(parts)


def build_from_unitgate_claim(claim, seed: int = 20260624,
                              contamination: str = "clean",
                              code_hash: Optional[str] = None,
                              data_backed: bool = False) -> EvidencePack:
    """Build an EvidencePack from a single UnitGate claim."""
    gate = UnitGate()
    gr = gate.check_claim(claim.lhs_unit, claim.rhs_units)
    normalized = _normalize_unitgate_input(claim.lhs_unit, claim.rhs_units)
    pack = EvidencePack(
        pack_id=f"ev_unit_{claim.id}",
        timestamp=now_iso(),
        gate_name="UnitGate",
        gate_version=GATE_VERSION,
        raw_claim_or_input=claim.statement,
        normalized_input=normalized,
        status=gr.verdict,
        sub_statuses=[],
        result_body={
            "lhs_dimension": gr.lhs_dimension,
            "rhs_dimension": gr.rhs_dimension,
            "note": gr.note,
        },
        code_hash=code_hash,
        data_hash=None,
        seed=seed,
        verifier_version=VERIFIER_VERSION,
        model_used=None,
        model_role="none",
        contamination_status=contamination,
        limitations=[
            "UnitGate checks dimensional consistency only; it does not prove physical truth.",
            "Exact rational exponents (no floats) for dimensional checks.",
        ],
        next_required_validation="dimensional check complete; proceed to PhysicsClaimBench if applicable",
        repro_command=(
            f"python -m proofbench_x run --physics --bench unitgate --json --seed {seed}"
        ),
        human_readable_summary=(
            f"UnitGate on '{claim.statement}': {gr.verdict} "
            f"(lhs={gr.lhs_dimension}, rhs={gr.rhs_dimension})"
        ),
        _data_backed=data_backed,
    )
    return pack.seal()


def build_from_physics_claim(claim, seed: int = 20260624,
                             contamination: str = "clean",
                             code_hash: Optional[str] = None,
                             data_backed: bool = False) -> EvidencePack:
    """Build an EvidencePack from a PhysicsClaimBench claim."""
    bench = PhysicsClaimBench()
    result = bench.evaluate(claim)
    normalized = f"{claim.id}|{claim.category}|{claim.expected_final_status}"
    pack = EvidencePack(
        pack_id=f"ev_phys_{claim.id}",
        timestamp=now_iso(),
        gate_name="PhysicsClaimBench",
        gate_version=GATE_VERSION,
        raw_claim_or_input=claim.statement,
        normalized_input=normalized,
        status=result.final_status,
        sub_statuses=[k for k, v in result.gate_results.items()
                      if isinstance(v, dict) and "verdict" in v],
        result_body=result.to_dict(),
        code_hash=code_hash,
        data_hash=None,
        seed=seed,
        verifier_version=VERIFIER_VERSION,
        model_used=None,
        model_role="none",
        contamination_status=contamination,
        limitations=[
            "PhysicsClaimBench routes through UnitGate/LimitGate/ConservationGate; not proof of physical truth.",
            "Counterexample search is bounded; 'no counterexample found' != 'proven true'.",
        ],
        next_required_validation=result.note,
        repro_command=(
            f"python -m proofbench_x run --physics --bench physicsclaim --json --seed {seed}"
        ),
        human_readable_summary=(
            f"PhysicsClaimBench on '{claim.statement}': {result.final_status}"
        ),
        _data_backed=data_backed,
    )
    return pack.seal()


def build_from_theory_claim(theory, seed: int = 20260625,
                            contamination: str = "clean",
                            code_hash: Optional[str] = None,
                            data_backed: bool = False) -> EvidencePack:
    """Build an EvidencePack from a TheoryGate claim."""
    gate = TheoryGate()
    pack_result = gate.evaluate(theory)
    normalized = f"{theory.theory_name}|{theory.category}"
    pack = EvidencePack(
        pack_id=f"ev_theory_{pack_result.theory_name[:32]}",
        timestamp=now_iso(),
        gate_name="TheoryGate",
        gate_version=GATE_VERSION,
        raw_claim_or_input=theory.raw_claim,
        normalized_input=normalized,
        status=pack_result.final_status,
        sub_statuses=[
            pack_result.physics_gate_result.get("any_dimensionally_invalid") and "DIMENSIONALLY_INVALID",
            pack_result.known_law_checklist_result.get("verdict", ""),
            pack_result.falsifiability_result.get("verdict", ""),
            pack_result.prediction_result.get("verdict", ""),
        ],
        result_body=pack_result.to_dict(),
        code_hash=code_hash,
        data_hash=None,
        seed=seed,
        verifier_version=VERIFIER_VERSION,
        model_used=None,
        model_role="none",
        contamination_status=contamination,
        limitations=pack_result.limitations + [
            "TheoryGate is a structural check; it does not prove new physics.",
            "CANDIDATE_THEORY means 'worth investigating', never 'proven true'.",
        ],
        next_required_validation=pack_result.next_required_validation,
        repro_command=(
            f"python -m proofbench_x run --theory --bench theorygate --json --seed {seed}"
        ),
        human_readable_summary=(
            f"TheoryGate on '{theory.theory_name}': {pack_result.final_status}"
        ),
        _data_backed=data_backed,
    )
    return pack.seal()


def build_all_evidence_packs(seed: int = 20260624,
                             code_hash: Optional[str] = None) -> list:
    """Build evidence packs from all available gate results.

    Returns a list of sealed EvidencePacks covering UnitGate, PhysicsClaimBench,
    and TheoryGate examples.
    """
    packs = []
    # UnitGate claims (first 5 for brevity)
    for claim in UNIT_CLAIMS[:5]:
        packs.append(build_from_unitgate_claim(claim, seed=seed, code_hash=code_hash))
    # PhysicsClaimBench claims (all 10)
    for claim in PHYSICS_BENCH_CLAIMS:
        packs.append(build_from_physics_claim(claim, seed=seed, code_hash=code_hash))
    # TheoryGate claims (all 10)
    for theory in THEORY_CLAIMS:
        packs.append(build_from_theory_claim(theory, seed=seed, code_hash=code_hash))
    return packs


__all__ = [
    "build_from_unitgate_claim", "build_from_physics_claim",
    "build_from_theory_claim", "build_all_evidence_packs",
    "VERIFIER_VERSION", "GATE_VERSION",
]
