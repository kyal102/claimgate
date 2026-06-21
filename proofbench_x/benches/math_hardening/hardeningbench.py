"""HardeningBench: run the full Research Hardening suite (all categories)."""
from __future__ import annotations
from ...core.math_hardening.math_hardening_bench import run_math_hardening_bench

def run_hardeningbench(seed: int = 20260629, model=None) -> dict:
    return run_math_hardening_bench(seed=seed)
