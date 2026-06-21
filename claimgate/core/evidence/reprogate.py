"""ReproGate v0: compare an evidence pack against a rerun result.

Given an original EvidencePack and a rerun EvidencePack (or rerun result),
ReproGate compares:
  * normalized input
  * gate name
  * gate version
  * verifier version
  * seed
  * status
  * certificate hash
  * result body (where applicable)
  * contamination status

Output (one of the 9 EvidencePack statuses):
  * REPRODUCIBLE              -- all required fields match
  * DRIFT_DETECTED            -- same input/gate/version produces different
                                 status, certificate, or result body
  * UNVERIFIABLE_ARTIFACT     -- required fields missing
  * CONTAMINATED_BY_MODEL     -- AI-assisted cases used for leaderboard/holdout
  * MISSING_SEED              -- deterministic replay requires seed and it's missing
  * MISSING_CODE_HASH         -- reproducibility requires code identity and it's missing
  * MISSING_DATA_HASH         -- data-backed claim lacks data identity
  * MISSING_REPRO_COMMAND     -- no replay command supplied
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .model import EvidencePack, _canonical_json


@dataclass
class ReproResult:
    verdict: str
    matched_fields: List[str] = field(default_factory=list)
    mismatched_fields: List[str] = field(default_factory=list)
    missing_fields: List[str] = field(default_factory=list)
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "verdict": self.verdict,
            "matched_fields": self.matched_fields,
            "mismatched_fields": self.mismatched_fields,
            "missing_fields": self.missing_fields,
            "note": self.note,
        }


class ReproGate:
    """Compare an original pack against a rerun pack."""

    def compare(self, original: EvidencePack, rerun: EvidencePack,
                leaderboard_use: bool = False) -> ReproResult:
        """Compare two evidence packs.

        Args:
            original: the pack from the first run
            rerun: the pack from the replay run
            leaderboard_use: if True, AI-assisted contamination -> CONTAMINATED_BY_MODEL

        Returns:
            ReproResult with verdict + field-level details
        """
        matched = []
        mismatched = []
        missing = []

        # --- unsupported artifact check (empty cert hash or no result body
        # on EITHER pack means the artifact cannot be verified) ---
        if (not original.certificate_hash or not rerun.certificate_hash
                or original.result_body is None or rerun.result_body is None):
            missing.append("certificate_hash_or_result_body")
            return ReproResult("UNVERIFIABLE_ARTIFACT", matched, mismatched, missing,
                               "artifact lacks certificate hash or result body; cannot be verified")

        # --- structural completeness checks (short-circuit on missing) ---
        if not original.repro_command or not rerun.repro_command:
            missing.append("repro_command")
            return ReproResult("MISSING_REPRO_COMMAND", matched, mismatched, missing,
                               "no replay command supplied")
        if original.seed is None or rerun.seed is None:
            missing.append("seed")
            return ReproResult("MISSING_SEED", matched, mismatched, missing,
                               "deterministic replay requires a seed")
        if original.code_hash is None or rerun.code_hash is None:
            missing.append("code_hash")
            return ReproResult("MISSING_CODE_HASH", matched, mismatched, missing,
                               "reproducibility requires code identity")
        if (original._data_backed or rerun._data_backed) and (
                original.data_hash is None or rerun.data_hash is None):
            missing.append("data_hash")
            return ReproResult("MISSING_DATA_HASH", matched, mismatched, missing,
                               "data-backed claim lacks data identity")

        # --- contamination check ---
        if leaderboard_use:
            for pack in (original, rerun):
                if pack.contamination_status in ("ai_assisted_build", "ai_assisted_holdout"):
                    return ReproResult("CONTAMINATED_BY_MODEL", matched, mismatched, missing,
                                       f"AI-assisted case ({pack.contamination_status}) "
                                       f"used for leaderboard/holdout claim")

        # --- field-by-field comparison ---
        # 1. normalized input
        if original.normalized_input == rerun.normalized_input:
            matched.append("normalized_input")
        else:
            mismatched.append("normalized_input")

        # 2. gate name
        if original.gate_name == rerun.gate_name:
            matched.append("gate_name")
        else:
            mismatched.append("gate_name")

        # 3. gate version
        if original.gate_version == rerun.gate_version:
            matched.append("gate_version")
        else:
            mismatched.append("gate_version")

        # 4. verifier version
        if original.verifier_version == rerun.verifier_version:
            matched.append("verifier_version")
        else:
            mismatched.append("verifier_version")

        # 5. seed
        if original.seed == rerun.seed:
            matched.append("seed")
        else:
            mismatched.append("seed")

        # 6. status (the gate's own status)
        if original.status == rerun.status:
            matched.append("status")
        else:
            mismatched.append("status")

        # 7. certificate hash
        if original.certificate_hash == rerun.certificate_hash:
            matched.append("certificate_hash")
        else:
            mismatched.append("certificate_hash")

        # 8. result body (canonical comparison)
        orig_body = _canonical_json(original.result_body) if original.result_body is not None else ""
        rerun_body = _canonical_json(rerun.result_body) if rerun.result_body is not None else ""
        if orig_body == rerun_body:
            matched.append("result_body")
        else:
            mismatched.append("result_body")

        # 9. contamination status
        if original.contamination_status == rerun.contamination_status:
            matched.append("contamination_status")
        else:
            mismatched.append("contamination_status")

        # --- verdict ---
        if mismatched:
            return ReproResult("DRIFT_DETECTED", matched, mismatched, missing,
                               f"drift in fields: {mismatched}")
        return ReproResult("REPRODUCIBLE", matched, mismatched, missing,
                           f"all {len(matched)} required fields match")


__all__ = ["ReproGate", "ReproResult"]
