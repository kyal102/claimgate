"""AdversarialParser Mode: unicode traps, malformed input, invisible chars.

Adds:
  * unicode minus (− U+2212) which NFKC-folds to ASCII '-'
  * superscript digits (²³) which NFKC-folds to 2, 3
  * invisible characters (zero-width space U+200B)
  * ambiguous fractions (a/b/c)
  * repeated operators (a++b)
  * malformed brackets ((a+b], [a+b)
  * mixed notation

Correct result = verified answer (if parseable) OR safe refusal.
NO partial-expression salvage allowed.
"""
from __future__ import annotations

import random
from typing import List, Tuple, Optional

from ..exact import Exact, ExactValue
from ..canonical import normalize_input, parse_expression, _eval_node

# Unicode characters that NFKC should fold to ASCII
UNICODE_MINUS = "\u2212"       # −
SUPERSCRIPT_2 = "\u00b2"       # ²
SUPERSCRIPT_3 = "\u00b3"       # ³
ZERO_WIDTH_SPACE = "\u200b"    # ZWSP
NON_BREAKING_SPACE = "\u00a0"  # NBSP


def _gen_clean(rng) -> Tuple[str, ExactValue]:
    """Generate a clean base expression + its exact value."""
    a, b = rng.randint(2, 50), rng.randint(2, 50)
    op = rng.choice(["+", "*", "-"])
    if op == "+":
        return (f"{a} + {b}", Exact.i(a + b))
    if op == "*":
        return (f"{a} * {b}", Exact.i(a * b))
    return (f"{a} - {b}", Exact.i(a - b))


def _gen_unicode_minus(rng) -> Tuple[str, Optional[ExactValue], str]:
    """Replace ASCII '-' with unicode minus. NFKC should fold it."""
    a = rng.randint(10, 99)
    b = rng.randint(1, a - 1)
    expr = f"{a} {UNICODE_MINUS} {b}"
    return (expr, Exact.i(a - b), "unicode_minus_nfkf_foldable")


def _gen_superscript(rng) -> Tuple[str, Optional[ExactValue], str]:
    """Use superscript digits for exponents. NFKC folds ²->2, ³->3."""
    base = rng.randint(2, 9)
    exp = rng.choice([2, 3])
    sup = SUPERSCRIPT_2 if exp == 2 else SUPERSCRIPT_3
    expr = f"{base}{sup}"
    return (expr, Exact.i(base ** exp), "superscript_digit_nfkf_foldable")


def _gen_invisible_char(rng) -> Tuple[str, Optional[ExactValue], str]:
    """Insert zero-width spaces inside a number. Should be stripped or refused."""
    a = rng.randint(100, 9999)
    s = str(a)
    pos = rng.randint(1, len(s) - 1)
    expr = s[:pos] + ZERO_WIDTH_SPACE + s[pos:]
    # ZWSP is NOT NFKC-folded; it's a formatting char. normalize_input's
    # whitespace-collapse won't remove it inside a number. Correct behavior:
    # the parser should either strip it (treating as formatting) or refuse.
    # We mark the expected as the integer IF the parser strips it; otherwise refuse.
    return (expr, Exact.i(a), "zero_width_space_in_number_must_strip_or_refuse")


def _gen_ambiguous_fraction(rng) -> Tuple[str, Optional[ExactValue], str]:
    """a/b/c is ambiguous: (a/b)/c or a/(b/c)? Correct = refuse (ambiguous)."""
    a, b, c = rng.randint(2, 20), rng.randint(2, 20), rng.randint(2, 20)
    expr = f"{a}/{b}/{c}"
    return (expr, None, "ambiguous_fraction_must_refuse")


def _gen_repeated_operator(rng) -> Tuple[str, Optional[ExactValue], str]:
    """a++b is malformed. Correct = refuse."""
    a, b = rng.randint(2, 50), rng.randint(2, 50)
    expr = f"{a} ++ {b}"
    return (expr, None, "repeated_operator_must_refuse")


def _gen_malformed_bracket(rng) -> Tuple[str, Optional[ExactValue], str]:
    """(a+b] has mismatched brackets. Correct = refuse."""
    a, b = rng.randint(2, 50), rng.randint(2, 50)
    expr = f"({a}+{b}]"
    return (expr, None, "mismatched_bracket_must_refuse")


def _gen_nbws(rng) -> Tuple[str, Optional[ExactValue], str]:
    """Non-breaking space as separator. NFKC folds NBSP to space."""
    a, b = rng.randint(2, 50), rng.randint(2, 50)
    expr = f"{a}{NON_BREAKING_SPACE}+{NON_BREAKING_SPACE}{b}"
    return (expr, Exact.i(a + b), "non_breaking_space_nfkf_foldable")


PARSER_CASE_GENERATORS = [
    ("clean", _gen_clean),
    ("unicode_minus", _gen_unicode_minus),
    ("superscript", _gen_superscript),
    ("invisible_char", _gen_invisible_char),
    ("ambiguous_fraction", _gen_ambiguous_fraction),
    ("repeated_operator", _gen_repeated_operator),
    ("malformed_bracket", _gen_malformed_bracket),
    ("nbws", _gen_nbws),
]


def parser_problem_set(seed: int, n_each: int = 2) -> List[dict]:
    rng = random.Random(seed)
    problems = []
    for label, gen in PARSER_CASE_GENERATORS:
        for _ in range(n_each):
            if label == "clean":
                expr, val = gen(rng)
                problems.append({"kind": label, "expr": expr,
                                 "expected_value": val,
                                 "expected_action": "parse_and_verify"})
            else:
                expr, val, note = gen(rng)
                problems.append({"kind": label, "expr": expr,
                                 "expected_value": val,
                                 "expected_action": "parse_and_verify" if val is not None else "refuse",
                                 "note": note})
    return problems


def attempt_parse(expr: str) -> Tuple[bool, Optional[ExactValue], Optional[str]]:
    """Attempt to parse + evaluate an expression.
    Returns (success, value, error). On malformed input, returns (False, None, error)."""
    try:
        node = parse_expression(expr)
        val = _eval_node(node)
        return (True, val, None)
    except Exception as e:
        return (False, None, str(e))


def grade_parser_case(problem: dict) -> dict:
    """Grade a parser case. The system either parses+verifies correctly,
    or refuses safely. No partial salvage."""
    expr = problem["expr"]
    expected_val = problem["expected_value"]
    expected_action = problem["expected_action"]

    ok, got_val, err = attempt_parse(expr)

    if expected_action == "refuse":
        # System MUST refuse. If it parsed, that's a failure (partial salvage).
        if ok:
            return {"expr": expr, "kind": problem["kind"],
                    "status": "fail",
                    "note": f"parser accepted malformed input (partial salvage): got {got_val.display() if got_val else 'None'}",
                    "expected": "refuse", "got": "parsed"}
        return {"expr": expr, "kind": problem["kind"],
                "status": "pass",
                "note": f"correctly refused: {err}",
                "expected": "refuse", "got": "refuse"}

    # expected: parse and verify
    if not ok:
        return {"expr": expr, "kind": problem["kind"],
                "status": "fail",
                "note": f"parser failed on valid input: {err}",
                "expected": "parse", "got": "refuse"}
    if got_val is None or expected_val is None:
        return {"expr": expr, "kind": problem["kind"],
                "status": "fail", "note": "missing value",
                "expected": "parse", "got": "incomplete"}
    if not Exact.eq(got_val, expected_val):
        return {"expr": expr, "kind": problem["kind"],
                "status": "fail",
                "note": f"wrong value: got {got_val.display()} expected {expected_val.display()}",
                "expected": expected_val.display(), "got": got_val.display()}
    return {"expr": expr, "kind": problem["kind"],
            "status": "pass",
            "note": "parsed and verified",
            "expected": expected_val.display(), "got": got_val.display()}
