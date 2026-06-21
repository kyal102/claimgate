"""DeepChain Mode: 10-50 step chained problems.

Each step feeds the next. Includes integer, rational, modular, gcd/lcm,
powers, signs, and simplification. Hidden intermediate truth is stored
in certificate/debug evidence. A chain passes ONLY if the final result
AND every intermediate verification are consistent.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List, Tuple, Optional

from ..exact import Exact, ExactValue, exact_mod_pow, exact_pow, exact_gcd, exact_lcm, factorial


@dataclass
class ChainStep:
    op: str           # "add" | "mul" | "div" | "mod" | "pow" | "gcd" | "lcm" | "neg" | "simplify"
    operand: Optional[int]
    description: str  # human-readable


@dataclass
class ChainProblem:
    id: str
    start: int
    steps: List[ChainStep]
    # hidden intermediate truth (never sent to model)
    intermediates: List[ExactValue] = field(default_factory=list)
    final: Optional[ExactValue] = None

    def render(self) -> str:
        """Render the chain as a human-readable problem string.
        Does NOT include intermediate values."""
        parts = [f"start with {self.start}"]
        for i, s in enumerate(self.steps, 1):
            parts.append(f"step{i}: {s.description}")
        parts.append("compute the exact final result")
        return " | ".join(parts)


def generate_chain(rng: random.Random, min_steps: int = 10,
                   max_steps: int = 50) -> ChainProblem:
    """Generate a deterministic chained problem with hidden intermediate truth."""
    n_steps = rng.randint(min_steps, max_steps)
    start = rng.randint(1, 100)
    steps: List[ChainStep] = []
    intermediates: List[ExactValue] = []
    current = Exact.i(start)

    for i in range(n_steps):
        op = rng.choice(["add", "mul", "div", "mod", "pow", "gcd", "lcm", "neg", "simplify"])
        if op == "add":
            v = rng.randint(-100, 200)
            steps.append(ChainStep("add", v, f"add {v}"))
            current = Exact.add(current, Exact.i(v))
        elif op == "mul":
            v = rng.randint(-20, 20)
            if v == 0:
                v = rng.randint(1, 20)
            steps.append(ChainStep("mul", v, f"multiply by {v}"))
            current = Exact.mul(current, Exact.i(v))
        elif op == "div":
            v = rng.randint(1, 50)
            steps.append(ChainStep("div", v, f"divide by {v} (exact rational)"))
            from fractions import Fraction
            if current.kind == "int":
                current = Exact.frac(current.int_val, v)
            elif current.kind == "rational":
                current = ExactValue(kind="rational",
                                     rat_val=current.rat_val / v)
            else:
                # mod value -> treat as int residue
                current = Exact.frac(current.mod_val[0], v)
        elif op == "mod":
            m = rng.choice([97, 101, 1000, 9973])
            steps.append(ChainStep("mod", m, f"reduce mod {m}"))
            if current.kind == "int":
                current = Exact.mod(current.int_val, m)
            elif current.kind == "rational":
                num, den = current.rat_val.numerator, current.rat_val.denominator
                inv = pow(den % m, -1, m) if den % m != 0 else None
                if inv is None:
                    # skip mod if not invertible; replace with simplify
                    steps[-1] = ChainStep("simplify", None, "simplify fraction")
                else:
                    current = Exact.mod((num % m) * inv % m, m)
            else:
                current = Exact.mod(current.mod_val[0], m)
        elif op == "pow":
            e = rng.randint(2, 6)
            steps.append(ChainStep("pow", e, f"raise to power {e}"))
            if current.kind == "int":
                if abs(current.int_val) > 10**6:
                    # avoid explosion; simplify instead
                    steps[-1] = ChainStep("simplify", None, "simplify")
                else:
                    current = Exact.i(current.int_val ** e)
            elif current.kind == "rational":
                from fractions import Fraction
                current = ExactValue(kind="rational",
                                     rat_val=current.rat_val ** e)
            else:
                # mod pow
                v, m = current.mod_val
                current = Exact.mod(exact_mod_pow(v, e, m), m)
        elif op == "gcd":
            v = rng.randint(1, 1000)
            steps.append(ChainStep("gcd", v, f"gcd with {v}"))
            if current.kind == "int":
                current = Exact.i(exact_gcd(current.int_val, v))
            else:
                steps[-1] = ChainStep("simplify", None, "simplify")
        elif op == "lcm":
            v = rng.randint(1, 100)
            steps.append(ChainStep("lcm", v, f"lcm with {v}"))
            if current.kind == "int":
                current = Exact.i(exact_lcm(current.int_val, v))
            else:
                steps[-1] = ChainStep("simplify", None, "simplify")
        elif op == "neg":
            steps.append(ChainStep("neg", None, "flip sign"))
            current = Exact.mul(current, Exact.i(-1))
        elif op == "simplify":
            steps.append(ChainStep("simplify", None, "simplify (canonicalize)"))
            # no-op on value; canonical form is automatic

        intermediates.append(current)

    return ChainProblem(
        id=f"chain_{rng.randint(0, 10**9)}",
        start=start, steps=steps,
        intermediates=intermediates,
        final=intermediates[-1] if intermediates else current,
    )


def verify_chain(chain: ChainProblem) -> Tuple[bool, str, List[str]]:
    """Re-derive every intermediate from the chain definition.
    Returns (all_consistent, final_canonical, intermediate_canonicals).
    This is the VERIFIER-side truth computation -- never sent to model."""
    current = Exact.i(chain.start)
    inter_cans = [current.canonical_string()]
    for i, step in enumerate(chain.steps):
        try:
            if step.op == "add":
                current = Exact.add(current, Exact.i(step.operand))
            elif step.op == "mul":
                current = Exact.mul(current, Exact.i(step.operand))
            elif step.op == "div":
                from fractions import Fraction
                if current.kind == "int":
                    current = Exact.frac(current.int_val, step.operand)
                elif current.kind == "rational":
                    current = ExactValue(kind="rational",
                                         rat_val=current.rat_val / step.operand)
                else:
                    current = Exact.frac(current.mod_val[0], step.operand)
            elif step.op == "mod":
                m = step.operand
                if current.kind == "int":
                    current = Exact.mod(current.int_val, m)
                elif current.kind == "rational":
                    num, den = current.rat_val.numerator, current.rat_val.denominator
                    inv = pow(den % m, -1, m) if den % m != 0 else None
                    if inv is not None:
                        current = Exact.mod((num % m) * inv % m, m)
                else:
                    current = Exact.mod(current.mod_val[0], m)
            elif step.op == "pow":
                e = step.operand
                if current.kind == "int":
                    current = Exact.i(current.int_val ** e)
                elif current.kind == "rational":
                    from fractions import Fraction
                    current = ExactValue(kind="rational", rat_val=current.rat_val ** e)
                else:
                    v, m = current.mod_val
                    current = Exact.mod(exact_mod_pow(v, e, m), m)
            elif step.op == "gcd":
                if current.kind == "int":
                    current = Exact.i(exact_gcd(current.int_val, step.operand))
            elif step.op == "lcm":
                if current.kind == "int":
                    current = Exact.i(exact_lcm(current.int_val, step.operand))
            elif step.op == "neg":
                current = Exact.mul(current, Exact.i(-1))
            elif step.op == "simplify":
                pass  # canonical form is automatic
            inter_cans.append(current.canonical_string())
        except Exception as e:
            return False, f"VERIFIER_ERROR_at_step_{i}: {e}", inter_cans

    # check consistency with stored intermediates
    stored = [Exact.i(chain.start).canonical_string()] + [iv.canonical_string() for iv in chain.intermediates]
    consistent = (inter_cans == stored)
    if not consistent:
        return False, "INTERMEDIATE_MISMATCH", inter_cans
    return True, current.canonical_string(), inter_cans
