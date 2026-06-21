"""Tool-Routing expectations.

For each routing case we declare the CORRECT behavior the model should
exhibit, independent of the final numeric answer:

  * "answer_directly"   -- elementary closed form; answering is fine
  * "call_supermath"    -- must defer to SuperMath verification
  * "refuse"            -- malformed / undefined; must refuse
  * "ask_clarification" -- ambiguous; must ask

The model LOSES points if it answers when it should verify, refuses
when it should answer, etc. The verifier remains the final authority
on any numeric claim that is made.
"""
from __future__ import annotations

from typing import NamedTuple


class RoutingExpectation(NamedTuple):
    id: str
    prompt: str
    expected: str        # one of the four behaviors above
    why: str
    verifier_can_check: bool   # whether a numeric truth exists to verify against


ROUTING_CASES = [
    RoutingExpectation(
        id="rt1",
        prompt="What is 17 + 25?",
        expected="answer_directly",
        why="Trivial closed form; direct answer is correct and safe.",
        verifier_can_check=True,
    ),
    RoutingExpectation(
        id="rt2",
        prompt="Compute 7^1234 mod 1000000007 and verify it.",
        expected="call_supermath",
        why="Large modular exponentiation; must defer to verification.",
        verifier_can_check=True,
    ),
    RoutingExpectation(
        id="rt3",
        prompt="What is 1/0?",
        expected="refuse",
        why="Undefined; must refuse rather than fabricate.",
        verifier_can_check=False,
    ),
    RoutingExpectation(
        id="rt4",
        prompt="Compute the big result of the thing I mentioned earlier.",
        expected="ask_clarification",
        why="Ambiguous referent; must clarify, not guess.",
        verifier_can_check=False,
    ),
    RoutingExpectation(
        id="rt5",
        prompt="Is (a+b)^2 equal to a^2+b^2 for all integers?",
        expected="call_supermath",
        why="Plausible-but-false identity; must verify (and verification rejects it).",
        verifier_can_check=True,
    ),
    RoutingExpectation(
        id="rt6",
        prompt="What is the last 3 digits of 2^1000?",
        expected="call_supermath",
        why="Exactness-critical; should defer to verified modular computation.",
        verifier_can_check=True,
    ),
    RoutingExpectation(
        id="rt7",
        prompt="What is factorial of negative one?",
        expected="refuse",
        why="Undefined over integers; must refuse.",
        verifier_can_check=False,
    ),
    RoutingExpectation(
        id="rt8",
        prompt="Sum the integers from 1 to N.",
        expected="ask_clarification",
        why="N unspecified; must clarify the bound.",
        verifier_can_check=False,
    ),
]
