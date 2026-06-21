"""Evidence benches: evidencebench + reprobench."""
from .evidencebench import run_evidence_bench
from .reprobench_bench import run_reprobench_bench

EVIDENCE_BENCH_NAMES = ["evidencebench", "reprobench"]

EVIDENCE_BENCH_DISPATCH = {
    "evidencebench": run_evidence_bench,
    "reprobench": run_reprobench_bench,
}

__all__ = ["EVIDENCE_BENCH_NAMES", "EVIDENCE_BENCH_DISPATCH",
           "run_evidence_bench", "run_reprobench_bench"]
