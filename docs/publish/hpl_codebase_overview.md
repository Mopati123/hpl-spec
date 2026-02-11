# HPL Codebase Overview

## Repository Role

This repository is the canonical, frozen specification and governance source
for HPL. It also contains the reference governed runtime kernel and tooling.
Execution exists, but is constitution-gated (token authority, refusal-first,
deterministic evidence, reconciliation/rollback). Unconstrained general-purpose
runtime is intentionally out of scope.

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

## 2) Implementation Code (Governed Kernel)

All executable code lives under `src/hpl/` and implements the governed runtime
kernel, the Level-1 pipeline, and the tooling required for evidence, anchoring,
and IO governance.

### Core pipeline

- `src/hpl/emergence/dsl/parser.py`: surface DSL S-expression parser
- `src/hpl/emergence/macros/expander.py`: macro expansion to axiomatic forms
- `src/hpl/axioms/validator.py`: axiomatic validator against BNF
- `src/hpl/dynamics/ir_emitter.py`: ProgramIR emission + schema validation

### Governed runtime kernel

- `src/hpl/scheduler.py`: deterministic planning + token issuance
- `src/hpl/runtime/engine.py`: effect execution, refusal-first gating
- `src/hpl/runtime/contracts.py`: contract preconditions/postconditions
- `src/hpl/runtime/effects/`: effect handlers (IO, bundle, ΔS, etc.)
- `src/hpl/runtime/io/`: governed IO lane + adapters
- `src/hpl/runtime/net/`: governed NET lane + adapters
- `src/hpl/observers/`: Papas observer reports (witness-only)
- `src/hpl/execution_token.py`: token policy enforcement (IO/ΔS budgets)
- `src/hpl/operators/registry.py`: operator registry enforcement
- `src/hpl/audit/`: constraint witness + inversion

### Supporting utilities

- `src/hpl/ast.py`: AST types and source locations
- `src/hpl/errors.py`: structured error types
- `src/hpl/trace.py`: traceability (sidecar metadata)
- `src/hpl/diagnostics.py`: diagnostics normalization (Level-2 tooling)

---

## 3) Tests

Located under `tests/`:

- parser / macro / IR pipeline tests
- scheduler + runtime gating tests
- IO lane tests (policy, redaction, reconcile/rollback)
- ΔS gate and refusal taxonomy tests
- anchor generator + verifier tests
- operator registry enforcement tests
- Papas observer report tests

Fixtures: `tests/fixtures/`

---

## 4) Tooling & CI Gates

Located under `tools/`:

- `ci_gate_spec_integrity.py`: Gate A (no executables in `_H`)
- `ci_gate_prohibited_behavior.py`: Gate C (prohibited behavior scan)
- `validate_ir_schema.py`: IR schema validation
- `validate_operator_registries.py`: registry schema validation
- `anchor_generator.py`: Phase-1 anchor generation
- `verify_anchor.py`: Phase-1 anchor verification

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
- Governed runtime kernel implemented (scheduler + runtime engine + IO lane)
- Phase-1 anchoring implemented (Merkle root + signature + verification)
- Operator registry enforcement implemented (opt-in hard-fail + re-validate)
- Papas observer reports implemented (witness-only)

---

If you want a line-by-line status map, see:
`docs/publish/hpl_capability_matrix.md`
