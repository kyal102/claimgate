"""ReplayBench bench: wrapper that calls run_replaybench from core.replay."""
from __future__ import annotations
from ...core.replay import run_replaybench, PUBLIC_WORDING


def run_replaybench_bench(seed: int = 20260627, model=None) -> dict:
    result = run_replaybench(seed=seed)
    result["public_wording"] = PUBLIC_WORDING
    return result
