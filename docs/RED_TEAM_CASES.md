# Red-Team Cases — ProofBench X / ClaimGate

Discovered failure families the stack is built to catch. Each is either caught by a gate (verdict shown) or refused. "Caught" means the deterministic verifier detects the problem; it never silently passes.

## Input / parser traps
| Family | Description | Handling |
|---|---|---|
| **unicode minus** | `−` (U+2212) vs ASCII `-` | normalized; mismatch refused, not silently accepted |
| **superscripts** | `x²`, `10³` unicode powers | normalized to explicit power or refused |
| **zero-width spaces** | hidden U+200B inside tokens | stripped/normalized; injection refused |
| **ambiguous division** | `a/b/c` left-assoc vs intended grouping | canonical grammar fixes associativity; ambiguity refused |
| **pow ambiguity** | `2^3^2` right-assoc vs left | explicit grammar; otherwise refused |
| **scientific notation exactness loss** | `1.23e4567` as an "exact" answer | rejected — exact preservation requires full digits |

## Math traps
| Family | Description | Handling |
|---|---|---|
| **false identities** | plausible but wrong (e.g. `(a+b)²=a²+b²`) | verifier computes lhs/rhs, rejects |
| **fake proof traps** | "proof" of a false/open statement | refused; no certificate issued |
| **missing domain assumptions** | identity true only on a domain | DomainGate flags required assumptions |
| **hidden nonzero assumptions** | division/inverse assuming `x≠0` | AssumptionGate surfaces the hidden condition |
| **sqrt absolute-value traps** | `√(x²)=x` (should be `|x|`) | WitnessGate counterexample at `x<0` |
| **log positivity traps** | `log(ab)=log a+log b` w/o `a,b>0` | AssumptionGate flags positivity |
| **modular inverse traps** | inverse mod m when `gcd≠1` | refused (no inverse exists) |
| **matrix invertibility traps** | inverse of a singular matrix | refused, not a fabricated inverse |

## Evidence / replay traps
| Family | Description | Handling |
|---|---|---|
| **certificate drift** | replayed cert hash ≠ original | `DRIFT_DETECTED` |
| **missing seed** | pack lacks a seed | ReproGate fails |
| **missing code hash** | pack lacks a real code hash | ReproGate fails |
| **missing data hash** | pack lacks a data hash where required | ReproGate fails |
| **missing repro command** | pack cannot be replayed | `MISSING_REPRO_COMMAND` |
| **unsupported artifact** | output not parseable/verifiable | `UNVERIFIABLE_ARTIFACT` |
| **contaminated holdout** | model saw the cases | flagged `CONTAMINATED`, not leaderboard-eligible |

## Claim-routing traps
| Family | Description | Handling |
|---|---|---|
| **claim extraction / routing bugs** | mis-split or mis-routed claims | recorded as routed-but-unverified; never reported as proved |

## Real engine fixes this red-teaming forced (prototype canonicalizer)
- `mod` accepted as an infix operator (was prefix-only) so `2^100 mod 997` parses.
- postfix factorial `!` tokenized so `328!` parses.
- function calls `gcd(a,b)`/`lcm(a,b)` supported; removed unsafe thousands-separator comma stripping that mangled `gcd(123,456)`.
- holdout prompt-leak detection switched from naive substring to token-boundary matching (substring falsely flagged answer `7` inside problem `997`).
- raised the integer→string digit cap so 10k+ digit exact-preservation cases run.
