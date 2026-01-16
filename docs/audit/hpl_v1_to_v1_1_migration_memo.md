# HPL v1 → v1.1 Migration Memo

## Executive Summary

HPL Spec v1.1 is now frozen and authoritative. It is **backward compatible** with v1
at the grammar and IR schema level, but it tightens **operator classification rules**
and removes the bootstrap `cls = C` default. Implementations certified under v1 may
continue to claim v1 conformance, but must be **re-certified** to claim v1.1.

---

## What v1.1 Is and Why It Exists

v1.1 formalizes operator classification to eliminate ambiguity and improve auditability.
This enables consistent class assignment without changing syntax or IR structure.

---

## Who Needs to Migrate (and Who Doesn’t)

**Must migrate to claim v1.1:**
- Any implementation claiming “HPL Spec v1.1” conformance.

**May remain on v1:**
- Implementations that do not need stricter class enforcement and remain certified
  under v1.

---

## What Did NOT Change

- **Grammar:** `docs/spec/02_bnf.md`
- **Macro boundary:** `docs/spec/02b_macro_boundary.md`
- **IR schema structure:** `docs/spec/04_ir_schema.json`
- **Level‑2 tooling validity:** L2-A/L2-B/L2-C remain valid and unaffected

---

## What DID Change (Normative)

1. **Operator classification rules are mandatory**  
   - `docs/spec/scr_v1_1_operator_classification_rules.md`

2. **Bootstrap `cls = C` default removed**  
   - `docs/spec/scr_v1_1_remove_bootstrap_cls_c.md`

3. **IR invariants clarified**  
   - `docs/spec/scr_v1_1_ir_invariants_clarification.md`

---

## Migration Steps (Mechanical)

1. **Replace defaulting with classification logic**  
   - Resolve operator classes from registry entries per v1.1 rules.

2. **Update registries and emitters accordingly**  
   - Ensure every operator reference resolves to a declared class.

3. **Run the v1.1 re‑certification checklist**  
   - `docs/spec/00l_recertification_checklist_v1_1.md`

---

## Certification Claims

**Valid:**
- “HPL Spec v1 — Level‑1 Front‑End Conformance”
- “HPL Spec v1.1 — Level‑1 Front‑End Conformance (Re‑certified)”

**Invalid:**
- Any mixed or ambiguous version claim.

---

## Timeline & Risk

- **Backward compatibility:** v1.1 does not change grammar or IR schema fields.
- **Adoption order (recommended):**
  1) Update classification logic
  2) Update registries
  3) Re‑certify under v1.1

---

## References

- Freeze declaration: `docs/spec/00_spec_freeze_declaration_v1_1.md`
- Re‑certification checklist: `docs/spec/00l_recertification_checklist_v1_1.md`
