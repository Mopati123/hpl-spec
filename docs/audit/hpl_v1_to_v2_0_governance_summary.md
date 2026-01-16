# HPL v1 -> v2.0 Governance Summary

## Executive Overview

HPL is a governed programming language whose evolution is controlled by
specification law before implementation. Governance was treated as first-class
so that semantics cannot drift from the spec and certification is mechanical,
not interpretive.

---

## v1 - Syntax and Front-End Law

- Grammar defined the axiomatic core language.
- Macro boundary separated surface DSL from axiomatic forms.
- IR schema provided a structural contract only.
- Semantics were intentionally absent to prevent premature execution rules.

---

## v1.1 - Refinement Without Semantics

- Operator classification rules were formalized.
- Bootstrap defaults were removed to reduce ambiguity.
- No execution semantics were introduced.
- v1.1 stayed front-end only and remained non-executing.

---

## Level-2 - Tooling Without Meaning

- Registry validation enforced schema-only correctness.
- Traceability created auditable metadata without changing IR.
- Diagnostics standardized error structure without changing pass/fail behavior.
- Tooling was frozen before execution semantics to prevent semantic leakage.

---

## v2.0 - Semantic Closure

- Scheduler authority defined execution ordering and tick control.
- Execution semantics defined state, evolution, and observables.
- Measurement and observation became explicit and auditable.
- Determinism policy bound replay claims to declared policies and disclosures.
- This is a breaking semantic release; v1 and v1.1 remain valid.

---

## Certification Architecture

- Conformance checklists specify required claims.
- Test mappings bind claims to evidence identifiers.
- Certification reports record results and declared policies.
- Claims are now auditable and reproducible.

---

## What HPL Is Not

- Not a runtime implementation
- Not a physics engine
- Not a trading system

Those are downstream implementations that must conform to the frozen specs.

---

## Current Status

- v1 frozen and certified
- v1.1 frozen with migration and re-certification paths
- v2.0 frozen with semantic law and certification machinery

Future evolution requires new SCRs and subsequent freezes.
