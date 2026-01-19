# HPL Spec Change Request (SCR) Review Checklist — v1

## Purpose

This checklist defines the **mandatory review criteria** for evaluating
Spec Change Requests (SCRs) against **HPL Spec v1**.

It ensures that:
- Spec evolution is disciplined and auditable
- Backward compatibility is preserved unless explicitly broken
- No implementation pressure drives spec law

This checklist governs **review and decision**, not submission.

---

## Normative References

All SCR reviews MUST be evaluated against:

- `docs/spec/00_spec_freeze_declaration_v1.md`
- `docs/spec/00g_release_versioning_policy_v1.md`
- `docs/spec/00h_spec_change_request_template_v1.md`
- `docs/spec/00b_conformance_checklist_v1.md`
- `docs/spec/00c_conformance_test_mapping_v1.md`

---

## Review Stages

Each SCR MUST pass **all stages** to be accepted.

---

## Stage 1 — Completeness Check (MUST PASS)

[ ] SCR uses the official template (`00h_spec_change_request_template_v1.md`)  
[ ] Target spec version is declared (e.g., v1.1 or v2.0)  
[ ] Affected documents are explicitly listed  
[ ] Change category is selected (clarification / extension / breaking)  
[ ] Motivation is clear and spec-level (not implementation-driven)

**Fail if any item is missing.**

---

## Stage 2 — Scope & Authority Check (MUST PASS)

[ ] Proposed change is within the authority of the spec (not tooling-only)  
[ ] Change does not contradict the current freeze declaration  
[ ] Change does not retroactively reinterpret v1 semantics  
[ ] Change is not already permitted under existing v1 allowances  

**Fail if the SCR attempts to “rewrite history.”**

---

## Stage 3 — Compatibility Assessment (MUST PASS)

[ ] Compatibility classification is correct:
- [ ] Backward-compatible (v1.1)
- [ ] Breaking (v2.0)

[ ] Justification for compatibility classification is sound  
[ ] No hidden breaking effects exist (implicit grammar, IR, or class changes)

**Fail if compatibility is misclassified.**

---

## Stage 4 — Impact Analysis Review (MUST PASS)

[ ] All affected areas are correctly identified  
[ ] IR schema impact is explicitly stated (or explicitly “none”)  
[ ] Operator class impact is explicitly stated (or explicitly “none”)  
[ ] Macro boundary impact is explicitly stated (or explicitly “none”)  

**Fail if impact analysis is incomplete or vague.**

---

## Stage 5 — Conformance & Certification Impact (MUST PASS)

[ ] Changes to conformance checklist are identified (if any)  
[ ] Changes to test mapping are identified (if any)  
[ ] Certification implications are explicitly stated  

**Fail if certification impact is not addressed.**

---

## Stage 6 — Migration Strategy (REQUIRED IF BREAKING)

(Only required for MAJOR changes)

[ ] Migration strategy is present and realistic  
[ ] Transition or deprecation plan is defined  
[ ] Target removal version is declared  

**Fail if breaking change lacks a migration path.**

---

## Stage 7 — Alternatives & Risk Review (SHOULD PASS)

[ ] Alternatives were considered and documented  
[ ] Risks (spec, ecosystem, tooling) are acknowledged  
[ ] Chosen approach is justified as minimal and precise  

---

## Stage 8 — Decision Readiness

[ ] SCR is ready for decision  
[ ] No unresolved review comments remain  

### Decision
- [ ] Accepted
- [ ] Accepted with modifications
- [ ] Deferred
- [ ] Rejected

Decision rationale recorded.

---

## Notes

- Approval of an SCR does **not** authorize implementation.
- Implementation may begin **only after** a new Spec Freeze Declaration is issued.
- All accepted SCRs MUST be referenced in the next freeze declaration.
