"""Report exporter: emits a research-grade markdown report + canonical JSON.

The markdown report follows the structure universities expect:
abstract, motivation, methodology, scoring, anti-gaming controls,
results (v0 + v1), limitations, no overclaiming.

Wording is enforced: "proof-aware mathematical verification benchmark."
Never "world's hardest", never "frontier models have no chance", etc.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional

from .schema import V0_SCORE_NAMES, V1_SCORE_NAMES


FORBIDDEN_PHRASES = [
    "world's hardest math benchmark",
    "frontier models have no chance",
    "official university benchmark",
    "solves open problems",
    "proves agi",
    "unbeatable",
]


def _meta():
    """Lazily import package metadata to avoid circular imports."""
    from .. import __descriptor__, __version__, __is_prototype__
    return __descriptor__, __version__, __is_prototype__


def _check_wording(text: str) -> list:
    """Return list of forbidden phrases found in text (anti-overclaim guard)."""
    low = text.lower()
    return [p for p in FORBIDDEN_PHRASES if p in low]


def export_research_report(
    v0_result: Optional[dict],
    v1_full_result: Optional[dict],
    duel_result: Optional[dict] = None,
    holdout_result: Optional[dict] = None,
    engine_fixes: Optional[list] = None,
    known_limitations: Optional[list] = None,
) -> str:
    """Render the research-grade markdown report."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    descriptor, version, is_prototype = _meta()
    lines = []
    a = lines.append

    a(f"# SuperMath ProofBench X — Research Report")
    a("")
    a(f"**Descriptor:** {descriptor}")
    a(f"**Version:** {version}")
    a(f"**Prototype:** {is_prototype}")
    a(f"**Generated:** {ts}")
    a("")

    a("## Abstract")
    a("")
    a("SuperMath ProofBench X is a proof-aware mathematical verification "
      "benchmark. It tests whether a system can verify, reproduce, certify, "
      "refuse, and reuse mathematical work *without trusting the model*. "
      "Unlike model-solving benchmarks (MATH, FrontierMath, GSM-Symbolic, "
      "Humanity's Last Exam), ProofBench measures the *verification "
      "infrastructure* around the model: deterministic replay, certificate "
      "drift, safe refusal, verifier authority, warm-lane reuse, and "
      "exactness preservation.")
    a("")

    a("## Motivation")
    a("")
    a("Existing math benchmarks ask: *can the model solve hard math?* "
      "ProofBench asks: *can the system verify the model's math without "
      "trusting it?* These are different questions. A model that solves "
      "90% of competition problems may still produce unreplayable results, "
      "accept false identities, lose exactness on large integers, or answer "
      "when it should defer to verification. ProofBench targets exactly "
      "these failure modes.")
    a("")

    a("## Benchmark category")
    a("")
    a("- **Kind:** proof-aware verification benchmark (not a solving benchmark)")
    a("- **Authority:** a deterministic exact-arithmetic verifier; never the model")
    a("- **Output:** certificates + scores, not just pass/fail")
    a("- **Open problems:** none used. Only closed, elementary, verifiable math.")
    a("")

    a("## Comparison to existing benchmarks")
    a("")
    a("| Benchmark | What it measures | ProofBench difference |")
    a("|---|---|---|")
    a("| MATH (12,500 problems) | Can the model solve competition math? | ProofBench asks whether the *system* can verify, not whether the model can solve. |")
    a("| FrontierMath | Can the model solve expert-vetted hard problems? | ProofBench uses closed elementary math; the difficulty is in verification, not problem hardness. |")
    a("| GSM-Symbolic | Symbolic/numeric variants of grade-school reasoning. | ProofBench's VAR-Lane generalizes this to exact arithmetic, modular, rational, and big-integer families. |")
    a("| Humanity's Last Exam | Held-out questions to reduce overfitting. | ProofBench's Holdout mode applies the same principle to verification cases, with anti-leak checks. |")
    a("| HARDMath | Auto-generated applied math validated against numerical ground truth. | ProofBench validates against *exact* ground truth (no floating point), and adds replay/certificate/warm-lane axes. |")
    a("")

    a("## Methodology")
    a("")
    a("The verifier re-derives the exact answer to every problem using exact "
      "arithmetic (Python `int`, `fractions.Fraction`, modular residues). "
      "It never looks up answers from a table. Model outputs are graded "
      "against the re-derived truth; the model never decides correctness. "
      "Certificates are issued only on successful verification and carry a "
      "deterministic SHA-256 hash of `(problem_canonical, result_canonical, "
      "lane_id)`.")
    a("")

    a("## Scoring")
    a("")
    a("### v0 scores (preserved)")
    a("")
    for s in V0_SCORE_NAMES:
        a(f"- **{s}**")
    a("")
    a("### v1 scores (adversarial verification)")
    a("")
    for s in V1_SCORE_NAMES:
        a(f"- **{s}**")
    a("")

    a("## Anti-gaming controls")
    a("")
    a("- Answers are never hardcoded in the verifier.")
    a("- Model outputs never override verifier output (Lane C may override the model; never the reverse).")
    a("- Failures are never hidden; every case yields an explicit status.")
    a("- No proof is faked; certificates issue only on real verification.")
    a("- No open problem is claimed solved.")
    a("- Unrun benches report `not_run`, never a faked zero.")
    a("- Holdout prompts are checked for answer leakage via token-boundary matching.")
    a("- Holdout cases built with AI assistance are NOT valid for an uncontaminated public leaderboard.")
    a("")

    a("## Results")
    a("")
    if v0_result:
        r = v0_result.get("result", v0_result)
        a(f"### v0 baseline")
        a("")
        a(f"- Cases: {r.get('n_cases', 'n/a')}")
        sc = r.get("score", {})
        a(f"- Score: {sc.get('value')} ({sc.get('detail','')})")
        a(f"- Is real v0: {r.get('is_real_v0', False)}")
        a("")
    if v1_full_result:
        a("### v1 (Adversarial Verification Mode)")
        a("")
        a(f"- Total v1 cases: {v1_full_result.get('total_v1_cases','n/a')}")
        a("")
        a("| Bench | n | Score | Detail |")
        a("|---|---|---|---|")
        for name, b in v1_full_result.get("benches", {}).items():
            sc = b.get("score", {})
            v = sc.get("value")
            vs = f"{v:.4f}" if isinstance(v, (int, float)) else str(v)
            a(f"| {name} | {b.get('n_cases',0)} | {vs} | {sc.get('detail','')} |")
        a("")
    if duel_result:
        a("### Model duel (3-lane comparison)")
        a("")
        a("| Lane | Score | Passed | Total | Overrides |")
        a("|---|---|---|---|---|")
        for lane in ("raw_model", "model_plus_tool", "dtl_verified"):
            d = duel_result.get(lane, {})
            sc = d.get("score")
            scs = f"{sc:.4f}" if isinstance(sc, (int, float)) else "not_run"
            a(f"| {lane} | {scs} | {d.get('passed',0)} | {d.get('total',0)} | — |")
        a(f"\nVerifier overrides applied (Lane C overrode model): "
          f"{duel_result.get('overrides_applied',0)}")
        a("")

    if engine_fixes:
        a("## Engine fixes driven by v1")
        a("")
        for i, f in enumerate(engine_fixes, 1):
            a(f"{i}. {f}")
        a("")

    a("## Limitations")
    a("")
    if known_limitations:
        for lim in known_limitations:
            a(f"- {lim}")
    else:
        a("- This is a prototype, not the integrated real-repo v1.")
        a("- The model adapter is a deterministic Stub, not a real LLM.")
        a("- `compute_saving_estimate` is time-based, not hardware-power-measured.")
        a("- Holdout cases were built with AI assistance and are not valid for an uncontaminated public leaderboard.")
    a("")

    a("## No overclaiming")
    a("")
    a("This report uses the descriptor **\"proof-aware mathematical "
      "verification benchmark\"** and avoids superlatives. It does not claim "
      "to be the world's hardest benchmark, to solve open problems, or to be "
      "an accredited academic-standard benchmark.")
    a("")

    # anti-overclaim self-check
    full = "\n".join(lines)
    bad = _check_wording(full)
    if bad:
        a("## ⚠ Wording self-check FAILED")
        a("")
        a("Forbidden phrases detected (must be removed before publication):")
        for p in bad:
            a(f"- `{p}`")
    else:
        a("## Wording self-check")
        a("")
        a("Passed: no forbidden superlative phrases detected.")

    return "\n".join(lines)


def export_json_report(v0_result, v1_full_result, duel_result=None,
                       holdout_result=None) -> dict:
    """Assemble a canonical JSON report envelope."""
    descriptor, version, is_prototype = _meta()
    return {
        "benchmark": "SuperMath ProofBench X",
        "descriptor": descriptor,
        "version": version,
        "is_prototype": is_prototype,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "v0": v0_result,
        "v1": v1_full_result,
        "duel": duel_result,
        "holdout": holdout_result,
    }
