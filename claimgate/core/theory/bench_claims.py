"""TheoryBench v0: 10 categories of theory claims.

Categories:
  - incomplete          : missing core fields (name/claim)
  - undefined_vars      : variables without name/meaning
  - missing_units       : variables without valid units
  - dim_invalid         : equations fail UnitGate
  - unfalsifiable       : no falsifiable conditions
  - no_prediction       : no measurable predictions
  - known_law_conflict  : declared known-law check fails
  - sim_needed          : complete but requires simulation
  - exp_needed          : complete but requires experiment
  - candidate           : complete, falsifiable, predictive -> CANDIDATE_THEORY
"""
from __future__ import annotations

from .model import TheoryClaim, Variable, KnownLawCheck, Prediction
from ..physics.unitgate import PhysicsClaim


def _build_theory_claims() -> list:
    out = []

    # 1. incomplete -- missing raw claim
    out.append(TheoryClaim(
        theory_name="Empty Theory",
        raw_claim="",
        category="incomplete",
        why="no raw claim stated",
        expected_final_status="THEORY_INCOMPLETE",
    ))

    # 2. undefined_vars -- variable has no meaning
    out.append(TheoryClaim(
        theory_name="Mystery Force Theory",
        raw_claim="Proposes a new force F = Q * z where Q and z are undefined quantities.",
        category="undefined_vars",
        variables=[
            Variable(name="Q", meaning="", unit_name="force"),
            Variable(name="z", meaning="mystery factor", unit_name="dimensionless"),
        ],
        why="variable Q has no meaning",
        expected_final_status="VARIABLES_UNDEFINED",
    ))

    # 3. missing_units -- variable has unknown unit
    out.append(TheoryClaim(
        theory_name="Phlogiston Field Theory",
        raw_claim="Proposes a field P with unit 'phlogiston' (not a real unit).",
        category="missing_units",
        variables=[
            Variable(name="P", meaning="phlogiston field strength", unit_name="phlogiston"),
        ],
        why="unit 'phlogiston' is not in the unit table",
        expected_final_status="UNITS_UNDEFINED",
    ))

    # 4. dim_invalid -- equation fails UnitGate
    out.append(TheoryClaim(
        theory_name="Energy-Acceleration Theory",
        raw_claim="Claims E = m * a (energy = mass * acceleration), which is dimensionally wrong.",
        category="dim_invalid",
        variables=[
            Variable(name="E", meaning="energy", unit_name="energy"),
            Variable(name="m", meaning="mass", unit_name="mass"),
            Variable(name="a", meaning="acceleration", unit_name="acceleration"),
        ],
        equations=[
            PhysicsClaim("tat1", "E = m * a", "energy",
                         [("mul", "mass"), ("mul", "acceleration")],
                         "DIMENSIONALLY_INVALID", ""),
        ],
        why="energy != mass * acceleration dimensionally",
        expected_final_status="DIMENSIONALLY_INVALID",
    ))

    # 5. unfalsifiable -- no falsifiable conditions
    out.append(TheoryClaim(
        theory_name="Cosmic Harmony Field",
        raw_claim="Proposes an undetectable harmony field that explains everything but predicts nothing testable.",
        category="unfalsifiable",
        variables=[
            Variable(name="H", meaning="harmony field", unit_name="energy"),
        ],
        equations=[
            PhysicsClaim("tat2", "H = E_total", "energy",
                         [("mul", "energy")], "DIMENSIONALLY_VALID", ""),
        ],
        known_law_checks=[
            KnownLawCheck("conservation_energy", "total energy conserved", True),
        ],
        falsifiable_conditions=[],  # none
        why="no falsifiable conditions stated",
        expected_final_status="NOT_FALSIFIABLE",
    ))

    # 6. no_prediction -- no measurable predictions
    out.append(TheoryClaim(
        theory_name="Quantum Resonance Framework",
        raw_claim="A framework with variables and falsifiable conditions but no measurable predictions.",
        category="no_prediction",
        variables=[
            Variable(name="R", meaning="resonance amplitude", unit_name="length"),
        ],
        equations=[
            PhysicsClaim("tat3", "R = L", "length",
                         [("mul", "length")], "DIMENSIONALLY_VALID", ""),
        ],
        known_law_checks=[
            KnownLawCheck("limit_zero", "R -> 0 as system size -> 0", True),
        ],
        falsifiable_conditions=[
            "If resonance amplitude is measured to be independent of system size, the theory is wrong.",
        ],
        predictions=[],  # none
        why="no measurable predictions",
        expected_final_status="NO_TESTABLE_PREDICTION",
    ))

    # 7. known_law_conflict -- declared check fails
    out.append(TheoryClaim(
        theory_name="Anti-Gravity Matter Theory",
        raw_claim="Claims a form of matter that produces repulsive gravity, but the Newtonian limit check fails.",
        category="known_law_conflict",
        variables=[
            Variable(name="F", meaning="force", unit_name="force"),
            Variable(name="m", meaning="mass", unit_name="mass"),
            Variable(name="a", meaning="acceleration", unit_name="acceleration"),
        ],
        equations=[
            PhysicsClaim("tat4", "F = m*a (force law, dimensionally valid)", "force",
                         [("mul", "mass"), ("mul", "acceleration")],
                         "DIMENSIONALLY_VALID", ""),
        ],
        known_law_checks=[
            KnownLawCheck("newtonian", "reduces to Newtonian gravity at weak fields", False,
                          "sign is reversed; does not reduce to Newtonian"),
        ],
        falsifiable_conditions=[
            "If no repulsive gravitational effect is observed in Cavendish-type experiments, theory is wrong.",
        ],
        predictions=[
            Prediction(observable="gravitational force sign",
                       condition="Cavendish experiment with candidate material",
                       expected_value="repulsive (negative)",
                       unit_name="force",
                       required_measurement="experiment"),
        ],
        why="Newtonian limit check fails (sign reversed)",
        expected_final_status="KNOWN_LIMIT_CONFLICT",
    ))

    # 8. sim_needed -- complete but requires simulation
    out.append(TheoryClaim(
        theory_name="Modified N-Body Dynamics",
        raw_claim="A complete, falsifiable, predictive theory of N-body orbital dynamics under a modified potential.",
        category="sim_needed",
        variables=[
            Variable(name="F", meaning="force", unit_name="force"),
            Variable(name="m", meaning="mass", unit_name="mass"),
            Variable(name="r", meaning="distance", unit_name="length"),
            Variable(name="a", meaning="acceleration", unit_name="acceleration"),
        ],
        equations=[
            PhysicsClaim("tat5", "F = m*a", "force",
                         [("mul", "mass"), ("mul", "acceleration")],
                         "DIMENSIONALLY_VALID", ""),
        ],
        known_law_checks=[
            KnownLawCheck("newtonian", "reduces to Newtonian at small perturbations", True),
            KnownLawCheck("conservation_energy", "energy conserved in closed system", True),
            KnownLawCheck("inverse_square", "approaches inverse-square at large r", True),
        ],
        falsifiable_conditions=[
            "If orbital simulations show no deviation from Newtonian at the predicted scale, theory is wrong.",
        ],
        predictions=[
            Prediction(observable="orbital precession rate",
                       condition="outer solar system bodies",
                       expected_value="deviation of 0.01 arcsec/century",
                       unit_name="frequency",
                       required_measurement="simulation"),
        ],
        requires_simulation=True,
        why="complete but requires simulation to test predictions",
        expected_final_status="NEEDS_SIMULATION",
    ))

    # 9. exp_needed -- complete but requires experiment
    out.append(TheoryClaim(
        theory_name="Sub-Millimeter Inverse-Square Deviation",
        raw_claim="A complete theory predicting deviation from inverse-square gravity at sub-millimeter scales.",
        category="exp_needed",
        variables=[
            Variable(name="F", meaning="force", unit_name="force"),
            Variable(name="m", meaning="mass", unit_name="mass"),
            Variable(name="a", meaning="acceleration", unit_name="acceleration"),
        ],
        equations=[
            PhysicsClaim("tat6", "F = m*a (force law, dimensionally valid)", "force",
                         [("mul", "mass"), ("mul", "acceleration")],
                         "DIMENSIONALLY_VALID", ""),
        ],
        known_law_checks=[
            KnownLawCheck("newtonian", "reduces to Newtonian at r > 1mm", True),
            KnownLawCheck("inverse_square", "approaches inverse-square at large r", True),
            KnownLawCheck("limit_infinity", "F -> 0 as r -> infinity", True),
        ],
        falsifiable_conditions=[
            "If torsion-balance experiments show no deviation at sub-mm scales, theory is wrong.",
        ],
        predictions=[
            Prediction(observable="gravitational force at r=0.1mm",
                       condition="torsion balance experiment",
                       expected_value="deviation of 5% from inverse-square",
                       unit_name="force",
                       required_measurement="experiment"),
        ],
        requires_experiment=True,
        why="complete but requires experiment to test predictions",
        expected_final_status="NEEDS_EXPERIMENT",
    ))

    # 10. candidate -- complete, falsifiable, predictive, no sim/exp flag
    out.append(TheoryClaim(
        theory_name="Candidate Relativistic Correction Template",
        raw_claim="A structurally complete theory template with variables, equations, known-law checks, falsifiable conditions, and predictions.",
        category="candidate",
        variables=[
            Variable(name="E", meaning="energy", unit_name="energy"),
            Variable(name="m", meaning="mass", unit_name="mass"),
            Variable(name="c", meaning="speed of light", unit_name="velocity"),
        ],
        equations=[
            PhysicsClaim("tat7", "E = m*c^2", "energy",
                         [("mul", "mass"), ("mul", "velocity"), ("mul", "velocity")],
                         "DIMENSIONALLY_VALID", ""),
        ],
        known_law_checks=[
            KnownLawCheck("newtonian", "reduces to Newtonian kinetic energy at v << c", True),
            KnownLawCheck("conservation_energy", "energy conserved", True),
            KnownLawCheck("limit_zero", "E -> 0 as m -> 0", True),
        ],
        falsifiable_conditions=[
            "If rest energy does not equal m*c^2 in particle accelerator experiments, theory is wrong.",
        ],
        predictions=[
            Prediction(observable="rest energy",
                       condition="particle accelerator",
                       expected_value="E = m*c^2",
                       unit_name="energy",
                       required_measurement="experiment"),
        ],
        why="structurally complete; CANDIDATE_THEORY (not proven)",
        expected_final_status="CANDIDATE_THEORY",
    ))

    return out


THEORY_CLAIMS = _build_theory_claims()
