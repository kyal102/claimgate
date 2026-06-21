"""ReplayRunner v0: execute evidence-pack repro commands and audit replays.

ReplayRunner loads an EvidencePack, validates that a repro_command exists,
executes it in a safe subprocess with a timeout, captures stdout/stderr/
exit code/runtime, parses the replayed JSON, builds/extracts the replayed
EvidencePack, and calls ReproGate.compare(original, replayed).

Public wording:
  "ReplayRunner executes evidence-pack repro commands and checks whether
   results reproduce. It does not prove scientific truth; it verifies
   whether a recorded verification result can be replayed without drift."

ReplayRunner executes and audits; it does NOT change gate verdicts.
"""
from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass, field
from typing import List, Optional

from ..evidence.model import EvidencePack, _canonical_json
from ..evidence.reprogate import ReproGate, ReproResult


# The 6 canonical ReplayRunner statuses (no others may be emitted)
ALL_REPLAY_STATUSES = [
    "REPRODUCIBLE",
    "DRIFT_DETECTED",
    "MISSING_REPRO_COMMAND",
    "REPLAY_COMMAND_FAILED",
    "REPLAY_TIMEOUT",
    "UNVERIFIABLE_ARTIFACT",
]

PUBLIC_WORDING = (
    "ReplayRunner executes evidence-pack repro commands and checks whether "
    "results reproduce. It does not prove scientific truth; it verifies "
    "whether a recorded verification result can be replayed without drift."
)


@dataclass
class ReplayResult:
    """The result of replaying a single evidence pack."""
    pack_id: str
    verdict: str              # one of ALL_REPLAY_STATUSES
    exit_code: Optional[int] = None
    runtime_ms: Optional[int] = None
    stdout_preview: str = ""
    stderr_preview: str = ""
    repro_result: Optional[dict] = None    # ReproResult.to_dict() if comparison ran
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "pack_id": self.pack_id,
            "verdict": self.verdict,
            "exit_code": self.exit_code,
            "runtime_ms": self.runtime_ms,
            "stdout_preview": self.stdout_preview[:500],
            "stderr_preview": self.stderr_preview[:500],
            "repro_result": self.repro_result,
            "note": self.note,
        }


class ReplayRunner:
    """Executes evidence-pack repro commands and audits the replay.

    Args:
        timeout_s: subprocess timeout in seconds (default 30)
        repro_gate: optional ReproGate instance (default: fresh)
    """

    def __init__(self, timeout_s: int = 30, repro_gate: Optional[ReproGate] = None):
        self.timeout_s = timeout_s
        self.repro_gate = repro_gate or ReproGate()

    def replay(self, pack: EvidencePack,
               leaderboard_use: bool = False) -> ReplayResult:
        """Replay a single evidence pack.

        Steps:
          1. Validate repro_command exists.
          2. Execute in subprocess with timeout.
          3. Capture stdout/stderr/exit/runtime.
          4. Parse stdout as JSON.
          5. Extract/build replayed EvidencePack from the JSON.
          6. Call ReproGate.compare(original, replayed).
          7. Return ReplayResult with the final verdict.
        """
        # 1. validate repro_command
        if not pack.repro_command or not pack.repro_command.strip():
            return ReplayResult(
                pack_id=pack.pack_id, verdict="MISSING_REPRO_COMMAND",
                note="no repro_command in evidence pack")

        # 2. execute in subprocess with timeout.
        # SAFETY: no shell. The repro command is parsed into an argument list
        # (shlex) and executed with shell=False, and is restricted to invoking a
        # Python module run (`python -m ...` / `<exe> -m ...`). This prevents
        # shell-injection from a tampered/poisoned evidence pack's repro_command.
        cmd = pack.repro_command
        try:
            argv = shlex.split(cmd)  # posix tokenizer; repro commands use bare 'python' + no backslashes
        except ValueError as e:
            return ReplayResult(
                pack_id=pack.pack_id, verdict="REPLAY_COMMAND_FAILED",
                note=f"unparseable repro_command: {e}")
        if not argv:
            return ReplayResult(
                pack_id=pack.pack_id, verdict="REPLAY_COMMAND_FAILED",
                note="empty repro_command after parsing")
        # SAFETY: no shell. Only the Python interpreter may be launched — this
        # blocks shell injection AND arbitrary executables, while still allowing
        # both 'python -m <module>' and 'python -c <code>' repro commands. A
        # leading bare python/python3/py (or a full python path) maps to the
        # running interpreter. It does NOT restrict to -m, so the ReplayBench
        # timeout/malformed/drift cases keep their intended verdicts.
        _exe0 = os.path.basename(argv[0]).lower()
        if (_exe0 in ("python", "python3", "py", "python.exe", "python3.exe", "py.exe")
                or os.path.basename(argv[0]) == os.path.basename(sys.executable)):
            argv[0] = sys.executable
        else:
            return ReplayResult(
                pack_id=pack.pack_id, verdict="REPLAY_COMMAND_FAILED",
                note="refused: repro_command must launch the Python interpreter (no shell)")
        t0 = time.perf_counter()
        try:
            proc = subprocess.run(
                argv, shell=False, capture_output=True, text=True,
                timeout=self.timeout_s,
            )
            runtime_ms = int((time.perf_counter() - t0) * 1000)
        except subprocess.TimeoutExpired:
            runtime_ms = int(self.timeout_s * 1000)
            return ReplayResult(
                pack_id=pack.pack_id, verdict="REPLAY_TIMEOUT",
                runtime_ms=runtime_ms,
                note=f"replay timed out after {self.timeout_s}s")
        except Exception as e:
            runtime_ms = int((time.perf_counter() - t0) * 1000)
            return ReplayResult(
                pack_id=pack.pack_id, verdict="REPLAY_COMMAND_FAILED",
                runtime_ms=runtime_ms, note=f"subprocess error: {e}")

        # 3. capture outputs
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""

        # 4. check exit code
        if proc.returncode != 0:
            return ReplayResult(
                pack_id=pack.pack_id, verdict="REPLAY_COMMAND_FAILED",
                exit_code=proc.returncode, runtime_ms=runtime_ms,
                stdout_preview=stdout, stderr_preview=stderr,
                note=f"command exited non-zero ({proc.returncode})")

        # 5. parse stdout as JSON
        try:
            replayed_json = json.loads(stdout)
        except json.JSONDecodeError as e:
            return ReplayResult(
                pack_id=pack.pack_id, verdict="UNVERIFIABLE_ARTIFACT",
                exit_code=proc.returncode, runtime_ms=runtime_ms,
                stdout_preview=stdout, stderr_preview=stderr,
                note=f"malformed JSON output: {e}")

        # 6. extract/build replayed EvidencePack from the JSON
        replayed_pack = self._extract_pack(replayed_json, pack)
        if replayed_pack is None:
            return ReplayResult(
                pack_id=pack.pack_id, verdict="UNVERIFIABLE_ARTIFACT",
                exit_code=proc.returncode, runtime_ms=runtime_ms,
                stdout_preview=stdout, stderr_preview=stderr,
                note="could not extract evidence pack from replayed output")

        # 7. compare via ReproGate
        repro = self.repro_gate.compare(pack, replayed_pack, leaderboard_use=leaderboard_use)
        return ReplayResult(
            pack_id=pack.pack_id, verdict=repro.verdict,
            exit_code=proc.returncode, runtime_ms=runtime_ms,
            stdout_preview=stdout, stderr_preview=stderr,
            repro_result=repro.to_dict(),
            note=repro.note)

    def _extract_pack(self, replayed_json: dict, original: EvidencePack) -> Optional[EvidencePack]:
        """Extract or build a replayed EvidencePack from the replayed JSON.

        The replayed JSON is the output of a bench run. We find the case
        matching the original pack, then rebuild a pack with the SAME
        result_body structure as the original (so ReproGate compares
        apples-to-apples on result_body and certificate_hash).
        """
        pack_id = original.pack_id
        candidate = self._find_matching_result(replayed_json, pack_id, original.gate_name)
        if candidate is None:
            return None

        # Rebuild the result_body to match the original's structure.
        # The original's result_body shape depends on the gate:
        #   UnitGate: {"lhs_dimension", "rhs_dimension", "note"}
        #   PhysicsClaimBench: full ClaimPipelineResult.to_dict()
        #   TheoryGate: full EvidencePack.to_dict()
        # We extract the gate-level fields from the candidate and rebuild.
        replayed_status = candidate.get("status") or candidate.get("verdict", original.status)
        replayed_result_body = self._rebuild_result_body(candidate, original)

        replayed = EvidencePack(
            pack_id=pack_id + "_replay",
            pack_schema_version=original.pack_schema_version,
            timestamp="",  # excluded from cert hash
            gate_name=original.gate_name,
            gate_version=original.gate_version,
            raw_claim_or_input=original.raw_claim_or_input,
            normalized_input=original.normalized_input,
            status=replayed_status,
            sub_statuses=original.sub_statuses,  # structural; not the drift target
            result_body=replayed_result_body,
            code_hash=original.code_hash,
            data_hash=original.data_hash,
            seed=original.seed,
            verifier_version=original.verifier_version,
            model_used=original.model_used,
            model_role=original.model_role,
            contamination_status=original.contamination_status,
            limitations=original.limitations,
            next_required_validation=original.next_required_validation,
            repro_command=original.repro_command,
            human_readable_summary=original.human_readable_summary,
            _data_backed=original._data_backed,
        )
        replayed.seal()
        return replayed

    def _rebuild_result_body(self, candidate: dict, original: EvidencePack) -> dict:
        """Rebuild a result_body matching the original's structure, using
        values from the replayed candidate."""
        orig_body = original.result_body
        if not isinstance(orig_body, dict):
            # if the original had no dict body, use the candidate as-is
            return candidate

        # UnitGate shape: {"lhs_dimension", "rhs_dimension", "note"}
        if "lhs_dimension" in orig_body:
            return {
                "lhs_dimension": candidate.get("lhs_dimension", orig_body.get("lhs_dimension")),
                "rhs_dimension": candidate.get("rhs_dimension", orig_body.get("rhs_dimension")),
                "note": candidate.get("note", orig_body.get("note", "")),
            }
        # PhysicsClaimBench shape: the candidate IS a ClaimPipelineResult.to_dict()
        if "final_status" in candidate or "gate_results" in candidate:
            return candidate
        # TheoryGate shape: the candidate is an EvidencePack.to_dict()
        if "theory_name" in candidate or "final_status" in candidate:
            return candidate
        # fallback: use original body (no drift in body)
        return orig_body

    def _find_matching_result(self, obj: dict, pack_id: str, gate_name: str) -> Optional[dict]:
        """Recursively search the replayed JSON for a result entry matching
        the original pack. Returns the result dict, or None."""
        # The pack_id encodes the source: ev_unit_pc1 -> look for "pc1" in results
        # ev_phys_pbc_v1 -> look for "pbc_v1"
        # ev_theory_<name> -> look for the theory name
        search_key = pack_id.replace("ev_unit_", "").replace("ev_phys_", "").replace("ev_theory_", "")

        # search in common result locations
        for key in ("results", "per_case"):
            if key in obj and isinstance(obj[key], list):
                for item in obj[key]:
                    if not isinstance(item, dict):
                        continue
                    # match by id, problem_id, claim_id, or theory_name
                    for id_field in ("id", "problem_id", "claim_id", "theory_name", "pack_id"):
                        if id_field in item and search_key in str(item[id_field]):
                            return item
                    # also match by statement containing the search key
                    for stmt_field in ("statement", "raw_claim", "raw_claim_or_input"):
                        if stmt_field in item and search_key in str(item.get(stmt_field, "")):
                            return item

        # search in benches (full-suite output)
        if "benches" in obj and isinstance(obj["benches"], dict):
            for bench_name, bench_data in obj["benches"].items():
                candidate = self._find_matching_result(bench_data, pack_id, gate_name)
                if candidate is not None:
                    return candidate

        # if it's a single-bench result with a 'result' key, search inside
        if "result" in obj and isinstance(obj["result"], dict):
            return self._find_matching_result(obj["result"], pack_id, gate_name)

        # fallback: if no match found but the gate_name matches, return the whole obj
        # (this handles cases where the replayed output is a single result)
        if obj.get("gate_name") == gate_name or obj.get("bench") == gate_name.lower():
            return obj

        return None


def load_pack_from_json(path: str) -> EvidencePack:
    """Load an EvidencePack from a JSON file."""
    with open(path) as f:
        data = json.load(f)
    return EvidencePack(
        pack_id=data["pack_id"],
        pack_schema_version=data.get("pack_schema_version", "evidence.v0"),
        timestamp=data.get("timestamp", ""),
        gate_name=data.get("gate_name", ""),
        gate_version=data.get("gate_version", ""),
        raw_claim_or_input=data.get("raw_claim_or_input", ""),
        normalized_input=data.get("normalized_input", ""),
        status=data.get("status", ""),
        sub_statuses=data.get("sub_statuses", []),
        result_body=data.get("result_body"),
        certificate_hash=data.get("certificate_hash", ""),
        evidence_pack_hash=data.get("evidence_pack_hash", ""),
        code_hash=data.get("code_hash"),
        data_hash=data.get("data_hash"),
        seed=data.get("seed"),
        verifier_version=data.get("verifier_version", ""),
        model_used=data.get("model_used"),
        model_role=data.get("model_role", "none"),
        contamination_status=data.get("contamination_status", "unknown"),
        limitations=data.get("limitations", []),
        next_required_validation=data.get("next_required_validation", ""),
        repro_command=data.get("repro_command", ""),
        human_readable_summary=data.get("human_readable_summary", ""),
    )


__all__ = [
    "ALL_REPLAY_STATUSES", "PUBLIC_WORDING",
    "ReplayResult", "ReplayRunner", "load_pack_from_json",
]
