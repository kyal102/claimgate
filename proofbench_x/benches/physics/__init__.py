"""Physics benches: 6 benches for PhysicsGate v0."""
from .unitgate import run_physics_unitgate
from .limitgate import run_physics_limitgate
from .conservationgate import run_physics_conservationgate
from .uncertaintygate import run_physics_uncertaintygate
from .physicscounter import run_physics_counterexample
from .physicsclaim import run_physics_claimbench

PHYSICS_BENCH_NAMES = [
    "unitgate", "limitgate", "conservationgate",
    "uncertaintygate", "physicscounter", "physicsclaim",
]

PHYSICS_BENCH_DISPATCH = {
    "unitgate": run_physics_unitgate,
    "limitgate": run_physics_limitgate,
    "conservationgate": run_physics_conservationgate,
    "uncertaintygate": run_physics_uncertaintygate,
    "physicscounter": run_physics_counterexample,
    "physicsclaim": run_physics_claimbench,
}

__all__ = ["PHYSICS_BENCH_NAMES", "PHYSICS_BENCH_DISPATCH",
           "run_physics_unitgate", "run_physics_limitgate",
           "run_physics_conservationgate", "run_physics_uncertaintygate",
           "run_physics_counterexample", "run_physics_claimbench"]
