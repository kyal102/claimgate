"""ReplayRunner v0: execute evidence-pack repro commands and audit replays.

Public wording:
  "ReplayRunner executes evidence-pack repro commands and checks whether
   results reproduce. It does not prove scientific truth; it verifies
   whether a recorded verification result can be replayed without drift."
"""
from .runner import (
    ALL_REPLAY_STATUSES, PUBLIC_WORDING,
    ReplayResult, ReplayRunner, load_pack_from_json,
)
from .replaybench import ReplayCase, REPLAY_CASES, run_replaybench

__all__ = [
    "ALL_REPLAY_STATUSES", "PUBLIC_WORDING",
    "ReplayResult", "ReplayRunner", "load_pack_from_json",
    "ReplayCase", "REPLAY_CASES", "run_replaybench",
]
