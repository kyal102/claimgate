"""ReproBench v0: 10 cases testing ReproGate's detection capabilities.

Cases:
 1. same input, same certificate -> REPRODUCIBLE
 2. same input, different certificate -> DRIFT_DETECTED
 3. missing seed -> MISSING_SEED
 4. missing code hash -> MISSING_CODE_HASH
 5. missing repro command -> MISSING_REPRO_COMMAND
 6. AI-assisted holdout used for leaderboard -> CONTAMINATED_BY_MODEL
 7. missing data hash for data-backed claim -> MISSING_DATA_HASH
 8. unsupported artifact -> UNVERIFIABLE_ARTIFACT
 9. same raw input, different formatting, same normalized input -> REPRODUCIBLE
10. same pack but changed gate version -> DRIFT_DETECTED (version mismatch)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .model import EvidencePack, now_iso
from .reprogate import ReproGate, ReproResult
from .builder import VERIFIER_VERSION, GATE_VERSION


@dataclass
class ReproCase:
    id: str
    description: str
    original: EvidencePack
    rerun: EvidencePack
    leaderboard_use: bool
    expected_verdict: str
    why: str


def _make_pack(pack_id: str, gate_name: str = "UnitGate",
               status: str = "DIMENSIONALLY_VALID",
               normalized_input: str = "force|mul:mass|mul:acceleration",
               seed: Optional[int] = 20260624,
               code_hash: Optional[str] = "abc123code",
               data_hash: Optional[str] = None,
               repro_command: str = "python -m proofbench_x run --physics --bench unitgate --json",
               contamination: str = "clean",
               gate_version: str = GATE_VERSION,
               verifier_version: str = VERIFIER_VERSION,
               result_body: dict = None,
               data_backed: bool = False,
               cert_hash: Optional[str] = None,  # if None, computed by seal()
               raw_claim_or_input: str = "F = m * a",
               ) -> EvidencePack:
    """Helper to build a pack with sensible defaults."""
    pack = EvidencePack(
        pack_id=pack_id,
        timestamp=now_iso(),
        gate_name=gate_name,
        gate_version=gate_version,
        raw_claim_or_input=raw_claim_or_input,
        normalized_input=normalized_input,
        status=status,
        sub_statuses=[],
        result_body=result_body or {"lhs_dimension": "M*L*T^-2", "rhs_dimension": "M*L*T^-2"},
        code_hash=code_hash,
        data_hash=data_hash,
        seed=seed,
        verifier_version=verifier_version,
        model_used=None,
        model_role="none",
        contamination_status=contamination,
        limitations=["test limitation"],
        next_required_validation="test next step",
        repro_command=repro_command,
        human_readable_summary="test summary",
        _data_backed=data_backed,
    )
    pack.seal()
    if cert_hash is not None:
        # override the computed cert hash (for drift test cases)
        pack.certificate_hash = cert_hash
    return pack


def _build_cases() -> list:
    cases = []

    # 1. REPRODUCIBLE
    orig = _make_pack("rb1_orig")
    rerun = _make_pack("rb1_rerun")
    cases.append(ReproCase("rb1", "same input, same certificate -> REPRODUCIBLE",
                           orig, rerun, leaderboard_use=False,
                           expected_verdict="REPRODUCIBLE",
                           why="identical packs should reproduce"))

    # 2. DRIFT_DETECTED (different certificate hash)
    orig = _make_pack("rb2_orig")
    rerun = _make_pack("rb2_rerun", cert_hash="different_hash_on_purpose")
    cases.append(ReproCase("rb2", "same input, different certificate -> DRIFT_DETECTED",
                           orig, rerun, leaderboard_use=False,
                           expected_verdict="DRIFT_DETECTED",
                           why="certificate hash mismatch indicates drift"))

    # 3. MISSING_SEED
    orig = _make_pack("rb3_orig", seed=None)
    rerun = _make_pack("rb3_rerun", seed=None)
    cases.append(ReproCase("rb3", "missing seed -> MISSING_SEED",
                           orig, rerun, leaderboard_use=False,
                           expected_verdict="MISSING_SEED",
                           why="deterministic replay requires a seed"))

    # 4. MISSING_CODE_HASH
    orig = _make_pack("rb4_orig", code_hash=None)
    rerun = _make_pack("rb4_rerun", code_hash=None)
    cases.append(ReproCase("rb4", "missing code hash -> MISSING_CODE_HASH",
                           orig, rerun, leaderboard_use=False,
                           expected_verdict="MISSING_CODE_HASH",
                           why="reproducibility requires code identity"))

    # 5. MISSING_REPRO_COMMAND
    orig = _make_pack("rb5_orig", repro_command="")
    rerun = _make_pack("rb5_rerun", repro_command="")
    cases.append(ReproCase("rb5", "missing repro command -> MISSING_REPRO_COMMAND",
                           orig, rerun, leaderboard_use=False,
                           expected_verdict="MISSING_REPRO_COMMAND",
                           why="no replay command supplied"))

    # 6. CONTAMINATED_BY_MODEL
    orig = _make_pack("rb6_orig", contamination="ai_assisted_holdout")
    rerun = _make_pack("rb6_rerun", contamination="ai_assisted_holdout")
    cases.append(ReproCase("rb6", "AI-assisted holdout used for leaderboard -> CONTAMINATED_BY_MODEL",
                           orig, rerun, leaderboard_use=True,
                           expected_verdict="CONTAMINATED_BY_MODEL",
                           why="AI-assisted cases not valid for leaderboard/holdout claims"))

    # 7. MISSING_DATA_HASH (data-backed claim without data_hash)
    orig = _make_pack("rb7_orig", data_backed=True, data_hash=None)
    rerun = _make_pack("rb7_rerun", data_backed=True, data_hash=None)
    cases.append(ReproCase("rb7", "missing data hash for data-backed claim -> MISSING_DATA_HASH",
                           orig, rerun, leaderboard_use=False,
                           expected_verdict="MISSING_DATA_HASH",
                           why="data-backed claim lacks data identity"))

    # 8. UNVERIFIABLE_ARTIFACT (missing result body and cert hash -> cannot verify)
    orig = _make_pack("rb8_orig")
    orig.result_body = None
    orig.certificate_hash = ""
    rerun = _make_pack("rb8_rerun")
    rerun.result_body = None
    rerun.certificate_hash = ""
    cases.append(ReproCase("rb8", "unsupported artifact -> UNVERIFIABLE_ARTIFACT",
                           orig, rerun, leaderboard_use=False,
                           expected_verdict="UNVERIFIABLE_ARTIFACT",
                           why="artifact lacks result body and cert hash; cannot be verified"))

    # 9. REPRODUCIBLE with formatting variation (same normalized input)
    orig = _make_pack("rb9_orig", raw_claim_or_input="F = m*a")
    rerun = _make_pack("rb9_rerun", raw_claim_or_input="F=m*a  (spaced differently)")
    # both have the SAME normalized_input, so should reproduce
    cases.append(ReproCase("rb9", "same raw input with different formatting, same normalized input -> REPRODUCIBLE",
                           orig, rerun, leaderboard_use=False,
                           expected_verdict="REPRODUCIBLE",
                           why="normalized input is equivalent despite formatting differences"))

    # 10. DRIFT_DETECTED (gate version mismatch)
    orig = _make_pack("rb10_orig", gate_version="v0")
    rerun = _make_pack("rb10_rerun", gate_version="v1")  # different version
    cases.append(ReproCase("rb10", "same pack but changed gate version -> DRIFT_DETECTED",
                           orig, rerun, leaderboard_use=False,
                           expected_verdict="DRIFT_DETECTED",
                           why="gate version mismatch is a form of drift"))

    return cases


REPRO_CASES = _build_cases()


def run_reprobench(seed: int = 20260626, model=None) -> dict:
    gate = ReproGate()
    results = []
    for case in REPRO_CASES:
        r = gate.compare(case.original, case.rerun, leaderboard_use=case.leaderboard_use)
        d = r.to_dict()
        d["id"] = case.id
        d["description"] = case.description
        d["expected_verdict"] = case.expected_verdict
        d["self_consistent"] = (r.verdict == case.expected_verdict)
        d["why"] = case.why
        results.append(d)
    passed = sum(1 for r in results if r["self_consistent"])
    score = {
        "name": "Repro Bench Score",
        "value": passed / len(results) if results else 0.0,
        "n": len(results),
        "detail": f"{passed}/{len(results)} repro cases correct",
    }
    status_tally = {}
    for r in results:
        s = r["verdict"]
        status_tally[s] = status_tally.get(s, 0) + 1
    return {
        "bench": "reprobench",
        "mode": "ReproBench v0 (reproducibility + drift + contamination detection)",
        "seed": seed, "n_cases": len(results),
        "status_tally": status_tally,
        "results": results, "score": score,
    }


__all__ = ["ReproCase", "REPRO_CASES", "run_reprobench"]
