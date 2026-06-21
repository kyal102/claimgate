"""Counterexample set: plausible-looking FALSE identities.

The system must REJECT these, REFUSE to verify them, or produce a
counterexample. Accepting any of them is a hard failure of
Counterexample Safety.

Each entry is a false identity that is structurally tempting to an LLM
(looks like a familiar true identity with a sign/exponent/operand
twist). We never mark these as true. The verifier numerically checks
them and they fail.

Note: these are NOT "fake proofs" we ask the model to produce. They are
claims presented to the model that the model must reject.
"""
from __future__ import annotations

from typing import NamedTuple


class Counterexample(NamedTuple):
    id: str
    claim: str          # the false identity as presented
    why_plausible: str  # what familiar true identity it mimics
    check_kind: str     # "int_eq" | "rational_eq" | "mod_eq"
    check: dict         # parameters the verifier uses to disprove


COUNTEREXAMPLES = [
    Counterexample(
        id="ce1",
        claim="(a+b)^2 = a^2 + b^2",
        why_plausible="Mimics the binomial-square identity; drops the 2ab cross term.",
        check_kind="int_eq",
        check={"a": 3, "b": 4},
    ),
    Counterexample(
        id="ce2",
        claim="sqrt(a^2 + b^2) = a + b",
        why_plausible="Treats sqrt as linear; false for all nonzero a,b.",
        check_kind="int_eq",
        check={"a": 5, "b": 12},
    ),
    Counterexample(
        id="ce3",
        claim="a^(b+c) = a^b + a^c",
        why_plausible="Mimics a^(b*c)= (a^b)^c; confuses product-in-exponent with sum.",
        check_kind="int_eq",
        check={"a": 2, "b": 3, "c": 4},
    ),
    Counterexample(
        id="ce4",
        claim="1/a + 1/b = 1/(a+b)",
        why_plausible="Mimics parallel-resistance style; actually 1/a+1/b=(a+b)/(ab).",
        check_kind="rational_eq",
        check={"a": 2, "b": 3},
    ),
    Counterexample(
        id="ce5",
        claim="(a mod m) + (b mod m) = (a + b)         (without mod)",
        why_plausible="Drops the outer reduction; residue arithmetic requires final mod.",
        check_kind="mod_eq",
        check={"a": 1700, "b": 2800, "m": 997},
    ),
    Counterexample(
        id="ce6",
        claim="a! + b! = (a+b)!",
        why_plausible="Mimics a^b * a^c = a^(b+c); factorial has no such rule.",
        check_kind="int_eq",
        check={"a": 3, "b": 4},
    ),
    Counterexample(
        id="ce7",
        claim="gcd(a,b) * a = lcm(a,b)",
        why_plausible="Real identity is gcd*lcm = a*b; swaps a factor.",
        check_kind="int_eq",
        check={"a": 12, "b": 18},
    ),
    Counterexample(
        id="ce8",
        claim="(a/b)^2 = a^2 / b",
        why_plausible="Drops the square on the denominator.",
        check_kind="rational_eq",
        check={"a": 3, "b": 2},
    ),
]
