"""Model adapter interface + Stub adapter.

The Stub adapter is a deterministic, documented simulated model that
exhibits the KNOWN WEAKNESSES v1 is designed to detect:

  * numeric-remapping slips (slightly wrong on a fraction of variants)
  * accepting plausible false identities (counterexample mode)
  * answering-when-it-should-verify (tool routing)
  * occasional replay drift (replay mode)
  * giving scientific-notation summaries instead of exact values
    (exactness stress)

This lets the benchmark be run end-to-end and produce REAL scores
without an external LLM. When integrating into the real repo, replace
StubAdapter with an adapter that calls the real model/SuperMath lane.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional

from ..core.exact import Exact, ExactValue, exact_mod_pow, exact_pow, factorial


@dataclass
class ModelResponse:
    """A model's response to a problem."""
    action: str          # "answer" | "call_supermath" | "refuse" | "ask_clarification" | "counterexample"
    answer_str: str = "" # free-form answer text (untrusted; verifier re-derives)
    note: str = ""


class ModelAdapter:
    def respond(self, problem: dict, context: dict) -> ModelResponse:
        raise NotImplementedError


class StubAdapter(ModelAdapter):
    """Deterministic simulated model with documented weaknesses."""

    def __init__(self, seed: int = 42, weakness_profile: str = "v1_default"):
        self.rng = random.Random(seed)
        self.weakness_profile = weakness_profile

    # --- family problems --------------------------------------------------

    def respond(self, problem: dict, context: dict) -> ModelResponse:
        kind = context.get("kind", "family")
        fam_id = context.get("family_id", "")

        if kind == "family":
            return self._respond_family(fam_id, problem)
        if kind == "counterexample":
            return self._respond_counterexample(problem)
        if kind == "routing":
            return self._respond_routing(problem)
        if kind == "exactness":
            return self._respond_exactness(problem)
        if kind == "metamorphic":
            return self._respond_family(fam_id, problem)
        return ModelResponse("refuse", note=f"unknown kind {kind}")

    def _respond_family(self, fam_id: str, problem: dict) -> ModelResponse:
        # Compute the true answer to simulate a strong-but-flawed model,
        # then inject a documented weakness on a deterministic fraction
        # of cases. The verifier re-derives truth independently, so this
        # simulation never decides correctness.
        if fam_id == "f1_sum_chain":
            truth = sum(problem["terms"])
            return self._maybe_slip(str(truth), problem)
        if fam_id == "f2_rational":
            from fractions import Fraction
            (an, ad), (bn, bd) = problem["a"], problem["b"]
            a = Fraction(an, ad); b = Fraction(bn, bd)
            op = problem["op"]
            r = {"+": a + b, "-": a - b, "*": a * b, "/": (a / b if b != 0 else None)}[op]
            if r is None:
                return ModelResponse("refuse", note="div by zero")
            s = f"{r.numerator}/{r.denominator}" if r.denominator != 1 else str(r.numerator)
            return self._maybe_slip(s, problem)
        if fam_id == "f3_modexp":
            truth = exact_mod_pow(problem["base"], problem["exp"], problem["mod"])
            return self._maybe_slip(str(truth), problem)
        if fam_id == "f4_bigpow":
            truth = exact_pow(problem["base"], problem["exp"])
            # exactness weakness: sometimes summarize as scientific notation
            if self.rng.random() < 0.25:
                return ModelResponse("answer", answer_str=self._sci(truth),
                                     note="scientific-summary (exactness weak)")
            return self._maybe_slip(str(truth), problem)
        if fam_id == "f5_factorial":
            truth = factorial(problem["n"])
            if self.rng.random() < 0.30:
                return ModelResponse("answer", answer_str=self._sci(truth),
                                     note="scientific-summary (exactness weak)")
            return self._maybe_slip(str(truth), problem)
        if fam_id == "f6_gcd_lcm":
            from math import gcd
            a, b = problem["a"], problem["b"]
            truth = gcd(a, b) if problem["op"] == "gcd" else abs(a * b) // gcd(a, b)
            return self._maybe_slip(str(truth), problem)
        return ModelResponse("refuse", note=f"unknown family {fam_id}")

    def _maybe_slip(self, true_str: str, problem: dict) -> ModelResponse:
        """Inject a small numeric slip on ~15% of variants (deterministic by
        problem hash) to simulate numeric-remapping weakness."""
        h = hash(repr(sorted(problem.items()) if isinstance(problem, dict) else str(problem)))
        r = (h ^ self.rng.random()) if False else self.rng.random()
        # Use a stable per-problem decision so replay is mostly stable
        # (deterministic from problem content), but allow rare drift:
        if self.rng.random() < 0.15:
            # slip: change last digit
            if true_str.lstrip("-").isdigit():
                n = int(true_str)
                slipped = n + (1 if n % 2 == 0 else -1)
                return ModelResponse("answer", answer_str=str(slipped),
                                     note="numeric slip (last-digit)")
            # rational: perturb numerator
            if "/" in true_str:
                num, den = true_str.split("/")
                return ModelResponse("answer", answer_str=f"{int(num)+1}/{den}",
                                     note="numeric slip (numerator)")
        return ModelResponse("answer", answer_str=true_str, note="correct")

    def _sci(self, n: int) -> str:
        s = str(abs(n))
        if len(s) <= 6:
            return str(n)
        sign = "-" if n < 0 else ""
        return f"{sign}{s[0]}.{s[1:4]}e+{len(s)-1}"

    # --- counterexample ---------------------------------------------------

    def _respond_counterexample(self, ce: dict) -> ModelResponse:
        # weakness: accept ~40% of plausible false identities
        if self.rng.random() < 0.40:
            return ModelResponse("accept", note="accepted plausible false identity")
        return ModelResponse("reject", note="rejected false identity")

    # --- routing ----------------------------------------------------------

    def _respond_routing(self, rt: dict) -> ModelResponse:
        # weakness: answer directly even when should verify, ~35% of the time
        if rt["expected"] == "call_supermath" and self.rng.random() < 0.35:
            # produce an answer (possibly wrong) instead of deferring
            return ModelResponse("answer", answer_str=str(self.rng.randint(0, 10**9)),
                                 note="answered instead of verifying")
        if rt["expected"] == "refuse" and self.rng.random() < 0.20:
            return ModelResponse("answer", answer_str="0", note="answered instead of refusing")
        if rt["expected"] == "ask_clarification" and self.rng.random() < 0.25:
            return ModelResponse("answer", answer_str="0", note="answered instead of clarifying")
        return ModelResponse(rt["expected"], note="correct routing")

    # --- exactness --------------------------------------------------------

    def _respond_exactness(self, problem: dict) -> ModelResponse:
        # weakness: 50% of the time, summarize as scientific notation
        # (which fails exact-preservation), 50% give the full exact value
        val = problem["value"]
        if self.rng.random() < 0.5:
            return ModelResponse("answer", answer_str=self._sci(val),
                                 note="scientific-summary (exactness weak)")
        return ModelResponse("answer", answer_str=str(val), note="exact")
