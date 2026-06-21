"""Replay/Drift Mode.

Run selected cases 10 times. Same input MUST produce:
  * same normalized input
  * same result
  * same exactness
  * same certificate hash
  * same lane ID
Any drift fails.

Note: the model adapter is the noisy component here. The verifier is
deterministic, so verifier-side drift would be a real engine bug. To
test verifier determinism specifically, we run with a deterministic
model (seed pinned per-case) so any drift must come from the engine.
"""
from __future__ import annotations

import random
from typing import List

from ..core.families import FAMILY_REGISTRY, make_variants
from ..core.verifier import Verifier
from ..core.canonical import normalize_input, canonicalize
from ..core.scores import replay_stability_score
from ..adapters import StubAdapter

RUNS = 10


def run_replay_drift(seed: int = 20260622, n_cases: int = 5, model=None) -> dict:
    v = Verifier()
    # Use a DETERMINISTIC model (same seed per case) so any drift is
    # attributable to the engine, not the model.
    rng = random.Random(seed)
    cases = []
    for fid, fam in sorted(FAMILY_REGISTRY.items()):
        variants = make_variants(fam, 3, seed)
        cases.append((fid, fam, variants[0]))
        if len(cases) >= n_cases:
            break
    results: List[dict] = []
    for fid, fam, problem in cases:
        runs = []
        for r in range(RUNS):
            # fresh deterministic model per run with SAME seed -> identical responses
            m = StubAdapter(seed=seed + r * 0)  # identical seed every run
            resp = m.respond(problem, {"kind": "family", "family_id": fid})
            vr = v.grade_family_case(fam, problem, resp.answer_str, f"replay:{fid}:r{r}")
            runs.append({
                "run": r,
                "normalized_input": normalize_input(fam.render(problem)),
                "status": vr.status,
                "expected": vr.expected,
                "got": vr.got,
                "certificate_hash": vr.certificate.hash if vr.certificate else None,
                "lane_id": vr.certificate.lane_id if vr.certificate else None,
                "result_kind": vr.certificate.result_kind if vr.certificate else None,
            })
        # stability check
        first = runs[0]
        stable = True
        drift_fields = []
        for run in runs[1:]:
            for field in ("normalized_input", "status", "expected", "got",
                          "certificate_hash", "lane_id", "result_kind"):
                if run.get(field) != first.get(field):
                    stable = False
                    drift_fields.append(field)
        results.append({
            "family": fid,
            "runs": RUNS,
            "stable": stable,
            "drift_fields": drift_fields,
            "first": first,
        })
    score = replay_stability_score(results)
    return {
        "bench": "replay_drift",
        "mode": "Replay/deterministic-replay stability",
        "runs_per_case": RUNS,
        "n_cases": len(results),
        "results": results,
        "score": score.to_dict(),
    }
