# HPL Implementation Intake Checklist — v1

## Purpose

This checklist is a **mandatory pre-implementation gate** for HPL Spec v1.
It ensures teams (human or automated) are aligned with the frozen specification
*before* any new executable code is written or extended.

Passing this checklist authorizes implementation work to begin under v1.

---

## Normative References (READ & ACKNOWLEDGE)

The implementer MUST acknowledge the following as authoritative law:

- `docs/spec/00_spec_freeze_declaration_v1.md`
- `docs/spec/00b_conformance_checklist_v1.md`
- `docs/spec/00c_conformance_test_mapping_v1.md`
- `docs/spec/00d_certification_report_template_v1.md`

Core specs:
- `docs/spec/01_alphabet.md`
- `docs/spec/02_bnf.md`
- `docs/spec/02b_macro_boundary.md`
- `docs/spec/03_operator_algebra.md`
- `docs/spec/04_ir_schema.json`
- `docs/spec/04b_ir_freeze_policy.md`
- `docs/spec/06_operator_registry_schema.json`
- `docs/UNIVERSE_INDEX.md`

---

## Intake Assertions (MUST ALL BE TRUE)

### Governance & Scope

[x] I understand that **HPL Spec v1 is frozen** and authoritative.  
[x] I will not modify any normative spec documents during implementation.  
[x] Any required clarification will be recorded under `docs/audit/`, not coded.  
[x] Any change request requires a new spec version (v1.1 or v2).

### Allowed Work (v1)

[x] Implement **front-end only** (Parser → Macro Expansion → Axiomatic Validation → IR Emission).  
[x] Add conformance tests that map directly to checklist items.  
[x] Validate IR strictly against `docs/spec/04_ir_schema.json`.  
[x] Keep all executable code outside `_H` sub-Hamiltonian folders.

### Prohibited Work (v1)

[x] Do NOT implement runtime, simulator, scheduler, observers, or backends.  
[x] Do NOT add new grammar constructs, operator classes, or IR fields.  
[x] Do NOT allow surface DSL constructs to reach IR construction.  
[x] Do NOT accept unknown IR fields or silently ignore schema violations.

---

## Bootstrap Allowances (Explicitly Understood)

[x] I understand that `cls = C` defaulting is **temporary** and governed by
    `docs/spec/04b_ir_freeze_policy.md`.  
[x] I understand that bootstrap canonicalization is **structural only** and non-semantic.  
[x] I understand that namespacing of surface-derived identifiers is **mandatory**.

---

## Certification Commitment

[x] I commit to producing a completed **Certification Report v1**
    (`docs/spec/00d_certification_report_template_v1.md`) before claiming conformance.  
[x] I commit to running and documenting all tests mapped in
    `docs/spec/00c_conformance_test_mapping_v1.md`.

---

## Intake Declaration

By checking all items above, I acknowledge that implementation work will be
performed strictly under **HPL Spec v1** and subject to certification.

- Implementer / Team: Codex execution (per user instruction)
- Role / Affiliation: Automated implementation agent
- Date: 2026-01-15
- Signature (typed acceptable): Codex

---

## Notes

- This checklist authorizes work; it does not certify outcomes.
- Failure to satisfy this checklist invalidates any subsequent certification claim.
