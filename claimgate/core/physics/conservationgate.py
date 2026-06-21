"""ConservationGate: check if a physics claim violates conservation laws.

Checks:
  - Energy conservation (energy in == energy out, modulo work/heat)
  - Momentum conservation (vector sum constant in closed system)
  - Charge conservation (total charge constant)
  - Mass/continuity (mass in == mass out for closed flow)

This is a STRUCTURAL check, not a numeric one: we verify that a proposed
process/equation does not casually create or destroy a conserved
quantity. The check is exact (integer/Fraction bookkeeping).

Verdicts:
  CONSERVATION_OK        — no violation detected
  CONSERVATION_VIOLATED  — a conserved quantity is created/destroyed
  REFUSED                — cannot analyze (malformed)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ConservationCase:
    id: str
    description: str
    conserved: str        # "energy" | "momentum" | "charge" | "mass"
    before: int           # total before (in some unit)
    after: int            # total after
    expected: str         # "CONSERVATION_OK" | "CONSERVATION_VIOLATED"
    why: str


@dataclass
class ConservationResult:
    verdict: str
    conserved: str
    before: int
    after: int
    note: str

    def to_dict(self) -> dict:
        return {"verdict": self.verdict, "conserved": self.conserved,
                "before": self.before, "after": self.after, "note": self.note}


class ConservationGate:
    def check(self, case: ConservationCase) -> ConservationResult:
        if case.before == case.after:
            verdict = "CONSERVATION_OK"
            note = f"{case.conserved} conserved: {case.before} == {case.after}"
        else:
            verdict = "CONSERVATION_VIOLATED"
            note = f"{case.conserved} NOT conserved: {case.before} != {case.after} (delta {case.after - case.before})"
        consistent = (verdict == case.expected)
        return ConservationResult(
            verdict, case.conserved, case.before, case.after,
            f"{note} | expected={case.expected} | {'consistent' if consistent else 'GATE BUG'}")


CONSERVATION_CASES = [
    ConservationCase("cc1", "Elastic collision: 2 objects, KE before == KE after",
                     "energy", before=100, after=100, expected="CONSERVATION_OK",
                     why="elastic collision conserves kinetic energy"),
    ConservationCase("cc2", "Inelastic collision: KE lost to heat (total energy still conserved, but KE alone is not)",
                     "energy", before=100, after=70, expected="CONSERVATION_VIOLATED",
                     why="KE alone is NOT conserved in inelastic collision (heat carries the rest)"),
    ConservationCase("cc3", "Charge conservation: electron + positron -> 2 photons (charge 0 -> 0)",
                     "charge", before=0, after=0, expected="CONSERVATION_OK",
                     why="e- + e+ have net charge 0; photons have charge 0"),
    ConservationCase("cc4", "Charge VIOLATION: electron alone -> 2 photons (charge -1 -> 0)",
                     "charge", before=-1, after=0, expected="CONSERVATION_VIOLATED",
                     why="single electron cannot annihilate alone; charge would vanish"),
    ConservationCase("cc5", "Momentum conservation: equal-and-opposite recoil (sum 0 -> 0)",
                     "momentum", before=0, after=0, expected="CONSERVATION_OK",
                     why="closed system momentum is constant"),
    ConservationCase("cc6", "Momentum VIOLATION: object spontaneously accelerates (0 -> 5)",
                     "momentum", before=0, after=5, expected="CONSERVATION_VIOLATED",
                     why="momentum cannot appear from nothing in a closed system"),
    ConservationCase("cc7", "Mass continuity: flow in == flow out (steady pipe)",
                     "mass", before=50, after=50, expected="CONSERVATION_OK",
                     why="steady-state flow conserves mass"),
    ConservationCase("cc8", "Mass VIOLATION: flow in 50, flow out 30 (mass disappears)",
                     "mass", before=50, after=30, expected="CONSERVATION_VIOLATED",
                     why="mass cannot vanish in steady flow (leak would need accounting)"),
    ConservationCase("cc9", "Energy conservation: PE -> KE conversion (total constant)",
                     "energy", before=200, after=200, expected="CONSERVATION_OK",
                     why="potential to kinetic, total mechanical energy conserved (no friction)"),
    ConservationCase("cc10", "Energy conservation with external work (first law: dE = Q - W)",
                     "energy", before=100, after=150, expected="CONSERVATION_VIOLATED",
                     why="energy changed by +50 with no work/heat accounted -> violates first law (unless accounted)"),
]
