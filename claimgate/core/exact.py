"""Exact arithmetic primitives.

The verifier computes truth using ONLY these primitives. There is no
answer-lookup table. Correctness is decided by re-deriving the answer
from the problem with exact (never floating-point) arithmetic.

Supported value kinds:
  * "int"     -- arbitrary-precision Python int
  * "rational"-- fractions.Fraction (exact)
  * "mod"     -- modular residue as (value, modulus), value in [0, modulus)

Floating point is NEVER used for correctness decisions. It may appear
only inside a model's (untrusted) output, and even then the verifier
re-derives exactly before comparing.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from fractions import Fraction
from typing import Union, Tuple

IntLike = Union[int, str]


@dataclass(frozen=True)
class ExactValue:
    """A tagged exact value."""
    kind: str          # "int" | "rational" | "mod"
    int_val: int = 0
    rat_val: Fraction = Fraction(0)
    mod_val: Tuple[int, int] = (0, 1)   # (residue, modulus)

    def display(self) -> str:
        if self.kind == "int":
            return str(self.int_val)
        if self.kind == "rational":
            r = self.rat_val
            return f"{r.numerator}/{r.denominator}" if r.denominator != 1 else str(r.numerator)
        if self.kind == "mod":
            v, m = self.mod_val
            return f"{v} mod {m}"
        raise ValueError(f"unknown kind {self.kind}")

    def canonical_string(self) -> str:
        """Stable canonical serialization for certificate hashing."""
        if self.kind == "int":
            return f"int:{self.int_val}"
        if self.kind == "rational":
            r = self.rat_val
            return f"rational:{r.numerator}/{r.denominator}"
        if self.kind == "mod":
            v, m = self.mod_val
            return f"mod:{v}/{m}"
        raise ValueError(f"unknown kind {self.kind}")


class Exact:
    """Namespace of exact-arithmetic constructors & helpers."""

    @staticmethod
    def i(x: IntLike) -> ExactValue:
        if isinstance(x, int):
            return ExactValue(kind="int", int_val=x)
        return ExactValue(kind="int", int_val=parse_int_strict(x))

    @staticmethod
    def frac(num: IntLike, den: IntLike = 1) -> ExactValue:
        n = num if isinstance(num, int) else parse_int_strict(num)
        d = den if isinstance(den, int) else parse_int_strict(den)
        if d == 0:
            raise ZeroDivisionError("fraction with zero denominator")
        return ExactValue(kind="rational", rat_val=Fraction(n, d))

    @staticmethod
    def mod(value: IntLike, modulus: int) -> ExactValue:
        if modulus <= 0:
            raise ValueError("modulus must be positive")
        v = value if isinstance(value, int) else parse_int_strict(value)
        return ExactValue(kind="mod", mod_val=(v % modulus, modulus))

    @staticmethod
    def add(a: ExactValue, b: ExactValue) -> ExactValue:
        a, b = _promote(a, b)
        if a.kind == "int":
            return ExactValue(kind="int", int_val=a.int_val + b.int_val)
        if a.kind == "rational":
            return ExactValue(kind="rational", rat_val=a.rat_val + b.rat_val)
        if a.kind == "mod":
            (av, am), (bv, bm) = a.mod_val, b.mod_val
            if am != bm:
                raise ValueError("mod mismatch in add")
            return ExactValue(kind="mod", mod_val=((av + bv) % am, am))
        raise ValueError(a.kind)

    @staticmethod
    def mul(a: ExactValue, b: ExactValue) -> ExactValue:
        a, b = _promote(a, b)
        if a.kind == "int":
            return ExactValue(kind="int", int_val=a.int_val * b.int_val)
        if a.kind == "rational":
            return ExactValue(kind="rational", rat_val=a.rat_val * b.rat_val)
        if a.kind == "mod":
            (av, am), (bv, bm) = a.mod_val, b.mod_val
            if am != bm:
                raise ValueError("mod mismatch in mul")
            return ExactValue(kind="mod", mod_val=((av * bv) % am, am))
        raise ValueError(a.kind)

    @staticmethod
    def eq(a: ExactValue, b: ExactValue) -> bool:
        a, b = _promote(a, b)
        if a.kind == "int":
            return a.int_val == b.int_val
        if a.kind == "rational":
            return a.rat_val == b.rat_val
        if a.kind == "mod":
            return a.mod_val == b.mod_val
        return False


def _promote(a: ExactValue, b: ExactValue) -> Tuple[ExactValue, ExactValue]:
    """Promote both values to a common kind: mod > rational > int.

    Two mod values are only compatible if same modulus; otherwise promote to int
    (the residue interpreted as an integer) -- this only happens for cross-modulus
    comparisons, which the benchmark does not perform for correctness.
    """
    if a.kind == b.kind:
        return a, b
    kinds = {a.kind, b.kind}
    # mod vs mod with different moduli -> treat as int residues (defensive only)
    if kinds == {"int", "rational"}:
        if a.kind == "int":
            a = ExactValue(kind="rational", rat_val=Fraction(a.int_val))
        else:
            b = ExactValue(kind="rational", rat_val=Fraction(b.int_val))
        return a, b
    if kinds == {"int", "mod"}:
        if a.kind == "int":
            (bv, bm) = b.mod_val
            # cannot meaningfully compare bare int to a residue without modulus context;
            # promote both to rational for a well-defined comparison
            a = ExactValue(kind="rational", rat_val=Fraction(a.int_val))
            b = ExactValue(kind="rational", rat_val=Fraction(bv))
        else:
            (av, am) = a.mod_val
            a = ExactValue(kind="rational", rat_val=Fraction(av))
            b = ExactValue(kind="rational", rat_val=Fraction(b.int_val))
        return a, b
    if kinds == {"rational", "mod"}:
        if a.kind == "rational":
            (bv, bm) = b.mod_val
            b = ExactValue(kind="rational", rat_val=Fraction(bv))
        else:
            (av, am) = a.mod_val
            a = ExactValue(kind="rational", rat_val=Fraction(av))
        return a, b
    # all three differ
    raise TypeError(f"cannot promote {a.kind} and {b.kind}")


_INT_RE = re.compile(r"^[+-]?\d+$")


def parse_int_strict(s: str) -> int:
    """Parse a decimal integer strictly. Rejects floats, whitespace tricks,
    unicode digits, thousands separators -- the canonical input must be plain."""
    if not isinstance(s, str):
        raise TypeError(f"expected str, got {type(s).__name__}")
    if not _INT_RE.match(s):
        raise ValueError(f"not a strict decimal integer: {s!r}")
    return int(s)


def big_int_preserve(n: int) -> Tuple[int, int]:
    """Return (digit_count, exact_value) to verify exact-preservation
    of huge integers (used by Exactness Stress, incl. 10k+ digit tests)."""
    return (len(str(abs(n))) - (1 if n < 0 else 0) if n != 0 else 1, n)


def exact_pow(base: int, exp: int) -> int:
    if exp < 0:
        raise ValueError("negative exponent on integer base")
    return base ** exp


def exact_mod_pow(base: int, exp: int, mod: int) -> int:
    if mod <= 0:
        raise ValueError("modulus must be positive")
    if exp < 0:
        # modular inverse path -- only valid when gcd(base, mod) == 1
        return pow(base, exp, mod)
    return pow(base, exp, mod)


def exact_gcd(a: int, b: int) -> int:
    from math import gcd
    return gcd(abs(a), abs(b))


def exact_lcm(a: int, b: int) -> int:
    if a == 0 or b == 0:
        return 0
    return abs(a * b) // exact_gcd(a, b)


def factorial(n: int) -> int:
    if n < 0:
        raise ValueError("factorial of negative")
    r = 1
    for k in range(2, n + 1):
        r *= k
    return r
