"""Math hardening benches: 5 benches."""
from .domainbench import run_domainbench
from .assumptionbench import run_assumptionbench
from .witnessbench import run_witnessbench
from .proofobjectbench import run_proofobjectbench
from .hardeningbench import run_hardeningbench

MATH_HARDENING_BENCH_NAMES = [
    "domainbench", "assumptionbench", "witnessbench",
    "proofobjectbench", "hardeningbench",
]

MATH_HARDENING_BENCH_DISPATCH = {
    "domainbench": run_domainbench,
    "assumptionbench": run_assumptionbench,
    "witnessbench": run_witnessbench,
    "proofobjectbench": run_proofobjectbench,
    "hardeningbench": run_hardeningbench,
}

__all__ = ["MATH_HARDENING_BENCH_NAMES", "MATH_HARDENING_BENCH_DISPATCH",
           "run_domainbench", "run_assumptionbench", "run_witnessbench",
           "run_proofobjectbench", "run_hardeningbench"]
