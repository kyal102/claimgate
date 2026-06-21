"""Canonical PhysicsBench claim set: 6 categories, conservative statuses.

Categories:
  - valid_known          : known-good equations; should pass all gates
  - invalid_fake         : plausible-but-false equations; should be refuted
  - equivalent_transform : algebraically equivalent form of a known law
  - unit_trap            : dimensionally wrong; must fail UnitGate
  - open_new_physics     : speculative claim; must be UNSUPPORTED_OPEN_CLAIM or NEEDS_EXPERIMENT
  - needs_simulation     : requires numeric simulation; not provable by gates alone
"""
from __future__ import annotations

from .claimbench import PhysicsBenchClaim
from .unitgate import PhysicsClaim as UnitClaim, CLAIMS as UNIT_CLAIMS
from .limitgate import LIMIT_CASES
from .conservationgate import CONSERVATION_CASES
from .counterexample import COUNTEREXAMPLE_CASES


def _build_claim_set() -> list:
    out = []

    # --- valid_known: known-good equations ---
    out.append(PhysicsBenchClaim(
        id="pbc_v1", statement="F = m * a (Newton's 2nd law)",
        category="valid_known",
        unit_claim=UNIT_CLAIMS[0],  # pc1
        limit_case=None, conservation_case=None, counterexample_case=None,
        expected_final_status="DIMENSIONALLY_VALID",
        why="known-good; passes UnitGate"))

    out.append(PhysicsBenchClaim(
        id="pbc_v2", statement="E_kinetic = m * v^2 / 2",
        category="valid_known",
        unit_claim=None, limit_case=None, conservation_case=None,
        counterexample_case=None,
        expected_final_status="DIMENSIONALLY_VALID",
        why="known-good kinetic energy (dimensional check passes)"))

    # --- invalid_fake: plausible-but-false ---
    out.append(PhysicsBenchClaim(
        id="pbc_i1", statement="E = m * a (FALSE: energy != mass * acceleration)",
        category="invalid_fake",
        unit_claim=UNIT_CLAIMS[1],  # pc2
        limit_case=None, conservation_case=None, counterexample_case=None,
        expected_final_status="DIMENSIONALLY_INVALID",
        why="dimensionally invalid; fails UnitGate immediately"))

    out.append(PhysicsBenchClaim(
        id="pbc_i2", statement="(a+b)^2 = a^2 + b^2 (FALSE: drops cross term)",
        category="invalid_fake",
        unit_claim=None, limit_case=None, conservation_case=None,
        counterexample_case=COUNTEREXAMPLE_CASES[1],  # pec2
        expected_final_status="REFUTED_BY_COUNTEREXAMPLE",
        why="algebraically false; counterexample search refutes it"))

    # --- equivalent_transform: algebraically equivalent form ---
    out.append(PhysicsBenchClaim(
        id="pbc_e1", statement="2*x = x + x (equivalent form)",
        category="equivalent_transform",
        unit_claim=None, limit_case=None, conservation_case=None,
        counterexample_case=COUNTEREXAMPLE_CASES[0],  # pec1
        expected_final_status="ALGEBRAICALLY_VALID",
        why="true identity; no counterexample found in range"))

    # --- unit_trap: dimensionally wrong ---
    out.append(PhysicsBenchClaim(
        id="pbc_u1", statement="E = F / d (FALSE: energy != force / distance)",
        category="unit_trap",
        unit_claim=UNIT_CLAIMS[6],  # pc7
        limit_case=None, conservation_case=None, counterexample_case=None,
        expected_final_status="DIMENSIONALLY_INVALID",
        why="unit trap: energy is force*distance, not force/distance"))

    out.append(PhysicsBenchClaim(
        id="pbc_u2", statement="p = m / v (FALSE: momentum != mass / velocity)",
        category="unit_trap",
        unit_claim=UNIT_CLAIMS[8],  # pc9
        limit_case=None, conservation_case=None, counterexample_case=None,
        expected_final_status="DIMENSIONALLY_INVALID",
        why="unit trap: momentum is mass*velocity, not mass/velocity"))

    # --- open_new_physics: speculative, must NOT claim truth ---
    out.append(PhysicsBenchClaim(
        id="pbc_o1", statement="Proposed: dark energy density ~ m * c^3 / h (speculative)",
        category="open_unsupported",
        unit_claim=None, limit_case=None, conservation_case=None,
        counterexample_case=None,
        expected_final_status="UNSUPPORTED_OPEN_CLAIM",
        why="speculative new-physics claim; v0 must mark UNSUPPORTED, never 'proven'"))

    out.append(PhysicsBenchClaim(
        id="pbc_o2", statement="Proposed: modified gravity F = G*m1*m2/r^2.1 (speculative exponent)",
        category="open_needs_experiment",
        unit_claim=None, limit_case=None, conservation_case=None,
        counterexample_case=None,
        expected_final_status="NEEDS_EXPERIMENT",
        why="modified-gravity claim; testable but requires experimental validation, not gate approval"))

    # --- needs_simulation ---
    out.append(PhysicsBenchClaim(
        id="pbc_s1", statement="N-body orbital stability under perturbation",
        category="needs_simulation",
        unit_claim=None, limit_case=None, conservation_case=None,
        counterexample_case=None,
        expected_final_status="NEEDS_SIMULATION",
        why="requires numeric simulation; gates cannot decide"))

    return out


BENCH_CLAIMS = _build_claim_set()
