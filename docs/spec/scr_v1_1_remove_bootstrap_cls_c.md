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

- SCR ID: SCR-2026-01-15-CLS-C-REMOVAL
- Title: Remove bootstrap `cls = C` default allowance
- Author(s): Codex execution (per user instruction)
- Date submitted: 2026-01-15
- Target spec version (e.g., v1.1 or v2.0): v1.1
- Affected documents: `docs/spec/04b_ir_freeze_policy.md`
- Change category:
  - [ ] Clarification (non-semantic)
  - [x] Backward-compatible extension
  - [ ] Breaking change (requires MAJOR version)

---

## Motivation

The bootstrap `cls = C` allowance is intended as temporary. Removing the allowance
enables deterministic operator classification and reduces ambiguity for backends
and audits.

---

## Proposed Change

- Remove the bootstrap allowance from `docs/spec/04b_ir_freeze_policy.md`.
- Replace with deterministic classification rules (to be specified).
- Explicitly state that `cls` must be defined by classification rules or registry annotations.

No changes are proposed to `docs/spec/02_bnf.md` or `docs/spec/04_ir_schema.json`.

---

## Impact Analysis (Required)

### A) Compatibility

- Does this change preserve backward compatibility?
  - [x] Yes (MINOR version)
  - [ ] No (MAJOR version required)

This change is a backward-compatible tightening of policy, not a schema change.

### B) Affected Areas

- [ ] Alphabet / Keywords
- [ ] Axiomatic Grammar (BNF)
- [ ] Macro Boundary
- [x] Operator Algebra / Classes
- [ ] IR Schema
- [ ] Operator Registry Schema
- [x] CI / Conformance / Certification
- [x] Release & Versioning Policy
- [ ] Other (specify)

---

## Migration Strategy (If Breaking)

N/A (MINOR version).

---

## Conformance Implications

- Update checklist items that reference bootstrap defaulting.
- Update conformance mapping and tests to enforce explicit classification.

---

## Alternatives Considered

- Keep the allowance indefinitely (rejected: leaves ambiguity).
- Mark as deprecated without removal timeline (rejected: weak enforcement).

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
  - [x] Draft
  - [ ] Under review
  - [ ] Approved
  - [ ] Implemented (spec-only)
  - [ ] Superseded

---

## Notes

- No implementation work may rely on an SCR until it is **approved and frozen**
  as part of a new spec version.
- All approved SCRs must be referenced in the next **Spec Freeze Declaration**.

---

## REVIEW RECORD (v1.1)

- Checklist: `docs/spec/00j_scr_review_checklist_v1.md`
- Review date: 2026-01-15
- Reviewers: Codex execution (per user instruction)
- Stage results:
  - Stage 1 (Completeness): PASS
  - Stage 2 (Scope & Authority): PASS
  - Stage 3 (Compatibility): NEEDS REVISION
  - Stage 4 (Impact Analysis): PASS
  - Stage 5 (Conformance & Certification): PASS
  - Stage 6 (Migration, if breaking): N/A
  - Stage 7 (Alternatives & Risk): PASS
  - Stage 8 (Decision Readiness): NEEDS REVISION
- Disposition: Accept with Modifications
- Conditions (if any): Define deterministic classification rules or explicitly
  cross-reference the operator-classification SCR and its acceptance.
- Reference summary: `docs/audit/scr_v1_1_review_summary.md`
