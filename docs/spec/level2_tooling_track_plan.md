# Level 2 Tooling Track Plan (Informational)

## Purpose

This plan outlines **non-runtime tooling** work to reach Level 2 conformance
without changing HPL Spec v1 semantics.

## Scope (Allowed)

- Operator registry validation tooling (schema-only)
- Traceability metadata improvements (macro expansion source maps)
- Structured diagnostics and stable error codes

## Non-Goals

- Runtime, scheduler, or backend behavior
- New grammar constructs or operator classes
- IR schema changes

## Candidate Work Items

1. Registry validator that checks `operators/registry.json` against
   `docs/spec/06_operator_registry_schema.json`.
2. Minimal source-map format for macro expansion traceability.
3. Error code taxonomy for parser, expander, and validator errors.

## Notes

This document is informational only and does not override the frozen v1 spec.

---

## EXECUTION AUTHORIZATION (Level-2)

Checklist reference: `docs/spec/00k_level2_execution_checklist_v1.md`

### Entry Gate (Checked)

[x] HPL Spec v1 is frozen and certified (Level-1 complete)  
[x] Level-1 CI gates are green  
[x] No open, approved SCRs are being implemented  
[x] Work is explicitly labeled **Level-2 (Tooling Only)**  

### Allowed Level-2 Work Items (Initial Scope)

- Operator registry validation tooling (schema-only)
- Traceability metadata (surface → expanded → axiomatic → IR)
- Structured diagnostics and stable error categories

### Prohibited Items (Acknowledged)

- No grammar changes, operator class changes, or IR schema changes
- No runtime, scheduler, observers, or backends
- No semantic enforcement by tooling
