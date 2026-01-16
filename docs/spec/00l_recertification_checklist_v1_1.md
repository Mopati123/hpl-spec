# HPL Re-Certification Checklist — v1.1

## Purpose

This checklist defines the **minimal deltas** required to re-certify an
implementation from **HPL Spec v1** to **HPL Spec v1.1**.

It assumes prior **v1 Level-1 certification** and focuses only on v1.1 changes.

---

## Eligibility Preconditions (MUST PASS)

[ ] Implementation is certified under **HPL Spec v1 (Level-1)**.  
[ ] v1.1 freeze declaration is present: `docs/spec/00_spec_freeze_declaration_v1_1.md`.  
[ ] v1.1 conformance artifacts are available:
    - `docs/spec/00b_conformance_checklist_v1_1.md`
    - `docs/spec/00c_conformance_test_mapping_v1_1.md`

---

## Delta Requirements (v1 → v1.1)

### A. Operator Classification Rules (Required)

[ ] Operator class assignment conforms to the v1.1 classification rules.  
    - Reference: `docs/spec/scr_v1_1_operator_classification_rules.md`

[ ] Registry class resolution is used for all operator references.  
[ ] No inference from usage context is performed.  

Mapped tests:
- `TEST_L1_IR_CLASSIFICATION_RULES_V1_1`

---

### B. Removal of Bootstrap `cls=C` Default (Required)

[ ] No defaulting of all operators to `C`.  
[ ] Unclassified operator references fail IR emission.  

Mapped fail-condition:
- `TEST_F_BOOTSTRAP_CLASS_DEFAULT_V1_1`

---

### C. IR Invariants Clarification (Required)

[ ] Invariants are interpreted per the v1.1 clarification note.  
    - Reference: `docs/spec/scr_v1_1_ir_invariants_clarification.md`

Evidence required:
- Documentation note or tests demonstrating alignment (if applicable).

---

## What Does NOT Require Re-Testing

The following remain valid from v1 certification and do not require re-execution
unless implementation changes were made:

- Surface parser (L1.1–L1.3)  
- Macro expansion boundary (L1.4–L1.9)  
- Axiomatic validation mechanics (L1.10–L1.12)  
- IR schema structure (L1.13–L1.17), except for classification rules  

---

## Required Evidence

[ ] Test results covering `TEST_L1_IR_CLASSIFICATION_RULES_V1_1`.  
[ ] Evidence that bootstrap `cls=C` is not used (test or audit note).  
[ ] Evidence of invariants clarification alignment (note or test).  

---

## Failure Conditions

Re-certification MUST be denied if:

[ ] Defaulting to `cls=C` persists under v1.1.  
[ ] Operator classes are inferred from usage rather than registry rules.  
[ ] Unknown IR fields are accepted or ignored.  

---

## Certification Claim Language

On success, the certification claim MUST state:

> “HPL Spec v1.1 — Level-1 Front-End Conformance (Re-certified)”

Mixed claims are invalid.

---

## Notes

This checklist is **additive** to v1 certification and does not override the
v1 conformance record.
