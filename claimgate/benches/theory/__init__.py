"""Theory benches: theorygate + theorybench."""
from .theorygate import run_theory_gate
from .theorybench import run_theory_bench

THEORY_BENCH_NAMES = ["theorygate", "theorybench"]

THEORY_BENCH_DISPATCH = {
    "theorygate": run_theory_gate,
    "theorybench": run_theory_bench,
}

__all__ = ["THEORY_BENCH_NAMES", "THEORY_BENCH_DISPATCH",
           "run_theory_gate", "run_theory_bench"]
