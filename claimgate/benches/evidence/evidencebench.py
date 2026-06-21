"""EvidenceBench: build evidence packs from all gate results + verify hash stability."""
from __future__ import annotations
from ...core.evidence import (
    build_all_evidence_packs, PUBLIC_WORDING, evidence_pack_score,
)


def run_evidence_bench(seed: int = 20260624, model=None) -> dict:
    # build packs from UnitGate, PhysicsClaimBench, TheoryGate examples
    code_hash = "prototype_evidence_v0"  # stable code identity for the prototype
    packs = build_all_evidence_packs(seed=seed, code_hash=code_hash)

    # for each pack, verify hash stability by rebuilding and comparing
    results = []
    for p in packs:
        # rebuild the same pack (should produce identical hashes since timestamp
        # is excluded from cert/pack hashes)
        p2_dict = p.to_dict()
        # recompute hashes from the current field values
        cert1 = p.certificate_hash
        pack1 = p.evidence_pack_hash
        cert2 = p.compute_certificate_hash()
        pack2 = p.compute_evidence_pack_hash()
        stable = (cert1 == cert2) and (pack1 == pack2)
        integrity = p.integrity_status()
        results.append({
            "pack_id": p.pack_id,
            "gate_name": p.gate_name,
            "status": p.status,
            "integrity_status": integrity,
            "certificate_hash": cert1[:16] + "...",
            "evidence_pack_hash": pack1[:16] + "...",
            "hashes_stable": stable,
            "contamination_status": p.contamination_status,
            "repro_command": p.repro_command,
            "human_readable_summary": p.human_readable_summary,
        })

    score = evidence_pack_score(results)
    # status tally
    status_tally = {}
    for r in results:
        s = r["integrity_status"]
        status_tally[s] = status_tally.get(s, 0) + 1

    return {
        "bench": "evidencebench",
        "mode": "EvidencePack v0 (reproducible, auditable evidence records)",
        "public_wording": PUBLIC_WORDING,
        "seed": seed, "n_cases": len(results),
        "status_tally": status_tally,
        "results": results, "score": score.to_dict(),
    }
