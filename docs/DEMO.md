# Paste an AI science claim. ClaimGate checks what survives.

> **ProofBench X · ClaimGate** — proof-aware claim verification (powered by the JARVI3 / DTL engine).

![ClaimGate](social_preview.png)

AI will confidently tell you it discovered new physics. **ClaimGate** doesn't argue with it — it extracts each claim, routes it to a verification gate, seals an evidence pack, and tells you exactly what survives and what doesn't. It does not prove scientific truth; it records what was checked, what failed, what needs evidence, and what needs an experiment.

## One command

```
python -m proofbench_x claim "Energy equals mass times acceleration and proves a new gravity effect that saves 90% power."
```

## Real output (not a mock-up — reproduce it yourself)

```
ClaimGate v0 — extracts and routes scientific claims to verification gates.
Extracted 3 claim(s): 0 passed, 1 failed, 2 need evidence/clarification.

[claim_000] gate=UnitGate        status=DIMENSIONALLY_INVALID
    "Energy equals mass times acceleration"        (E has units M·L²·T⁻², m·a has M·L·T⁻²)

[claim_001] gate=ClaimGate       status=UNSUPPORTED_CLAIM
    "proves a new gravity effect"                  (no support; an open/unsupported assertion)

[claim_002] gate=ExperimentalGate status=NEEDS_DATA
    "saves 90% power"                              (quantitative — needs a benchmark dataset + data_hash)

evidence packs created: 3   ·   each sealed with a certificate hash   ·   replay: reproducible
```

The full JSON (with certificates, evidence packs, and `next_required_validation` for each claim) is in [`EXAMPLE_REPORTS/claimgate_viral_demo.json`](EXAMPLE_REPORTS/claimgate_viral_demo.json).

## Try your own

```
python -m proofbench_x claim "your messy AI or human science claim here"
python -m proofbench_x claim "your claim" --json   # full evidence packs
```

## What it is — and isn't

ClaimGate **extracts and routes** claims; the deterministic gates decide verdicts and the verifier is the final authority. It **does not** prove new physics, prove scientific truth, replace experiment, or solve open problems. Open problems are refused (`UNSUPPORTED_CLAIM`), never "proved". See [`LIMITATIONS.md`](LIMITATIONS.md) and [`CONTAMINATION_POLICY.md`](CONTAMINATION_POLICY.md). Prototype status — numbers require a real-repo re-run before any official claim.

> **Set this image as the repo's social preview** (GitHub → repo Settings → Social preview → upload `docs/social_preview.png`) so the hook shows when the repo is shared.
