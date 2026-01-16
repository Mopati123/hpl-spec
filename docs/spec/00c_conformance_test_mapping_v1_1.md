# HPL Conformance Test Mapping — v1.1

## Purpose

This document defines a **normative mapping** between the **HPL Conformance Checklist v1.1**
(`docs/spec/00b_conformance_checklist_v1_1.md`) and **test identifiers** used to certify an
implementation.

The mapping is:
- **Spec-only** (no executable code)
- **Structural**, not semantic
- **Deterministic and auditable**
- **Implementation-agnostic**

An implementation is considered conformant iff all tests mapped to the required checklist
items pass.

---

## Scope

This mapping applies to **HPL Spec v1.1** as frozen in:
- `docs/spec/00_spec_freeze_declaration_v1_1.md` (to be issued)

It certifies:
- **Level 0 — Spec Integrity**
- **Level 1 — Front-End Conformance**
- **Level 2 — Recommended Non-runtime Tooling**

Runtime, simulator, scheduler, and backend behavior are explicitly **out of scope**.

---

## Naming Conventions

Test identifiers are symbolic and descriptive.  
They do **not** prescribe a test framework, language, or file layout.

Format (recommended, not enforced):

```

TEST_<LEVEL>*<AREA>*<SHORT_DESCRIPTION>

```

---

## Level 0 — Spec Integrity Mapping (MUST PASS)

| Checklist Item | Test Identifier(s) | Pass / Fail Criteria |
|---------------|-------------------|----------------------|
| L0.1 | `TEST_L0_SPEC_UNMODIFIED` | No normative spec files differ from frozen versions. |
| L0.2 | `TEST_L0_IMPL_OUTSIDE_H_FOLDERS` | No executable code exists inside `_H` directories. |
| L0.3 | `TEST_L0_H_FOLDERS_ONTOLOGY_ONLY` | `_H` folders contain only docs, registries, manifests. |
| L0.4 | `TEST_L0_SURFACE_AXIOMATIC_BOUNDARY` | Clear separation between surface DSL artifacts and axiomatic grammar enforcement. |

---

## Level 1 — Front-End Conformance Mapping (MUST PASS)

### Step 1 — Surface Parsing

| Checklist Item | Test Identifier(s) | Pass / Fail Criteria |
|---------------|-------------------|----------------------|
| L1.1 | `TEST_L1_PARSER_SURFACE_SEXPR` | Parser accepts well-formed S-expression surface input. |
| L1.2 | `TEST_L1_PARSER_MOMENTUM_EXAMPLE` | `examples/momentum_trade.hpl` parses without error. |
| L1.3 | `TEST_L1_PARSER_STRUCTURAL_ERRORS` | Invalid surface syntax fails with structural (not semantic) errors. |

---

### Step 2 — Macro Expansion (Normative Boundary)

| Checklist Item | Test Identifier(s) | Pass / Fail Criteria |
|---------------|-------------------|----------------------|
| L1.4 | `TEST_L1_MACRO_DETERMINISM` | Same surface input yields identical expanded output. |
| L1.5 | `TEST_L1_MACRO_PURITY` | Expansion performs no I/O or runtime side effects. |
| L1.6 | `TEST_L1_MACRO_TOTALITY` | Expansion yields axiomatic forms or explicit expansion error. |
| L1.7 | `TEST_L1_MACRO_NO_LEAKAGE` | No surface constructs reach IR construction. |
| L1.8 | `TEST_L1_MACRO_NAMESPACING` | Surface-derived identifiers are namespaced (e.g., `SURF_`). |
| L1.9 | `TEST_L1_MACRO_BOOTSTRAP_CANONICALIZATION` | Bootstrap canonicalization, if used, is structural only. |

---

### Step 3 — Axiomatic Validation

| Checklist Item | Test Identifier(s) | Pass / Fail Criteria |
|---------------|-------------------|----------------------|
| L1.10 | `TEST_L1_VALIDATOR_BNF_CONFORMANCE` | Expanded forms conform to `docs/spec/02_bnf.md`. |
| L1.11 | `TEST_L1_VALIDATOR_NO_SURFACE_FORMS` | Any residual surface construct is rejected. |
| L1.12 | `TEST_L1_VALIDATOR_ERROR_REPORTING` | Validation errors identify failing form and location/path. |

---

### Step 4 — IR Emission (ProgramIR)

| Checklist Item | Test Identifier(s) | Pass / Fail Criteria |
|---------------|-------------------|----------------------|
| L1.13 | `TEST_L1_IR_EMISSION_SCHEMA` | Emitted ProgramIR validates against `04_ir_schema.json`. |
| L1.14 | `TEST_L1_IR_NO_UNKNOWN_FIELDS` | IR contains no fields outside the schema. |
| L1.15 | `TEST_L1_IR_OPERATOR_CLASS_ENUM` | Operator classes are within `{U, M, Ω, C, I, A}`. |
| L1.16 | `TEST_L1_IR_CLASSIFICATION_RULES_V1_1` | Operator classes resolve from registry rules; no bootstrap defaulting. |
| L1.17 | `TEST_L1_IR_SCHEMA_VALIDATION_EXECUTED` | Schema validation is explicitly performed in the pipeline. |

---

## Level 2 — Recommended Non-runtime Tooling Mapping (SHOULD PASS)

| Checklist Item | Test Identifier(s) | Pass / Fail Criteria |
|---------------|-------------------|----------------------|
| L2.1 | `TEST_L2_REGISTRY_SCHEMA_VALIDATION` | Operator registries validate against registry schema. |
| L2.2 | `TEST_L2_REGISTRY_NO_EXEC_CODE` | Registry entries contain no executable content. |
| L2.3 | `TEST_L2_MACRO_TRACEABILITY` | Expansion retains source mapping metadata. |
| L2.4 | `TEST_L2_DIAGNOSTICS_TAXONOMY` | Diagnostics emit required taxonomy fields. |
| L2.5 | `TEST_L2_STRUCTURED_ERRORS` | Errors are machine-readable and stable. |

---

## Prohibited Behavior Mapping (FAIL CONDITIONS)

| Checklist Item | Test Identifier(s) | Fail Condition |
|---------------|-------------------|---------------|
| F.1 | `TEST_F_RUNTIME_IMPLEMENTATION_PRESENT` | Runtime/simulator/backends implemented under v1.1. |
| F.2 | `TEST_F_SURFACE_TO_IR_LEAKAGE` | Surface forms reach IR construction. |
| F.3 | `TEST_F_UNSPECIFIED_FEATURES` | New grammar, IR fields, or operator classes added. |
| F.4 | `TEST_F_UNKNOWN_IR_FIELDS_ACCEPTED` | Unknown IR fields accepted or ignored. |
| F.5 | `TEST_F_BOOTSTRAP_CLASS_DEFAULT_V1_1` | Defaulting all operators to `C`. |

---

## Certification Use

An implementation is **certified conformant** to HPL Spec v1.1 iff:

- All **Level 0** tests pass, and
- All **Level 1** tests pass, and
- No **Fail-condition tests** are triggered.

Level 2 conformance is recommended but not required for v1.1 certification.

---

## Notes

- This document maps **what must be tested**, not **how**.
- Test identifiers may map to one or more concrete tests.
- No test in this mapping asserts runtime, economic, or quantum semantics.
