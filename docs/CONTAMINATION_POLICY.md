# Contamination Policy — ProofBench X

The goal: a model's benchmark score must reflect what it can verify on **unseen** problems, not what it (or its builder) was exposed to during development.

## Rules

1. **AI-assisted cases are not valid for an uncontaminated public leaderboard.**
   Any case whose generation, selection, or expected answer was produced with help from a model that is later evaluated is contaminated for that model.

2. **The private holdout must be generated after implementation.**
   Leaderboard runs use cases generated *after* the system was built, from the same deterministic generators but with a **new seed**, and never previously published.

3. **Model builders must not see expected answers.**
   The system under test receives only the problem prompt. Expected answers, case files, and verifier internals are never shown to the model. (Enforced in code: the duel/scoring layer sends prompt-only inputs.)

4. **Public / dev cases are for development only.**
   The default-seed public/dev set is for regression and demonstration. Scores on it are **informational** and must be labeled `CONTAMINATED` when produced by a model that had access during development.

## Specific to this build

Claude/AI assisted in building and debugging ProofBench X and ClaimGate. Therefore:
- A Claude raw or tool-assisted score on the dev cases is **contaminated** and must be marked so.
- A fair Claude score requires a fresh post-implementation holdout (`--holdout --seed <new>`), with expected answers withheld.
- The DTL-verified score is the verifier's own correctness (no model), but is still only *official* on an uncontaminated holdout.

## Required label on every run
Each run records `is_prototype` and a contamination flag. Public reporting must carry:

> "Built with AI assistance. Raw scores on dev cases are not uncontaminated. Fair model comparison uses fresh holdout cases generated after implementation."
