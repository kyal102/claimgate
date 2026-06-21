# Leaderboard Specification — ProofBench X

A leaderboard entry is a tuple of **separately reported** tracks and integrity metrics. **No entry is valid without a fresh, uncontaminated post-implementation holdout** (see `CONTAMINATION_POLICY.md`).

## Tracks (scored separately, never merged)
- **raw_model** — the model answers from the prompt alone. No tools, no verifier access, no expected answers.
- **model_with_tool** — the model may call the verification gate; the verifier is final authority; the model cannot override the verified result.
- **dtl_verified** — the deterministic verifier's own correctness (no model in the loop).

## Integrity metrics (reported for every entry)
- **model_override_resistance** — a model answer must never change the verified result (target: 0 overrides accepted).
- **certificate_stability** — same input ⇒ same certificate hash; zero drift.
- **replay_success** — repro commands re-execute and reproduce without drift (ReplayBench green).
- **refusal_safety** — open problems / invalid input are refused, not answered; no fake proofs.
- **exactness** — exact cases return exact values (no lossy scientific summaries).
- **contamination_status** — `holdout` (fair) or `contaminated` (dev/AI-assisted).

## Eligibility rules
- Public/dev-seed results are **informational only** and must be labeled `CONTAMINATED`.
- Only a run on a **fresh holdout seed generated after implementation**, with expected answers withheld from the model, is leaderboard-eligible.
- Model-only and tool-using systems are scored on **separate** tracks; never compared as if equal.
- An explanation is never counted as a correct answer when the final answer is wrong.

## No-result conditions
An entry is rejected if: it used dev/contaminated cases, the model saw expected answers, any override was accepted, a certificate drifted, replay failed, or a fake/open-problem proof was emitted.
