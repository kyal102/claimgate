"""v2 HoldoutHard bench."""
from __future__ import annotations
import re
from typing import List
from ..core.v2 import holdout_hardness_score
from ..core.families import FAMILY_REGISTRY, make_variants
from ..core.verifier import Verifier

_TOKEN_NUM_RE = re.compile(r"\d+")

def _prompt_leaks_answer(prompt: str, expected_str: str) -> bool:
    p = prompt.lower()
    e = expected_str.strip()
    if "/" in e:
        try:
            en, ed = e.split("/"); en, ed = en.strip(), ed.strip()
        except Exception:
            return False
        seq = re.findall(r"\d+\s*/\s*\d+|\d+", p)
        norm = [re.sub(r"\s+", "", s) for s in seq]
        return (f"{en}/{ed}") in norm
    nums = _TOKEN_NUM_RE.findall(p)
    return e in nums

def run_v2_holdout(seed: int = 20260623, n_per_family: int = 5, model=None) -> dict:
    v = Verifier()
    results: List[dict] = []
    for fid, fam in sorted(FAMILY_REGISTRY.items()):
        variants = make_variants(fam, n_per_family, seed)
        for j, problem in enumerate(variants):
            pid = f"holdouthard:{fid}:{j}"
            truth, cert = v.verify_family_case(fam, problem, pid)
            expected_str = truth.display()
            prompt = (f"Verify and compute the exact result of: {fam.render(problem)}. "
                      f"(Family: {fam.name}. Do not assume the answer.)")
            leaked = _prompt_leaks_answer(prompt, expected_str)
            results.append({"problem_id": pid, "family": fid, "prompt": prompt,
                            "expected": expected_str, "expected_canonical": truth.canonical_string(),
                            "certificate_hash": cert.hash, "lane_id": cert.lane_id,
                            "prompt_leaked_answer": leaked,
                            "contamination_note": "Built with AI assistance -> NOT valid for uncontaminated public leaderboard."})
    score = holdout_hardness_score(results)
    return {"bench": "v2_holdout", "mode": "HoldoutHard (fresh seeded, no leakage)",
            "seed": seed, "n_cases": len(results), "results": results,
            "score": score.to_dict(),
            "contamination_disclaimer": "Holdout cases built with AI assistance are NOT valid for uncontaminated public leaderboard."}
