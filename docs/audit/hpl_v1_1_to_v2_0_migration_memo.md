# HPL v1.1 -> v2.0 Migration Memo

## Executive Summary

HPL Spec v2.0 introduces the first authoritative **execution semantics** layer
for the language. This is a **breaking** change relative to v1/v1.1, which are
front-end specifications only. v1 and v1.1 remain valid and unchanged.

This memo describes what v2.0 introduces, what stays the same, and how to
migrate or choose to remain on v1/v1.1.

---

## What v2.0 Introduces

- **Scheduler authority as semantic law** (ordering and tick authority).
- **Execution semantics** for state, evolution, and observables.
- **Measurement and observation semantics** with explicit authorization.
- **Determinism policy** that binds replayability to declared policies.

These semantics are defined by the READY Level-3 SCRs and will be frozen only
after completing v2.0 governance prerequisites.

---

## What Does NOT Change

- **Grammar:** `docs/spec/02_bnf.md` is unchanged.
- **Macro boundary:** `docs/spec/02b_macro_boundary.md` is unchanged.
- **IR schema:** `docs/spec/04_ir_schema.json` is unchanged.
- **Level-2 tooling:** registry validation, traceability, and diagnostics remain
  valid and non-semantic.

---

## What Changes (Breaking)

- **Scheduler authority becomes semantic:** execution ordering is no longer
  implementation-defined; it must follow declared scheduler policy.
- **Execution is defined:** state evolution and observables are now governed by
  normative rules rather than left unspecified.
- **Measurement semantics are explicit:** observations must be authorized and
  auditable.
- **Determinism claims require policy declarations:** replayability depends on
  declared scheduler policy and nondeterminism disclosure.

---

## Migration Paths

### 1) Stay on v1 or v1.1 (Front-End Only)

- No changes required.
- Existing certifications remain valid.
- Do not claim v2.0 conformance.

### 2) Migrate to v2.0 (Execution Semantics)

- Adopt the Level-3 scheduler model, execution semantics, measurement/observation
  rules, and determinism policy.
- Prepare Level-3 conformance evidence and testing per the v2.0 checklist and
  mapping once finalized.

### 3) Dual-Target Strategy (Optional)

- Maintain v1/v1.1 front-end compliance while adding v2.0 semantics behind a
  feature gate.
- Report certification claims per version separately (no mixed claims).

---

## Certification Impact

- **v1/v1.1 certifications remain valid** and unaffected.
- **v2.0 requires new Level-3 certification** using the v2.0 conformance checklist
  and test mapping.
- Mixed claims (e.g., "v1.1 + v2.0") are invalid.

---

## Risk & Adoption Guidance

### Migrate early if:
- You need deterministic replay or audit-grade execution semantics.
- You plan runtime or scheduler development aligned to v2.0.

### Delay migration if:
- You only require front-end tooling and static IR emission.
- Your runtime strategy is undecided.

---

## References

- `docs/spec/scr_level3_scheduler_model.md`
- `docs/spec/scr_level3_execution_semantics.md`
- `docs/spec/scr_level3_measurement_observation.md`
- `docs/spec/scr_level3_determinism_policy.md`
- `docs/spec/00m_v2_0_freeze_prerequisites.md`
- `docs/spec/00n_conformance_checklist_level3_v2_0.md`
- `docs/spec/00o_conformance_test_mapping_level3_v2_0.md`

---

## Notes

- This memo is advisory and does not itself freeze v2.0.
- v2.0 freeze requires completion of the prerequisites in
  `docs/spec/00m_v2_0_freeze_prerequisites.md`.
