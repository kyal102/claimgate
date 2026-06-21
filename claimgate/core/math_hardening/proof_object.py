"""ProofObject v0: structured proof/certificate object for each math claim.

Fields:
  proof_object_id, claim, normalized_claim, domain, assumptions,
  gate_results, normal_form, result, witness (if failed),
  certificate_hash, evidence_pack_id (if available),
  replay_command, limitations
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import List, Optional, Any

from .domain_gate import DomainGateResult
from .assumption_gate import AssumptionResult
from .witness_gate import Witness


@dataclass
class ProofObject:
    """A structured proof/certificate object for a mathematical claim."""
    proof_object_id: str
    claim: str                           # original claim text
    normalized_claim: str                # canonical form
    domain: str                          # declared domain
    assumptions: List[str]               # declared assumptions
    gate_results: dict = field(default_factory=dict)   # per-gate results
    normal_form: str = ""               # canonical normal form
    result: str = ""                     # final result (PASS/FAIL/CONDITIONAL)
    witness: Optional[dict] = None       # counterexample witness if failed
    certificate_hash: str = ""          # deterministic hash
    evidence_pack_id: str = ""          # link to EvidencePack if available
    replay_command: str = ""            # command to replay
    limitations: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "proof_object_id": self.proof_object_id,
            "claim": self.claim,
            "normalized_claim": self.normalized_claim,
            "domain": self.domain,
            "assumptions": self.assumptions,
            "gate_results": self.gate_results,
            "normal_form": self.normal_form,
            "result": self.result,
            "witness": self.witness,
            "certificate_hash": self.certificate_hash,
            "evidence_pack_id": self.evidence_pack_id,
            "replay_command": self.replay_command,
            "limitations": self.limitations,
        }

    def compute_certificate_hash(self) -> str:
        """Deterministic hash over (proof_object_id, normalized_claim, domain,
        result, witness_hash). Excludes timestamp."""
        witness_str = ""
        if self.witness:
            witness_str = json.dumps(self.witness, sort_keys=True, default=str)
        cert_input = "|".join([
            self.proof_object_id,
            self.normalized_claim,
            self.domain,
            self.result,
            witness_str,
        ])
        return hashlib.sha256(cert_input.encode("utf-8")).hexdigest()

    def seal(self) -> "ProofObject":
        """Compute and set the certificate hash. Returns self."""
        self.certificate_hash = self.compute_certificate_hash()
        return self


def build_proof_object(
    proof_object_id: str,
    claim: str,
    normalized_claim: str,
    domain: str,
    assumptions: List[str],
    domain_result: Optional[DomainGateResult],
    assumption_result: Optional[AssumptionResult],
    witness_result: Optional[dict],
    normal_form: str = "",
    result: str = "PASS",
    evidence_pack_id: str = "",
    replay_command: str = "",
) -> ProofObject:
    """Build a sealed ProofObject from gate results."""
    gate_results = {}
    if domain_result:
        gate_results["domain_gate"] = domain_result.to_dict()
    if assumption_result:
        gate_results["assumption_gate"] = assumption_result.to_dict()
    if witness_result:
        gate_results["witness_gate"] = witness_result

    limitations = [
        "ProofObject is a structured certificate; it does not prove new mathematics.",
        "The verifier remains final authority.",
        "Witness (if present) is a counterexample, not a proof of falsehood everywhere.",
    ]

    obj = ProofObject(
        proof_object_id=proof_object_id,
        claim=claim,
        normalized_claim=normalized_claim,
        domain=domain,
        assumptions=assumptions,
        gate_results=gate_results,
        normal_form=normal_form,
        result=result,
        witness=witness_result.get("witness") if witness_result else None,
        evidence_pack_id=evidence_pack_id,
        replay_command=replay_command,
        limitations=limitations,
    )
    return obj.seal()


__all__ = ["ProofObject", "build_proof_object"]
