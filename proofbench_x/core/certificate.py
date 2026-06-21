"""Certificates of verification.

A Certificate is issued ONLY when the verifier has re-derived the exact
answer from the problem (never from a model output). It carries:

  * the problem id and family
  * the canonical problem string
  * the exact result (ExactValue) and its canonical string
  * the lane id (warm-lane cache key)
  * a deterministic sha256 hash of (problem_canon, result_canon)

No proof is ever faked. If the verifier cannot derive the answer, NO
certificate is issued and the case is recorded as `unverified` -- never
as `pass`.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field, asdict
from typing import Optional

from .exact import ExactValue


@dataclass(frozen=True)
class Certificate:
    problem_id: str
    family: str
    problem_canonical: str
    result_kind: str
    result_canonical: str
    lane_id: str
    verified: bool
    note: str = ""
    hash: str = field(default="")

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


def cert_hash(problem_canonical: str, result_canonical: str, lane_id: str) -> str:
    """Deterministic certificate hash. Same inputs -> same hash, always."""
    h = hashlib.sha256()
    h.update(problem_canonical.encode("utf-8"))
    h.update(b"\x1f")
    h.update(result_canonical.encode("utf-8"))
    h.update(b"\x1f")
    h.update(lane_id.encode("utf-8"))
    return h.hexdigest()


def issue_certificate(
    problem_id: str,
    family: str,
    problem_canonical: str,
    result: ExactValue,
    lane_id: str,
    note: str = "",
) -> Certificate:
    rc = result.canonical_string()
    h = cert_hash(problem_canonical, rc, lane_id)
    return Certificate(
        problem_id=problem_id,
        family=family,
        problem_canonical=problem_canonical,
        result_kind=result.kind,
        result_canonical=rc,
        lane_id=lane_id,
        verified=True,
        note=note,
        hash=h,
    )


def refused_certificate(
    problem_id: str,
    family: str,
    problem_canonical: str,
    lane_id: str,
    reason: str,
) -> Certificate:
    """A 'refused' certificate: the verifier refused to verify (e.g. malformed
    input, or a counterexample that must be rejected). Refusal is a first-class
    verification outcome, not a failure of the verifier."""
    h = cert_hash(problem_canonical, f"REFUSED:{reason}", lane_id)
    return Certificate(
        problem_id=problem_id,
        family=family,
        problem_canonical=problem_canonical,
        result_kind="refused",
        result_canonical=f"REFUSED:{reason}",
        lane_id=lane_id,
        verified=False,
        note=reason,
        hash=h,
    )
