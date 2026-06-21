"""CLI for ProofBench X v1 prototype.

Examples:
  python -m claimgate run --v1 --json
  python -m claimgate run --v1 --bench varlane
  python -m claimgate run --v1 --bench metamorphic
  python -m claimgate run --v1 --bench counterexample
  python -m claimgate run --v1 --bench exactstress
  python -m claimgate run --v1 --bench toolrouting
  python -m claimgate run --v1 --bench replay
  python -m claimgate run --v1 --bench warmpower
  python -m claimgate run --v1 --holdout --seed 20260622
  python -m claimgate run --v0
  python -m claimgate selftest
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Optional

from .benches import BENCH_NAMES, BENCH_DISPATCH
from . import __descriptor__, __version__, __is_prototype__


def _run_bench(name: str, seed: int) -> dict:
    fn = BENCH_DISPATCH[name]
    if name == "holdout":
        return fn(seed=seed)
    if name == "v0":
        return fn(seed=seed)
    return fn(seed=seed)


def _run_v1_full(seed: int) -> dict:
    benches = {}
    for name in BENCH_NAMES:
        if name == "v0":
            continue
        benches[name] = _run_bench(name, seed)
    scores = {}
    for name, res in benches.items():
        if res.get("score"):
            scores[name] = res["score"]
    total_cases = sum(r.get("n_cases", 0) for r in benches.values())
    return {
        "benchmark": "SuperMath ProofBench X",
        "version": __version__,
        "descriptor": __descriptor__,
        "mode": "Adversarial Verification (v1)",
        "is_prototype": __is_prototype__,
        "seed": seed,
        "n_benches": len(benches),
        "total_v1_cases": total_cases,
        "benches": benches,
        "scores": scores,
    }


def _run_v1_single(name: str, seed: int) -> dict:
    res = _run_bench(name, seed)
    return {
        "benchmark": "SuperMath ProofBench X",
        "version": __version__,
        "descriptor": __descriptor__,
        "mode": "Adversarial Verification (v1) -- single bench",
        "is_prototype": __is_prototype__,
        "seed": seed,
        "bench": name,
        "result": res,
        "score": res.get("score"),
    }


def _run_v0(seed: int) -> dict:
    res = _run_bench("v0", seed)
    return {
        "benchmark": "SuperMath ProofBench X",
        "version": __version__,
        "descriptor": __descriptor__,
        "mode": "v0 prototype baseline (NOT real v0)",
        "is_prototype": True,
        "result": res,
    }


def _run_v2_single(name: str, seed: int) -> dict:
    from .benches import V2_BENCH_DISPATCH
    res = V2_BENCH_DISPATCH[name](seed=seed)
    return {
        "benchmark": "SuperMath ProofBench X",
        "version": __version__,
        "descriptor": __descriptor__,
        "mode": f"v2 Invariance & Adversarial Reasoning -- single bench: {name}",
        "is_prototype": __is_prototype__,
        "seed": seed,
        "bench": name,
        "result": res,
        "score": res.get("score"),
    }


def _run_v2_full(seed: int) -> dict:
    from .benches import V2_BENCH_DISPATCH, V2_BENCH_NAMES
    benches = {}
    for name in V2_BENCH_NAMES:
        benches[name] = V2_BENCH_DISPATCH[name](seed=seed)
    scores = {name: res.get("score") for name, res in benches.items() if res.get("score")}
    total_cases = sum(r.get("n_cases", 0) for r in benches.values())
    return {
        "benchmark": "SuperMath ProofBench X",
        "version": __version__,
        "descriptor": __descriptor__,
        "mode": "v2 Invariance & Adversarial Reasoning",
        "is_prototype": __is_prototype__,
        "seed": seed,
        "n_benches": len(benches),
        "total_v2_cases": total_cases,
        "benches": benches,
        "scores": scores,
    }


def _run_physics_single(name: str, seed: int) -> dict:
    from .benches.physics import PHYSICS_BENCH_DISPATCH
    res = PHYSICS_BENCH_DISPATCH[name](seed=seed)
    return {
        "benchmark": "PhysicsGate v0",
        "version": __version__,
        "descriptor": "proof-aware mathematical verification benchmark (physics layer)",
        "mode": f"PhysicsGate -- single bench: {name}",
        "is_prototype": __is_prototype__,
        "seed": seed, "bench": name, "result": res,
        "score": res.get("score"),
    }


def _run_physics_full(seed: int) -> dict:
    from .benches.physics import PHYSICS_BENCH_DISPATCH, PHYSICS_BENCH_NAMES
    from .core.physics import PUBLIC_WORDING
    benches = {}
    for name in PHYSICS_BENCH_NAMES:
        benches[name] = PHYSICS_BENCH_DISPATCH[name](seed=seed)
    scores = {name: res.get("score") for name, res in benches.items() if res.get("score")}
    total_cases = sum(r.get("n_cases", 0) for r in benches.values())
    return {
        "benchmark": "PhysicsGate v0",
        "version": __version__,
        "descriptor": "proof-aware mathematical verification benchmark (physics layer)",
        "public_wording": PUBLIC_WORDING,
        "mode": "PhysicsGate v0 (mathematical and dimensional coherence)",
        "is_prototype": __is_prototype__,
        "seed": seed, "n_benches": len(benches),
        "total_physics_cases": total_cases,
        "benches": benches, "scores": scores,
    }


def _run_theory_single(name: str, seed: int) -> dict:
    from .benches.theory import THEORY_BENCH_DISPATCH
    from .core.theory import PUBLIC_WORDING as THEORY_WORDING
    res = THEORY_BENCH_DISPATCH[name](seed=seed)
    return {
        "benchmark": "TheoryGate v0",
        "version": __version__,
        "descriptor": "proof-aware mathematical verification benchmark (theory layer)",
        "public_wording": THEORY_WORDING,
        "mode": f"TheoryGate v0 -- single bench: {name}",
        "is_prototype": __is_prototype__,
        "seed": seed, "bench": name, "result": res,
        "score": res.get("score"),
    }


def _run_theory_full(seed: int) -> dict:
    from .benches.theory import THEORY_BENCH_DISPATCH, THEORY_BENCH_NAMES
    from .core.theory import PUBLIC_WORDING as THEORY_WORDING
    benches = {}
    for name in THEORY_BENCH_NAMES:
        benches[name] = THEORY_BENCH_DISPATCH[name](seed=seed)
    scores = {name: res.get("score") for name, res in benches.items() if res.get("score")}
    total_cases = sum(r.get("n_cases", 0) for r in benches.values())
    return {
        "benchmark": "TheoryGate v0",
        "version": __version__,
        "descriptor": "proof-aware mathematical verification benchmark (theory layer)",
        "public_wording": THEORY_WORDING,
        "mode": "TheoryGate v0 (structural theory check)",
        "is_prototype": __is_prototype__,
        "seed": seed, "n_benches": len(benches),
        "total_theory_cases": total_cases,
        "benches": benches, "scores": scores,
    }


def _run_evidence_single(name: str, seed: int) -> dict:
    from .benches.evidence import EVIDENCE_BENCH_DISPATCH
    from .core.evidence import PUBLIC_WORDING as EVIDENCE_WORDING
    res = EVIDENCE_BENCH_DISPATCH[name](seed=seed)
    return {
        "benchmark": "EvidencePack/ReproGate v0",
        "version": __version__,
        "descriptor": "proof-aware mathematical verification benchmark (evidence layer)",
        "public_wording": EVIDENCE_WORDING,
        "mode": f"Evidence v0 -- single bench: {name}",
        "is_prototype": __is_prototype__,
        "seed": seed, "bench": name, "result": res,
        "score": res.get("score"),
    }


def _run_evidence_full(seed: int) -> dict:
    from .benches.evidence import EVIDENCE_BENCH_DISPATCH, EVIDENCE_BENCH_NAMES
    from .core.evidence import PUBLIC_WORDING as EVIDENCE_WORDING
    benches = {}
    for name in EVIDENCE_BENCH_NAMES:
        benches[name] = EVIDENCE_BENCH_DISPATCH[name](seed=seed)
    scores = {name: res.get("score") for name, res in benches.items() if res.get("score")}
    total_cases = sum(r.get("n_cases", 0) for r in benches.values())
    return {
        "benchmark": "EvidencePack/ReproGate v0",
        "version": __version__,
        "descriptor": "proof-aware mathematical verification benchmark (evidence layer)",
        "public_wording": EVIDENCE_WORDING,
        "mode": "EvidencePack v0 + ReproGate v0 (reproducibility + audit layer)",
        "is_prototype": __is_prototype__,
        "seed": seed, "n_benches": len(benches),
        "total_evidence_cases": total_cases,
        "benches": benches, "scores": scores,
    }


def _run_replay_single(name: str, seed: int) -> dict:
    from .benches.replay import REPLAY_BENCH_DISPATCH
    from .core.replay import PUBLIC_WORDING as REPLAY_WORDING
    res = REPLAY_BENCH_DISPATCH[name](seed=seed)
    return {
        "benchmark": "ReplayRunner v0",
        "version": __version__,
        "descriptor": "proof-aware mathematical verification benchmark (replay layer)",
        "public_wording": REPLAY_WORDING,
        "mode": f"ReplayRunner v0 -- single bench: {name}",
        "is_prototype": __is_prototype__,
        "seed": seed, "bench": name, "result": res,
        "score": res.get("score"),
    }


def _run_replay_full(seed: int) -> dict:
    from .benches.replay import REPLAY_BENCH_DISPATCH, REPLAY_BENCH_NAMES
    from .core.replay import PUBLIC_WORDING as REPLAY_WORDING
    benches = {}
    for name in REPLAY_BENCH_NAMES:
        benches[name] = REPLAY_BENCH_DISPATCH[name](seed=seed)
    scores = {name: res.get("score") for name, res in benches.items() if res.get("score")}
    total_cases = sum(r.get("n_cases", 0) for r in benches.values())
    return {
        "benchmark": "ReplayRunner v0",
        "version": __version__,
        "descriptor": "proof-aware mathematical verification benchmark (replay layer)",
        "public_wording": REPLAY_WORDING,
        "mode": "ReplayRunner v0 (execute + audit evidence-pack replays)",
        "is_prototype": __is_prototype__,
        "seed": seed, "n_benches": len(benches),
        "total_replay_cases": total_cases,
        "benches": benches, "scores": scores,
    }


def _do_replay(args) -> int:
    """Replay a single evidence pack from a JSON file."""
    from .core.replay import ReplayRunner, load_pack_from_json, PUBLIC_WORDING
    pack = load_pack_from_json(args.pack)
    runner = ReplayRunner(timeout_s=args.timeout)
    result = runner.replay(pack)
    output = {
        "benchmark": "ReplayRunner v0",
        "public_wording": PUBLIC_WORDING,
        "input_pack": args.pack,
        "result": result.to_dict(),
    }
    if args.json:
        print(json.dumps(output, indent=2, default=str))
    else:
        print(f"# ReplayRunner v0 -- {PUBLIC_WORDING}")
        print(f"   input pack: {args.pack}")
        print(f"   pack_id: {result.pack_id}")
        print(f"   verdict: {result.verdict}")
        print(f"   exit_code: {result.exit_code}")
        print(f"   runtime_ms: {result.runtime_ms}")
        print(f"   note: {result.note}")
    return 0


def _run_claim_single(name: str, seed: int) -> dict:
    from .benches.claimgate import CLAIM_BENCH_DISPATCH
    from .core.claimgate import PUBLIC_WORDING as CLAIM_WORDING
    res = CLAIM_BENCH_DISPATCH[name](seed=seed)
    return {
        "benchmark": "ClaimGate v0",
        "version": __version__,
        "descriptor": "proof-aware mathematical verification benchmark (claim layer)",
        "public_wording": CLAIM_WORDING,
        "mode": f"ClaimGate v0 -- single bench: {name}",
        "is_prototype": __is_prototype__,
        "seed": seed, "bench": name, "result": res,
        "score": res.get("score"),
    }


def _run_claim_full(seed: int) -> dict:
    from .benches.claimgate import CLAIM_BENCH_DISPATCH, CLAIM_BENCH_NAMES
    from .core.claimgate import PUBLIC_WORDING as CLAIM_WORDING
    benches = {}
    for name in CLAIM_BENCH_NAMES:
        benches[name] = CLAIM_BENCH_DISPATCH[name](seed=seed)
    scores = {name: res.get("score") for name, res in benches.items() if res.get("score")}
    total_cases = sum(r.get("n_cases", 0) for r in benches.values())
    total_claims = sum(r.get("total_claims_extracted", 0) for r in benches.values())
    total_packs = sum(r.get("total_evidence_packs_created", 0) for r in benches.values())
    return {
        "benchmark": "ClaimGate v0",
        "version": __version__,
        "descriptor": "proof-aware mathematical verification benchmark (claim layer)",
        "public_wording": CLAIM_WORDING,
        "mode": "ClaimGate v0 (extract + classify + route claims to gates)",
        "is_prototype": __is_prototype__,
        "seed": seed, "n_benches": len(benches),
        "total_claim_cases": total_cases,
        "total_claims_extracted": total_claims,
        "total_evidence_packs_created": total_packs,
        "benches": benches, "scores": scores,
    }


def _do_claim(args) -> int:
    """Extract and route claims from a text string."""
    from .core.claimgate import generate_report, PUBLIC_WORDING
    report = generate_report(args.text, seed=args.seed)
    output = {
        "benchmark": "ClaimGate v0",
        "public_wording": PUBLIC_WORDING,
        "report": report.to_dict(),
    }
    if args.json:
        print(json.dumps(output, indent=2, default=str))
    else:
        print(f"# ClaimGate v0 -- {PUBLIC_WORDING}")
        print(f"   original text: {args.text}")
        print(f"   claims extracted: {report.n_claims}")
        print(f"   evidence packs created: {report.n_evidence_packs}")
        print(f"   summary: {report.summary}")
        print()
        for c in report.extracted_claims:
            print(f"   [{c.claim_id}] type={c.claim_type} gate={c.routed_gate} status={c.gate_status}")
            print(f"       text: {c.raw_text[:80]}")
            print(f"       pack: {c.evidence_pack_id} cert={c.certificate_hash[:16]}...")
    return 0


def _run_math_hardening_single(name: str, seed: int) -> dict:
    from .benches.math_hardening import MATH_HARDENING_BENCH_DISPATCH
    from .core.math_hardening import PUBLIC_WORDING as HARDENING_WORDING
    res = MATH_HARDENING_BENCH_DISPATCH[name](seed=seed)
    return {
        "benchmark": "ProofBench X Research Hardening v0",
        "version": __version__,
        "descriptor": "proof-aware mathematical verification benchmark (hardening layer)",
        "public_wording": HARDENING_WORDING,
        "mode": f"Research Hardening v0 -- single bench: {name}",
        "is_prototype": __is_prototype__,
        "seed": seed, "bench": name, "result": res,
        "score": res.get("score"),
    }


def _run_math_hardening_full(seed: int) -> dict:
    from .core.math_hardening.math_hardening_bench import run_math_hardening_bench
    from .core.math_hardening import PUBLIC_WORDING as HARDENING_WORDING
    result = run_math_hardening_bench(seed=seed)
    return {
        "benchmark": "ProofBench X Research Hardening v0",
        "version": __version__,
        "descriptor": "proof-aware mathematical verification benchmark (hardening layer)",
        "public_wording": HARDENING_WORDING,
        "mode": "Research Hardening v0 (domain + assumption + witness + proof objects)",
        "is_prototype": __is_prototype__,
        "seed": seed,
        "total_hardening_cases": result["n_cases"],
        "result": result,
        "score": result.get("score"),
    }


def _selftest() -> dict:
    from .core.exact import Exact, exact_pow, exact_mod_pow, factorial
    from .core.canonical import canonicalize
    from .core.verifier import Verifier
    from .core.families import FAMILY_REGISTRY
    from .core.counterexamples import COUNTEREXAMPLES

    checks = []
    v = Verifier()
    # exact int
    checks.append(("exact_int", Exact.i(5).canonical_string() == "int:5"))
    # exact rational reduction
    checks.append(("exact_frac_reduce", Exact.frac(2, 4).canonical_string() == "rational:1/2"))
    # mod
    checks.append(("exact_mod", Exact.mod(10, 7).canonical_string() == "mod:3/7"))
    # big int preserve
    big = exact_pow(2, 100)
    checks.append(("bigint_2_100", big == 1267650600228229401496703205376))
    # mod exp
    checks.append(("modexp", exact_mod_pow(2, 100, 1000000007) == 1267650600228229401496703205376 % 1000000007))
    # canonicalize commutativity (sum commutes -> same canonical string)
    checks.append(("canon_commute", canonicalize("1 + 2") == canonicalize("2 + 1")))
    # power-vs-mul equivalence: canonical strings need NOT match, but the
    # metamorphic verifier must confirm equivalence via exact value equality.
    eq_pm, _, _, vpm_a, vpm_b = v.verify_metamorphic_pair("3^2", "3*3")
    checks.append(("equiv_powmul", eq_pm and vpm_a is not None and vpm_b is not None
                   and vpm_a.canonical_string() == vpm_b.canonical_string()))
    # scaled-fraction equivalence: same -- verifier must confirm via value.
    eq_sf, _, _, vsf_a, vsf_b = v.verify_metamorphic_pair("1/2", "2/4")
    checks.append(("equiv_scaledfrac", eq_sf and vsf_a is not None and vsf_b is not None
                   and vsf_a.canonical_string() == vsf_b.canonical_string()))
    # family solver sanity
    fam = FAMILY_REGISTRY["f1_sum_chain"]
    truth, cert = v.verify_family_case(fam, fam.base, "selftest:f1")
    checks.append(("family_solver_cert", cert.verified and cert.hash != ""))
    # counterexample is actually false
    ce = COUNTEREXAMPLES[0]
    is_false, _ = v.check_counterexample(ce)
    checks.append(("ce1_is_false", is_false))
    # all counterexamples are actually false (verifier self-check)
    ce_all_false = all(v.check_counterexample(c)[0] for c in COUNTEREXAMPLES)
    checks.append(("all_ce_actually_false", ce_all_false))

    passed = sum(1 for _, ok in checks if ok)
    failed = [(name, ok) for name, ok in checks if not ok]
    return {
        "selftest": "SuperMath ProofBench X v1 prototype",
        "n_checks": len(checks),
        "passed": passed,
        "failed": failed,
        "all_pass": passed == len(checks),
    }


def main(argv: Optional[list] = None) -> int:
    # Python 3.12+ caps int->str conversion at 4300 digits by default (DoS guard).
    # Exactness Stress mode deliberately tests 10k+ digit preservation, so we
    # raise the cap. This is a documented configuration requirement of v1, not
    # a correctness issue.
    try:
        import sys as _sys
        if hasattr(_sys, "set_int_max_str_digits"):
            _sys.set_int_max_str_digits(200000)
    except Exception:
        pass

    p = argparse.ArgumentParser(
        prog="claimgate",
        description=f"SuperMath ProofBench X v1 -- {__descriptor__} (prototype)",
    )
    sub = p.add_subparsers(dest="cmd")

    run = sub.add_parser("run", help="run a benchmark")
    run.add_argument("--math-hardening", action="store_true", help="run ProofBench X Research Hardening v0")
    run.add_argument("--claim", action="store_true", help="run ClaimGate v0")
    run.add_argument("--replay", action="store_true", help="run ReplayRunner v0")
    run.add_argument("--evidence", action="store_true", help="run EvidencePack v0")
    run.add_argument("--repro", action="store_true", help="run ReproGate v0")
    run.add_argument("--theory", action="store_true", help="run TheoryGate v0")
    run.add_argument("--physics", action="store_true", help="run PhysicsGate v0")
    run.add_argument("--v2", action="store_true", help="run v2 (Invariance & Adversarial Reasoning)")
    run.add_argument("--v1", action="store_true", help="run v1 (Adversarial Verification)")
    run.add_argument("--v0", action="store_true", help="run v0 prototype baseline")
    run.add_argument("--json", action="store_true", help="emit JSON")
    from .benches import V2_BENCH_NAMES
    from .benches.physics import PHYSICS_BENCH_NAMES
    from .benches.theory import THEORY_BENCH_NAMES
    from .benches.evidence import EVIDENCE_BENCH_NAMES
    from .benches.replay import REPLAY_BENCH_NAMES
    from .benches.claimgate import CLAIM_BENCH_NAMES
    from .benches.math_hardening import MATH_HARDENING_BENCH_NAMES
    run.add_argument("--bench",
                     choices=([b for b in BENCH_NAMES if b != "v0"] + ["duel"]
                              + V2_BENCH_NAMES + PHYSICS_BENCH_NAMES
                              + THEORY_BENCH_NAMES + EVIDENCE_BENCH_NAMES
                              + REPLAY_BENCH_NAMES + CLAIM_BENCH_NAMES
                              + MATH_HARDENING_BENCH_NAMES),
                     help="run a single bench (v1/v2/physics/theory/evidence/replay/claim/hardening name, or 'duel')")
    run.add_argument("--holdout", action="store_true", help="run holdout bench")
    run.add_argument("--seed", type=int, default=20260622, help="master seed")

    sub.add_parser("selftest", help="run core self-tests")
    sub.add_parser("syntax", help="compile-check all modules (py_compile)")
    sub.add_parser("schema", help="print the JSON result schema")
    sub.add_parser("leaderboard-spec", help="print the leaderboard specification")
    rep = sub.add_parser("report", help="emit a research-grade markdown + JSON report")
    rep.add_argument("--json", action="store_true", help="emit JSON instead of markdown")
    rep.add_argument("--seed", type=int, default=20260622, help="master seed")
    rep.add_argument("--out", type=str, default=None, help="write to file (default: stdout)")

    replay_cmd = sub.add_parser("replay", help="replay a single evidence pack from a JSON file")
    replay_cmd.add_argument("--pack", type=str, required=True, help="path to evidence_pack.json")
    replay_cmd.add_argument("--json", action="store_true", help="emit JSON")
    replay_cmd.add_argument("--timeout", type=int, default=30, help="replay timeout in seconds")

    claim_cmd = sub.add_parser("claim", help="extract and route claims from a text string")
    claim_cmd.add_argument("text", type=str, help="the text to extract claims from")
    claim_cmd.add_argument("--json", action="store_true", help="emit JSON")
    claim_cmd.add_argument("--seed", type=int, default=20260628, help="master seed")

    args = p.parse_args(argv)

    if args.cmd == "selftest":
        result = _selftest()
        print(json.dumps(result, indent=2, default=str))
        return 0 if result["all_pass"] else 1

    if args.cmd == "syntax":
        import py_compile
        root = os.path.dirname(os.path.abspath(__file__))
        errors = []
        count = 0
        for dirpath, _, files in os.walk(root):
            for f in files:
                if f.endswith(".py"):
                    fp = os.path.join(dirpath, f)
                    count += 1
                    try:
                        py_compile.compile(fp, doraise=True)
                    except py_compile.PyCompileError as e:
                        errors.append(str(e))
        print(json.dumps({"syntax_check": "py_compile", "files": count,
                          "errors": errors, "ok": len(errors) == 0}, indent=2))
        return 0 if not errors else 1

    if args.cmd == "schema":
        from .core.schema import RESULT_SCHEMA
        print(json.dumps(RESULT_SCHEMA, indent=2))
        return 0

    if args.cmd == "leaderboard-spec":
        print(_leaderboard_spec())
        return 0

    if args.cmd == "report":
        return _do_report(args)

    if args.cmd == "replay":
        return _do_replay(args)

    if args.cmd == "claim":
        return _do_claim(args)

    if args.cmd == "run":
        seed = args.seed
        if args.math_hardening and args.bench and args.bench in MATH_HARDENING_BENCH_NAMES:
            result = _run_math_hardening_single(args.bench, seed)
        elif args.math_hardening:
            result = _run_math_hardening_full(seed)
        elif args.claim and args.bench and args.bench in CLAIM_BENCH_NAMES:
            result = _run_claim_single(args.bench, seed)
        elif args.claim:
            result = _run_claim_full(seed)
        elif args.replay and args.bench and args.bench in REPLAY_BENCH_NAMES:
            result = _run_replay_single(args.bench, seed)
        elif args.replay:
            result = _run_replay_full(seed)
        elif args.evidence and args.bench and args.bench in EVIDENCE_BENCH_NAMES:
            result = _run_evidence_single(args.bench, seed)
        elif args.evidence:
            result = _run_evidence_full(seed)
        elif args.repro and args.bench and args.bench in EVIDENCE_BENCH_NAMES:
            result = _run_evidence_single(args.bench, seed)
        elif args.repro:
            result = _run_evidence_full(seed)
        elif args.theory and args.bench and args.bench in THEORY_BENCH_NAMES:
            result = _run_theory_single(args.bench, seed)
        elif args.theory:
            result = _run_theory_full(seed)
        elif args.physics and args.bench and args.bench in PHYSICS_BENCH_NAMES:
            result = _run_physics_single(args.bench, seed)
        elif args.physics:
            result = _run_physics_full(seed)
        elif args.holdout and args.v2:
            result = _run_v2_single("holdout", seed)
        elif args.holdout:
            result = _run_v1_single("holdout", seed)
        elif args.v0:
            result = _run_v0(seed)
        elif args.v2 and args.bench and args.bench in V2_BENCH_NAMES:
            result = _run_v2_single(args.bench, seed)
        elif args.v2:
            result = _run_v2_full(seed)
        elif args.bench:
            if args.bench == "duel":
                from .benches.baseline_duel import run_baseline_duel
                duel = run_baseline_duel(seed=seed)
                result = {
                    "benchmark": "SuperMath ProofBench X",
                    "version": __version__,
                    "descriptor": __descriptor__,
                    "mode": "Baseline duel (3-lane)",
                    "is_prototype": __is_prototype__,
                    "seed": seed,
                    "result": duel,
                }
            elif args.bench in V2_BENCH_NAMES:
                result = _run_v2_single(args.bench, seed)
            elif args.bench in PHYSICS_BENCH_NAMES:
                result = _run_physics_single(args.bench, seed)
            elif args.bench in THEORY_BENCH_NAMES:
                result = _run_theory_single(args.bench, seed)
            elif args.bench in EVIDENCE_BENCH_NAMES:
                result = _run_evidence_single(args.bench, seed)
            elif args.bench in REPLAY_BENCH_NAMES:
                result = _run_replay_single(args.bench, seed)
            elif args.bench in CLAIM_BENCH_NAMES:
                result = _run_claim_single(args.bench, seed)
            elif args.bench in MATH_HARDENING_BENCH_NAMES:
                result = _run_math_hardening_single(args.bench, seed)
            else:
                result = _run_v1_single(args.bench, seed)
        elif args.v1:
            result = _run_v1_full(seed)
        else:
            p.print_help()
            return 2

        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            _print_summary(result)
        return 0

    p.print_help()
    return 2


def _leaderboard_spec() -> str:
    return """# SuperMath ProofBench X -- Leaderboard Specification

Descriptor: proof-aware mathematical verification benchmark.

## Lanes (columns)

A leaderboard entry reports scores in THREE lanes, computed on the SAME
problem set:

1. raw_model        -- model answers directly; no tools; no verification.
2. model_plus_tool  -- model may call SuperMath; model still produces final answer.
3. dtl_verified     -- DTL/SuperMath verifier is final authority; may override model.

## Scores (rows)

v0 scores (preserved):
  - Math Trust Score
  - DTL Acceleration
  - Proof Integrity
  - Model Trap Resistance

v1 scores (adversarial verification):
  - Variant Consistency Score
  - Metamorphic Stability Score
  - Counterexample Safety Score
  - Exactness Stress Score
  - Tool Routing Score
  - Replay Stability Score
  - Warm Lane Efficiency Score
  - Holdout Integrity Score

## Eligibility rules

  * Public/dev cases are NOT valid for uncontaminated leaderboard scoring
    if the case set was authored or curated with AI assistance. Fair model
    scores require a FRESH private holdout seed the model has never seen.
  * Expected answers must NEVER be sent to the model in any lane.
  * Model answers cannot override verifier output in Lane C.
  * A lane that did not run is reported as `not_run`, never as a faked zero.
  * `compute_saving_estimate` is time-based; it is NOT a hardware power
    measurement and must not be reported as real power savings.

## Reproducibility

Every entry must include: seed, version, model identifier, tool identifier,
and the exact CLI command used. A third party running the same command with
the same seed must obtain the same scores (deterministic verifier).
"""


def _do_report(args) -> int:
    from .benches.v0_baseline import run_v0
    from .benches.holdout import run_holdout
    from .benches.baseline_duel import run_baseline_duel
    from .core.report import export_research_report, export_json_report

    seed = args.seed
    v0 = run_v0(seed=seed)
    v1 = _run_v1_full(seed)
    holdout = run_holdout(seed=seed)
    duel = run_baseline_duel(seed=seed)

    engine_fixes = [
        "Canonicalizer grammar: 'mod' as infix operator (v1 surfaced f3 render '2^100 mod 997' unparseable).",
        "Canonicalizer grammar: postfix factorial '!' (v1 surfaced f5 render '328!' untokenizable).",
        "Canonicalizer grammar: function calls gcd(a,b)/lcm(a,b); removed unsafe comma stripping from normalize_input.",
        "Holdout leak detection: token-boundary matching instead of naive substring (avoid false-positive '7' inside '997').",
        "Raised sys.set_int_max_str_digits for 10k+ digit exact-preservation tests (Python 3.12 default cap).",
    ]
    limitations = [
        "This is a prototype, not the integrated real-repo v1.",
        "The model adapter is a deterministic Stub, not a real LLM.",
        "compute_saving_estimate is time-based, not hardware-power-measured.",
        "Holdout cases were built with AI assistance and are not valid for an uncontaminated public leaderboard.",
        "v0 scores are emitted as PROTOTYPE hooks; they must be wired to the real v0 score functions on integration.",
    ]

    if args.json:
        envelope = export_json_report(v0, v1, duel, holdout)
        text = json.dumps(envelope, indent=2, default=str)
    else:
        text = export_research_report(
            v0_result=v0,
            v1_full_result=v1,
            duel_result=duel,
            holdout_result=holdout,
            engine_fixes=engine_fixes,
            known_limitations=limitations,
        )

    if args.out:
        with open(args.out, "w") as f:
            f.write(text)
        print(f"report written to {args.out}")
    else:
        print(text)
    return 0


def _print_summary(result: dict) -> None:
    print(f"# {result.get('benchmark','ProofBench X')} -- {result.get('mode','')}")
    print(f"   descriptor: {result.get('descriptor','')}")
    print(f"   version: {result.get('version','')}")
    print(f"   is_prototype: {result.get('is_prototype', True)}")
    if "total_v1_cases" in result:
        print(f"   total_v1_cases: {result['total_v1_cases']}")
        print(f"   benches: {list(result.get('benches', {}).keys())}")
        for name, b in result.get("benches", {}).items():
            sc = b.get("score", {})
            print(f"     - {name}: n={b.get('n_cases',0)} score={sc.get('value')} ({sc.get('detail','')})")
    elif "result" in result:
        r = result["result"]
        print(f"   bench: {r.get('bench')}")
        print(f"   n_cases: {r.get('n_cases',0)}")
        sc = r.get("score", {})
        if sc:
            print(f"   score: {sc.get('value')} ({sc.get('detail','')})")
    elif "bench" in result:
        r = result["result"]
        print(f"   bench: {r.get('bench')}")
        print(f"   n_cases: {r.get('n_cases',0)}")
        sc = result.get("score") or r.get("score", {})
        if sc:
            print(f"   score: {sc.get('value')} ({sc.get('detail','')})")
    print()
    print("(Prototype. Prototype build.)")


if __name__ == "__main__":
    raise SystemExit(main())
