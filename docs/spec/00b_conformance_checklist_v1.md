# HPL Conformance Checklist — v1

## Purpose

This checklist certifies whether an implementation conforms to **HPL Spec v1** as declared in:
- `docs/spec/00_spec_freeze_declaration_v1.md`

Conformance is defined as: implementing behavior that is consistent with all **normative v1 documents** and does not introduce semantics, syntax, fields, or operator classes beyond the frozen scope.

---

## Normative References (MUST)

The implementation MUST treat the following as authoritative:

- `docs/spec/01_alphabet.md`
- `docs/spec/02_bnf.md`
- `docs/spec/02b_macro_boundary.md`
- `docs/spec/03_operator_algebra.md`
- `docs/spec/04_ir_schema.json`
- `docs/spec/04b_ir_freeze_policy.md`
- `docs/spec/06_operator_registry_schema.json`
- `docs/UNIVERSE_INDEX.md`

Informational (not required for v1 conformance):
- `docs/spec/05_qasm_lowering.md`

---

## Conformance Levels

- **Level 0 — Spec Integrity:** No normative specs modified; implementation is separate.
- **Level 1 — Front-End Conformance:** Parser → Macro Expansion → Axiomatic Validation → IR Emission conforms.
- **Level 2 — Extended Tooling (Non-runtime):** Registry schema validation, error reporting, trace mapping.
- **Level 3+ — Runtime/Backends:** Out of scope for v1 unless explicitly added by a new spec version.

This checklist certifies Level 1 (minimum) and Level 2 (recommended).

---

## Level 0 — Spec Integrity (MUST PASS)

[ ] L0.1 Implementation does not modify or reinterpret normative spec files.
[ ] L0.2 Implementation is located outside `_H` sub-Hamiltonian folders.
[ ] L0.3 `_H` folders remain ontology + registries + docs only (no executable code).
[ ] L0.4 The repo maintains a clear boundary between:
      - Surface DSL (examples) and
      - Axiomatic core (BNF-defined)

---

## Level 1 — Front-End Conformance (MUST PASS)

### Step 1 — Surface Parsing

[ ] L1.1 The parser can ingest surface DSL programs written as S-expressions (lists + atoms).
[ ] L1.2 `examples/momentum_trade.hpl` parses successfully.
[ ] L1.3 Parser errors are structural and do not guess semantics.

### Step 2 — Macro Expansion (Normative Boundary)

[ ] L1.4 Macro expansion is deterministic: same input → same output.
[ ] L1.5 Macro expansion is pure: no I/O, measurement, scheduling, or state mutation.
[ ] L1.6 Macro expansion is total:
      - yields axiomatic forms, OR
      - fails with a structural expansion error.
[ ] L1.7 No leakage: IR construction and execution are forbidden on surface forms.
[ ] L1.8 Namespacing of surface-derived identifiers is enforced (e.g., `SURF_`).
[ ] L1.9 Bootstrap canonicalization MAY be used only as structural mapping and is treated as non-semantic.

### Step 3 — Axiomatic Validation

[ ] L1.10 Post-expansion output is validated strictly against `docs/spec/02_bnf.md`.
[ ] L1.11 Any residual surface constructs after expansion are rejected.
[ ] L1.12 Validation errors clearly identify failing form and location/path.

### Step 4 — IR Emission (ProgramIR)

[ ] L1.13 IR emission produces a ProgramIR object conforming to `docs/spec/04_ir_schema.json`.
[ ] L1.14 IR contains no unknown fields (per `04b_ir_freeze_policy.md`).
[ ] L1.15 Operator classes used are within `{U, M, Ω, C, I, A}`.
[ ] L1.16 Bootstrap default `cls=C` is used only under the allowance:
      - only for unclassified, surface-derived operators
      - and is treated as temporary per freeze policy.
[ ] L1.17 IR schema validation is executed as part of the pipeline (automated check).

---

## Level 2 — Recommended Non-runtime Tooling (SHOULD PASS)

[ ] L2.1 Operator registries validate against `docs/spec/06_operator_registry_schema.json`.
[ ] L2.2 Registry entries do not embed executable code; only reference future implementation paths.
[ ] L2.3 Macro expander provides trace mapping from surface to expanded forms (minimum viable).
[ ] L2.4 An audit note exists for any minimal assumptions, stored under `docs/audit/`.
[ ] L2.5 Error types are stable and machine-readable (structured errors).

---

## Prohibited Behaviors (FAIL)

[ ] F.1 Implementing simulator/runtime/scheduler/backends as normative behavior under v1 without a new spec version.
[ ] F.2 Allowing surface constructs to reach IR construction.
[ ] F.3 Adding new operator classes, IR fields, or grammar constructs not present in v1 specs.
[ ] F.4 Accepting unknown IR fields or silently ignoring them.

---

## Certification Record

Implementation name/version: ___________________________

Date: ___________________________

Conformance level achieved (0/1/2): ___________________

Evidence (tests/logs/artifacts): _______________________

Signed (maintainer): _________________________________
