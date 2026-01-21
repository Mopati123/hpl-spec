# HPL Codebase Overview

## Repository Role

This repository is the canonical, frozen specification and governance source
for HPL v1 -> v2.0. It also contains a partial reference implementation for the
Level-1 pipeline and Level-2 tooling.

---

## 1) Top-Level Structure

### Sub-Hamiltonians (`*_H` folders)

Spec-only modules defining ontology and boundaries:

- `axioms_H`: alphabet, grammar, operator algebra, invariants
- `dynamics_H`: time-evolution semantics, scheduler authority, epoch model
- `emergence_H`: surface DSL & macros (spec side)
- `backends_H`: lowering targets (e.g., QASM mapping)
- `observers_H`: observer identity & authorization model
- `audit_H`: audit artifacts, trace schemas, proof hooks
- `runtime_H`: orchestration contracts (spec only)
- `tools_H`: tooling intent (spec only)
- `tests_H`: conformance intent (spec only)
- `infra_H`: packaging / CI/CD intent (spec only)
- `data_H`: fixtures and traces (spec only)

Registries present:
- `axioms_H/operators/registry.json`
- `dynamics_H/operators/registry.json`
- `emergence_H/operators/registry.json`
- `backends_H/operators/registry.json`

Other `_H` folders contain `docs/` and `manifests/` placeholders only.

---

## 2) Implementation Code (Partial)

All executable code lives under `src/hpl/` and implements the Level-1 pipeline
plus Level-2 tooling.

### Core pipeline

- `src/hpl/emergence/dsl/parser.py`: surface DSL S-expression parser
- `src/hpl/emergence/macros/expander.py`: macro expansion to axiomatic forms
- `src/hpl/axioms/validator.py`: axiomatic validator against BNF
- `src/hpl/dynamics/ir_emitter.py`: ProgramIR emission + schema validation

### Supporting utilities

- `src/hpl/ast.py`: AST types and source locations
- `src/hpl/errors.py`: structured error types
- `src/hpl/trace.py`: traceability (sidecar metadata)
- `src/hpl/diagnostics.py`: diagnostics normalization (Level-2 tooling)

---

## 3) Tests

Located under `tests/`:

- `test_parser.py`
- `test_macro_expansion.py`
- `test_axiomatic_validation.py`
- `test_ir_emission.py`
- `test_pipeline.py`
- `test_registry_validator.py`
- `test_traceability.py`
- `test_diagnostics.py`

Fixtures: `tests/fixtures/`

---

## 4) Tooling & CI Gates

Located under `tools/`:

- `ci_gate_spec_integrity.py`: Gate A (no executables in `_H`)
- `ci_gate_prohibited_behavior.py`: Gate C (prohibited behavior scan)
- `validate_ir_schema.py`: IR schema validation
- `validate_operator_registries.py`: registry schema validation

---

## 5) Examples

- `examples/momentum_trade.hpl`: surface DSL example (requires macro expansion)

---

## 6) Normative Specs & Governance

- Freeze declarations (v1, v1.1, v2.0)
- Conformance checklists + mappings
- Certification report templates (v1, v2.0)
- IR schema and freeze policy
- Operator registry schema
- QASM lowering rules
- SCR templates and review checklists
- Migration memos (v1 -> v1.1, v1.1 -> v2.0)

---

## 7) Current Status (Truthful)

- v1 frozen and certified (front-end)
- v1.1 frozen (refined law + migration)
- v2.0 frozen (semantic layer: scheduler, execution, observation, determinism)
- Level-2 tooling complete and frozen
- Level-1 implementation present and tested (parser -> macro -> validator -> IR)

---

If you want this overview indexed in `UNIVERSE_INDEX.md`, add a pointer under
Publications or Audit & Evidence.
