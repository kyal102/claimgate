<p align="center"><img src="assets/logo.png" alt="ClaimGate" width="140"></p>

# ClaimGate · ProofBench X

## Paste an AI science claim. ClaimGate checks what survives.

![ClaimGate](docs/social_preview.png)

AI will confidently tell you it discovered new physics. **ClaimGate** doesn't argue — it extracts each claim, routes it to a deterministic verification gate, seals an evidence pack with a certificate hash, and tells you exactly what survives.

### One command (no dependencies — pure Python stdlib)

```bash
python -m claimgate claim "Energy equals mass times acceleration and proves a new gravity effect that saves 90% power."
```

### Real output (reproduce it yourself)

| Claim | Gate | Verdict |
|---|---|---|
| Energy = mass × acceleration | UnitGate | **DIMENSIONALLY_INVALID** |
| proves a new gravity effect | ClaimGate | **UNSUPPORTED_CLAIM** |
| saves 90% power | ExperimentalGate | **NEEDS_DATA** |

*3 claims extracted · 3 evidence packs sealed · replay reproducible.*

**AI proposes. Gates verify. Unsupported claims do not survive.**

This does **not** prove scientific truth. It records what was checked, what failed, what needs evidence, and what still requires simulation or experiment. Open problems are refused (`UNSUPPORTED_CLAIM`), never "proved".

---

→ **[60-second demo](docs/DEMO.md)** · **[Benchmark docs](docs/README.md)** · **[Limitations](docs/LIMITATIONS.md)** · **[Contamination policy](docs/CONTAMINATION_POLICY.md)**

## More commands

```bash
python -m claimgate selftest                  # core self-tests
python -m claimgate run --physics --json      # PhysicsGate (dimensional coherence)
python -m claimgate run --replay  --json      # evidence-pack replay audit
python -m claimgate claim "your claim" --json # full evidence packs
python -m pytest tests/ -q                        # anti-cheat tests
```

## The math benchmark

ProofBench X is also a **math verification benchmark** — it tests whether a system can verify exact arithmetic, metamorphic equivalence, counterexamples, certificate stability and replay *without trusting a model*.

```bash
python -m claimgate run --v1 --json     # 395 cases
python -m claimgate run --v2 --json     # 115 cases
```

The verifier's integrity scores are perfect (metamorphic, certificate stability, replay, parser, disguise, deep-chain all **1.0**); the bundled **simulated** model fails exactly where untrusted models fail (numeric slips, false identities, lost exactness). **That gap is the point.** → **[Math benchmark scoreboard](docs/MATH_BENCHMARK.md)**

## Ecosystem

ClaimGate is the front door. Each gate it routes to is also a **small, standalone,
MIT-licensed tool** you can adopt on its own — pure stdlib, no private code:

| Tool | Does | Repo |
|------|------|------|
| **UnitGate** | dimensional consistency of `LHS = RHS` | [kyal102/unitgate](https://github.com/kyal102/unitgate) |
| **EvidencePack** | seal a verdict with a deterministic certificate hash | [kyal102/evidencepack](https://github.com/kyal102/evidencepack) |
| **ReplayGate** | re-run a sealed pack, detect drift (safe `shell=False` allowlist) | [kyal102/replaygate](https://github.com/kyal102/replaygate) |
| **ClaimLint** | lint README/docs for over-claims (CLI + GitHub Action) | [kyal102/claimlint](https://github.com/kyal102/claimlint) |
| **ClaimStack** | end-to-end demo wiring the above into one pipeline | [kyal102/claimstack-demo](https://github.com/kyal102/claimstack-demo) |

Try it in one command:

```bash
python -m claimgate --demo
```

## What this is

**ProofBench X / ClaimGate** is proof-aware verification infrastructure: exact math, symbolic invariance, counterexample witnesses, dimensional (PhysicsGate) and theory (TheoryGate) coherence checks, sealed evidence packs, drift-detecting replay, and claim extraction/routing — all decided by a deterministic verifier, never a model. Powered by the **JARVI3 / DTL** verification engine.

> Prototype status — no public-leaderboard eligibility until an uncontaminated, post-implementation holdout exists (see [docs/CONTAMINATION_POLICY.md](docs/CONTAMINATION_POLICY.md)). The verifier is the final authority.

## License

MIT — see [LICENSE](LICENSE). (Change if you prefer a different license.)
