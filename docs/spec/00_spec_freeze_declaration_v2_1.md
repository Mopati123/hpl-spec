# HPL Spec Freeze Declaration - v2.1

## Status

**DECLARED - FROZEN (Normative)**

This document formally declares **HPL Spec v2.1** as frozen and authoritative,
subject to the scope, constraints, and prohibitions defined herein.

---

## Scope of the Freeze

HPL Spec **v2.1** introduces a minimal amendment:

1. **Papas Observer Identity**
   - Source: `docs/spec/scr_v2_1_papas_observer.md`
   - Effect: Adds `papas` as a first-class internal observer with explicit
     denials of collapse and semantic authority.

2. **Witness Record Schema**
   - Source: `audit_H/manifests/trace_schema.json`
   - Effect: Adds witness records and permits `papas` as a witness signer.

No other changes are included in this freeze.

---

## Normative References (v2.1)

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
- `docs/spec/00p_certification_report_template_v2_0.md`

### Governance
- `docs/spec/00g_release_versioning_policy_v1.md`
- `docs/spec/00h_spec_change_request_template_v1.md`
- `docs/spec/00j_scr_review_checklist_v1.md`
- `docs/spec/00m_v2_0_freeze_prerequisites.md`
- `docs/spec/scr_v2_1_papas_observer.md`

### Migration
- `docs/audit/hpl_v1_1_to_v2_0_migration_memo.md`

---

## Compatibility Statement

- **HPL Spec v2.1 is a backward-compatible amendment** to v2.0.
- HPL Spec v1 and v1.1 remain valid and frozen.
- v2.0 implementations remain valid; v2.1 adds observer and audit artifacts.

---

## Prohibitions Under This Freeze

While this freeze is in effect:

- No changes may be made to:
  - Scheduler semantics
  - Execution semantics
  - Measurement or observation rules
  - Determinism policy definitions

- No reinterpretation of v2.1 semantics is permitted without:
  1. A new Spec Change Request (SCR), and
  2. A subsequent freeze declaration (v2.2 or v3.0).

---

## Certification Implications

- v2.1 conformance claims MUST:
  - Declare the scheduler policy used
  - Preserve all v2.0 Level-3 certification requirements
  - Treat Papas witness records as optional evidence artifacts

---

## Declaration

By issuing this document, the maintainers declare that:

- HPL Spec v2.1 is a minimal, governance-compliant amendment to v2.0.
- The Papas observer identity and witness schema are now frozen law.
- The specification is frozen until superseded by a future declared version.

**Effective Date:** 2026-01-16

---

## Notes

- This declaration extends the v2.0 semantic freeze without altering execution
  semantics.
- No runtime implementation is implied or required by this freeze.
