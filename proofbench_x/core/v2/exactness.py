"""ExactnessTorture Mode: 10k+ digit operations, determinants, neg rationals.

Includes:
  * 10k+ digit integer multiplication
  * large modular exponentiation
  * fraction chains (product of 100 fractions)
  * large exact integer determinants (2x2, 3x3, 4x4 via Bareiss)
  * negative rational simplification

No scientific-summary-only output counts as exact unless the FULL exact
value is preserved in the result/certificate.
"""
from __future__ import annotations

import random
from fractions import Fraction
from typing import List, Tuple

from ..exact import Exact, ExactValue, exact_pow, exact_mod_pow


def _bareiss_determinant(matrix: List[List[int]]) -> int:
    """Fraction-free Bareiss algorithm for exact integer determinant.
    O(n^3) with integer-only arithmetic. Returns exact int determinant."""
    n = len(matrix)
    M = [row[:] for row in matrix]
    sign = 1
    prev = 1
    for k in range(n - 1):
        if M[k][k] == 0:
            # find a row to swap
            swap = -1
            for i in range(k + 1, n):
                if M[i][k] != 0:
                    swap = i
                    break
            if swap == -1:
                return 0  # singular
            M[k], M[swap] = M[swap], M[k]
            sign = -sign
        for i in range(k + 1, n):
            for j in range(k + 1, n):
                M[i][j] = (M[i][j] * M[k][k] - M[i][k] * M[k][j]) // prev
            M[i][k] = 0
        prev = M[k][k]
    return sign * M[n - 1][n - 1]


def gen_big_multiplication(rng) -> dict:
    """Product of two 5k+ digit numbers -> 10k+ digit result."""
    a = rng.randint(10**5000, 10**5001 - 1)
    b = rng.randint(10**5000, 10**5001 - 1)
    return {"subkind": "bigint_mul_10k_plus",
            "value": a * b,
            "digits": len(str(abs(a * b)))}


def gen_big_modexp(rng) -> dict:
    """Large modular exponentiation."""
    base = rng.randint(2, 10**6)
    exp = rng.randint(10**5, 10**6)
    mod = 10**9 + 7
    return {"subkind": "large_modexp",
            "value": exact_mod_pow(base, exp, mod),
            "digits": len(str(exact_mod_pow(base, exp, mod)))}


def gen_fraction_chain(rng) -> dict:
    """Product of 100 fractions -- exact rational."""
    acc = Fraction(1)
    for _ in range(100):
        acc *= Fraction(rng.randint(1, 99), rng.randint(1, 99))
    return {"subkind": "fraction_chain_100",
            "value": acc,
            "num_digits": len(str(abs(acc.numerator))),
            "den_digits": len(str(abs(acc.denominator)))}


def gen_determinant(rng, size=3) -> dict:
    """Exact integer determinant via Bareiss."""
    n = size
    M = [[rng.randint(-50, 50) for _ in range(n)] for _ in range(n)]
    det = _bareiss_determinant(M)
    return {"subkind": f"det_{n}x{n}_bareiss",
            "matrix": M,
            "value": det,
            "digits": len(str(abs(det)))}


def gen_negative_rational_simplification(rng) -> dict:
    """(-a)/b simplified to -a/b and a/(-b) -> -a/b; verify canonical form."""
    a = rng.randint(1, 1000)
    b = rng.randint(1, 1000)
    # (-a)/b == a/(-b) == -(a/b) ; all must canonicalize to the same
    from fractions import Fraction
    r = Fraction(-a, b)
    return {"subkind": "negative_rational_simplification",
            "a": a, "b": b,
            "value": r,
            "canonical": f"{r.numerator}/{r.denominator}"}


def exactness_torture_set(seed: int, n_big=3, n_mod=4, n_frac=3,
                          n_det3=3, n_det4=2, n_neg=4) -> List[dict]:
    rng = random.Random(seed)
    cases = []
    for _ in range(n_big):
        cases.append(gen_big_multiplication(rng))
    for _ in range(n_mod):
        cases.append(gen_big_modexp(rng))
    for _ in range(n_frac):
        cases.append(gen_fraction_chain(rng))
    for _ in range(n_det3):
        cases.append(gen_determinant(rng, size=3))
    for _ in range(n_det4):
        cases.append(gen_determinant(rng, size=4))
    for _ in range(n_neg):
        cases.append(gen_negative_rational_simplification(rng))
    return cases
