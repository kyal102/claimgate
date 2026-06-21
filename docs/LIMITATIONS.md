# Limitations — ProofBench X / ClaimGate

Stated plainly, because the value of this system is honesty about what it does and does not establish.

- **Prototype status.** First built in an isolated sandbox, then ported additively into the production engine. **Prototype numbers must be re-run on the production engine before they are cited.** No official benchmark status is claimed until that holds and an uncontaminated holdout exists.
- **No new mathematics is proved.** Only closed, elementary, re-derivable math is verified. Open problems are **refused** (`UNSUPPORTED_CLAIM`), never proved.
- **No new physics is proved.** PhysicsGate checks mathematical and dimensional coherence of physics claims. It does not prove new physics and does not replace experiment.
- **No experimental validation.** Nothing here runs or replaces a physical experiment, lab measurement, or large-scale simulation. Claims needing those are marked `needs simulation` / `needs experiment`.
- **Bounded counterexample search.** Counterexample / falsifiability checks search a bounded space. Absence of a found counterexample is **not** a proof of truth.
- **Heuristic claim extraction.** ClaimGate's extractor/classifier uses regex and heuristics. It can miss, mis-split, or mis-route claims; routing is recorded, not guaranteed optimal.
- **Real-repo integration required.** This stack must keep the production SuperMath verifier and DTL paths intact; it is additive. Its results are only as trustworthy as the in-repo re-run that produced them.
- **Stub participant.** The bundled model adapter is a **simulated** participant with documented weaknesses, used so the benchmark can run end-to-end without an external model. It is never the verifier and never a real model score.
- **TheoryGate scope.** TheoryGate checks whether a proposed theory is mathematically structured, dimensionally coherent, falsifiable and prediction-bearing. It does not prove new physics or replace simulation, experiment, or peer review.

The verifier remains the final authority, and "could not verify" is always preferred over a fabricated pass.
