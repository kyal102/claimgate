# Reproducibility — ProofBench X / ClaimGate

Everything is deterministic: a run is a pure function of `(code, seed)`. Same seed ⇒ identical cases, results, and certificate hashes.

## Run the benches (real repo)

```
python -m claimgate selftest          # core self-tests
python -m claimgate syntax            # compile-check all modules
python -m claimgate run --v1 --json
python -m claimgate run --v2 --json
python -m claimgate run --math-hardening --json
python -m claimgate run --physics --json
python -m claimgate run --theory --json
python -m claimgate run --evidence --json
python -m claimgate run --repro --json
python -m claimgate run --replay --json
python -m claimgate run --claim --json
python -m claimgate run --v1 --bench varlane --holdout --seed <new> --json
python -m claimgate claim "paste a claim here"
```

Anti-cheat tests:
```
python -m pytest tests/test_claimgate.py -q
```

## EvidencePack
Every gate output can emit a sealed EvidencePack containing: `pack_id`, `pack_schema_version`, `timestamp`, `gate_name`, `gate_version`, `raw_claim_or_input`, `normalized_input`, `status`, `sub_statuses`, `result_body`, `certificate_hash`, `evidence_pack_hash`, `code_hash`, `data_hash`, `seed`, `verifier_version`, `model_used`, `model_role`, `contamination_status`, `limitations`, `next_required_validation`, `repro_command`, `human_readable_summary`. The `code_hash` is computed from the verifying source files (not a static string).

## ReproGate
Compares an original EvidencePack against a re-derived one and **fails on**: certificate drift, missing seed, missing code hash, missing data hash, missing repro command, or an otherwise unverifiable artifact. Reproduction is a first-class, checked outcome.

## ReplayRunner
Executes a pack's `repro_command` with a timeout, **no shell** (argument-list execution; only the Python interpreter may be launched), captures stdout/stderr/exit/runtime, parses the replayed JSON, rebuilds the replayed EvidencePack, and calls ReproGate to compare. ReplayRunner audits; it never changes gate verdicts.

## How drift fails CI
Run the replay/repro benches in CI; any of `DRIFT_DETECTED`, `MISSING_REPRO_COMMAND`, `UNVERIFIABLE_ARTIFACT`, or a sub-1.0 ReplayBench score should fail the build. The in-repo ReplayBench is currently **7/7 (1.0000)** with zero `shell=True`.
