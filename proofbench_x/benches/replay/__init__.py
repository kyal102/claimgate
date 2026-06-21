"""Replay benches: replaybench."""
from .replaybench_bench import run_replaybench_bench

REPLAY_BENCH_NAMES = ["replaybench"]

REPLAY_BENCH_DISPATCH = {
    "replaybench": run_replaybench_bench,
}

__all__ = ["REPLAY_BENCH_NAMES", "REPLAY_BENCH_DISPATCH", "run_replaybench_bench"]
