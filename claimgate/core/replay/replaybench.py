"""ReplayBench v0: 7 cases testing ReplayRunner's detection capabilities.

Cases:
 1. valid UnitGate evidence pack replay -> REPRODUCIBLE
 2. valid PhysicsClaimBench evidence pack replay -> REPRODUCIBLE
 3. missing repro command -> MISSING_REPRO_COMMAND
 4. command exits non-zero -> REPLAY_COMMAND_FAILED
 5. command times out -> REPLAY_TIMEOUT
 6. command returns malformed JSON -> UNVERIFIABLE_ARTIFACT
 7. command returns changed certificate -> DRIFT_DETECTED
"""
from __future__ import annotations

import os
import sys
import tempfile
from dataclasses import dataclass
from typing import Optional

from .runner import ReplayRunner, ReplayResult, ALL_REPLAY_STATUSES
from ..evidence.model import EvidencePack, now_iso
from ..evidence.builder import (
    build_from_unitgate_claim, build_from_physics_claim,
    VERIFIER_VERSION, GATE_VERSION,
)
from ..physics.unitgate import CLAIMS as UNIT_CLAIMS
from ..physics.bench_claims import BENCH_CLAIMS as PHYSICS_BENCH_CLAIMS


@dataclass
class ReplayCase:
    id: str
    description: str
    pack: EvidencePack
    expected_verdict: str
    why: str
    # optional: override the runner's timeout for this case
    timeout_s: Optional[int] = None


def _py_emit(text: str) -> str:
    """A shell-free repro_command that writes ``text`` to stdout via the Python
    interpreter. base64 keeps the payload free of quotes/backslashes/shell
    metacharacters so it survives arg-list (shell=False) execution unchanged."""
    import base64
    b64 = base64.b64encode(text.encode("utf-8")).decode("ascii")
    return f"python -c \"import base64,sys;sys.stdout.write(base64.b64decode('{b64}').decode())\""


def _make_malformed_pack() -> tuple:
    """Create a pack whose repro_command writes malformed JSON to stdout."""
    # shell-free: emit malformed (unparseable) JSON via the python interpreter
    script = _py_emit("{not valid json")
    pack = EvidencePack(
        pack_id="rb_malformed",
        timestamp=now_iso(),
        gate_name="UnitGate",
        gate_version=GATE_VERSION,
        raw_claim_or_input="malformed test",
        normalized_input="malformed|test",
        status="DIMENSIONALLY_VALID",
        result_body={"test": True},
        code_hash="abc123",
        seed=20260624,
        verifier_version=VERIFIER_VERSION,
        repro_command=script,
        human_readable_summary="malformed output test",
    )
    pack.seal()
    return pack


def _make_failing_pack() -> EvidencePack:
    """Create a pack whose repro_command exits non-zero."""
    pack = EvidencePack(
        pack_id="rb_failing",
        timestamp=now_iso(),
        gate_name="UnitGate",
        gate_version=GATE_VERSION,
        raw_claim_or_input="failing test",
        normalized_input="failing|test",
        status="DIMENSIONALLY_VALID",
        result_body={"test": True},
        code_hash="abc123",
        seed=20260624,
        verifier_version=VERIFIER_VERSION,
        repro_command='python -c "import sys;sys.exit(1)"',
        human_readable_summary="failing command test",
    )
    pack.seal()
    return pack


def _make_timeout_pack() -> EvidencePack:
    """Create a pack whose repro_command sleeps longer than the timeout."""
    pack = EvidencePack(
        pack_id="rb_timeout",
        timestamp=now_iso(),
        gate_name="UnitGate",
        gate_version=GATE_VERSION,
        raw_claim_or_input="timeout test",
        normalized_input="timeout|test",
        status="DIMENSIONALLY_VALID",
        result_body={"test": True},
        code_hash="abc123",
        seed=20260624,
        verifier_version=VERIFIER_VERSION,
        repro_command='python -c "import time;time.sleep(10)"',
        human_readable_summary="timeout test",
    )
    pack.seal()
    return pack


def _make_drift_pack() -> tuple:
    """Create a pack whose repro_command produces a DIFFERENT certificate.
    We do this by having the repro_command echo a JSON with a different result_body,
    which causes a different certificate_hash."""
    # The original pack claims DIMENSIONALLY_VALID for F=m*a
    # The replayed JSON will claim DIMENSIONALLY_INVALID (drift)
    drift_json = json_dumps({
        "pack_id": "drift_test",
        "gate_name": "UnitGate",
        "gate_version": GATE_VERSION,
        "status": "DIMENSIONALLY_INVALID",  # CHANGED -- drift
        "results": [{
            "id": "pc1_drift",
            "statement": "F = m * a (drifted)",
            "status": "DIMENSIONALLY_INVALID",
            "verdict": "DIMENSIONALLY_INVALID",
            "result_body": {"lhs_dimension": "M*L*T^-2", "rhs_dimension": "M*L*T^-1"},
        }],
    })
    pack = EvidencePack(
        pack_id="ev_unit_pc1_drift",
        timestamp=now_iso(),
        gate_name="UnitGate",
        gate_version=GATE_VERSION,
        raw_claim_or_input="F = m * a (Newton's 2nd law)",
        normalized_input="force|mul:mass|mul:acceleration",
        status="DIMENSIONALLY_VALID",
        result_body={"lhs_dimension": "M*L*T^-2", "rhs_dimension": "M*L*T^-2"},
        code_hash="abc123",
        seed=20260624,
        verifier_version=VERIFIER_VERSION,
        repro_command=_py_emit(drift_json),
        human_readable_summary="drift test",
    )
    pack.seal()
    return pack


def json_dumps(obj) -> str:
    # Clean JSON (no shell escaping): the drift payload is emitted via _py_emit,
    # which base64-encodes it for shell-free arg-list execution.
    import json
    return json.dumps(obj, default=str)


def _build_cases() -> list:
    cases = []

    # 1. valid UnitGate pack replay -> REPRODUCIBLE
    # Use the actual unitgate bench command so the replay produces real output
    pack1 = build_from_unitgate_claim(UNIT_CLAIMS[0], seed=20260624, code_hash="prototype_evidence_v0")
    # override the repro_command to target the specific bench
    pack1.repro_command = (
        "python -m claimgate run --physics --bench unitgate --json --seed 20260624"
    )
    cases.append(ReplayCase("rlb1", "valid UnitGate evidence pack replay -> REPRODUCIBLE",
                            pack1, "REPRODUCIBLE",
                            "replaying the unitgate bench should reproduce the same certificate"))

    # 2. valid PhysicsClaimBench pack replay -> REPRODUCIBLE
    pack2 = build_from_physics_claim(PHYSICS_BENCH_CLAIMS[0], seed=20260624, code_hash="prototype_evidence_v0")
    pack2.repro_command = (
        "python -m claimgate run --physics --bench physicsclaim --json --seed 20260624"
    )
    cases.append(ReplayCase("rlb2", "valid PhysicsClaimBench evidence pack replay -> REPRODUCIBLE",
                            pack2, "REPRODUCIBLE",
                            "replaying the physicsclaim bench should reproduce the same certificate"))

    # 3. missing repro command -> MISSING_REPRO_COMMAND
    pack3 = build_from_unitgate_claim(UNIT_CLAIMS[0], seed=20260624, code_hash="prototype_evidence_v0")
    pack3.repro_command = ""
    cases.append(ReplayCase("rlb3", "missing repro command -> MISSING_REPRO_COMMAND",
                            pack3, "MISSING_REPRO_COMMAND",
                            "pack with empty repro_command should be refused"))

    # 4. command exits non-zero -> REPLAY_COMMAND_FAILED
    pack4 = _make_failing_pack()
    cases.append(ReplayCase("rlb4", "command exits non-zero -> REPLAY_COMMAND_FAILED",
                            pack4, "REPLAY_COMMAND_FAILED",
                            "repro_command 'exit 1' should fail"))

    # 5. command times out -> REPLAY_TIMEOUT
    pack5 = _make_timeout_pack()
    cases.append(ReplayCase("rlb5", "command times out -> REPLAY_TIMEOUT",
                            pack5, "REPLAY_TIMEOUT",
                            "repro_command 'sleep 10' should time out",
                            timeout_s=1))

    # 6. command returns malformed JSON -> UNVERIFIABLE_ARTIFACT
    pack6 = _make_malformed_pack()
    cases.append(ReplayCase("rlb6", "command returns malformed JSON -> UNVERIFIABLE_ARTIFACT",
                            pack6, "UNVERIFIABLE_ARTIFACT",
                            "malformed JSON output cannot be parsed"))

    # 7. command returns changed certificate -> DRIFT_DETECTED
    pack7 = _make_drift_pack()
    cases.append(ReplayCase("rlb7", "command returns changed certificate -> DRIFT_DETECTED",
                            pack7, "DRIFT_DETECTED",
                            "replayed status differs from original -> drift"))

    return cases


REPLAY_CASES = _build_cases()


def run_replaybench(seed: int = 20260627, model=None) -> dict:
    results = []
    for case in REPLAY_CASES:
        runner = ReplayRunner(timeout_s=case.timeout_s or 30)
        r = runner.replay(case.pack)
        d = r.to_dict()
        d["id"] = case.id
        d["description"] = case.description
        d["expected_verdict"] = case.expected_verdict
        d["self_consistent"] = (r.verdict == case.expected_verdict)
        d["why"] = case.why
        results.append(d)
    passed = sum(1 for r in results if r["self_consistent"])
    score = {
        "name": "Replay Bench Score",
        "value": passed / len(results) if results else 0.0,
        "n": len(results),
        "detail": f"{passed}/{len(results)} replay cases correct",
    }
    status_tally = {}
    for r in results:
        s = r["verdict"]
        status_tally[s] = status_tally.get(s, 0) + 1
    return {
        "bench": "replaybench",
        "mode": "ReplayBench v0 (execute + audit evidence-pack replays)",
        "public_wording": __import__("claimgate.core.replay.runner",
                                     fromlist=["PUBLIC_WORDING"]).PUBLIC_WORDING,
        "seed": seed, "n_cases": len(results),
        "status_tally": status_tally,
        "results": results, "score": score,
    }


__all__ = ["ReplayCase", "REPLAY_CASES", "run_replaybench"]
