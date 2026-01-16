# HPL Spec Change Request (SCR) - v2.0

## Purpose

This template governs **proposals to change, extend, or clarify** the Hamiltonian
Programming Language (HPL) specification after the **v1.1 freeze**.

It ensures that:
- All changes are explicit, reviewable, and versioned
- Backward compatibility is assessed before approval
- No implementation-driven drift occurs

Submission of an SCR does **not** imply approval.

---

## Normative References

All change requests are evaluated against:

- `docs/spec/00_spec_freeze_declaration_v1_1.md`
- `docs/spec/00g_release_versioning_policy_v1.md`
- `docs/spec/00h_spec_change_request_template_v1.md`
- `docs/spec/00j_scr_review_checklist_v1.md`

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

- SCR ID: SCR-LEVEL3-DETERMINISM-POLICY
- Title: Level-3 Determinism Policy
- Author(s): Codex execution (per user instruction)
- Date submitted: 2026-01-16
- Target spec version (e.g., v1.1 or v2.0): v2.0
- Affected documents:
  - New v2.0 determinism policy document (to be created)
  - v2.0 conformance checklist and test mapping (to be created)
- Change category:
  - [ ] Clarification (non-semantic)
  - [ ] Backward-compatible extension
  - [x] Breaking change (requires MAJOR version)

---

## Motivation

Clarify when and how HPL guarantees determinism, replayability, and acceptable
nondeterminism.

---

## Proposed Change

### Definitions

- **Determinism:** The property that identical inputs and declared scheduler
  policy yield identical observable outcomes.
- **Replayability:** The ability to reproduce outcomes by reusing the declared
  scheduler policy and required nondeterminism disclosures.
- **Nondeterministic operators:** Declared operators whose outcomes are not
  fixed by inputs and policy alone.

### Proposed Policy (Draft)

- Determinism is guaranteed up to declared nondeterministic operators.
- Scheduler policy must be declared for certification claims.
  Determinism and replay claims are valid only with a declared scheduler policy
  and explicit nondeterminism declarations in
  `docs/spec/scr_level3_measurement_observation.md`.

---

## Impact Analysis (Required)

### A) Compatibility

- Does this change preserve backward compatibility?
  - [ ] Yes (MINOR version)
  - [x] No (MAJOR version required)

### B) Affected Areas

- [ ] Alphabet / Keywords
- [ ] Axiomatic Grammar (BNF)
- [ ] Macro Boundary
- [ ] Operator Algebra / Classes
- [ ] IR Schema
- [ ] Operator Registry Schema
- [x] CI / Conformance / Certification
- [x] Release & Versioning Policy
- [x] Other (specify): Level-3 determinism policy

Impact statements:
- IR schema: no changes proposed.
- Operator classes: no changes proposed.
- Macro boundary: no changes proposed.

---

## Migration Strategy (If Breaking)

- v1/v1.1 implementations remain valid but cannot claim v2.0 conformance.
- Migration requires adopting the determinism policy and new Level-3 conformance
  tests that validate determinism claims.
- No automatic migration; semantics must be implemented explicitly.

---

## Conformance Implications

- Determinism claims become certifiable properties under Level-3 tests.
- Existing tooling remains valid under v1/v1.1.

---

## Risks

- Determinism claims may be overstated without explicit nondeterminism
  declarations; mitigation is mandatory disclosure in conformance evidence.
- Replayability depends on declared scheduler policies and seeds; absence of
  these artifacts invalidates determinism claims.

---

## Alternatives Considered

- Omit a determinism policy (rejected: leaves certification claims ambiguous).

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

- Approval of this SCR does not authorize implementation.
- Implementation may begin only after a v2.0 freeze declaration.

---

## REVIEW RECORD (v2.0)

- Checklist: `docs/spec/00j_scr_review_checklist_v1.md`
- Review date: 2026-01-16
- Reviewers: Codex execution (per user instruction)
- Stage results:
  - Stage 1 (Completeness): PASS
  - Stage 2 (Scope & Authority): PASS
  - Stage 3 (Compatibility): PASS
  - Stage 4 (Impact Analysis): PASS
  - Stage 5 (Conformance & Certification): PASS
  - Stage 6 (Migration, if breaking): PASS
  - Stage 7 (Alternatives & Risk): PASS
  - Stage 8 (Decision Readiness): PASS
- Disposition: Ready
- Conditions (if any): None
- Reference summary: None
