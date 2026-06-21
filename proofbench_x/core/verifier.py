"""The Verifier: final authority on correctness.

Design invariants (golden rules):
  * The verifier NEVER looks up answers from a table. It re-derives the
    exact answer from the problem using the solvers in `families.py`,
    `metamorphic.py`, and direct exact arithmetic.
  * Model outputs NEVER decide correctness. A model output is compared
    against the verifier-derived truth; the model is graded, never
    trusted.
  * No proof is faked. A Certificate is issued only when the verifier
    actually computed the answer.
  * Failures are never hidden. Every case yields a result record with
    pass/fail/refused/unverified explicitly.
  * No open problem is ever claimed solved. Only closed elementary math
    is used.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple

from .exact import Exact, ExactValue, exact_mod_pow, exact_pow, factorial, exact_gcd, exact_lcm, parse_int_strict
from .canonical import canonicalize, normalize_input, parse_expression, _eval_node
from .certificate import Certificate, issue_certificate, refused_certificate, cert_hash
from .families import Family, FAMILY_REGISTRY
from .counterexamples import COUNTEREXAMPLES, Counterexample


@dataclass
class VerificationResult:
    problem_id: str
    family: str
    status: str               # "pass" | "fail" | "refused" | "unverified"
    expected: Optional[str]   # canonical string of ground truth
    got: Optional[str]        # canonical string of model/evaluated output
    certificate: Optional[Certificate]
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "problem_id": self.problem_id,
            "family": self.family,
            "status": self.status,
            "expected": self.expected,
            "got": self.got,
            "certificate": self.certificate.to_dict() if self.certificate else None,
            "note": self.note,
        }


class Verifier:
    """Stateless verifier. All methods are pure functions of their inputs."""

    # --- family-level verification -----------------------------------------

    def verify_family_case(self, family: Family, problem: dict, problem_id: str) -> Tuple[ExactValue, Certificate]:
        """Re-derive the exact answer for a family problem and issue a cert."""
        try:
            truth = family.verify(problem)
        except ZeroDivisionError as e:
            raise
        canon_prob = canonicalize(family.render(problem))
        lane = family.lane_id(problem)
        cert = issue_certificate(
            problem_id=problem_id, family=family.id,
            problem_canonical=canon_prob, result=truth, lane_id=lane,
            note="family-solver",
        )
        return truth, cert

    def grade_family_case(self, family: Family, problem: dict,
                          model_answer_str: str, problem_id: str) -> VerificationResult:
        """Grade a model's answer against the re-derived truth."""
        canon_prob = canonicalize(family.render(problem))
        lane = family.lane_id(problem)
        try:
            truth, cert = self.verify_family_case(family, problem, problem_id)
        except ZeroDivisionError:
            cert = refused_certificate(problem_id, family.id, canon_prob, lane, "division-by-zero")
            return VerificationResult(problem_id, family.id, "refused",
                                      None, None, cert, "division by zero")
        expected = truth.canonical_string()
        got = self._parse_model_answer(model_answer_str, truth)
        if got is None:
            return VerificationResult(problem_id, family.id, "fail",
                                      expected, None, cert,
                                      f"model answer not parseable: {model_answer_str!r}")
        status = "pass" if got == expected else "fail"
        note = "" if status == "pass" else "mismatch"
        return VerificationResult(problem_id, family.id, status, expected, got, cert, note)

    # --- metamorphic verification -----------------------------------------

    def verify_metamorphic_pair(self, expr_a: str, expr_b: str) -> Tuple[bool, str, str, Optional[ExactValue], Optional[ExactValue]]:
        """Two expressions are metamorphically equivalent iff their canonical
        strings match AND their exact values match."""
        try:
            ca = canonicalize(expr_a)
            cb = canonicalize(expr_b)
        except Exception:
            return False, "", "", None, None
        if ca != cb:
            # still check value equality (some equivalences our canonicalizer
            # doesn't fully fold, e.g. commuted sum canonicalizes the same)
            try:
                va = _eval_node(parse_expression(expr_a))
                vb = _eval_node(parse_expression(expr_b))
                return Exact.eq(va, vb), ca, cb, va, vb
            except Exception:
                return False, ca, cb, None, None
        va = _eval_node(parse_expression(expr_a))
        vb = _eval_node(parse_expression(expr_b))
        return Exact.eq(va, vb), ca, cb, va, vb

    # --- counterexample verification --------------------------------------

    def check_counterexample(self, ce: Counterexample) -> Tuple[bool, str]:
        """Numerically disprove a claimed identity. Returns (is_false, detail).
        is_false==True means the identity is indeed false (good: model must reject).
        is_false==False would mean our counterexample is actually true (a bug)."""
        k = ce.check_kind
        c = ce.check
        if k == "int_eq":
            if ce.id == "ce1":
                a, b = c["a"], c["b"]
                lhs = (a + b) ** 2
                rhs = a * a + b * b
                return (lhs != rhs), f"lhs={lhs} rhs={rhs}"
            if ce.id == "ce2":
                a, b = c["a"], c["b"]
                import math
                lhs = math.isqrt(a * a + b * b)
                rhs = a + b
                # compare exact squares to avoid float
                return (lhs * lhs != (a + b) * (a + b)), f"sqrt(a^2+b^2)={lhs} vs a+b={rhs}"
            if ce.id == "ce3":
                a, b, ccc = c["a"], c["b"], c["c"]
                lhs = exact_pow(a, b + ccc)
                rhs = exact_pow(a, b) + exact_pow(a, ccc)
                return (lhs != rhs), f"lhs={lhs} rhs={rhs}"
            if ce.id == "ce6":
                a, b = c["a"], c["b"]
                lhs = factorial(a) + factorial(b)
                rhs = factorial(a + b)
                return (lhs != rhs), f"lhs={lhs} rhs={rhs}"
            if ce.id == "ce7":
                a, b = c["a"], c["b"]
                lhs = exact_gcd(a, b) * a
                rhs = exact_lcm(a, b)
                return (lhs != rhs), f"lhs={lhs} rhs={rhs}"
        if k == "rational_eq":
            if ce.id == "ce4":
                a, b = c["a"], c["b"]
                lhs = Exact.frac(a + b, a * b)
                rhs = Exact.frac(1, a + b)
                return (not Exact.eq(lhs, rhs)), f"lhs={lhs.display()} rhs={rhs.display()}"
            if ce.id == "ce8":
                a, b = c["a"], c["b"]
                lhs = Exact.frac(a * a, b * b)
                rhs = Exact.frac(a * a, b)
                return (not Exact.eq(lhs, rhs)), f"lhs={lhs.display()} rhs={rhs.display()}"
        if k == "mod_eq":
            if ce.id == "ce5":
                a, b, m = c["a"], c["b"], c["m"]
                lhs = (a % m) + (b % m)
                rhs = a + b
                return (lhs != rhs), f"lhs={lhs} rhs={rhs}"
        # generic fallback: if we can't disprove, refuse to claim false
        return False, "no-disproof-available (verifier refused to claim)"

    def grade_counterexample(self, ce: Counterexample, model_action: str) -> VerificationResult:
        """model_action in {reject, refuse, counterexample_provided, accept}."""
        is_false, detail = self.check_counterexample(ce)
        canon = f"ce:{ce.id}"
        if not is_false:
            # Our counterexample was actually TRUE -- a verifier bug. Never hide.
            return VerificationResult(ce.id, "counterexample", "unverified",
                                      None, None, None,
                                      f"VERIFIER BUG: counterexample {ce.id} is actually true: {detail}")
        if model_action == "accept":
            cert = issue_certificate(ce.id, "counterexample", canon,
                                     Exact.i(0), "ce", note="model-accepted-false-identity")
            return VerificationResult(ce.id, "counterexample", "fail",
                                      "reject/refuse/counterexample", "accept", cert,
                                      f"model accepted a false identity ({ce.claim}); {detail}")
        # reject / refuse / counterexample_provided are all acceptable
        cert = issue_certificate(ce.id, "counterexample", canon,
                                 Exact.i(1), "ce", note=f"model-{model_action}")
        return VerificationResult(ce.id, "counterexample", "pass",
                                  "reject/refuse/counterexample", model_action, cert,
                                  f"model correctly rejected; {detail}")

    # --- exactness preservation -------------------------------------------

    def check_exact_preservation(self, value: int, model_value_str: str) -> VerificationResult:
        """Verify that a huge integer is preserved EXACTLY (every digit).
        A scientific-summary-only answer (e.g. '1.23e+4567') does NOT count."""
        pid = f"exact:{len(str(abs(value)))}"
        try:
            got = parse_int_strict(model_value_str.strip())
        except Exception:
            return VerificationResult(pid, "exactness", "fail",
                                      str(value), None, None,
                                      f"not a strict decimal integer: {model_value_str!r}")
        if got != value:
            return VerificationResult(pid, "exactness", "fail",
                                      str(value), str(got), None,
                                      "exact value not preserved")
        cert = issue_certificate(pid, "exactness", canonicalize(str(value)),
                                 Exact.i(value), "exact", note="full-digit-preservation")
        return VerificationResult(pid, "exactness", "pass", str(value), str(got), cert,
                                  "exact value preserved in full")

    # --- helpers ----------------------------------------------------------

    def _parse_model_answer(self, s: str, reference: ExactValue) -> Optional[str]:
        """Best-effort parse a model's free-form answer to the canonical
        string of an ExactValue of the same kind as `reference`."""
        if s is None:
            return None
        s2 = normalize_input(str(s))
        try:
            if reference.kind == "mod":
                # accept "v mod m" or bare "v"
                if " mod " in s2:
                    parts = s2.split(" mod ")
                    if len(parts) == 2:
                        v = parse_int_strict(parts[0])
                        return Exact.mod(v, reference.mod_val[1]).canonical_string()
                v = parse_int_strict(s2)
                return Exact.mod(v, reference.mod_val[1]).canonical_string()
            if reference.kind == "rational":
                if "/" in s2:
                    n, d = s2.split("/")
                    return Exact.frac(parse_int_strict(n), parse_int_strict(d)).canonical_string()
                v = parse_int_strict(s2)
                return Exact.frac(v, 1).canonical_string()
            # int
            v = parse_int_strict(s2)
            return Exact.i(v).canonical_string()
        except Exception:
            return None


# module-level singleton for convenience
_verifier = Verifier()


def solve(family: Family, problem: dict, problem_id: str):
    """Convenience: re-derive (truth, certificate) for a family problem."""
    return _verifier.verify_family_case(family, problem, problem_id)
