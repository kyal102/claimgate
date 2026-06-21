"""Bench modules: v0 prototype baseline + 8 v1 benches + baseline duel + 10 v2 benches."""

from .v0_baseline import run_v0
from .var_lane import run_var_lane
from .metamorphic import run_metamorphic
from .counterexample import run_counterexample
from .exact_stress import run_exact_stress
from .tool_routing import run_tool_routing
from .replay_drift import run_replay_drift
from .warm_power import run_warm_power
from .holdout import run_holdout
from .baseline_duel import run_baseline_duel

# v2 benches
from .v2_deepchain import run_v2_deepchain
from .v2_disguise import run_v2_disguise
from .v2_parser import run_v2_parser
from .v2_counterexample import run_v2_counterexample
from .v2_exactness import run_v2_exactness
from .v2_routing import run_v2_routing
from .v2_certificate import run_v2_certificate
from .v2_holdout import run_v2_holdout
from .v2_warmpower import run_v2_warmpower
from .v2_refusal import run_v2_refusal

# physics benches
from .physics import (
    PHYSICS_BENCH_NAMES, PHYSICS_BENCH_DISPATCH,
    run_physics_unitgate, run_physics_limitgate, run_physics_conservationgate,
    run_physics_uncertaintygate, run_physics_counterexample, run_physics_claimbench,
)

# theory benches
from .theory import (
    THEORY_BENCH_NAMES, THEORY_BENCH_DISPATCH,
    run_theory_gate, run_theory_bench,
)

# evidence benches
from .evidence import (
    EVIDENCE_BENCH_NAMES, EVIDENCE_BENCH_DISPATCH,
    run_evidence_bench, run_reprobench_bench,
)

# replay benches
from .replay import (
    REPLAY_BENCH_NAMES, REPLAY_BENCH_DISPATCH,
    run_replaybench_bench,
)

# claimgate benches
from .claimgate import (
    CLAIM_BENCH_NAMES, CLAIM_BENCH_DISPATCH,
    run_claimbench_bench,
)

# math_hardening benches
from .math_hardening import (
    MATH_HARDENING_BENCH_NAMES, MATH_HARDENING_BENCH_DISPATCH,
    run_domainbench, run_assumptionbench, run_witnessbench,
    run_proofobjectbench, run_hardeningbench,
)

BENCH_NAMES = [
    "v0", "varlane", "metamorphic", "counterexample",
    "exactstress", "toolrouting", "replay", "warmpower", "holdout",
]

V2_BENCH_NAMES = [
    "deepchain", "disguise", "parser", "counterexample",
    "exactness", "routing", "certificate", "holdout", "warmpower", "refusal",
]

V2_BENCH_DISPATCH = {
    "deepchain": run_v2_deepchain,
    "disguise": run_v2_disguise,
    "parser": run_v2_parser,
    "counterexample": run_v2_counterexample,
    "exactness": run_v2_exactness,
    "routing": run_v2_routing,
    "certificate": run_v2_certificate,
    "holdout": run_v2_holdout,
    "warmpower": run_v2_warmpower,
    "refusal": run_v2_refusal,
}

BENCH_DISPATCH = {
    "v0": run_v0,
    "varlane": run_var_lane,
    "metamorphic": run_metamorphic,
    "counterexample": run_counterexample,
    "exactstress": run_exact_stress,
    "toolrouting": run_tool_routing,
    "replay": run_replay_drift,
    "warmpower": run_warm_power,
    "holdout": run_holdout,
    "duel": run_baseline_duel,
}

__all__ = ["BENCH_NAMES", "V2_BENCH_NAMES", "BENCH_DISPATCH", "V2_BENCH_DISPATCH",
           "run_v0", "run_var_lane", "run_metamorphic", "run_counterexample",
           "run_exact_stress", "run_tool_routing", "run_replay_drift", "run_warm_power",
           "run_holdout", "run_baseline_duel",
           "run_v2_deepchain", "run_v2_disguise", "run_v2_parser", "run_v2_counterexample",
           "run_v2_exactness", "run_v2_routing", "run_v2_certificate", "run_v2_holdout",
           "run_v2_warmpower", "run_v2_refusal"]
