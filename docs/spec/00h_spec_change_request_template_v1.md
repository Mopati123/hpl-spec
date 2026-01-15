# HPL Spec Change Request (SCR) — v1

## Purpose

This template governs **proposals to change, extend, or clarify** the Hamiltonian
Programming Language (HPL) specification after the **v1 freeze**.

It ensures that:
- All changes are explicit, reviewable, and versioned
- Backward compatibility is assessed before approval
- No implementation-driven drift occurs

Submission of an SCR does **not** imply approval.

---

## Normative References

All change requests are evaluated against:

- `docs/spec/00_spec_freeze_declaration_v1.md`
- `docs/spec/00b_conformance_checklist_v1.md`
- `docs/spec/00c_conformance_test_mapping_v1.md`
- `docs/spec/00d_certification_report_template_v1.md`
- `docs/spec/00e_implementation_intake_checklist_v1.md`
- `docs/spec/00f_ci_gate_policy_v1.md`
- `docs/spec/00g_release_versioning_policy_v1.md`

Core language law:
- `docs/spec/01_alphabet.md`
- `docs/spec/02_bnf.md`
- `docs/spec/02b_macro_boundary.md`
- `docs/spec/03_operator_algebra.md`
- `docs/spec/04_ir_schema.json`
- `docs/spec/04b_ir_freeze_policy.md`
- `docs/spec/06_operator_registry_schema.json`
- `docs/UNIVERSE_INDEX.md`

---

## Change Request Metadata

- SCR ID:
- Title:
- Author(s):
- Date submitted:
- Target spec version (e.g., v1.1 or v2.0):
- Affected documents:
- Change category:
  - [ ] Clarification (non-semantic)
  - [ ] Backward-compatible extension
  - [ ] Breaking change (requires MAJOR version)

---

## Motivation

Describe the problem or limitation in the current specification.

- What is unclear, insufficient, or blocking?
- Why does this require a spec change rather than an implementation choice?

---

## Proposed Change

Describe the proposed modification **precisely**:

- New or changed text (quote current → proposed)
- New rules, constraints, or definitions (if any)
- Explicitly state what is **not** changing

Avoid implementation details.

---

## Impact Analysis (Required)

### A) Compatibility

- Does this change preserve backward compatibility?
  - [ ] Yes (MINOR version)
  - [ ] No (MAJOR version required)

Explain why.

### B) Affected Areas

Check all that apply:
- [ ] Alphabet / Keywords
- [ ] Axiomatic Grammar (BNF)
- [ ] Macro Boundary
- [ ] Operator Algebra / Classes
- [ ] IR Schema
- [ ] Operator Registry Schema
- [ ] CI / Conformance / Certification
- [ ] Release & Versioning Policy
- [ ] Other (specify)

---

## Migration Strategy (If Breaking)

(Required for MAJOR changes only)

- How should existing implementations adapt?
- Are shims, deprecations, or dual-support periods defined?
- Target removal version (if applicable):

---

## Conformance Implications

Describe how this change affects:

- Conformance Checklist items
- Conformance Test Mapping
- Certification Reports

List any checklist items that must be updated or added.

---

## Alternatives Considered

List alternative approaches and explain why they were rejected.

---

## Decision Record

(To be completed by spec maintainers)

- Decision:
  - [ ] Accepted
  - [ ] Accepted with modifications
  - [ ] Rejected
  - [ ] Deferred

- Decision rationale:
- Approved target version:
- Required follow-up actions:
- Updated freeze declaration required:
  - [ ] Yes
  - [ ] No

---

## Status

- Current status:
  - [ ] Draft
  - [ ] Under review
  - [ ] Approved
  - [ ] Implemented (spec-only)
  - [ ] Superseded

---

## Notes

- No implementation work may rely on an SCR until it is **approved and frozen**
  as part of a new spec version.
- All approved SCRs must be referenced in the next **Spec Freeze Declaration**.
