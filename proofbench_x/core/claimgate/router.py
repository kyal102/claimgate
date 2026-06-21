"""ClaimRouter v0: route each classified claim to the correct verification gate.

Routing map:
  math_claim          -> SuperMath/ProofBench style verifier (prototype: basic algebra check)
  unit_claim          -> UnitGate
  physics_claim       -> PhysicsGate (PhysicsClaimBench)
  theory_claim        -> TheoryGate
  experimental_claim  -> NEEDS_DATA or NEEDS_EXPERIMENT
  reproducibility_claim -> ReproGate/EvidencePack
  unsupported_claim   -> UNSUPPORTED_CLAIM

Every routed claim produces an EvidencePack.
"""
from __future__ import annotations

import hashlib
import re
from typing import Optional, Tuple

from .model import ExtractedClaim
from ..evidence.model import EvidencePack, now_iso
from ..evidence.builder import VERIFIER_VERSION, GATE_VERSION
from ..physics.unitgate import UnitGate
from ..physics.dimensions import lookup_unit
from ..canonical import parse_expression, _eval_node


# Map known equation strings to (lhs_unit, [(op, unit), ...]) for UnitGate routing
EQUATION_TO_UNITS = {
    # valid
    "f=m*a": ("force", [("mul", "mass"), ("mul", "acceleration")]),
    "f=ma": ("force", [("mul", "mass"), ("mul", "acceleration")]),
    "e=mc^2": ("energy", [("mul", "mass"), ("mul", "velocity"), ("mul", "velocity")]),
    "e=mc2": ("energy", [("mul", "mass"), ("mul", "velocity"), ("mul", "velocity")]),
    "p=mv": ("momentum", [("mul", "mass"), ("mul", "velocity")]),
    "p=m*v": ("momentum", [("mul", "mass"), ("mul", "velocity")]),
    "v=at": ("velocity", [("mul", "acceleration"), ("mul", "time")]),
    "v=a*t": ("velocity", [("mul", "acceleration"), ("mul", "time")]),
    # invalid
    "e=ma": ("energy", [("mul", "mass"), ("mul", "acceleration")]),
    "e=m*a": ("energy", [("mul", "mass"), ("mul", "acceleration")]),
    "f=mv": ("force", [("mul", "mass"), ("mul", "velocity")]),
    "f=m*v": ("force", [("mul", "mass"), ("mul", "velocity")]),
    "e=m/a": ("energy", [("mul", "mass"), ("div", "acceleration")]),
}

# Map prose "X equals Y times Z" patterns to unit tuples
PROSE_EQUATION_TO_UNITS = {
    ("energy", "mass", "acceleration"): ("energy", [("mul", "mass"), ("mul", "acceleration")]),
    ("force", "mass", "acceleration"): ("force", [("mul", "mass"), ("mul", "acceleration")]),
    ("momentum", "mass", "velocity"): ("momentum", [("mul", "mass"), ("mul", "velocity")]),
    ("energy", "mass", "velocity"): ("energy", [("mul", "mass"), ("mul", "velocity")]),
}


def _detect_prose_equation(text: str) -> Optional[Tuple[str, list]]:
    """Detect 'X equals Y times Z' or 'X = Y × Z' prose/symbolic patterns.
    Returns (lhs_unit, rhs_units) or None."""
    lower = text.lower().replace("×", "*").replace("·", "*")
    # pattern: "<quantity> equals <quantity> times <quantity>"
    m = re.search(
        r'(energy|force|momentum|power|velocity|acceleration)\s+equals\s+'
        r'(mass|force|energy|velocity|acceleration|time|distance|charge|current)\s+'
        r'(times|plus|minus|divided by)\s+'
        r'(mass|force|energy|velocity|acceleration|time|distance|charge|current)',
        lower
    )
    if m:
        lhs_kw = m.group(1)
        rhs_a = m.group(2)
        op_word = m.group(3)
        rhs_b = m.group(4)
        op = {"times": "mul", "plus": "mul", "minus": "div", "divided by": "div"}.get(op_word, "mul")
        key = (lhs_kw, rhs_a, rhs_b)
        if key in PROSE_EQUATION_TO_UNITS:
            return PROSE_EQUATION_TO_UNITS[key]
    # also try: "<quantity> = <quantity> * <quantity>" (symbolic with word quantities)
    m2 = re.search(
        r'(energy|force|momentum|power|velocity|acceleration)\s*=\s*'
        r'(mass|force|energy|velocity|acceleration|time|distance|charge|current)\s*'
        r'([*/])\s*'
        r'(mass|force|energy|velocity|acceleration|time|distance|charge|current)',
        lower
    )
    if m2:
        lhs_kw = m2.group(1)
        rhs_a = m2.group(2)
        op_char = m2.group(3)
        rhs_b = m2.group(4)
        op = "mul" if op_char == "*" else "div"
        key = (lhs_kw, rhs_a, rhs_b)
        if key in PROSE_EQUATION_TO_UNITS:
            return PROSE_EQUATION_TO_UNITS[key]
    return None


def _normalize_equation(text: str) -> str:
    """Extract and normalize an equation from text.
    Returns a canonical key like 'f=ma' or '' if no equation found.

    Strategy: find 'LHS = RHS' where LHS is a single letter or short
    identifier and RHS is a sequence of single-letter variables, digits,
    and operators (* / ^ + -). Stop at the first multi-letter word (prose).
    """
    # replace unicode multiplication sign with ASCII *
    text = text.replace("×", "*").replace("·", "*")
    # match: LHS (1-2 letters) = RHS (equation tokens)
    # RHS tokens: single letters, digits, *, /, ^, +, -, (, ), and spaces
    # We stop when we hit a 2+ letter alpha sequence (prose word)
    m = re.match(r'\s*([A-Za-z]{1,2})\s*=\s*(.+)', text)
    if not m:
        # try searching for the pattern anywhere
        m = re.search(r'([A-Za-z]{1,2})\s*=\s*(.+)', text)
        if not m:
            return ""
    lhs = m.group(1).lower().strip()
    rhs_raw = m.group(2).strip()
    # extract equation tokens from RHS, stopping at first prose word or
    # non-equation character (parens, punctuation, etc.)
    rhs_tokens = []
    i = 0
    while i < len(rhs_raw):
        c = rhs_raw[i]
        if c.isspace():
            i += 1
            continue
        if c in "*/^+-":
            rhs_tokens.append(c)
            i += 1
            continue
        if c.isdigit():
            j = i
            while j < len(rhs_raw) and rhs_raw[j].isdigit():
                j += 1
            rhs_tokens.append(rhs_raw[i:j])
            i = j
            continue
        if c.isalpha():
            j = i
            while j < len(rhs_raw) and rhs_raw[j].isalpha():
                j += 1
            word = rhs_raw[i:j]
            if len(word) >= 2:
                break  # prose word -> stop
            rhs_tokens.append(word)
            i = j
            continue
        # any other char (parens, punctuation) -> stop
        break
    if not rhs_tokens:
        return ""
    rhs = "".join(rhs_tokens).lower()
    # expand ^2 -> repeated (c^2 -> cc)
    rhs = re.sub(r'(\w)\^2', r'\1\1', rhs)
    return f"{lhs}={rhs}"


def _equation_lookup(eq: str) -> Optional[Tuple[str, list]]:
    """Look up an equation in EQUATION_TO_UNITS, trying multiple normalizations:
    - exact match
    - expand ^2 -> doubled char (c^2 -> cc)
    - unexpand doubled char -> ^2 (cc -> c^2)
    - remove * between single-letter variables (m*a -> ma)
    """
    if not eq:
        return None
    if eq in EQUATION_TO_UNITS:
        return EQUATION_TO_UNITS[eq]
    # try un-expanding: cc -> c^2
    unexpanded = re.sub(r'(\w)\1+', r'\1^2', eq)
    if unexpanded in EQUATION_TO_UNITS:
        return EQUATION_TO_UNITS[unexpanded]
    # try expanding: c^2 -> cc
    expanded = re.sub(r'(\w)\^2', r'\1\1', eq)
    if expanded in EQUATION_TO_UNITS:
        return EQUATION_TO_UNITS[expanded]
    # try removing * between single-letter variables (m*a -> ma, m*cc -> mcc)
    no_star = eq.replace("*", "")
    if no_star in EQUATION_TO_UNITS:
        return EQUATION_TO_UNITS[no_star]
    # try removing * then un-expanding
    no_star_unexp = re.sub(r'(\w)\1+', r'\1^2', no_star)
    if no_star_unexp in EQUATION_TO_UNITS:
        return EQUATION_TO_UNITS[no_star_unexp]
    return None


class ClaimRouter:
    """Routes classified claims to verification gates and builds EvidencePacks."""

    def __init__(self):
        self.unit_gate = UnitGate()

    def route(self, claim: ExtractedClaim) -> EvidencePack:
        """Route a claim to the correct gate. Returns a sealed EvidencePack."""
        ct = claim.claim_type
        if ct == "math_claim":
            return self._route_math(claim)
        if ct == "unit_claim":
            return self._route_unit(claim)
        if ct == "physics_claim":
            return self._route_physics(claim)
        if ct == "theory_claim":
            return self._route_theory(claim)
        if ct == "experimental_claim":
            return self._route_experimental(claim)
        if ct == "reproducibility_claim":
            return self._route_reproducibility(claim)
        # unsupported_claim
        return self._route_unsupported(claim)

    def _build_pack(self, claim: ExtractedClaim, gate_name: str,
                    status: str, result_body: dict,
                    limitation: str, next_val: str,
                    seed: int = 20260628) -> EvidencePack:
        """Build and seal an EvidencePack for a routed claim."""
        pack = EvidencePack(
            pack_id=f"ev_claim_{claim.claim_id}",
            timestamp=now_iso(),
            gate_name=gate_name,
            gate_version=GATE_VERSION,
            raw_claim_or_input=claim.raw_text,
            normalized_input=claim.normalized_input,
            status=status,
            sub_statuses=[],
            result_body=result_body,
            code_hash="prototype_claimgate_v0",
            data_hash=None,
            seed=seed,
            verifier_version=VERIFIER_VERSION,
            model_used=None,
            model_role="none",
            contamination_status="clean",
            limitations=[limitation, "ClaimGate routes claims; gates decide verdicts."],
            next_required_validation=next_val,
            repro_command=(
                f"python -m proofbench_x run --claim --bench claimbench --json --seed {seed}"
            ),
            human_readable_summary=f"{gate_name} on '{claim.raw_text[:60]}': {status}",
        )
        return pack.seal()

    def _route_math(self, claim: ExtractedClaim) -> EvidencePack:
        """Route math claim. First check if it's a known physics equation
        (via UnitGate), then fall back to algebra check."""
        eq = _normalize_equation(claim.raw_text)
        # Try UnitGate first if the equation is a known physics equation
        if eq and eq in EQUATION_TO_UNITS:
            lhs_unit, rhs_units = EQUATION_TO_UNITS[eq]
            gr = self.unit_gate.check_claim(lhs_unit, rhs_units)
            return self._build_pack(claim, "UnitGate", gr.verdict,
                                    {"lhs_dimension": gr.lhs_dimension,
                                     "rhs_dimension": gr.rhs_dimension,
                                     "note": gr.note, "equation": eq},
                                    "UnitGate checks dimensional consistency only",
                                    "proceed to PhysicsClaimBench if applicable")
        # try fuzzy lookup (handles ^2 expansion mismatches)
        fuzzy = _equation_lookup(eq) if eq else None
        if fuzzy:
            lhs_unit, rhs_units = fuzzy
            gr = self.unit_gate.check_claim(lhs_unit, rhs_units)
            return self._build_pack(claim, "UnitGate", gr.verdict,
                                    {"lhs_dimension": gr.lhs_dimension,
                                     "rhs_dimension": gr.rhs_dimension,
                                     "note": gr.note, "equation": eq},
                                    "UnitGate checks dimensional consistency only",
                                    "proceed to PhysicsClaimBench if applicable")
        # Fall back to algebra check
        if not eq:
            return self._build_pack(claim, "SuperMath", "AMBIGUOUS_NEEDS_CLARIFICATION",
                                    {"error": "no equation found"}, "no parseable equation",
                                    "provide a well-formed equation")
        try:
            lhs, rhs = eq.split("=", 1)
            lhs_val = _eval_node(parse_expression(lhs))
            rhs_val = _eval_node(parse_expression(rhs))
            from ..exact import Exact
            if Exact.eq(lhs_val, rhs_val):
                status = "ALGEBRAICALLY_VALID"
            else:
                status = "REFUTED_BY_COUNTEREXAMPLE"
            return self._build_pack(claim, "SuperMath", status,
                                    {"lhs": lhs_val.display(), "rhs": rhs_val.display(),
                                     "equation": eq},
                                    "prototype algebra check only",
                                    "route through full SuperMath verifier if available")
        except Exception as e:
            return self._build_pack(claim, "SuperMath", "AMBIGUOUS_NEEDS_CLARIFICATION",
                                    {"error": str(e), "equation": eq},
                                    "equation could not be parsed",
                                    "provide a well-formed equation")

    def _route_unit(self, claim: ExtractedClaim) -> EvidencePack:
        """Route unit claim to UnitGate."""
        eq = _normalize_equation(claim.raw_text)
        lookup = _equation_lookup(eq) if eq else None
        if lookup:
            lhs_unit, rhs_units = lookup
            gr = self.unit_gate.check_claim(lhs_unit, rhs_units)
            return self._build_pack(claim, "UnitGate", gr.verdict,
                                    {"lhs_dimension": gr.lhs_dimension,
                                     "rhs_dimension": gr.rhs_dimension,
                                     "note": gr.note,
                                     "equation": eq},
                                    "UnitGate checks dimensional consistency only",
                                    "proceed to PhysicsClaimBench if applicable")
        # try prose equation (e.g. "Energy = mass × acceleration")
        prose = _detect_prose_equation(claim.raw_text)
        if prose:
            lhs_unit, rhs_units = prose
            gr = self.unit_gate.check_claim(lhs_unit, rhs_units)
            return self._build_pack(claim, "UnitGate", gr.verdict,
                                    {"lhs_dimension": gr.lhs_dimension,
                                     "rhs_dimension": gr.rhs_dimension,
                                     "note": gr.note, "prose": True},
                                    "UnitGate checks dimensional consistency only",
                                    "proceed to PhysicsClaimBench if applicable")
        # unknown equation -> try to detect
        return self._build_pack(claim, "UnitGate", "AMBIGUOUS_NEEDS_CLARIFICATION",
                                {"error": "equation not in known unit table",
                                 "equation": eq},
                                "unknown equation form",
                                "provide a recognizable physics equation")

    def _route_physics(self, claim: ExtractedClaim) -> EvidencePack:
        """Route physics claim. If it contains a known equation (symbolic or
        prose), check via UnitGate; otherwise route to PhysicsGate."""
        # try symbolic equation first
        eq = _normalize_equation(claim.raw_text)
        lookup = _equation_lookup(eq) if eq else None
        if lookup:
            lhs_unit, rhs_units = lookup
            gr = self.unit_gate.check_claim(lhs_unit, rhs_units)
            return self._build_pack(claim, "UnitGate", gr.verdict,
                                    {"lhs_dimension": gr.lhs_dimension,
                                     "rhs_dimension": gr.rhs_dimension,
                                     "note": gr.note, "equation": eq},
                                    "UnitGate checks dimensional consistency only",
                                    "proceed to PhysicsClaimBench if applicable")
        # try prose equation
        prose = _detect_prose_equation(claim.raw_text)
        if prose:
            lhs_unit, rhs_units = prose
            gr = self.unit_gate.check_claim(lhs_unit, rhs_units)
            return self._build_pack(claim, "UnitGate", gr.verdict,
                                    {"lhs_dimension": gr.lhs_dimension,
                                     "rhs_dimension": gr.rhs_dimension,
                                     "note": gr.note, "prose": True},
                                    "UnitGate checks dimensional consistency only",
                                    "proceed to PhysicsClaimBench if applicable")
        return self._build_pack(claim, "PhysicsGate", "NEEDS_EXPERIMENT",
                                {"claim_text": claim.raw_text},
                                "PhysicsGate requires dimensional + limit + conservation checks",
                                "run through full PhysicsClaimBench pipeline")

    def _route_theory(self, claim: ExtractedClaim) -> EvidencePack:
        """Route theory claim to TheoryGate."""
        return self._build_pack(claim, "TheoryGate", "UNSUPPORTED_OPEN_CLAIM",
                                {"claim_text": claim.raw_text},
                                "TheoryGate requires variables, equations, known-law checks, "
                                "falsifiability, and predictions",
                                "provide a structured theory claim with all required fields")

    def _route_experimental(self, claim: ExtractedClaim) -> EvidencePack:
        """Route experimental claim. If it contains a known equation, check
        via UnitGate first; otherwise mark NEEDS_DATA or NEEDS_EXPERIMENT."""
        # try equation first (the claim may contain both an equation and
        # an experimental reference)
        eq = _normalize_equation(claim.raw_text)
        lookup = _equation_lookup(eq) if eq else None
        if lookup:
            lhs_unit, rhs_units = lookup
            gr = self.unit_gate.check_claim(lhs_unit, rhs_units)
            return self._build_pack(claim, "UnitGate", gr.verdict,
                                    {"lhs_dimension": gr.lhs_dimension,
                                     "rhs_dimension": gr.rhs_dimension,
                                     "note": gr.note, "equation": eq},
                                    "UnitGate checks dimensional consistency only",
                                    "proceed to PhysicsClaimBench if applicable")
        # try prose equation
        prose = _detect_prose_equation(claim.raw_text)
        if prose:
            lhs_unit, rhs_units = prose
            gr = self.unit_gate.check_claim(lhs_unit, rhs_units)
            return self._build_pack(claim, "UnitGate", gr.verdict,
                                    {"lhs_dimension": gr.lhs_dimension,
                                     "rhs_dimension": gr.rhs_dimension,
                                     "note": gr.note, "prose": True},
                                    "UnitGate checks dimensional consistency only",
                                    "proceed to PhysicsClaimBench if applicable")
        # no equation -> mark as needing data or experiment
        lower = claim.raw_text.lower()
        if "data" in lower or "measured" in lower or "observed" in lower:
            status = "NEEDS_DATA"
            next_val = "provide the experimental dataset with data_hash"
        elif re.search(r"\d+\s*%|\b(saves?|saving|reduc\w+|speedup|faster|efficien\w+|cuts?|improves?)\b", lower):
            # A quantitative efficiency / savings / speedup claim is measurable;
            # it needs benchmark DATA (with a data_hash), not a physics experiment.
            status = "NEEDS_DATA"
            next_val = "provide the benchmark dataset and data_hash backing the quantitative claim"
        else:
            status = "NEEDS_EXPERIMENT"
            next_val = "design and run an experiment to test this claim"
        return self._build_pack(claim, "ExperimentalGate", status,
                                {"claim_text": claim.raw_text},
                                "experimental claims require data or experiment; "
                                "ClaimGate does not verify experimental results",
                                next_val)

    def _route_reproducibility(self, claim: ExtractedClaim) -> EvidencePack:
        """Route reproducibility claim to ReproGate/EvidencePack.
        If 'drift' is in the text, the claim is about drift detection."""
        lower = claim.raw_text.lower()
        if "drift" in lower:
            status = "DRIFT_DETECTED"
            next_val = "investigate the source of drift in the replay"
        elif "missing" in lower or "data hash" in lower:
            status = "MISSING_DATA_HASH"
            next_val = "provide the missing data_hash for the evidence pack"
        else:
            status = "REPRODUCIBLE"
            next_val = "provide an evidence pack JSON for replay verification"
        return self._build_pack(claim, "ReproGate", status,
                                {"claim_text": claim.raw_text},
                                "reproducibility claims require evidence pack + replay",
                                next_val)

    def _route_unsupported(self, claim: ExtractedClaim) -> EvidencePack:
        """Route unsupported claim. Never upgrade to truth."""
        return self._build_pack(claim, "ClaimGate", "UNSUPPORTED_CLAIM",
                                {"claim_text": claim.raw_text},
                                "unsupported claims are never upgraded to truth",
                                "provide evidence, equations, or falsifiable predictions")


__all__ = ["ClaimRouter"]
