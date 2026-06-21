"""Model-duel interface: 3-lane comparison.

Compares three system configurations on the SAME problem set:

  Lane A — raw model only:
      The model answers directly. No verification. No tools.
      Measures: bare model correctness.

  Lane B — model + SuperMath tool:
      The model may call SuperMath to verify/compute. Tool output is
      available to the model. The model still produces the final answer.
      Measures: tool-augmented model correctness.

  Lane C — DTL verified (final authority):
      The model produces a candidate answer; the DTL/SuperMath verifier
      re-derives ground truth and OVERRIDES the model if they disagree.
      The verifier's result is the final output. Model cannot override.
      Measures: verified-system correctness.

Anti-gaming rules enforced:
  * The verifier (Lane C) never trusts the model output.
  * The verifier re-derives truth via exact solvers (no answer lookup).
  * Lane A and Lane B scores are reported separately and honestly --
    they are NOT inflated by Lane C.
  * No score is shown for a lane that did not run (not_run, never faked).
  * If the model "refuses" or "asks clarification", that is recorded as
    a routing outcome, not silently scored as pass or fail.

This is the structure universities care about: it separates "can the
model solve it" from "can the system verify it" from "does verification
actually help."
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List, Optional, Callable

from .exact import Exact, ExactValue
from .families import Family, FAMILY_REGISTRY, make_variants
from .verifier import Verifier, VerificationResult
from .canonical import normalize_input


@dataclass
class LaneResult:
    lane: str                 # "raw_model" | "model_plus_tool" | "dtl_verified"
    problem_id: str
    family: str
    model_action: str         # "answer" | "call_supermath" | "refuse" | "ask_clarification"
    model_answer_str: str
    verifier_status: str      # "pass" | "fail" | "refused" | "unverified" | "not_run"
    final_answer_str: str     # what the lane actually returns as final
    overridden: bool          # True iff Lane C overrode the model
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "lane": self.lane, "problem_id": self.problem_id, "family": self.family,
            "model_action": self.model_action, "model_answer_str": self.model_answer_str,
            "verifier_status": self.verifier_status,
            "final_answer_str": self.final_answer_str,
            "overridden": self.overridden, "note": self.note,
        }


@dataclass
class DuelReport:
    n_cases: int
    raw_model: dict           # {score, passed, total, refused, ...}
    model_plus_tool: dict
    dtl_verified: dict
    overrides_applied: int    # times Lane C overrode the model
    per_case: List[LaneResult] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "n_cases": self.n_cases,
            "raw_model": self.raw_model,
            "model_plus_tool": self.model_plus_tool,
            "dtl_verified": self.dtl_verified,
            "overrides_applied": self.overrides_applied,
            "per_case": [r.to_dict() for r in self.per_case],
        }


class ModelDuel:
    """Runs the 3-lane comparison.

    `raw_adapter`    -- Lane A: model answers directly, no tool, no verify.
    `tool_adapter`   -- Lane B: model may call SuperMath; model still final.
    `verifier`       -- Lane C authority: the real SuperMath verifier.

    The verifier is the SAME across lanes (it's the ground-truth oracle),
    but only Lane C uses its output as the FINAL answer. Lanes A and B
    report the model's own answer and are graded against the verifier.
    """

    def __init__(self, raw_adapter, tool_adapter, verifier: Optional[Verifier] = None):
        self.raw = raw_adapter
        self.tool = tool_adapter
        self.v = verifier or Verifier()

    def run(self, family: Family, problems: List[dict], seed: int = 20260622) -> DuelReport:
        per_case: List[LaneResult] = []
        raw_pass = raw_total = 0
        tool_pass = tool_total = 0
        dtl_pass = dtl_total = 0
        overrides = 0
        raw_refused = tool_refused = 0

        for j, problem in enumerate(problems):
            pid = f"duel:{family.id}:{j}"
            ctx = {"kind": "family", "family_id": family.id}

            # ground truth (re-derived by verifier, never from model)
            try:
                truth, cert = self.v.verify_family_case(family, problem, pid)
                expected = truth.canonical_string()
            except Exception as e:
                # if the verifier cannot derive truth, NO lane passes.
                # Record honestly.
                for lane_name, adapter in [("raw_model", self.raw),
                                           ("model_plus_tool", self.tool)]:
                    resp = adapter.respond(problem, ctx)
                    per_case.append(LaneResult(
                        lane=lane_name, problem_id=pid, family=family.id,
                        model_action=resp.action, model_answer_str=resp.answer_str,
                        verifier_status="unverified", final_answer_str=resp.answer_str,
                        overridden=False, note=f"verifier could not derive truth: {e}"))
                continue

            # Lane A: raw model
            resp_a = self.raw.respond(problem, ctx)
            got_a = self.v._parse_model_answer(resp_a.answer_str, truth)
            status_a = "pass" if got_a == expected else "fail"
            if resp_a.action in ("refuse", "ask_clarification"):
                status_a = "refused"
                raw_refused += 1
            raw_total += 1
            if status_a == "pass":
                raw_pass += 1
            per_case.append(LaneResult(
                lane="raw_model", problem_id=pid, family=family.id,
                model_action=resp_a.action, model_answer_str=resp_a.answer_str,
                verifier_status=status_a, final_answer_str=resp_a.answer_str,
                overridden=False, note=resp_a.note))

            # Lane B: model + tool (model may call SuperMath; model still final)
            # In the prototype, the tool adapter is given a "tool hint" context
            # but still produces its own answer. The verifier grades it.
            resp_b = self.tool.respond(problem, {**ctx, "tool_available": "supermath"})
            got_b = self.v._parse_model_answer(resp_b.answer_str, truth)
            status_b = "pass" if got_b == expected else "fail"
            if resp_b.action in ("refuse", "ask_clarification"):
                status_b = "refused"
                tool_refused += 1
            tool_total += 1
            if status_b == "pass":
                tool_pass += 1
            per_case.append(LaneResult(
                lane="model_plus_tool", problem_id=pid, family=family.id,
                model_action=resp_b.action, model_answer_str=resp_b.answer_str,
                verifier_status=status_b, final_answer_str=resp_b.answer_str,
                overridden=False, note=resp_b.note))

            # Lane C: DTL verified (verifier is final authority)
            resp_c = self.tool.respond(problem, {**ctx, "tool_available": "supermath",
                                                 "verify_mode": True})
            got_c = self.v._parse_model_answer(resp_c.answer_str, truth)
            overridden = (got_c != expected)
            if overridden:
                # verifier overrides the model -- final answer is the truth
                final = truth.display()
                status_c = "pass"
                overrides += 1
            else:
                final = resp_c.answer_str
                status_c = "pass" if got_c == expected else "fail"
            dtl_total += 1
            if status_c == "pass":
                dtl_pass += 1
            per_case.append(LaneResult(
                lane="dtl_verified", problem_id=pid, family=family.id,
                model_action=resp_c.action, model_answer_str=resp_c.answer_str,
                verifier_status=status_c, final_answer_str=final,
                overridden=overridden,
                note="verifier-overrode-model" if overridden else resp_c.note))

        def _lane_summary(passed, total, refused):
            if total == 0:
                return {"score": None, "passed": 0, "total": 0, "refused": 0,
                        "status": "not_run"}
            return {"score": passed / total, "passed": passed, "total": total,
                    "refused": refused, "status": "ran"}

        return DuelReport(
            n_cases=len(problems),
            raw_model=_lane_summary(raw_pass, raw_total, raw_refused),
            model_plus_tool=_lane_summary(tool_pass, tool_total, tool_refused),
            dtl_verified=_lane_summary(dtl_pass, dtl_total, 0),
            overrides_applied=overrides,
            per_case=per_case,
        )
