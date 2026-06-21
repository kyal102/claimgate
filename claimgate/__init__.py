"""
Prototype: SuperMath ProofBench X v1 -- Adversarial Verification Mode
=====================================================================

  *** PROTOTYPE -- NOT THE REAL v0 MODULE ***

This package is a self-contained, runnable prototype of the v1
"Adversarial Verification Mode" extension for SuperMath ProofBench X.

It is intentionally placed OUTSIDE the production import path
(`the host project's production verifier`) so that it cannot be
accidentally merged into or confused with the real v0 module that lives
in the host project (the host project).

This sandbox could not authenticate to the the host project, so this
prototype was built blind to the real v0 internals. It therefore:

  * Does NOT reproduce the real v0 baseline. A clearly-labeled
    `v0_prototype_baseline` bench is provided ONLY so the v1 machinery
    has something to compare against and to prove v0-shaped tests still
    pass. It is explicitly NOT the real v0.
  * Does NOT write to `docs/supermath_claimgate/` or `Packages.html`.
  * Does NOT hardcode any answers in the verifier.
  * Does NOT let model outputs decide correctness.
  * Does NOT hide failures, fake proofs, or claim open problems solved.
  * Does NOT show unrun/fake scores in its output.

See PATCH_PLAN.md for the exact integration steps into the real repo.

Descriptor (mandatory wording):
    "proof-aware mathematical verification benchmark"
(Never "world's hardest math benchmark.")
"""

__version__ = "1.0.0-prototype"
__descriptor__ = "proof-aware mathematical verification benchmark"
__is_prototype__ = True
