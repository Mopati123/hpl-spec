# HPL v2.0 Certified Implementation - Normative Requirements Matrix and Evidence Plan (Corrected)

## 1. Sources and Scope

### Normative sources

- `docs/spec/00_spec_freeze_declaration_v2_0.md`
- `docs/spec/scr_level3_scheduler_model.md`
- `docs/spec/scr_level3_execution_semantics.md`
- `docs/spec/scr_level3_measurement_observation.md`
- `docs/spec/scr_level3_determinism_policy.md`

### Advisory sources (non-normative)

- `docs/audit/hpl_v1_1_to_v2_0_migration_memo.md`

This matrix includes only explicit MUST requirements from the normative sources.
Advisory guidance is listed separately and labeled as non-normative.

---

## 2. Normative Requirements Matrix (MUST)

| Req ID | Normative requirement (MUST) | Source(s) | Implementation mapping (example) | Evidence plan (example) |
| --- | --- | --- | --- | --- |
| R-CON-1 | v2.0 conformance claims MUST pass the Level-3 conformance checklist. | 00_spec_freeze_declaration_v2_0.md | Conformance process | Checklist results attached to certification report. |
| R-CON-2 | v2.0 conformance claims MUST satisfy the Level-3 test mapping. | 00_spec_freeze_declaration_v2_0.md | Conformance process | Test mapping results and evidence artifacts. |
| R-SCH-1 | Conformance claims MUST explicitly declare the scheduler policy used. | 00_spec_freeze_declaration_v2_0.md; scr_level3_determinism_policy.md | Scheduler policy declaration | Certification report includes declared policy identifier. |
| R-SCH-2 | Certification claims MUST declare the scheduler policy identifier and version; any policy used for certification MUST be explicitly named and versioned. | scr_level3_scheduler_model.md | Scheduler policy metadata | Evidence shows policy ID + version used for certification. |
| R-OBS-1 | Any nondeterministic observation behavior MUST be declared under the determinism policy. | scr_level3_measurement_observation.md | Determinism policy declaration | Determinism policy records nondeterministic observations. |
| R-OBS-2 | Nondeterministic observation MUST be declared to avoid invalid replay claims. | scr_level3_measurement_observation.md | Determinism policy declaration | Evidence that nondeterminism declarations exist for replay claims. |
| R-MIG-1 | No automatic migration; semantics MUST be implemented explicitly. | scr_level3_scheduler_model.md; scr_level3_execution_semantics.md; scr_level3_measurement_observation.md; scr_level3_determinism_policy.md | Semantic implementation | Evidence shows explicit v2.0 semantics with no automatic migration. |

---

## 3. Advisory Guidance (Non-Normative)

| Advisory ID | Advisory guidance | Source | Notes |
| --- | --- | --- | --- |
| A-ORD-1 | Execution ordering should follow declared scheduler policy. | hpl_v1_1_to_v2_0_migration_memo.md | Advisory for migration clarity. |
| A-AUTH-1 | Observations should be authorized and auditable. | hpl_v1_1_to_v2_0_migration_memo.md | Advisory for audit readiness. |

---

## 4. Evidence Plan Summary

- **Checklist evidence:** Provide the completed Level-3 checklist with pass/fail status.
- **Test mapping evidence:** Provide results for all Level-3 mapped tests with artifacts.
- **Scheduler policy declaration:** Include policy identifier and version in the certification report.
- **Determinism policy evidence:** Record any nondeterministic observations in the policy declaration.
- **Explicit semantics proof:** Show that v2.0 semantics are implemented deliberately (no auto-migration).

---

## 5. Notes

- This matrix does not introduce new requirements.
- Implementation choices (file formats, API shapes, CI cadence) are optional and
  may be used as evidence, but are not required by the spec.
