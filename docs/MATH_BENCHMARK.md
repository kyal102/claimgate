# ProofBench X — Math Verification Benchmark

A benchmark for **verified mathematical infrastructure**, not for model answers. It asks: *can a system verify, reproduce, certify, and safely refuse math without trusting a model?* The deterministic verifier re-derives every truth; a model output is graded, never trusted.

> **Prototype.** These are real in-repo numbers, but the bundled participant is a **simulated** model (documented weaknesses) — not a real model and not an official leaderboard number. No leaderboard eligibility until an uncontaminated, post-implementation holdout (see [CONTAMINATION_POLICY.md](CONTAMINATION_POLICY.md)). Full numbers in [`../results/math_benchmark_scoreboard.json`](../results/math_benchmark_scoreboard.json).

## Run it

```bash
python -m claimgate run --v1 --json     # adversarial verification (395 cases)
python -m claimgate run --v2 --json     # invariance & adversarial reasoning (115 cases)
python -m claimgate run --v1 --bench metamorphic --json
python -m claimgate run --v1 --bench counterexample --json
python -m claimgate run --v1 --holdout --seed 20260622 --json   # fresh holdout
```

## What it tests
ExactCore (no float drift, full-digit preservation), metamorphic equivalence (commuted sums, pow-vs-mul, factored-vs-expanded, surface noise), counterexample resistance (plausible-but-false identities), deep reasoning chains, parser/disguise traps, certificate stability, replay reproducibility, and refusal safety.

## Scoreboard (real, prototype) — read it honestly

**Verifier integrity** — the benchmark's own soundness. All perfect:

| Check | Score |
|---|---|
| Metamorphic equivalence | **1.0** |
| Certificate stability (no drift) | **1.0** |
| Replay reproducibility | **1.0** |
| Parser robustness | **1.0** |
| Disguise resistance | **1.0** |
| Deep-chain integrity | **1.0** |
| Holdout determinism | **1.0** |
| Warm-lane (no regression) | **1.0** |

**Simulated stub participant** — the bundled fake model with documented weaknesses (this is the *demonstration*, not the benchmark's score):

| Where untrusted models fail | Stub score |
|---|---|
| Variant consistency (numeric slips) | 0.0 |
| Counterexample rejection (v1 / v2) | 0.75 / 0.8 |
| Exact preservation (sci-notation summaries) | 0.5 / 0.58 |
| Tool routing | 0.75 |
| Refusal safety | 0.7 |

**The gap is the point.** The verifier holds; the model fails exactly where models fail — numeric slips, accepting plausible-but-false identities, losing exactness to scientific summaries, mis-routing, under-refusing. You don't trust a model's math. You verify it.

## How to score a *real* model
Plug a real model adapter in place of the stub and run on a **fresh holdout seed** (so the model never saw the cases), then report its raw track and its tool-assisted track separately from the verifier's. See [LEADERBOARD_SPEC.md](LEADERBOARD_SPEC.md) and [DATASET_CARD.md](DATASET_CARD.md).

## What this is NOT
It is not a "hardest math" benchmark, does not prove new mathematics, does not solve open problems, and claims no official leaderboard rank. Open problems are refused. The verifier is the final authority.
