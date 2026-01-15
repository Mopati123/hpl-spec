# HPL Spec Freeze Declaration — v1 (Pre-Implementation)

## Status

**Frozen — Normative Specification v1**

This document declares the Hamiltonian Programming Language (HPL) specification
frozen at version **v1**, prior to any normative implementation requirements.

From this point forward, the specification is authoritative. Any implementation
work must conform to the frozen documents listed below.

---

## Scope of Freeze

The following documents constitute the **normative HPL Spec v1**:

### Core Language Law
- `docs/spec/01_alphabet.md`
- `docs/spec/02_bnf.md`
- `docs/spec/02b_macro_boundary.md`

### Semantic & Algebraic Law
- `docs/spec/03_operator_algebra.md`

### Intermediate Representation (IR)
- `docs/spec/04_ir_schema.json`
- `docs/spec/04b_ir_freeze_policy.md`

### Operator Ontology
- `docs/spec/06_operator_registry_schema.json`

### Backend Mapping (Non-Executable, Informational)
- `docs/spec/05_qasm_lowering.md`  
  *(Informational subset mapping; not required for v1 conformance)*

### Universe Governance
- `docs/UNIVERSE_INDEX.md`

---

## Normative Guarantees

As of this freeze:

1. **Axiomatic authority**
   - `02_bnf.md` defines the only forms permitted to reach IR construction.
   - All surface DSL constructs are non-authoritative and MUST macro-expand.

2. **Macro boundary**
   - Macro expansion is deterministic, pure, total, and non-leaking.
   - Bootstrap canonicalization is explicitly temporary and non-semantic.

3. **IR stability**
   - IR v1 is frozen.
   - Additions must be backward compatible.
   - Removals or renames require a version bump.
   - Unknown fields are forbidden.

4. **Operator classification**
   - Operator class enum is fixed as `{U, M, Ω, C, I, A}`.
   - Bootstrap defaulting of `cls = C` is permitted only under the allowance
     defined in `04b_ir_freeze_policy.md` and MUST be removed once classification
     rules are frozen as normative specification.

5. **Ontology via structure**
   - Top-level `_H` directories define sub-Hamiltonians and semantic boundaries.
   - Implementation code MUST NOT alter `_H` folders.

---

## Non-Normative Artifacts

The following are explicitly **non-normative** and do not affect conformance:

- `examples/*.hpl` (surface DSL examples)
- `docs/audit/*` (historical records, assumptions, notes)
- Future implementation files under `src/`

---

## Change Control

Any change to a frozen document listed in the **Scope of Freeze** requires:

1. Explicit version increment (e.g. v1 → v1.1 or v2).
2. Updated freeze declaration.
3. Clear classification as:
   - backward compatible, or
   - breaking change.

No implementation convenience or runtime behavior may override this requirement.

---

## Declaration

This freeze establishes **HPL Spec v1** as a complete, coherent, and
implementation-ready specification.

All future work—human or automated—must treat this specification as law.

**Declared:** HPL Spec v1  
**Phase:** Pre-Implementation  
**Authority:** Specification First (Law before Runtime)
