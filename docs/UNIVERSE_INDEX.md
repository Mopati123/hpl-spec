# HPL Universe Index

**Sub-Hamiltonians (top-level `_H` folders):**
- `axioms_H`: immutable laws (alphabet, BNF, operator algebra, invariants)
- `dynamics_H`: time-evolution semantics, scheduler/collapse authority, epoch model
- `emergence_H`: user-facing DSL, macros, strategy surface forms
- `backends_H`: lowering targets (classical + quantum), QASM mapping rules
- `observers_H`: observer identities and measurement authorization model
- `audit_H`: audit artifacts, trace schema, proof hooks
- `runtime_H`: orchestration semantics, execution contracts
- `tools_H`: CLI + dev tooling contracts (spec-only)
- `tests_H`: test plan and conformance criteria (spec-only)
- `infra_H`: packaging, versioning, CI/CD intent (spec-only)
- `data_H`: fixtures, corpora, recorded traces (spec-only)

**Important constraint:** This repo contains no executable implementation code yet.

## Governance Specs (Normative)

- Operator registry schema: `docs/spec/06_operator_registry_schema.json`
- IR compatibility / freeze policy: `docs/spec/04b_ir_freeze_policy.md`
- Macro boundary (surface → axiomatic): `docs/spec/02b_macro_boundary.md`

## Conformance & Certification

See **Implementation Governance (Normative)** below for the complete, authoritative list of
conformance, certification, and intake artifacts.

## Implementation Governance (Normative)

- Spec Freeze Declaration (v1): `docs/spec/00_spec_freeze_declaration_v1.md`
- Conformance Checklist (v1): `docs/spec/00b_conformance_checklist_v1.md`
- Conformance Test Mapping (v1): `docs/spec/00c_conformance_test_mapping_v1.md`
- Certification Report Template (v1): `docs/spec/00d_certification_report_template_v1.md`
- Implementation Intake Checklist (v1): `docs/spec/00e_implementation_intake_checklist_v1.md`
- Spec Change Request Template (v1): `docs/spec/00h_spec_change_request_template_v1.md`
- Spec v1.1 Roadmap Skeleton (Informational): `docs/spec/00i_spec_v1_1_roadmap_skeleton.md`
- v1 Compliance Memo: `docs/audit/hpl_v1_compliance_memo.md`
- Level-2 Tooling Track Plan (Informational): `docs/spec/level2_tooling_track_plan.md`
 - Diagnostics Error Taxonomy (Informational): `docs/spec/diagnostics_error_taxonomy_v1.md`

## Future Evolution (Informational)

- SCR: Remove bootstrap cls=C: `docs/spec/scr_v1_1_remove_bootstrap_cls_c.md`
- SCR: Operator classification rules: `docs/spec/scr_v1_1_operator_classification_rules.md`
- SCR: IR invariants clarification: `docs/spec/scr_v1_1_ir_invariants_clarification.md`

## Audit & Evidence

- L2-C diagnostics test run: `docs/audit/level2_diagnostics_test_run_2026-01-16.md`
