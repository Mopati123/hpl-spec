# HPL Spec v2.0 Freeze Prerequisites

## Purpose

This document defines the **mandatory prerequisites** for declaring a frozen
**HPL Spec v2.0**. It ensures that the first semantic layer for execution is
frozen only when governance, conformance, and migration artifacts are complete.

This document is **spec-only** and introduces no new semantics.

---

## Scope of v2.0 Freeze

The v2.0 freeze MUST include the following READY Level-3 SCRs:

- `docs/spec/scr_level3_scheduler_model.md`
- `docs/spec/scr_level3_execution_semantics.md`
- `docs/spec/scr_level3_measurement_observation.md`
- `docs/spec/scr_level3_determinism_policy.md`

No additional SCRs may be included without explicit approval and a refreshed
prerequisites review.

---

## Compatibility Statement

- HPL Spec v2.0 is a **breaking** semantic release.
- HPL Spec v1 and v1.1 remain valid and unchanged.
- Implementations certified under v1/v1.1 remain valid only for those versions
  and must not claim v2.0 conformance without re-certification.

---

## Conformance Machinery (Required)

Before freezing v2.0, the following artifacts MUST exist (at least as
skeletons with authoritative scope):

- Level-3 conformance checklist (v2.0)
- Level-3 conformance test mapping (v2.0)

These artifacts must be sufficient to certify semantic requirements as defined
by the v2.0 SCRs.

---

## Migration Artifacts (Required)

Before freezing v2.0, the following artifacts MUST exist:

- v1.1 -> v2.0 migration memo

The memo must explain what changes, what does not, and how re-certification is
performed under v2.0.

---

## Audit Requirements

Before freezing v2.0, the following audit artifacts MUST exist:

- Consolidated decision log covering the four Level-3 SCRs included in scope

This ensures traceability for the transition into the first semantic release.

---

## Implementation Boundary

- A v2.0 freeze does NOT require runtime implementation.
- The semantic layer MUST be specified with sufficient precision to be testable
  via the Level-3 conformance checklist and mapping.

---

## Declaration Readiness Checklist

All items below MUST be satisfied prior to declaring v2.0 frozen:

[ ] All four Level-3 SCRs listed in Scope are READY
[ ] Level-3 conformance checklist (v2.0) exists
[ ] Level-3 test mapping (v2.0) exists
[ ] v1.1 -> v2.0 migration memo exists
[ ] Consolidated v2.0 decision log exists
[ ] No unresolved dependencies between Level-3 SCRs remain

---

## Notes

- This prerequisites document does not authorize implementation.
- Freeze declaration requires a separate v2.0 Spec Freeze Declaration.
