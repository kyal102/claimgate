# Contributing to ProofBench X / ClaimGate

Thanks for your interest! This project is **proof-aware verification infrastructure**: the deterministic verifier is the final authority, and a model can never override it. Contributions must preserve that.

## Ground rules
- **No cheating.** The verifier re-derives truth; never hardcode benchmark answers, never let a model output decide correctness.
- **No over-claims.** No "proves new physics", "solves open problems", "official leaderboard", or "scientific truth guaranteed" wording. Open problems are refused, not proved.
- **Reproducible.** Everything is a pure function of `(code, seed)`. Same seed ⇒ identical cases, results, and certificate hashes.
- **No new dependencies** without strong reason — the core is pure Python stdlib.

## Dev loop
```bash
python -m claimgate selftest          # core self-tests (must be 11/11)
python -m claimgate syntax            # compile-check all modules (0 errors)
python -m pytest tests/ -q               # anti-cheat tests (must pass)
python -m claimgate run --replay --json   # ReplayBench must be 7/7
```

## What CI enforces (must stay green)
Syntax, anti-cheat tests, `shell=True` count == 0, ReplayBench == 1.0, and ClaimGate must keep refusing open-problem claims (e.g. "I have proven the Riemann Hypothesis" → `UNSUPPORTED_CLAIM`).

## Good first contributions
- New red-team cases in `docs/RED_TEAM_CASES.md` (with a gate that catches them).
- New deterministic benchmark cases (with a seed).
- Better claim extraction/routing heuristics (keep them transparent — no NLP model).

By contributing you agree your work is licensed under the repo's MIT license.
