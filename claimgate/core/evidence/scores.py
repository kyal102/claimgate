"""Evidence scores."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List


@dataclass
class EvidenceScore:
    name: str
    value: float
    n: int
    detail: str = ""
    def to_dict(self) -> dict:
        return {"name": self.name, "value": self.value, "n": self.n, "detail": self.detail}


EVIDENCE_SCORE_NAMES = [
    "Evidence Pack Score",
    "Repro Bench Score",
]


def evidence_pack_score(results: List[dict]) -> EvidenceScore:
    """Fraction of evidence packs with stable cert + pack hashes across reruns."""
    if not results:
        return EvidenceScore("Evidence Pack Score", 0.0, 0, "not_run")
    passed = sum(1 for r in results if r.get("hashes_stable"))
    return EvidenceScore("Evidence Pack Score", passed / len(results), len(results),
                        f"{passed}/{len(results)} packs have stable cert + pack hashes across reruns")


def repro_bench_score(results: List[dict]) -> EvidenceScore:
    if not results:
        return EvidenceScore("Repro Bench Score", 0.0, 0, "not_run")
    passed = sum(1 for r in results if r.get("self_consistent"))
    return EvidenceScore("Repro Bench Score", passed / len(results), len(results),
                        f"{passed}/{len(results)} repro cases correct")
