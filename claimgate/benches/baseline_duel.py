"""Baseline duel bench: 3-lane comparison (raw / model+tool / DTL-verified).

Runs the ModelDuel across all families on a shared problem set, so the
report can show the contrast between bare-model correctness and
verified-system correctness on the SAME problems.
"""
from __future__ import annotations

from typing import List

from ..core.families import FAMILY_REGISTRY, make_variants
from ..core.duel import ModelDuel
from ..core.verifier import Verifier
from ..adapters import StubAdapter


def run_baseline_duel(seed: int = 20260622, variants_per_family: int = 5,
                      raw_adapter=None, tool_adapter=None) -> dict:
    """Run the 3-lane duel. Adapters default to StubAdapter (deterministic,
    documented simulated weaknesses). For a real baseline, pass real adapters."""
    raw = raw_adapter or StubAdapter(seed=seed, weakness_profile="duel_raw")
    tool = tool_adapter or StubAdapter(seed=seed + 1, weakness_profile="duel_tool")
    duel = ModelDuel(raw_adapter=raw, tool_adapter=tool, verifier=Verifier())

    per_family = {}
    all_reports = []
    for fid, fam in sorted(FAMILY_REGISTRY.items()):
        problems = make_variants(fam, variants_per_family, seed)
        report = duel.run(fam, problems, seed=seed)
        per_family[fid] = {
            "n_cases": report.n_cases,
            "raw_model": report.raw_model,
            "model_plus_tool": report.model_plus_tool,
            "dtl_verified": report.dtl_verified,
            "overrides_applied": report.overrides_applied,
        }
        all_reports.append(report)

    # aggregate across families
    total_cases = sum(r.n_cases for r in all_reports)
    raw_pass = sum(r.raw_model["passed"] for r in all_reports)
    raw_total = sum(r.raw_model["total"] for r in all_reports)
    tool_pass = sum(r.model_plus_tool["passed"] for r in all_reports)
    tool_total = sum(r.model_plus_tool["total"] for r in all_reports)
    dtl_pass = sum(r.dtl_verified["passed"] for r in all_reports)
    dtl_total = sum(r.dtl_verified["total"] for r in all_reports)
    overrides = sum(r.overrides_applied for r in all_reports)

    summary = {
        "bench": "baseline_duel",
        "mode": "3-lane model duel (raw / model+tool / DTL-verified)",
        "n_cases": total_cases,
        "raw_model": {"score": raw_pass / raw_total if raw_total else None,
                      "passed": raw_pass, "total": raw_total},
        "model_plus_tool": {"score": tool_pass / tool_total if tool_total else None,
                            "passed": tool_pass, "total": tool_total},
        "dtl_verified": {"score": dtl_pass / dtl_total if dtl_total else None,
                         "passed": dtl_pass, "total": dtl_total},
        "overrides_applied": overrides,
        "per_family": per_family,
        "anti_override_rule": "verifier is final authority in Lane C; model cannot override",
        "note": "Stub adapters used in prototype; wire real model adapters for real baselines.",
    }
    return summary
