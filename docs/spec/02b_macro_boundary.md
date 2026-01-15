# Macro Boundary (Normative)

This document defines the macro-expansion boundary between the Surface DSL and the Axiomatic Core.

## 1. Definitions

- **Surface form:** Any construct not defined in `docs/spec/02_bnf.md`.
- **Axiomatic core form:** Any construct defined in `docs/spec/02_bnf.md`.
- **Macro expansion:** A deterministic rewrite from surface forms to axiomatic core forms.

## 2. Requirements

1. **Determinism:** The same surface input must expand to the same axiomatic output.
2. **Purity:** Macro expansion must not perform I/O, measurement, scheduling, or state mutation.
3. **Totality:** Expansion must either produce axiomatic forms or fail with a structural error.
4. **No leakage:** IR construction and execution are forbidden on surface forms.
5. **Traceability:** The expanded output must retain source mapping sufficient for debugging/audit.
6. **Namespacing:** Expanded operators derived from surface identifiers MUST be namespaced
   (e.g., `SURF_`) to preserve provenance and avoid collisions.

## 2b. Bootstrap Canonicalization

During bootstrap, macro expansion MAY temporarily canonicalize surface programs into a single
`(hamiltonian ...)` containing terms derived from surface identifiers. This
canonicalization is structural only and carries no semantic meaning until operator
library and coefficient semantics are specified.

## 3. Conformance

A program is valid for IR construction iff, after expansion:
- It conforms to `docs/spec/02_bnf.md`, and
- Its expanded operator classes and invariant declarations are representable in `docs/spec/04_ir_schema.json`.
