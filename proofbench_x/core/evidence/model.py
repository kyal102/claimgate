"""EvidencePack v0: common evidence schema for all gates.

Every SuperMath, ProofBench, PhysicsGate, and TheoryGate result can be
turned into an EvidencePack — a reproducible, auditable record of what
was checked, how it was checked, and whether it can be reproduced.

Public wording:
  "EvidencePack and ReproGate make verification results reproducible and
   auditable. They do not prove scientific truth; they preserve what was
   checked, how it was checked, and whether it can be reproduced."
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional, Any


# The 9 canonical EvidencePack statuses (no others may be emitted)
ALL_EVIDENCE_STATUSES = [
    "EVIDENCE_PACK_CREATED",
    "MISSING_REPRO_COMMAND",
    "MISSING_SEED",
    "MISSING_CODE_HASH",
    "MISSING_DATA_HASH",
    "CONTAMINATED_BY_MODEL",
    "REPRODUCIBLE",
    "DRIFT_DETECTED",
    "UNVERIFIABLE_ARTIFACT",
]

PUBLIC_WORDING = (
    "EvidencePack and ReproGate make verification results reproducible and "
    "auditable. They do not prove scientific truth; they preserve what was "
    "checked, how it was checked, and whether it can be reproduced."
)

PACK_SCHEMA_VERSION = "evidence.v0"

# Model roles
MODEL_ROLES = ["none", "proposer", "participant", "verifier_attempt"]

# Contamination statuses
CONTAMINATION_STATUSES = [
    "clean",                      # no AI assistance
    "ai_assisted_build",          # AI helped build the case (not valid for leaderboard)
    "ai_assisted_holdout",        # AI-assisted holdout (not valid for uncontaminated scoring)
    "unknown",                    # contamination status not determined
]


@dataclass
class EvidencePack:
    """A reproducible, auditable evidence record for a gate result.

    Hashing rules:
      * certificate_hash is derived from the verified result/certificate,
        NOT raw formatting. Same (gate, input, seed, versions, result)
        -> same hash. Timestamp is excluded.
      * evidence_pack_hash is derived from canonical JSON with stable
        key ordering, excluding timestamp and the hash fields themselves.
      * Rerunning the same gate/input/version/seed produces the same
        certificate_hash and evidence_pack_hash.
    """
    # identity
    pack_id: str
    pack_schema_version: str = PACK_SCHEMA_VERSION
    timestamp: str = ""                # ISO-8601 UTC (NOT part of cert/pack hashes)
    gate_name: str = ""
    gate_version: str = ""             # e.g. "v0"
    # input
    raw_claim_or_input: str = ""
    normalized_input: str = ""
    # result
    status: str = ""                   # the gate's own status (e.g. DIMENSIONALLY_VALID)
    sub_statuses: List[str] = field(default_factory=list)
    result_body: Any = None            # the full gate result dict (for body comparison)
    certificate_hash: str = ""         # derived from verified result
    evidence_pack_hash: str = ""       # derived from canonical JSON of the pack
    # provenance
    code_hash: Optional[str] = None    # hash of the verifying code (if available)
    data_hash: Optional[str] = None    # hash of backing data (if applicable)
    seed: Optional[int] = None
    verifier_version: str = ""
    model_used: Optional[str] = None
    model_role: str = "none"           # one of MODEL_ROLES
    contamination_status: str = "unknown"
    # reproducibility
    limitations: List[str] = field(default_factory=list)
    next_required_validation: str = ""
    repro_command: str = ""            # exact CLI command to reproduce
    human_readable_summary: str = ""
    # internal flag: does this claim require a data_hash?
    _data_backed: bool = False

    def to_dict(self, include_hashes: bool = True) -> dict:
        d = {
            "pack_id": self.pack_id,
            "pack_schema_version": self.pack_schema_version,
            "timestamp": self.timestamp,
            "gate_name": self.gate_name,
            "gate_version": self.gate_version,
            "raw_claim_or_input": self.raw_claim_or_input,
            "normalized_input": self.normalized_input,
            "status": self.status,
            "sub_statuses": self.sub_statuses,
            "result_body": self.result_body,
            "certificate_hash": self.certificate_hash,
            "evidence_pack_hash": self.evidence_pack_hash,
            "code_hash": self.code_hash,
            "data_hash": self.data_hash,
            "seed": self.seed,
            "verifier_version": self.verifier_version,
            "model_used": self.model_used,
            "model_role": self.model_role,
            "contamination_status": self.contamination_status,
            "limitations": self.limitations,
            "next_required_validation": self.next_required_validation,
            "repro_command": self.repro_command,
            "human_readable_summary": self.human_readable_summary,
        }
        return d

    def compute_certificate_hash(self) -> str:
        """Deterministic hash over the VERIFIED RESULT identity.

        Same (gate_name, gate_version, normalized_input, status, seed,
        verifier_version, result_body_canonical) -> same hash.
        Timestamp and formatting are deliberately excluded.
        """
        result_canon = _canonical_json(self.result_body) if self.result_body is not None else ""
        cert_input = "|".join([
            self.gate_name,
            self.gate_version,
            self.normalized_input,
            self.status,
            str(self.seed) if self.seed is not None else "",
            self.verifier_version,
            result_canon,
        ])
        return hashlib.sha256(cert_input.encode("utf-8")).hexdigest()

    def compute_evidence_pack_hash(self) -> str:
        """Deterministic hash over canonical JSON of the pack.

        Excludes: timestamp, certificate_hash, evidence_pack_hash (to avoid
        circular dependency). All other fields are included with stable key
        ordering.
        """
        d = self.to_dict()
        # remove fields that must not affect the pack hash
        for k in ("timestamp", "certificate_hash", "evidence_pack_hash"):
            d.pop(k, None)
        canon = _canonical_json(d)
        return hashlib.sha256(canon.encode("utf-8")).hexdigest()

    def seal(self) -> "EvidencePack":
        """Compute and set both hashes. Returns self for chaining."""
        self.certificate_hash = self.compute_certificate_hash()
        self.evidence_pack_hash = self.compute_evidence_pack_hash()
        return self

    def integrity_status(self) -> str:
        """Assess the pack's reproducibility integrity (structural check).

        Returns the FIRST missing-field status found, or EVIDENCE_PACK_CREATED
        if all required fields are present. Full reproducibility requires
        ReproGate to compare two packs.
        """
        if not self.repro_command:
            return "MISSING_REPRO_COMMAND"
        if self.seed is None:
            return "MISSING_SEED"
        if self.code_hash is None:
            return "MISSING_CODE_HASH"
        if self.data_hash is None and self._data_backed:
            return "MISSING_DATA_HASH"
        if self.contamination_status in ("ai_assisted_build", "ai_assisted_holdout"):
            return "CONTAMINATED_BY_MODEL"
        return "EVIDENCE_PACK_CREATED"


def _canonical_json(obj: Any) -> str:
    """Stable JSON serialization: sorted keys, no extra whitespace."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


__all__ = [
    "ALL_EVIDENCE_STATUSES", "PUBLIC_WORDING", "PACK_SCHEMA_VERSION",
    "MODEL_ROLES", "CONTAMINATION_STATUSES",
    "EvidencePack", "now_iso", "_canonical_json",
]
