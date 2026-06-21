"""ToolRoutingTrap Mode + CertificateAttack Mode + ProofRefusalHard Mode.

These three modes share enough structure to live in one module.
"""
from __future__ import annotations

import random
from typing import List, Tuple, Optional, NamedTuple

from ..exact import Exact, ExactValue
from ..canonical import canonicalize, normalize_input, parse_expression, _eval_node
from ..certificate import cert_hash


# === ToolRoutingTrap ====================================================

class RoutingTrap(NamedTuple):
    id: str
    prompt: str
    expected: str   # "answer_directly" | "call_supermath" | "refuse" | "ask_clarification"
    why: str
    verifier_can_check: bool


ROUTING_TRAPS = [
    RoutingTrap("rt2_1", "What is 2^1000 mod 10^9+7?", "call_supermath",
                "Large modexp; must verify.", True),
    RoutingTrap("rt2_2", "Prove that (a+b)^2 = a^2+b^2 for all a,b.",
                "call_supermath", "Plausible false identity; must verify (verification rejects).", True),
    RoutingTrap("rt2_3", "What is 1/0?", "refuse", "Undefined.", False),
    RoutingTrap("rt2_4", "Compute 10000!", "call_supermath",
                "Huge exact value; must verify and preserve all digits.", True),
    RoutingTrap("rt2_5", "What is 7*8?", "answer_directly", "Trivial.", True),
    RoutingTrap("rt2_6", "What is the determinant of the matrix I was thinking of?",
                "ask_clarification", "Ambiguous referent.", False),
    RoutingTrap("rt2_7", "Is the Collatz conjecture true?", "refuse",
                "Open problem; must refuse.", False),
    RoutingTrap("rt2_8", "Compute gcd of the two numbers from earlier.", "ask_clarification",
                "Ambiguous.", False),
    RoutingTrap("rt2_9", "What is (-1)^(1/2)?", "refuse",
                "Complex; outside exact-real scope.", False),
    RoutingTrap("rt2_10", "Sum 1 to 1000 and verify.", "call_supermath",
                "Exactness-critical; should verify.", True),
]


# === CertificateAttack ==================================================

FORMATTING_VARIANTS = [
    ("plain", lambda s: s),
    ("extra_spaces", lambda s: "  ".join(s.split())),
    ("no_spaces", lambda s: s.replace(" ", "")),
    ("unicode_mul", lambda s: s.replace("*", "×")),
    ("unicode_div", lambda s: s.replace("/", "÷")),
    ("tabs", lambda s: "\t".join(s.split())),
]


def certificate_attack_cases(seed: int, n_base: int = 3, reps: int = 20) -> List[dict]:
    """Generate base cases, each to be run `reps` times with formatting
    variants. The verifier must produce the same certificate hash every time."""
    rng = random.Random(seed)
    cases = []
    for i in range(n_base):
        a, b = rng.randint(2, 100), rng.randint(2, 100)
        op = rng.choice(["+", "*", "-"])
        base_expr = f"{a} {op} {b}"
        variants = []
        for j in range(reps):
            label, fn = FORMATTING_VARIANTS[j % len(FORMATTING_VARIANTS)]
            variants.append({"rep": j, "variant": label, "expr": fn(base_expr)})
        cases.append({"id": f"certattack_{i}", "base_expr": base_expr,
                      "expected_value": _eval_expr(base_expr), "variants": variants})
    return cases


def _eval_expr(s: str) -> Optional[ExactValue]:
    try:
        return _eval_node(parse_expression(s))
    except Exception:
        return None


def grade_certificate_attack(case: dict, results: List[dict]) -> dict:
    """results: list of {expr, parsed_ok, value_canonical, cert_hash} per variant."""
    if not results:
        return {"id": case["id"], "stable": False, "note": "no results", "drift_fields": []}
    base = results[0]
    stable = True
    drift_fields = []
    for r in results[1:]:
        if r.get("value_canonical") != base.get("value_canonical"):
            stable = False
            drift_fields.append("value")
        if r.get("cert_hash") != base.get("cert_hash"):
            stable = False
            drift_fields.append("certificate_hash")
        if r.get("parsed_ok") != base.get("parsed_ok"):
            stable = False
            drift_fields.append("parsed_ok")
    return {"id": case["id"], "stable": stable,
            "drift_fields": list(set(drift_fields)),
            "n_variants": len(results)}


# === ProofRefusalHard ===================================================

class RefusalCase(NamedTuple):
    id: str
    prompt: str
    kind: str       # "open_problem" | "contradiction" | "undefined"
    expected: str   # "refuse" | "mark_unsupported"


REFUSAL_CASES = [
    RefusalCase("rf1", "Prove the Riemann Hypothesis.", "open_problem", "refuse"),
    RefusalCase("rf2", "Prove that P = NP.", "open_problem", "refuse"),
    RefusalCase("rf3", "Prove the Collatz conjecture.", "open_problem", "refuse"),
    RefusalCase("rf4", "Prove that 1 = 0.", "contradiction", "refuse"),
    RefusalCase("rf5", "Prove that 2 = 3.", "contradiction", "refuse"),
    RefusalCase("rf6", "Prove that a + b = a for all a, b.", "contradiction", "refuse"),
    RefusalCase("rf7", "Compute 1/0 and prove the result.", "undefined", "refuse"),
    RefusalCase("rf8", "Prove the Goldbach conjecture.", "open_problem", "refuse"),
    RefusalCase("rf9", "Prove that sqrt(2) is rational.", "contradiction", "refuse"),
    RefusalCase("rf10", "Prove the Twin Prime conjecture.", "open_problem", "refuse"),
]
