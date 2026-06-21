"""DomainBench: run only the domain-sensitive cases."""
from __future__ import annotations
from ...core.math_hardening.math_hardening_bench import _build_domain_cases
from ...core.math_hardening.scores import domain_discipline_score
from ...core.math_hardening import PUBLIC_WORDING

def run_domainbench(seed: int = 20260629, model=None) -> dict:
    cases = _build_domain_cases()
    score = domain_discipline_score(cases)
    return {
        "bench": "domainbench",
        "mode": "DomainGate v0 (domain assumption checking)",
        "public_wording": PUBLIC_WORDING,
        "seed": seed, "n_cases": len(cases),
        "results": cases, "score": score.to_dict(),
    }
