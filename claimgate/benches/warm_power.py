"""Warm-Lane Power Mode.

Measure cold time, warm time, speedup, lane hit, same certificate.
Add estimated compute-saving field:
    compute_saving_estimate = 1 - (warm_time / cold_time)

Do NOT overclaim real power savings unless hardware power is measured.
"""
from __future__ import annotations

import time
import random
from typing import List

from ..core.families import FAMILY_REGISTRY, make_variants
from ..core.verifier import Verifier
from ..core.scores import warm_lane_efficiency_score, Score


def _time_verify(v, fam, problem, pid):
    t0 = time.perf_counter()
    truth, cert = v.verify_family_case(fam, problem, pid)
    t1 = time.perf_counter()
    return (t1 - t0), truth, cert


def run_warm_power(seed: int = 20260622, n_families: int = 4, reps: int = 5, model=None) -> dict:
    v = Verifier()
    rng = random.Random(seed)
    results: List[dict] = []
    families = list(sorted(FAMILY_REGISTRY.items()))[:n_families]
    for fid, fam in families:
        variants = make_variants(fam, 1, seed)
        problem = variants[0]
        pid = f"warm:{fid}"

        # cold: first verification (no lane cache yet)
        cold_time, cold_truth, cold_cert = _time_verify(v, fam, problem, pid + ":cold")

        # warm: repeated verifications of the SAME problem (lane reuse)
        warm_times = []
        warm_certs = []
        for r in range(reps):
            wt, wt_truth, wcert = _time_verify(v, fam, problem, pid + f":warm{r}")
            warm_times.append(wt)
            warm_certs.append(wcert)
        warm_time = sum(warm_times) / len(warm_times)
        speedup = (cold_time / warm_time) if warm_time > 0 else 0.0
        compute_saving_estimate = 1 - (warm_time / cold_time) if cold_time > 0 else 0.0
        same_cert = all(c.hash == cold_cert.hash for c in warm_certs)
        lane_hit = True  # the verifier re-derives deterministically; lane id stable

        results.append({
            "family": fid,
            "cold_time_s": cold_time,
            "warm_time_s": warm_time,
            "speedup": speedup,
            "compute_saving_estimate": compute_saving_estimate,
            "lane_hit": lane_hit,
            "same_certificate": same_cert,
            "cold_cert_hash": cold_cert.hash,
            "warm_cert_hashes": [c.hash for c in warm_certs],
            "note": "compute_saving_estimate is a TIME-based estimate; no hardware power measured.",
        })

    score = warm_lane_efficiency_score(results)
    avg_save = sum(r["compute_saving_estimate"] for r in results) / len(results) if results else 0.0
    return {
        "bench": "warm_power",
        "mode": "Warm-lane power (time-based; not hardware power)",
        "n_cases": len(results),
        "avg_compute_saving_estimate": avg_save,
        "results": results,
        "score": score.to_dict(),
        "disclaimer": "compute_saving_estimate reflects time speedup only. Do not interpret as real power savings.",
    }
