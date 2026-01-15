# Macro Expansion Bootstrap Notes (Superseded Assumptions)

This file records implementation notes that were originally assumptions and are now
governed by frozen specs.

## Now-Normative Rules (see specs)

1. Namespacing of surface-derived identifiers is mandatory.
   - Source of truth: `docs/spec/02b_macro_boundary.md`

2. Bootstrap canonicalization is allowed:
   - Macro expansion MAY emit a single `(hamiltonian ...)` form with `term` entries
     derived from surface identifiers, as a structural bootstrap mapping (not semantic
     meaning).
   - Source of truth: `docs/spec/02b_macro_boundary.md`

3. Operator class defaults:
   - Implementations MAY default `cls` to `C` only under the bootstrap allowance defined
     in the freeze policy.
   - Source of truth: `docs/spec/04b_ir_freeze_policy.md`

4. Operator class enum:
   - The canonical observer class is `Ω` (not `?`), as corrected in the IR schema.
   - Source of truth: `docs/spec/04_ir_schema.json` and `docs/spec/04b_ir_freeze_policy.md`

## Historical Record

Earlier versions of this file documented provisional assumptions prior to the above
specs being frozen. Those assumptions are now superseded by the cited spec documents.
