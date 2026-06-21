"""ClaimBench bench: wrapper that calls run_claimbench from core.claimgate."""
from __future__ import annotations
from ...core.claimgate import run_claimbench, PUBLIC_WORDING


def run_claimbench_bench(seed: int = 20260628, model=None) -> dict:
    result = run_claimbench(seed=seed)
    result["public_wording"] = PUBLIC_WORDING
    return result
