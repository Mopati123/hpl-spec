# HPL v1 Compliance Memo

## Status

HPL Spec v1 is certified at **Level-1 Front-End Conformance**.

## What Is Certified

- Surface parser (S-expression)
- Macro expansion (deterministic, pure, total)
- Axiomatic validation (BNF-conformant, no surface leakage)
- ProgramIR emission (schema-valid, no unknown fields)

## Explicitly Out of Scope

- Runtime or scheduler semantics
- Simulator execution models
- Observers/backends and QASM execution
- Economic/market semantics

## Certification Anchor

- Tag: `hpl-spec-v1-level1-certified`
- Certification report: `docs/spec/00d_certification_report_template_v1.md`
- Evidence: `docs/audit/level1_test_run_2026-01-15.md`

## Notes

This memo is informational and does not modify the frozen v1 specification.
