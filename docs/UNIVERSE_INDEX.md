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
- Macro boundary (surface -> axiomatic): `docs/spec/02b_macro_boundary.md`

## Conformance & Certification

See **Implementation Governance (Normative)** below for the complete, authoritative list of
conformance, certification, and intake artifacts.

## Implementation Governance (Normative)

- Spec Freeze Declaration (v1): `docs/spec/00_spec_freeze_declaration_v1.md`
- HPL Spec Freeze v1.1: `docs/spec/00_spec_freeze_declaration_v1_1.md`
- HPL Spec Freeze v2.0: `docs/spec/00_spec_freeze_declaration_v2_0.md`
- HPL Spec Freeze v2.1: `docs/spec/00_spec_freeze_declaration_v2_1.md`
- HPL Spec Freeze v2.2: `docs/spec/00_spec_freeze_declaration_v2_2.md`
- HPL Spec Freeze v2.4: `docs/spec/00_spec_freeze_declaration_v2_4.md`
- HPL Spec Freeze v2.5: `docs/spec/00_spec_freeze_declaration_v2_5.md`
- SCR v2.5 Quantum Execution Semantics: `docs/spec/scr_v2_5_quantum_execution_semantics.md`
- Quantum Execution Semantics (v2.5): `docs/spec/12_quantum_execution_semantics_v1.md`
- SCR v2.4 Tech Stack + Quantum Proof Semantics: `docs/spec/scr_v2_4_tech_stack_quantum_proof_semantics.md`
- Tech Stack + Quantum Proof Semantics (v2.4): `docs/spec/11_tech_stack_quantum_proof_semantics.md`
- Conformance Checklist (v1): `docs/spec/00b_conformance_checklist_v1.md`
- Conformance Checklist (v1.1): `docs/spec/00b_conformance_checklist_v1_1.md`
- Conformance Test Mapping (v1): `docs/spec/00c_conformance_test_mapping_v1.md`
- Conformance Test Mapping (v1.1): `docs/spec/00c_conformance_test_mapping_v1_1.md`
- Certification Report Template (v1): `docs/spec/00d_certification_report_template_v1.md`
- Certification Report Template (v2.0): `docs/spec/00p_certification_report_template_v2_0.md`
- Implementation Intake Checklist (v1): `docs/spec/00e_implementation_intake_checklist_v1.md`
- Spec Change Request Template (v1): `docs/spec/00h_spec_change_request_template_v1.md`
- Spec v1.1 Roadmap Skeleton (Informational): `docs/spec/00i_spec_v1_1_roadmap_skeleton.md`
- v1 Compliance Memo: `docs/audit/hpl_v1_compliance_memo.md`
- Level-2 Tooling Track Plan (Informational): `docs/spec/level2_tooling_track_plan.md`
- Diagnostics Error Taxonomy (Informational): `docs/spec/diagnostics_error_taxonomy_v1.md`

## Future Evolution (Informational)
- SCR v2.2 Coupling Topology: `docs/spec/scr_v2_2_coupling_topology.md`
- SCR: Papas Observer Identity (v2.1): `docs/spec/scr_v2_1_papas_observer.md`

- SCR: Remove bootstrap cls=C: `docs/spec/scr_v1_1_remove_bootstrap_cls_c.md`
- SCR: Operator classification rules: `docs/spec/scr_v1_1_operator_classification_rules.md`
- SCR: IR invariants clarification: `docs/spec/scr_v1_1_ir_invariants_clarification.md`

## Level-3 Planning (Proposed / Unfrozen)

- SCR: Scheduler Model — `docs/spec/scr_level3_scheduler_model.md`
- SCR: Execution Semantics — `docs/spec/scr_level3_execution_semantics.md`
- SCR: Measurement & Observation — `docs/spec/scr_level3_measurement_observation.md`
- SCR: Determinism Policy — `docs/spec/scr_level3_determinism_policy.md`
- v2.0 Freeze Prerequisites: `docs/spec/00m_v2_0_freeze_prerequisites.md`
- Level-3 Conformance Checklist (v2.0): `docs/spec/00n_conformance_checklist_level3_v2_0.md`
- Level-3 Conformance Test Mapping (v2.0): `docs/spec/00o_conformance_test_mapping_level3_v2_0.md`

## Audit & Evidence

- L2-C diagnostics test run: `docs/audit/level2_diagnostics_test_run_2026-01-16.md`
- Level-2 tooling completion: `docs/audit/level2_tooling_completion_2026-01-16.md`
- Repo file manifest snapshot (SHA 6cf610308346a304b86b6f88e0aff423c16d503e): `docs/audit/hpl_full_file_manifest_2026-01-27.md`
- HPL v1 -> v1.1 Migration Memo: `docs/audit/hpl_v1_to_v1_1_migration_memo.md`
- HPL v1.1 -> v2.0 Migration Memo: `docs/audit/hpl_v1_1_to_v2_0_migration_memo.md`


- Level-3 Requirements Matrix (v2.0): `docs/audit/level3_requirements_matrix_v2_0.md`
## Certification Examples

- Level-3 Certification Walkthrough Note: `docs/audit/level3_certification_walkthrough_2026-01-16.md`
- Level-3 Certification Walkthrough: `docs/audit/example_level3_certification_walkthrough.md`

## Publications

- HPL v1 -> v2.0 Evolution Overview (External): `docs/publish/hpl_v1_to_v2_0_evolution_overview.md`
- HPL Codebase Overview: `docs/publish/hpl_codebase_overview.md`
- HPL External Packet (PDF-friendly): docs/publish/hpl_external_packet_v1.md
- Production Readiness Checklist: docs/publish/production_readiness_checklist.md
- Trading Paper-Mode Runbook: docs/publish/trading_paper_mode_runbook.md
- Trading Shadow-Mode Runbook: docs/publish/trading_shadow_mode_runbook.md

