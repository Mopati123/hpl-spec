# HPL v1 -> v2.0 Evolution Overview

## 1. Abstract

HPL is a governed programming language whose specification evolves through
explicit, auditable freezes. Governance is treated as a first-class design
problem so that semantics are defined before implementation and certification
is mechanical rather than interpretive. HPL is unusual in that it separates
syntax, tooling, and semantics into distinct phases, each frozen and certified
before the next layer is introduced.

## 2. The Problem HPL Addresses

Most languages introduce syntax, tooling, and semantics together. This blends
specification and implementation, making auditability and determinism claims
hard to verify. HPL separates these concerns to prevent semantic drift and to
allow certification based on declared, frozen artifacts.

## 3. v1: Syntax Without Meaning (Deliberate)

- Grammar defines the axiomatic core.
- Macro boundary separates surface DSL from axiomatic forms.
- IR schema defines structure only.
- Execution semantics are explicitly excluded.

This phase establishes a stable front-end law without runtime meaning.

## 4. v1.1: Law Refinement Without Execution

- Operator classification rules are formalized.
- Bootstrap defaults are removed to reduce ambiguity.
- No execution semantics are introduced.

This refines the law while remaining non-executing.

## 5. Level-2: Tooling Without Semantics

- Registry validation enforces schema correctness.
- Traceability records transformations without changing IR.
- Diagnostics standardize error reporting without changing pass/fail behavior.

Tooling is frozen before execution semantics to avoid semantic leakage.

## 6. v2.0: Semantic Closure

- Scheduler authority defines execution ordering and tick control.
- Execution semantics define state, evolution, and observables.
- Measurement and observation are explicit and auditable.
- Determinism policy binds replay claims to declared policies and disclosures.

This is a breaking but necessary step to define execution semantics.

## 7. Certification as a Design Outcome

- Conformance checklists define required claims.
- Test mappings bind claims to evidence identifiers.
- Certification reports record results and declared policies.

Claims are now verifiable and auditable without implementation ambiguity.

## 8. What HPL Is Not

- Not a runtime.
- Not a physics simulator.
- Not a trading system.

Those are downstream implementations that must conform to the frozen specs.

## 9. Current Status and Future Work

- v2.0 is frozen and authoritative.
- Future evolution requires new SCRs and subsequent freezes.
- Implementations must conform to the frozen specs and certification process.
