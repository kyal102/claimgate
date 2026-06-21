"""ClaimGate benches: claimbench."""
from .claimbench_bench import run_claimbench_bench

CLAIM_BENCH_NAMES = ["claimbench"]

CLAIM_BENCH_DISPATCH = {
    "claimbench": run_claimbench_bench,
}

__all__ = ["CLAIM_BENCH_NAMES", "CLAIM_BENCH_DISPATCH", "run_claimbench_bench"]
