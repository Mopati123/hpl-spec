# HPL CI Gate Policy — v1

## Purpose

This document defines the **mandatory CI gating rules** for repositories claiming
conformance with **HPL Spec v1**.

The policy ensures that:
- No implementation merges violate the frozen specification.
- Conformance is mechanically enforced, not manually interpreted.
- Certification artifacts remain authoritative.

This policy introduces **no new language requirements**. It operationalizes
existing governance documents.

---

## Normative References

This policy enforces compliance with:

- `docs/spec/00_spec_freeze_declaration_v1.md`
- `docs/spec/00b_conformance_checklist_v1.md`
- `docs/spec/00c_conformance_test_mapping_v1.md`
- `docs/spec/00d_certification_report_template_v1.md`
- `docs/spec/00e_implementation_intake_checklist_v1.md`

Core specs:
- `docs/spec/02_bnf.md`
- `docs/spec/02b_macro_boundary.md`
- `docs/spec/04_ir_schema.json`
- `docs/spec/04b_ir_freeze_policy.md`
- `docs/spec/06_operator_registry_schema.json`

---

## Gate Levels

### Gate A — Spec Integrity (MUST PASS)

Triggered on:
- Any pull request
- Any commit to protected branches

Checks:
- No changes to frozen normative spec files unless accompanied by:
  - a version bump, and
  - an updated freeze declaration.
- No executable code added to `_H` sub-Hamiltonian directories.

Failure of Gate A **blocks merge**.

---

### Gate B — Front-End Conformance (MUST PASS)

Triggered on:
- Any change to implementation under `src/`

Checks:
- All Level 1 tests defined in
  `docs/spec/00c_conformance_test_mapping_v1.md` pass.
- The pipeline produces a ProgramIR that validates against
  `docs/spec/04_ir_schema.json`.
- No surface DSL constructs reach IR construction.

Failure of Gate B **blocks merge**.

---

### Gate C — Prohibited Behavior Scan (MUST PASS)

Triggered on:
- Any pull request affecting code or tests

Checks:
- No runtime, simulator, scheduler, observer, or backend implementations are introduced under v1.
- No new grammar constructs, operator classes, or IR fields beyond v1 specs.
- No acceptance or silent ignoring of unknown IR fields.

Failure of Gate C **blocks merge**.

---

### Gate D — Certification Readiness (SHOULD PASS)

Triggered on:
- Release branches or certification candidates

Checks:
- A completed (or draft) certification report exists at:
  `docs/spec/00d_certification_report_template_v1.md`
- Evidence fields reference test outputs or logs.

Failure of Gate D does **not** block merge but blocks **certification claims**.

---

## Required CI Artifacts

A conformant CI pipeline MUST produce:

- Test results covering all Level 1 checklist items
- Schema validation output for ProgramIR
- A clear pass/fail signal for each gate (A–C)

Artifacts SHOULD be retained for audit.

---

## Enforcement Rules

- CI gating decisions override manual approvals.
- Emergency overrides require explicit documentation under `docs/audit/`
  and invalidate certification until resolved.
- CI configuration MUST NOT weaken or bypass these gates.

---

## Scope Limitations

This policy does NOT:
- Define how tests are implemented
- Require a specific CI provider or tool
- Certify runtime correctness, performance, or economics

It enforces **structural and governance conformance only**.

---

## Policy Status

- Applies to: **HPL Spec v1**
- Phase: **Pre-Runtime / Front-End Only**
- Authority: **Specification First**

Any modification to this policy requires a spec version increment.
