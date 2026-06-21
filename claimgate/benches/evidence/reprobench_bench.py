"""ReproBench bench: wrapper that calls run_reprobench from core.evidence."""
from __future__ import annotations
from ...core.evidence import run_reprobench, PUBLIC_WORDING


def run_reprobench_bench(seed: int = 20260626, model=None) -> dict:
    result = run_reprobench(seed=seed)
    result["public_wording"] = PUBLIC_WORDING
    return result
