# HPL Level-2 Execution Checklist — v1

## Purpose

This checklist governs **Level-2 tooling work** for HPL under **Spec v1**.

Level-2 work:
- Improves **tooling, observability, and diagnostics**
- Introduces **no new language semantics**
- Requires **no Spec Change Request (SCR)**

Passing this checklist authorizes Level-2 implementation to proceed while keeping
the **v1 language law immutable**.

---

## Normative References

Level-2 execution MUST comply with:

- `docs/spec/00_spec_freeze_declaration_v1.md`
- `docs/spec/00b_conformance_checklist_v1.md`
- `docs/spec/00f_ci_gate_policy_v1.md`
- `docs/spec/00g_release_versioning_policy_v1.md`

And respect:
- `docs/spec/02b_macro_boundary.md`
- `docs/spec/04_ir_schema.json`
- `docs/spec/04b_ir_freeze_policy.md`
- `docs/spec/06_operator_registry_schema.json`

---

## Definition: Level-2 Tooling

Level-2 tooling is **non-semantic** work that:

- Does NOT change:
  - Grammar
  - Operator classes
  - IR schema
  - Macro boundary rules
- Does NOT introduce:
  - Runtime execution
  - Scheduler logic
  - Observers
  - Backends

Examples of allowed Level-2 tooling:
- Operator registry validators
- Traceability metadata
- Structured diagnostics
- Error normalization
- Developer tooling / introspection

---

## Entry Gate (MUST ALL BE TRUE)

[ ] HPL Spec v1 is frozen and certified (Level-1 complete)  
[ ] Level-1 CI gates are green  
[ ] No open, approved SCRs are being implemented  
[ ] Work is explicitly labeled **Level-2 (Tooling Only)**  

---

## Allowed Level-2 Work Items

### A. Operator Registry Tooling

[ ] Validate registry files against `06_operator_registry_schema.json`  
[ ] Enforce structural correctness (types, required fields)  
[ ] No semantic interpretation of operators  

---

### B. Traceability & Source Mapping

[ ] Preserve mappings:
   - Surface → Expanded → Axiomatic → IR  
[ ] Trace data is metadata only (non-normative)  
[ ] Trace failures do not affect program validity  

---

### C. Diagnostics & Errors

[ ] Standardize error categories (parse, macro, validation, IR)  
[ ] Errors remain structural, not semantic  
[ ] No auto-correction or heuristic behavior  

---

### D. Developer Tooling

[ ] CLI helpers, inspectors, or formatters  
[ ] Visualization of AST / IR (read-only)  
[ ] No execution or simulation capability  

---

## Explicitly Prohibited in Level-2

[ ] Adding new grammar constructs  
[ ] Changing operator class meaning  
[ ] Modifying IR fields or schema  
[ ] Introducing runtime semantics  
[ ] Implementing schedulers or backends  
[ ] Using Level-2 tooling to “enforce” semantics  

Any prohibited change requires an SCR.

---

## CI & Governance Enforcement

[ ] CI Gate A (Spec Integrity) passes  
[ ] CI Gate C (Prohibited Behavior) passes  
[ ] No CI rules weakened or bypassed  

Any CI failure blocks merge.

---

## Evidence & Audit (REQUIRED)

[ ] Each Level-2 feature has:
   - A short description
   - Clear justification as tooling-only
   - Reference to this checklist  

[ ] Evidence recorded under `docs/audit/` (if non-obvious)

---

## Exit Criteria

Level-2 execution is considered valid when:

- All checklist items above are satisfied
- CI gates remain green
- No semantic drift is introduced

Level-2 work does NOT require certification, but MUST remain compatible with
existing Level-1 certification.

---

## Declaration

By executing Level-2 work under this checklist, the implementer affirms that:

- v1 language law remains unchanged
- Tooling does not reinterpret semantics
- Any semantic need will be raised via SCR

---

## Notes

- Level-2 is intentionally permissive but tightly bounded.
- Violations invalidate Level-1 certification claims until resolved.
