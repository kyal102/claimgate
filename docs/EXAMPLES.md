# Examples

All commands use only the Python standard library. Verdicts come from the
deterministic verifier, never from a language model.

## 30-second showcase

```bash
python -m claimgate --demo
```

Routes a few sample claims, shows the gate verdicts, and runs the verifier
self-test in one command.

## Route claims from a string

```bash
python -m claimgate claim "Energy equals mass times acceleration and proves a new gravity effect that saves 90% power."
```

Each claim is extracted, classified, routed to a gate, and sealed into an
evidence pack:

| Claim | Gate | Verdict | Meaning |
|-------|------|---------|---------|
| Energy = mass × acceleration | UnitGate | `DIMENSIONALLY_INVALID` | the units don't match |
| proves a new gravity effect | ClaimGate | `UNSUPPORTED_CLAIM` | a tool can't establish this; refused, not "proved" |
| saves 90% power | ExperimentalGate | `NEEDS_DATA` | needs a reproducible benchmark + data |

Add `--json` for machine-readable output:

```bash
python -m claimgate claim "saves 40% energy" --json
```

## Verifier self-test

```bash
python -m claimgate selftest
```

Runs the deterministic core checks (exact arithmetic, canonicalization,
metamorphic equivalence, counterexample detection) and exits non-zero on any
failure.

## Replay a sealed evidence pack

```bash
python -m claimgate replay --pack path/to/evidence_pack.json
```

Re-runs the pack's recorded command and reports whether it reproduces.

## Reproducible benchmark report

```bash
python -m claimgate report --seed 20260622 --out report.md
python -m claimgate report --seed 20260622 --json --out report.json
```

The same seed yields the same scores (deterministic verifier).

## What the verdicts mean

- `DIMENSIONALLY_VALID` / `DIMENSIONALLY_INVALID` — units match / don't match.
  Valid means the units are consistent, **not** that the equation is physically
  correct or that any coefficient is right.
- `UNSUPPORTED_CLAIM` — a deterministic tool cannot establish the claim from the
  text. It is **refused, not disproved**.
- `NEEDS_DATA` / needs experiment — attach a reproducible benchmark, dataset, or
  experiment before the claim can be assessed.
- `AMBIGUOUS_NEEDS_CLARIFICATION` — the claim could not be parsed into a check.

See [LIMITATIONS.md](LIMITATIONS.md) for the full scope and caveats.
