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
