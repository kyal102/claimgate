# Benchmark Card — ProofBench X (Prototype)

## Purpose
Measure whether a *system* can **verify, reproduce, certify, and safely refuse** mathematical and scientific claims **without trusting a model**. It scores the verification/trust layer, not a model's eloquence.

## What it tests
- **Exactness** — exact integer / rational / modular / big-integer arithmetic; no float drift on exact cases; full-digit preservation (scientific summaries are rejected).
- **Invariance & metamorphic equivalence** — equivalent forms (commuted sums, pow-vs-mul, factored-vs-expanded, surface noise) must agree.
- **Adversarial reasoning (v2)** — disguised inputs, deep chains, parser traps, refusal correctness.
- **Counterexample resistance** — plausible-but-false identities must be rejected; the verifier independently computes the disproof.
- **Domain / assumption hardening** — hidden non-zero / positivity / invertibility conditions, proof-object construction, witness checks.
- **PhysicsGate** — unit/dimensional coherence, limits, conservation templates, uncertainty propagation, bounded counterexample search.
- **TheoryGate** — variable definition, known-law consistency, falsifiability, prediction-bearing structure.
- **Certificate stability** — same input → same certificate hash; drift is detectable.
- **Replay** — repro commands re-execute (no shell) and reproduce without drift.
- **Model-override resistance** — a model answer can never change the verified result.

## What it does NOT test
- Whether a model can *answer* frontier math problems (this is not a model-answer benchmark).
- New mathematics or new physics (none is proved; open problems are refused).
- Experimental/physical truth (no experiment or simulation is run or replaced).
- Public-leaderboard standing (none is claimed; see `LEADERBOARD_SPEC.md`).

## Supported gates
SuperMath/ProofBench X v1, ProofBench X v2, Research Hardening (Domain/Assumption/Witness/ProofObject), PhysicsGate (Unit/Limit/Conservation/Uncertainty/Counterexample), TheoryGate (Variable/KnownLaw/Falsifiability/Prediction), EvidencePack + ReproGate, ReplayRunner, ClaimGate.

## Case counts (real in-repo run; `is_prototype=true`)
| Lane | Cases |
|---|---|
| ProofBench X v1 | 395 |
| ProofBench X v2 | 115 |
| Math Hardening | 66 |
| PhysicsGate | 57 |
| EvidencePack / ReproGate | 35 |
| TheoryGate | 20 |
| ClaimBench | 20 |
| ReplayBench | 7 (7/7 green) |

(These are reproducible via the commands in `REPRODUCIBILITY.md`. The v1 stub-participant scores reflect the simulated model's documented weaknesses, which the bench is designed to detect — not the verifier's correctness.)

## Scoring
Per-lane named scores (e.g. Variant Consistency, Counterexample Rejection, Exact Preservation, Certificate Stability, Replay, Refusal Safety). Verified outcomes only: an explanation is never scored as correctness when the final answer is wrong, and a model answer never overrides the verifier.

## Limitations
See `LIMITATIONS.md`. Prototype; bounded counterexample search; regex/heuristic claim extraction; real-repo re-run required before any official number.

## Contamination rules
See `CONTAMINATION_POLICY.md`. Cases generated with AI assistance and the public/dev set are for development only; leaderboard results require a fresh, post-implementation private holdout where model builders never see expected answers.
