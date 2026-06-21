"""Holdout Mode.

Generate private seeded holdout cases AFTER implementation. Do NOT
expose expected answers in model prompts. Mark dev/public cases as not
valid for uncontaminated model leaderboard if Claude helped build them.

Integrity rule: no prompt may contain the expected answer as a discrete
token. We check this explicitly using TOKEN-BOUNDARY matching (NOT naive
substring matching, which falsely flags e.g. answer "7" inside "997").
The Holdout Integrity Score is 1.0 only if zero prompts leak.
"""
from __future__ import annotations

import random
import re
from typing import List, Optional

from ..core.families import FAMILY_REGISTRY, make_variants, Family
from ..core.verifier import Verifier
from ..core.scores import holdout_integrity_score


_TOKEN_NUM_RE = re.compile(r"\d+")


def _prompt_leaks_answer(prompt: str, expected_str: str) -> bool:
    """Return True iff `expected_str` appears in `prompt` as a discrete
    mathematical token (a standalone integer, or an a/b rational pair).

    Naive substring matching is deliberately avoided: it would false-positive
    on e.g. expected "7" appearing inside the problem number "997".
    """
    p = prompt.lower()
    e = expected_str.strip()
    if "/" in e:
        # rational "a/b": check for the exact two-number sequence
        try:
            en, ed = e.split("/")
            en, ed = en.strip(), ed.strip()
        except Exception:
            return False
        seq = re.findall(r"\d+\s*/\s*\d+|\d+", p)
        # normalize matched rationals
        norm = [re.sub(r"\s+", "", s) for s in seq]
        return (f"{en}/{ed}") in norm
    # integer: check if expected appears as a standalone integer token
    nums = _TOKEN_NUM_RE.findall(p)
    return e in nums


def run_holdout(seed: int = 20260622, n_per_family: int = 5, model=None) -> dict:
    v = Verifier()
    results: List[dict] = []
    for fid, fam in sorted(FAMILY_REGISTRY.items()):
        variants = make_variants(fam, n_per_family, seed)
        for j, problem in enumerate(variants):
            pid = f"holdout:{fid}:{j}"
            truth, cert = v.verify_family_case(fam, problem, pid)
            expected_str = truth.display()
            # build a prompt that deliberately does NOT include the answer
            prompt = (
                f"Verify and compute the exact result of: {fam.render(problem)}. "
                f"(Family: {fam.name}. Do not assume the answer.)"
            )
            leaked = _prompt_leaks_answer(prompt, expected_str)
            results.append({
                "problem_id": pid,
                "family": fid,
                "prompt": prompt,
                "expected": expected_str,   # stored privately, NEVER sent to model
                "expected_canonical": truth.canonical_string(),
                "certificate_hash": cert.hash,
                "lane_id": cert.lane_id,
                "prompt_leaked_answer": leaked,
                "contamination_note": (
                    "If this holdout set was generated with AI assistance, "
                    "these cases are NOT valid for an uncontaminated public "
                    "model leaderboard."
                ),
            })
    score = holdout_integrity_score(results)
    return {
        "bench": "holdout",
        "mode": "Private seeded holdout (no answer leakage)",
        "seed": seed,
        "n_cases": len(results),
        "results": results,
        "score": score.to_dict(),
        "contamination_disclaimer": (
            "Holdout cases here were generated programmatically. If any AI "
            "assisted in constructing them, they must NOT be used for an "
            "uncontaminated public model leaderboard."
        ),
    }
