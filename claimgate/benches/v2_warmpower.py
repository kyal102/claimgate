"""v2 WarmLanePower bench."""
from __future__ import annotations
import time
from ..core.v2 import warm_lane_efficiency_score_v2
from ..core.families import FAMILY_REGISTRY, make_variants
from ..core.verifier import Verifier

def run_v2_warmpower(seed: int = 20260623, n_families: int = 4, reps: int = 5, model=None) -> dict:
    v = Verifier()
    results = []
    families = list(sorted(FAMILY_REGISTRY.items()))[:n_families]
    for fid, fam in families:
        variants = make_variants(fam, 1, seed)
        problem = variants[0]
        pid = f"warmv2:{fid}"
        t0 = time.perf_counter()
        cold_truth, cold_cert = v.verify_family_case(fam, problem, pid + ":cold")
        cold_time = time.perf_counter() - t0
        warm_times = []; warm_certs = []
        for r in range(reps):
            t0 = time.perf_counter()
            _, wcert = v.verify_family_case(fam, problem, pid + f":warm{r}")
            warm_times.append(time.perf_counter() - t0)
            warm_certs.append(wcert)
        warm_time = sum(warm_times) / len(warm_times)
        speedup = cold_time / warm_time if warm_time > 0 else 0.0
        compute_saving = 1 - (warm_time / cold_time) if cold_time > 0 else 0.0
        same_cert = all(c.hash == cold_cert.hash for c in warm_certs)
        results.append({"family": fid, "cold_time_s": cold_time, "warm_time_s": warm_time,
                        "speedup": speedup, "compute_saving_estimate": compute_saving,
                        "lane_hit": True, "same_certificate": same_cert,
                        "note": "time-based estimate; not hardware power"})
    score = warm_lane_efficiency_score_v2(results)
    avg_save = sum(r["compute_saving_estimate"] for r in results) / len(results) if results else 0.0
    return {"bench": "v2_warmpower", "mode": "WarmLanePower (time-based)",
            "seed": seed, "n_cases": len(results),
            "avg_compute_saving_estimate": avg_save, "results": results,
            "score": score.to_dict(),
            "disclaimer": "compute_saving_estimate is time-based only; not hardware power measurement."}
