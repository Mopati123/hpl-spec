# HPL Spec Freeze Declaration - v2.0

## Status

**DECLARED - FROZEN (Normative)**

This document formally declares **HPL Spec v2.0** as frozen and authoritative,
subject to the scope, constraints, and prohibitions defined herein.

---

## Scope of the Freeze

HPL Spec **v2.0** incorporates the following **Level-3 semantic Spec Change Requests (SCRs)**,
all of which are **READY** and review-complete:

1. **Scheduler Model**
   - Source: `docs/spec/scr_level3_scheduler_model.md`
   - Effect: Establishes the scheduler as the sole semantic authority over execution ordering and evolution.

2. **Execution Semantics**
   - Source: `docs/spec/scr_level3_execution_semantics.md`
   - Effect: Defines program state, evolution, and observables under scheduler control.

3. **Measurement & Observation**
   - Source: `docs/spec/scr_level3_measurement_observation.md`
   - Effect: Defines explicit, auditable measurement events and observer capabilities.

4. **Determinism Policy**
   - Source: `docs/spec/scr_level3_determinism_policy.md`
   - Effect: Specifies how determinism, replayability, and nondeterminism claims are declared and certified.

No other SCRs are included in this freeze.

---

## Normative References (v2.0)

The following documents are authoritative for **HPL Spec v2.0**:

### Language & Structure
- `docs/spec/02_bnf.md`
- `docs/spec/02b_macro_boundary.md`

### Intermediate Representation
- `docs/spec/04_ir_schema.json`
- `docs/spec/04b_ir_freeze_policy.md`

### Operator Registry
- `docs/spec/06_operator_registry_schema.json`

### Level-3 Conformance & Certification
- `docs/spec/00n_conformance_checklist_level3_v2_0.md`
- `docs/spec/00o_conformance_test_mapping_level3_v2_0.md`

### Governance
- `docs/spec/00g_release_versioning_policy_v1.md`
- `docs/spec/00h_spec_change_request_template_v1.md`
- `docs/spec/00j_scr_review_checklist_v1.md`
- `docs/spec/00m_v2_0_freeze_prerequisites.md`

### Migration
- `docs/audit/hpl_v1_1_to_v2_0_migration_memo.md`

---

## Compatibility Statement

- **HPL Spec v2.0 is a breaking release.**
- HPL Spec **v1** and **v1.1** remain **valid, frozen, and supported**.
- Implementations certified under v1 or v1.1 **do not implicitly conform** to v2.0.
- Any claim of v2.0 conformance **requires Level-3 certification**.

---

## Prohibitions Under This Freeze

While this freeze is in effect:

- No changes MAY be made to:
  - Scheduler semantics
  - Execution semantics
  - Measurement or observation rules
  - Determinism policy definitions

- No reinterpretation of v2.0 semantics is permitted without:
  1. A new Spec Change Request (SCR), and
  2. A subsequent freeze declaration (v2.1 or v3.0).

---

## Certification Implications

- v2.0 conformance claims MUST:
  - Pass the **Level-3 conformance checklist**
  - Satisfy the **Level-3 test mapping**
  - Explicitly declare the **scheduler policy** used

- Mixed claims (e.g., "v1 grammar with v2 execution") are **invalid**.

---

## Declaration

By issuing this document, the maintainers declare that:

- HPL Spec v2.0 semantics are complete, coherent, and review-closed.
- All included Level-3 SCRs are resolved and aligned.
- The specification is frozen until superseded by a future declared version.

**Effective Date:** 2026-01-16

---

## Notes

- This declaration extends the HPL lineage from **syntax -> tooling -> semantics**.
- No runtime or hardware implementation is implied or required by this freeze.
- Future work must proceed via governance, not assumption.
