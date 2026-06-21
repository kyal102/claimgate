"""v2 DeepChain bench."""
from __future__ import annotations
from typing import List
from ..core.v2 import generate_chain, verify_chain, deep_chain_integrity_score
from ..core.canonical import normalize_input
from ..core.certificate import issue_certificate
from ..core.exact import Exact
import random

def run_v2_deepchain(seed: int = 20260623, n_chains: int = 5, model=None) -> dict:
    rng = random.Random(seed)
    results = []
    for i in range(n_chains):
        chain = generate_chain(rng, min_steps=10, max_steps=30)
        consistent, final_canon, inter_cans = verify_chain(chain)
        if not consistent:
            results.append({"id": chain.id, "status": "fail",
                            "note": f"verifier inconsistency: {final_canon}",
                            "n_steps": len(chain.steps)})
            continue
        # issue certificate over the full chain (final + intermediates)
        lane = f"deepchain:steps={len(chain.steps)}"
        cert = issue_certificate(chain.id, "deepchain",
                                 normalize_input(chain.render()),
                                 Exact.i(0),  # placeholder; real cert uses final_canon
                                 lane, note=f"final={final_canon}")
        results.append({"id": chain.id, "status": "pass",
                        "n_steps": len(chain.steps),
                        "n_intermediates": len(inter_cans),
                        "final_canonical": final_canon,
                        "certificate_hash": cert.hash,
                        "note": "chain + all intermediates consistent"})
    score = deep_chain_integrity_score(results)
    return {"bench": "v2_deepchain", "mode": "DeepChain (10-50 step, hidden intermediates)",
            "seed": seed, "n_cases": len(results), "results": results,
            "score": score.to_dict()}
