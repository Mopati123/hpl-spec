# Repository Root Architecture and File Manifest

Main SHA: `8a7925547d403521db5e7db6d34600314ad642de`
Tracked files: `331`

## Top-Level Summary

- Root-level files:
  - `.gitignore`
  - `README.md`
  - `pyproject.toml`
  - `pytest.ini`
  - `requirements.txt`
- Top-level directories (tracked file counts):
  - `.github/`: 4 files
  - `.vscode/`: 1 files
  - `audit_H/`: 9 files
  - `axioms_H/`: 7 files
  - `backends_H/`: 4 files
  - `config/`: 2 files
  - `data_H/`: 4 files
  - `docs/`: 97 files
  - `dynamics_H/`: 7 files
  - `emergence_H/`: 4 files
  - `examples/`: 1 files
  - `infra_H/`: 3 files
  - `observers_H/`: 5 files
  - `runtime_H/`: 6 files
  - `src/`: 54 files
  - `tests/`: 89 files
  - `tests_H/`: 6 files
  - `tools/`: 17 files
  - `tools_H/`: 6 files

## Full Tracked Tree

```text
|-- .github/
|   |-- instructions/
|   |   `-- kluster-code-verify.instructions.md
|   |-- workflows/
|   |   |-- ci-gates.yml
|   |   `-- ci-nightly.yml
|   `-- copilot-instructions.md
|-- .vscode/
|   `-- settings.json
|-- audit_H/
|   |-- docs/
|   |   |-- .keep
|   |   |-- anchor_event_schema.md
|   |   |-- coupling_event_schema.md
|   |   |-- evidence_chain_requirements.md
|   |   `-- witness_attestation.md
|   |-- manifests/
|   |   |-- .keep
|   |   |-- coupling_event_manifest.yaml
|   |   `-- trace_schema.json
|   `-- README.md
|-- axioms_H/
|   |-- docs/
|   |   |-- .keep
|   |   |-- coupling_topology_axioms.md
|   |   |-- epoch_anchor_axioms.md
|   |   `-- tech_stack_axioms.md
|   |-- manifests/
|   |   `-- .keep
|   |-- operators/
|   |   `-- registry.json
|   `-- README.md
|-- backends_H/
|   |-- docs/
|   |   `-- .keep
|   |-- manifests/
|   |   `-- .keep
|   |-- operators/
|   |   `-- registry.json
|   `-- README.md
|-- config/
|   |-- keys/
|   |   `-- ci_ed25519.pub
|   `-- papas_policy.yaml
|-- data_H/
|   |-- docs/
|   |   `-- .keep
|   |-- epoch_anchors/
|   |   `-- .gitkeep
|   |-- manifests/
|   |   `-- .keep
|   `-- README.md
|-- docs/
|   |-- audit/
|   |   |-- conformance_restoration_patch_2026-01-15.md
|   |   |-- example_level3_certification_walkthrough.md
|   |   |-- hpl_full_file_manifest_2026-01-27.md
|   |   |-- hpl_v1_1_to_v2_0_migration_memo.md
|   |   |-- hpl_v1_compliance_memo.md
|   |   |-- hpl_v1_to_v1_1_migration_memo.md
|   |   |-- hpl_v1_to_v2_0_governance_summary.md
|   |   |-- level1_test_run_2026-01-15.md
|   |   |-- level2_diagnostics_authorization_2026-01-16.md
|   |   |-- level2_diagnostics_test_run_2026-01-16.md
|   |   |-- level2_execution_authorization_2026-01-15.md
|   |   |-- level2_registry_validation_authorization_2026-01-15.md
|   |   |-- level2_registry_validator_test_run_2026-01-16.md
|   |   |-- level2_tooling_completion_2026-01-16.md
|   |   |-- level2_traceability_authorization_2026-01-16.md
|   |   |-- level2_traceability_test_run_2026-01-16.md
|   |   |-- level3_certification_walkthrough_2026-01-16.md
|   |   |-- level3_requirements_matrix_v2_0.md
|   |   |-- macro_expansion_assumptions.md
|   |   |-- reproducibility_contract.md
|   |   |-- scr_level3_scheduler_review_update_2026-01-16.md
|   |   |-- scr_v1_1_decision_log_2026-01-16.md
|   |   `-- scr_v1_1_review_summary.md
|   |-- publish/
|   |   |-- constraint_inversion_runbook.md
|   |   |-- delta_s_kernel_runbook.md
|   |   |-- ecmo_runbook.md
|   |   |-- first_live_instantiation_plan.md
|   |   |-- hpl_capability_matrix.md
|   |   |-- hpl_codebase_overview.md
|   |   |-- hpl_constitution_whitepaper_v1.md
|   |   |-- hpl_execution_lifecycle_diagram.md
|   |   |-- hpl_external_packet_v1.md
|   |   |-- hpl_public_capability_statement.md
|   |   |-- hpl_technical_spec_summary.md
|   |   |-- hpl_v1_to_v2_0_evolution_overview.md
|   |   |-- io_lane_runbook.md
|   |   |-- navier_stokes_runbook.md
|   |   |-- net_lane_runbook.md
|   |   |-- phase1_anchor_runbook.md
|   |   |-- production_readiness_checklist.md
|   |   |-- quickstart_install_run.md
|   |   |-- trading_paper_mode_runbook.md
|   |   `-- trading_shadow_mode_runbook.md
|   |-- spec/
|   |   |-- 00_spec_freeze_declaration_v1.md
|   |   |-- 00_spec_freeze_declaration_v1_1.md
|   |   |-- 00_spec_freeze_declaration_v2_0.md
|   |   |-- 00_spec_freeze_declaration_v2_1.md
|   |   |-- 00_spec_freeze_declaration_v2_2.md
|   |   |-- 00_spec_freeze_declaration_v2_3.md
|   |   |-- 00_spec_freeze_declaration_v2_4.md
|   |   |-- 00_spec_freeze_declaration_v2_5.md
|   |   |-- 00b_conformance_checklist_v1.md
|   |   |-- 00b_conformance_checklist_v1_1.md
|   |   |-- 00c_conformance_test_mapping_v1.md
|   |   |-- 00c_conformance_test_mapping_v1_1.md
|   |   |-- 00d_certification_report_template_v1.md
|   |   |-- 00e_implementation_intake_checklist_v1.md
|   |   |-- 00f_ci_gate_policy_v1.md
|   |   |-- 00g_release_versioning_policy_v1.md
|   |   |-- 00h_spec_change_request_template_v1.md
|   |   |-- 00i_spec_v1_1_roadmap_skeleton.md
|   |   |-- 00j_scr_review_checklist_v1.md
|   |   |-- 00k_level2_execution_checklist_v1.md
|   |   |-- 00l_recertification_checklist_v1_1.md
|   |   |-- 00m_v2_0_freeze_prerequisites.md
|   |   |-- 00n_conformance_checklist_level3_v2_0.md
|   |   |-- 00o_conformance_test_mapping_level3_v2_0.md
|   |   |-- 00p_certification_report_template_v2_0.md
|   |   |-- 01_alphabet.md
|   |   |-- 02_bnf.md
|   |   |-- 02b_macro_boundary.md
|   |   |-- 03_operator_algebra.md
|   |   |-- 04_ir_schema.json
|   |   |-- 04b_ir_freeze_policy.md
|   |   |-- 05_qasm_lowering.md
|   |   |-- 06_operator_registry_schema.json
|   |   |-- 07_epoch_anchoring.md
|   |   |-- 08_hpl_primitives_evolve_collapse_anchor.md
|   |   |-- 09_effect_types_eto_lambda.md
|   |   |-- 10_registry_as_linker.md
|   |   |-- 11_tech_stack_quantum_proof_semantics.md
|   |   |-- 12_quantum_execution_semantics_v1.md
|   |   |-- diagnostics_error_taxonomy_v1.md
|   |   |-- level2_tooling_track_plan.md
|   |   |-- scr_level3_determinism_policy.md
|   |   |-- scr_level3_execution_semantics.md
|   |   |-- scr_level3_measurement_observation.md
|   |   |-- scr_level3_scheduler_model.md
|   |   |-- scr_v1_1_ir_invariants_clarification.md
|   |   |-- scr_v1_1_operator_classification_rules.md
|   |   |-- scr_v1_1_remove_bootstrap_cls_c.md
|   |   |-- scr_v2_1_papas_observer.md
|   |   |-- scr_v2_2_coupling_topology.md
|   |   |-- scr_v2_3_epoch_anchoring_and_primitives.md
|   |   |-- scr_v2_4_tech_stack_quantum_proof_semantics.md
|   |   `-- scr_v2_5_quantum_execution_semantics.md
|   `-- UNIVERSE_INDEX.md
|-- dynamics_H/
|   |-- docs/
|   |   |-- .keep
|   |   |-- coupling_operator_semantics.md
|   |   |-- evolve_collapse_semantics.md
|   |   `-- quantum_proof_semantics_dynamics.md
|   |-- manifests/
|   |   `-- .keep
|   |-- operators/
|   |   `-- registry.json
|   `-- README.md
|-- emergence_H/
|   |-- docs/
|   |   `-- .keep
|   |-- manifests/
|   |   `-- .keep
|   |-- operators/
|   |   `-- registry.json
|   `-- README.md
|-- examples/
|   `-- momentum_trade.hpl
|-- infra_H/
|   |-- docs/
|   |   `-- .keep
|   |-- manifests/
|   |   `-- .keep
|   `-- README.md
|-- observers_H/
|   |-- docs/
|   |   |-- .keep
|   |   `-- papas.md
|   |-- manifests/
|   |   |-- .keep
|   |   `-- observers.json
|   `-- README.md
|-- runtime_H/
|   |-- docs/
|   |   |-- .keep
|   |   |-- backend_lane_runtime_contract.md
|   |   |-- epoch_verification_gate.md
|   |   `-- scheduler_gated_coupling.md
|   |-- manifests/
|   |   `-- .keep
|   `-- README.md
|-- src/
|   `-- hpl/
|       |-- audit/
|       |   |-- __init__.py
|       |   |-- constraint_inversion.py
|       |   |-- constraint_witness.py
|       |   |-- coupling_event.py
|       |   `-- dev_change_event.py
|       |-- axioms/
|       |   |-- __init__.py
|       |   `-- validator.py
|       |-- backends/
|       |   |-- __init__.py
|       |   |-- backend_ir.py
|       |   |-- classical_lowering.py
|       |   `-- qasm_lowering.py
|       |-- dynamics/
|       |   |-- __init__.py
|       |   `-- ir_emitter.py
|       |-- emergence/
|       |   |-- dsl/
|       |   |   |-- __init__.py
|       |   |   `-- parser.py
|       |   |-- macros/
|       |   |   |-- __init__.py
|       |   |   `-- expander.py
|       |   `-- __init__.py
|       |-- observers/
|       |   |-- __init__.py
|       |   `-- papas.py
|       |-- operators/
|       |   |-- __init__.py
|       |   `-- registry.py
|       |-- runtime/
|       |   |-- effects/
|       |   |   |-- __init__.py
|       |   |   |-- effect_step.py
|       |   |   |-- effect_types.py
|       |   |   |-- handler_registry.py
|       |   |   |-- handlers.py
|       |   |   `-- measurement_selection.py
|       |   |-- io/
|       |   |   |-- adapters/
|       |   |   |   |-- __init__.py
|       |   |   |   |-- deriv.py
|       |   |   |   |-- mt5.py
|       |   |   |   `-- tradingview.py
|       |   |   |-- __init__.py
|       |   |   |-- adapter.py
|       |   |   `-- adapter_contract.py
|       |   |-- net/
|       |   |   |-- adapters/
|       |   |   |   |-- local_loopback.py
|       |   |   |   `-- ws.py
|       |   |   |-- __init__.py
|       |   |   |-- adapter.py
|       |   |   |-- adapter_contract.py
|       |   |   `-- stabilizer.py
|       |   |-- __init__.py
|       |   |-- context.py
|       |   |-- contracts.py
|       |   |-- engine.py
|       |   `-- redaction.py
|       |-- __init__.py
|       |-- ast.py
|       |-- cli.py
|       |-- diagnostics.py
|       |-- errors.py
|       |-- execution_token.py
|       |-- scheduler.py
|       `-- trace.py
|-- tests/
|   |-- fixtures/
|   |   |-- keys/
|   |   |   |-- ci_ed25519_test.pub
|   |   |   `-- ci_ed25519_test.sk
|   |   |-- pde/
|   |   |   |-- ns_policy_forbidden.json
|   |   |   |-- ns_policy_safe.json
|   |   |   `-- ns_state_initial.json
|   |   |-- trading/
|   |   |   |-- policy_forbidden.json
|   |   |   |-- policy_safe.json
|   |   |   |-- price_series_simple.json
|   |   |   |-- shadow_model.json
|   |   |   |-- shadow_policy_forbidden.json
|   |   |   `-- shadow_policy_safe.json
|   |   |-- agent_policy.json
|   |   |-- agent_proposal_allow.json
|   |   |-- agent_proposal_deny.json
|   |   |-- coupling_registry_invalid_missing_audit_obligation.json
|   |   |-- coupling_registry_invalid_projector_mismatch.json
|   |   |-- coupling_registry_invalid_undeclared_edge.json
|   |   |-- coupling_registry_valid.json
|   |   |-- ecmo_boundary_ambiguous.json
|   |   |-- ecmo_boundary_ci.json
|   |   |-- ecmo_boundary_regulator.json
|   |   |-- observers_registry_missing_papas.json
|   |   |-- observers_registry_v2_1.json
|   |   |-- program_ir_minimal.json
|   |   |-- registry_invalid.json
|   |   |-- registry_valid.json
|   |   `-- trace_schema_with_witness.json
|   |-- test_agent_governance_demo.py
|   |-- test_anchor_generator.py
|   |-- test_anchor_signing.py
|   |-- test_axiomatic_validation.py
|   |-- test_budget_exhaustion.py
|   |-- test_bundle_constraint_inversion_roles.py
|   |-- test_bundle_delta_s_roles.py
|   |-- test_bundle_io_roles.py
|   |-- test_bundle_net_roles.py
|   |-- test_bundle_quantum_semantics_required_roles.py
|   |-- test_bundle_signing.py
|   |-- test_ci_governance_demo.py
|   |-- test_classical_lowering.py
|   |-- test_cli_invert.py
|   |-- test_cli_lifecycle.py
|   |-- test_cli_smoke.py
|   |-- test_constraint_inversion.py
|   |-- test_coupling_event_emission.py
|   |-- test_coupling_topology_validator.py
|   |-- test_delta_s_kernel.py
|   |-- test_deriv_adapter_gate.py
|   |-- test_dev_change_event.py
|   |-- test_diagnostics.py
|   |-- test_ecmo_auto_track_lifecycle.py
|   |-- test_epoch_anchor_generation.py
|   |-- test_epoch_anchor_verification.py
|   |-- test_evidence_bundle.py
|   |-- test_full_lifecycle_kernel.py
|   |-- test_io_adapter_contract.py
|   |-- test_io_adapter_stub.py
|   |-- test_io_effect_pack.py
|   |-- test_io_policy_defaults.py
|   |-- test_io_reconciliation.py
|   |-- test_io_token_gate.py
|   |-- test_ir_emission.py
|   |-- test_macro_expansion.py
|   |-- test_measurement_selection.py
|   |-- test_mt5_adapter_gate.py
|   |-- test_navier_stokes_demo.py
|   |-- test_navier_stokes_effects.py
|   |-- test_net_policy_defaults.py
|   |-- test_operator_registry_enforcement.py
|   |-- test_packaging_entrypoint.py
|   |-- test_papas_observer_contract.py
|   |-- test_papas_observer_reports.py
|   |-- test_papas_runner.py
|   |-- test_parser.py
|   |-- test_pipeline.py
|   |-- test_qasm_lowering.py
|   |-- test_quantum_execution_semantics_validator.py
|   |-- test_redaction_gate.py
|   |-- test_registry_validator.py
|   |-- test_runtime_backend_token_gate.py
|   |-- test_runtime_contracts.py
|   |-- test_runtime_execution_kernel.py
|   |-- test_scheduler_authority.py
|   |-- test_traceability.py
|   |-- test_trading_io_demos.py
|   |-- test_trading_paper_mode_demo.py
|   |-- test_trading_paper_mode_effects.py
|   |-- test_trading_shadow_mode_demo.py
|   `-- test_trading_shadow_mode_effects.py
|-- tests_H/
|   |-- docs/
|   |   |-- .keep
|   |   |-- anchor_conformance_tests.md
|   |   |-- coupling_conformance_tests.md
|   |   `-- tech_stack_conformance_tests.md
|   |-- manifests/
|   |   `-- .keep
|   `-- README.md
|-- tools/
|   |-- anchor_epoch.py
|   |-- anchor_generator.py
|   |-- bundle_evidence.py
|   |-- ci_gate_prohibited_behavior.py
|   |-- ci_gate_spec_integrity.py
|   |-- compare_anchor_contract.py
|   |-- papas_runner.py
|   |-- phase1_anchor_demo.ps1
|   |-- sign_anchor.py
|   |-- validate_coupling_topology.py
|   |-- validate_ir_schema.py
|   |-- validate_observer_registry.py
|   |-- validate_operator_registries.py
|   |-- validate_quantum_execution_semantics.py
|   |-- verify_anchor.py
|   |-- verify_anchor_signature.py
|   `-- verify_epoch.py
|-- tools_H/
|   |-- docs/
|   |   |-- .keep
|   |   |-- anchor_validator_rules.md
|   |   |-- coupling_topology_validation.md
|   |   `-- tech_stack_validator_rules.md
|   |-- manifests/
|   |   `-- .keep
|   `-- README.md
|-- .gitignore
|-- README.md
|-- pyproject.toml
|-- pytest.ini
`-- requirements.txt
```

## Full Tracked File List

```text
.github/copilot-instructions.md
.github/instructions/kluster-code-verify.instructions.md
.github/workflows/ci-gates.yml
.github/workflows/ci-nightly.yml
.gitignore
.vscode/settings.json
README.md
audit_H/README.md
audit_H/docs/.keep
audit_H/docs/anchor_event_schema.md
audit_H/docs/coupling_event_schema.md
audit_H/docs/evidence_chain_requirements.md
audit_H/docs/witness_attestation.md
audit_H/manifests/.keep
audit_H/manifests/coupling_event_manifest.yaml
audit_H/manifests/trace_schema.json
axioms_H/README.md
axioms_H/docs/.keep
axioms_H/docs/coupling_topology_axioms.md
axioms_H/docs/epoch_anchor_axioms.md
axioms_H/docs/tech_stack_axioms.md
axioms_H/manifests/.keep
axioms_H/operators/registry.json
backends_H/README.md
backends_H/docs/.keep
backends_H/manifests/.keep
backends_H/operators/registry.json
config/keys/ci_ed25519.pub
config/papas_policy.yaml
data_H/README.md
data_H/docs/.keep
data_H/epoch_anchors/.gitkeep
data_H/manifests/.keep
docs/UNIVERSE_INDEX.md
docs/audit/conformance_restoration_patch_2026-01-15.md
docs/audit/example_level3_certification_walkthrough.md
docs/audit/hpl_full_file_manifest_2026-01-27.md
docs/audit/hpl_v1_1_to_v2_0_migration_memo.md
docs/audit/hpl_v1_compliance_memo.md
docs/audit/hpl_v1_to_v1_1_migration_memo.md
docs/audit/hpl_v1_to_v2_0_governance_summary.md
docs/audit/level1_test_run_2026-01-15.md
docs/audit/level2_diagnostics_authorization_2026-01-16.md
docs/audit/level2_diagnostics_test_run_2026-01-16.md
docs/audit/level2_execution_authorization_2026-01-15.md
docs/audit/level2_registry_validation_authorization_2026-01-15.md
docs/audit/level2_registry_validator_test_run_2026-01-16.md
docs/audit/level2_tooling_completion_2026-01-16.md
docs/audit/level2_traceability_authorization_2026-01-16.md
docs/audit/level2_traceability_test_run_2026-01-16.md
docs/audit/level3_certification_walkthrough_2026-01-16.md
docs/audit/level3_requirements_matrix_v2_0.md
docs/audit/macro_expansion_assumptions.md
docs/audit/reproducibility_contract.md
docs/audit/scr_level3_scheduler_review_update_2026-01-16.md
docs/audit/scr_v1_1_decision_log_2026-01-16.md
docs/audit/scr_v1_1_review_summary.md
docs/publish/constraint_inversion_runbook.md
docs/publish/delta_s_kernel_runbook.md
docs/publish/ecmo_runbook.md
docs/publish/first_live_instantiation_plan.md
docs/publish/hpl_capability_matrix.md
docs/publish/hpl_codebase_overview.md
docs/publish/hpl_constitution_whitepaper_v1.md
docs/publish/hpl_execution_lifecycle_diagram.md
docs/publish/hpl_external_packet_v1.md
docs/publish/hpl_public_capability_statement.md
docs/publish/hpl_technical_spec_summary.md
docs/publish/hpl_v1_to_v2_0_evolution_overview.md
docs/publish/io_lane_runbook.md
docs/publish/navier_stokes_runbook.md
docs/publish/net_lane_runbook.md
docs/publish/phase1_anchor_runbook.md
docs/publish/production_readiness_checklist.md
docs/publish/quickstart_install_run.md
docs/publish/trading_paper_mode_runbook.md
docs/publish/trading_shadow_mode_runbook.md
docs/spec/00_spec_freeze_declaration_v1.md
docs/spec/00_spec_freeze_declaration_v1_1.md
docs/spec/00_spec_freeze_declaration_v2_0.md
docs/spec/00_spec_freeze_declaration_v2_1.md
docs/spec/00_spec_freeze_declaration_v2_2.md
docs/spec/00_spec_freeze_declaration_v2_3.md
docs/spec/00_spec_freeze_declaration_v2_4.md
docs/spec/00_spec_freeze_declaration_v2_5.md
docs/spec/00b_conformance_checklist_v1.md
docs/spec/00b_conformance_checklist_v1_1.md
docs/spec/00c_conformance_test_mapping_v1.md
docs/spec/00c_conformance_test_mapping_v1_1.md
docs/spec/00d_certification_report_template_v1.md
docs/spec/00e_implementation_intake_checklist_v1.md
docs/spec/00f_ci_gate_policy_v1.md
docs/spec/00g_release_versioning_policy_v1.md
docs/spec/00h_spec_change_request_template_v1.md
docs/spec/00i_spec_v1_1_roadmap_skeleton.md
docs/spec/00j_scr_review_checklist_v1.md
docs/spec/00k_level2_execution_checklist_v1.md
docs/spec/00l_recertification_checklist_v1_1.md
docs/spec/00m_v2_0_freeze_prerequisites.md
docs/spec/00n_conformance_checklist_level3_v2_0.md
docs/spec/00o_conformance_test_mapping_level3_v2_0.md
docs/spec/00p_certification_report_template_v2_0.md
docs/spec/01_alphabet.md
docs/spec/02_bnf.md
docs/spec/02b_macro_boundary.md
docs/spec/03_operator_algebra.md
docs/spec/04_ir_schema.json
docs/spec/04b_ir_freeze_policy.md
docs/spec/05_qasm_lowering.md
docs/spec/06_operator_registry_schema.json
docs/spec/07_epoch_anchoring.md
docs/spec/08_hpl_primitives_evolve_collapse_anchor.md
docs/spec/09_effect_types_eto_lambda.md
docs/spec/10_registry_as_linker.md
docs/spec/11_tech_stack_quantum_proof_semantics.md
docs/spec/12_quantum_execution_semantics_v1.md
docs/spec/diagnostics_error_taxonomy_v1.md
docs/spec/level2_tooling_track_plan.md
docs/spec/scr_level3_determinism_policy.md
docs/spec/scr_level3_execution_semantics.md
docs/spec/scr_level3_measurement_observation.md
docs/spec/scr_level3_scheduler_model.md
docs/spec/scr_v1_1_ir_invariants_clarification.md
docs/spec/scr_v1_1_operator_classification_rules.md
docs/spec/scr_v1_1_remove_bootstrap_cls_c.md
docs/spec/scr_v2_1_papas_observer.md
docs/spec/scr_v2_2_coupling_topology.md
docs/spec/scr_v2_3_epoch_anchoring_and_primitives.md
docs/spec/scr_v2_4_tech_stack_quantum_proof_semantics.md
docs/spec/scr_v2_5_quantum_execution_semantics.md
dynamics_H/README.md
dynamics_H/docs/.keep
dynamics_H/docs/coupling_operator_semantics.md
dynamics_H/docs/evolve_collapse_semantics.md
dynamics_H/docs/quantum_proof_semantics_dynamics.md
dynamics_H/manifests/.keep
dynamics_H/operators/registry.json
emergence_H/README.md
emergence_H/docs/.keep
emergence_H/manifests/.keep
emergence_H/operators/registry.json
examples/momentum_trade.hpl
infra_H/README.md
infra_H/docs/.keep
infra_H/manifests/.keep
observers_H/README.md
observers_H/docs/.keep
observers_H/docs/papas.md
observers_H/manifests/.keep
observers_H/manifests/observers.json
pyproject.toml
pytest.ini
requirements.txt
runtime_H/README.md
runtime_H/docs/.keep
runtime_H/docs/backend_lane_runtime_contract.md
runtime_H/docs/epoch_verification_gate.md
runtime_H/docs/scheduler_gated_coupling.md
runtime_H/manifests/.keep
src/hpl/__init__.py
src/hpl/ast.py
src/hpl/audit/__init__.py
src/hpl/audit/constraint_inversion.py
src/hpl/audit/constraint_witness.py
src/hpl/audit/coupling_event.py
src/hpl/audit/dev_change_event.py
src/hpl/axioms/__init__.py
src/hpl/axioms/validator.py
src/hpl/backends/__init__.py
src/hpl/backends/backend_ir.py
src/hpl/backends/classical_lowering.py
src/hpl/backends/qasm_lowering.py
src/hpl/cli.py
src/hpl/diagnostics.py
src/hpl/dynamics/__init__.py
src/hpl/dynamics/ir_emitter.py
src/hpl/emergence/__init__.py
src/hpl/emergence/dsl/__init__.py
src/hpl/emergence/dsl/parser.py
src/hpl/emergence/macros/__init__.py
src/hpl/emergence/macros/expander.py
src/hpl/errors.py
src/hpl/execution_token.py
src/hpl/observers/__init__.py
src/hpl/observers/papas.py
src/hpl/operators/__init__.py
src/hpl/operators/registry.py
src/hpl/runtime/__init__.py
src/hpl/runtime/context.py
src/hpl/runtime/contracts.py
src/hpl/runtime/effects/__init__.py
src/hpl/runtime/effects/effect_step.py
src/hpl/runtime/effects/effect_types.py
src/hpl/runtime/effects/handler_registry.py
src/hpl/runtime/effects/handlers.py
src/hpl/runtime/effects/measurement_selection.py
src/hpl/runtime/engine.py
src/hpl/runtime/io/__init__.py
src/hpl/runtime/io/adapter.py
src/hpl/runtime/io/adapter_contract.py
src/hpl/runtime/io/adapters/__init__.py
src/hpl/runtime/io/adapters/deriv.py
src/hpl/runtime/io/adapters/mt5.py
src/hpl/runtime/io/adapters/tradingview.py
src/hpl/runtime/net/__init__.py
src/hpl/runtime/net/adapter.py
src/hpl/runtime/net/adapter_contract.py
src/hpl/runtime/net/adapters/local_loopback.py
src/hpl/runtime/net/adapters/ws.py
src/hpl/runtime/net/stabilizer.py
src/hpl/runtime/redaction.py
src/hpl/scheduler.py
src/hpl/trace.py
tests/fixtures/agent_policy.json
tests/fixtures/agent_proposal_allow.json
tests/fixtures/agent_proposal_deny.json
tests/fixtures/coupling_registry_invalid_missing_audit_obligation.json
tests/fixtures/coupling_registry_invalid_projector_mismatch.json
tests/fixtures/coupling_registry_invalid_undeclared_edge.json
tests/fixtures/coupling_registry_valid.json
tests/fixtures/ecmo_boundary_ambiguous.json
tests/fixtures/ecmo_boundary_ci.json
tests/fixtures/ecmo_boundary_regulator.json
tests/fixtures/keys/ci_ed25519_test.pub
tests/fixtures/keys/ci_ed25519_test.sk
tests/fixtures/observers_registry_missing_papas.json
tests/fixtures/observers_registry_v2_1.json
tests/fixtures/pde/ns_policy_forbidden.json
tests/fixtures/pde/ns_policy_safe.json
tests/fixtures/pde/ns_state_initial.json
tests/fixtures/program_ir_minimal.json
tests/fixtures/registry_invalid.json
tests/fixtures/registry_valid.json
tests/fixtures/trace_schema_with_witness.json
tests/fixtures/trading/policy_forbidden.json
tests/fixtures/trading/policy_safe.json
tests/fixtures/trading/price_series_simple.json
tests/fixtures/trading/shadow_model.json
tests/fixtures/trading/shadow_policy_forbidden.json
tests/fixtures/trading/shadow_policy_safe.json
tests/test_agent_governance_demo.py
tests/test_anchor_generator.py
tests/test_anchor_signing.py
tests/test_axiomatic_validation.py
tests/test_budget_exhaustion.py
tests/test_bundle_constraint_inversion_roles.py
tests/test_bundle_delta_s_roles.py
tests/test_bundle_io_roles.py
tests/test_bundle_net_roles.py
tests/test_bundle_quantum_semantics_required_roles.py
tests/test_bundle_signing.py
tests/test_ci_governance_demo.py
tests/test_classical_lowering.py
tests/test_cli_invert.py
tests/test_cli_lifecycle.py
tests/test_cli_smoke.py
tests/test_constraint_inversion.py
tests/test_coupling_event_emission.py
tests/test_coupling_topology_validator.py
tests/test_delta_s_kernel.py
tests/test_deriv_adapter_gate.py
tests/test_dev_change_event.py
tests/test_diagnostics.py
tests/test_ecmo_auto_track_lifecycle.py
tests/test_epoch_anchor_generation.py
tests/test_epoch_anchor_verification.py
tests/test_evidence_bundle.py
tests/test_full_lifecycle_kernel.py
tests/test_io_adapter_contract.py
tests/test_io_adapter_stub.py
tests/test_io_effect_pack.py
tests/test_io_policy_defaults.py
tests/test_io_reconciliation.py
tests/test_io_token_gate.py
tests/test_ir_emission.py
tests/test_macro_expansion.py
tests/test_measurement_selection.py
tests/test_mt5_adapter_gate.py
tests/test_navier_stokes_demo.py
tests/test_navier_stokes_effects.py
tests/test_net_policy_defaults.py
tests/test_operator_registry_enforcement.py
tests/test_packaging_entrypoint.py
tests/test_papas_observer_contract.py
tests/test_papas_observer_reports.py
tests/test_papas_runner.py
tests/test_parser.py
tests/test_pipeline.py
tests/test_qasm_lowering.py
tests/test_quantum_execution_semantics_validator.py
tests/test_redaction_gate.py
tests/test_registry_validator.py
tests/test_runtime_backend_token_gate.py
tests/test_runtime_contracts.py
tests/test_runtime_execution_kernel.py
tests/test_scheduler_authority.py
tests/test_traceability.py
tests/test_trading_io_demos.py
tests/test_trading_paper_mode_demo.py
tests/test_trading_paper_mode_effects.py
tests/test_trading_shadow_mode_demo.py
tests/test_trading_shadow_mode_effects.py
tests_H/README.md
tests_H/docs/.keep
tests_H/docs/anchor_conformance_tests.md
tests_H/docs/coupling_conformance_tests.md
tests_H/docs/tech_stack_conformance_tests.md
tests_H/manifests/.keep
tools/anchor_epoch.py
tools/anchor_generator.py
tools/bundle_evidence.py
tools/ci_gate_prohibited_behavior.py
tools/ci_gate_spec_integrity.py
tools/compare_anchor_contract.py
tools/papas_runner.py
tools/phase1_anchor_demo.ps1
tools/sign_anchor.py
tools/validate_coupling_topology.py
tools/validate_ir_schema.py
tools/validate_observer_registry.py
tools/validate_operator_registries.py
tools/validate_quantum_execution_semantics.py
tools/verify_anchor.py
tools/verify_anchor_signature.py
tools/verify_epoch.py
tools_H/README.md
tools_H/docs/.keep
tools_H/docs/anchor_validator_rules.md
tools_H/docs/coupling_topology_validation.md
tools_H/docs/tech_stack_validator_rules.md
tools_H/manifests/.keep
```
