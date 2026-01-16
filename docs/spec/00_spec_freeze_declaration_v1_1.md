# HPL Spec Freeze Declaration — v1.1

## Status

**DECLARED — FROZEN (Normative)**

This document formally declares **HPL Spec v1.1** as frozen and authoritative,
subject to the constraints and scope defined herein.

---

## Scope of the Freeze

HPL Spec **v1.1** incorporates the following **accepted Spec Change Requests (SCRs)**:

1. **IR Invariants Clarification**
   - Source: `scr_v1_1_ir_invariants_clarification.md`
   - Status: ACCEPTED
   - Effect: Clarifies invariant requirements without altering grammar or IR schema.

2. **Operator Classification Rules**
   - Source: `scr_v1_1_operator_classification_rules.md`
   - Status: ACCEPTED WITH MODIFICATIONS (Completed)
   - Effect: Introduces normative, structural rules for assigning operator classes
     (`U, M, Ω, C, I, A`) without introducing runtime semantics.

3. **Removal of Bootstrap `cls=C` Allowance**
   - Source: `scr_v1_1_remove_bootstrap_cls_c.md`
   - Status: ACCEPTED WITH MODIFICATIONS (Completed)
   - Effect: Removes the v1 bootstrap defaulting allowance; operator classes MUST
     now conform to the v1.1 classification rules.

No other SCRs are included in this freeze.

---

## Normative References (v1.1)

This freeze makes the following documents authoritative for **v1.1**:

- Grammar:
  - `docs/spec/02_bnf.md`
  - `docs/spec/02b_macro_boundary.md`

- IR:
  - `docs/spec/04_ir_schema.json`
  - `docs/spec/04b_ir_freeze_policy.md`

- Operator Registry:
  - `docs/spec/06_operator_registry_schema.json`

- Conformance & Certification:
  - `docs/spec/00b_conformance_checklist_v1_1.md`
  - `docs/spec/00c_conformance_test_mapping_v1_1.md`
  - `docs/spec/00d_certification_report_template_v1.md`

- Governance:
  - `docs/spec/00g_release_versioning_policy_v1.md`
  - `docs/spec/00h_spec_change_request_template_v1.md`
  - `docs/spec/00j_scr_review_checklist_v1.md`

---

## Compatibility Statement

- HPL Spec **v1.1** is **backward compatible** with v1 at the grammar and IR schema level.
- v1.1 introduces **stricter conformance requirements** for operator class assignment.
- Implementations certified under **v1** remain valid for v1 but **must be re-certified**
  to claim v1.1 conformance.

---

## Prohibitions Under This Freeze

While this freeze is in effect:

- No changes MAY be made to:
  - Grammar productions
  - Macro boundary rules
  - IR schema fields or meanings
  - Operator class definitions or criteria

- No new semantics MAY be introduced without:
  - A new SCR
  - A subsequent freeze declaration (v1.2 or v2.0)

---

## Implementation Guidance (Non-Normative)

- Implementations SHOULD:
  - Update IR emission to comply with v1.1 operator classification rules.
  - Remove any reliance on bootstrap `cls=C` defaulting.
  - Update conformance tests to use the v1.1 checklist and mapping.

- Tooling developed under Level-2 remains valid and unaffected by this freeze.

---

## Certification Implications

- Certification claims MUST explicitly state the target version:
  - “HPL Spec v1 (Level-1)” or
  - “HPL Spec v1.1 (Level-1)”

- Mixed claims are invalid.

---

## Declaration

By issuing this document, the maintainers declare that:

- HPL Spec v1.1 is complete, coherent, and review-closed.
- All included SCRs are resolved and aligned.
- The specification is frozen until superseded by a future declared version.

**Effective Date:** 2026-01-16

---

## Notes

- This document supersedes no prior freeze; it **extends** the v1 lineage.
- v1 remains frozen and valid as originally declared.
