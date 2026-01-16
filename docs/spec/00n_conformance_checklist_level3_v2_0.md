# HPL Level-3 Conformance Checklist - v2.0 (Skeleton)

## Purpose

This checklist defines the minimum conformance requirements for Level-3
semantics under HPL Spec v2.0. It is a skeleton to be finalized before a v2.0
freeze and certification.

---

## Eligibility Preconditions

[ ] Implementation is certified against HPL Spec v1.1 (Level-1 or higher)
[ ] Level-2 tooling remains non-semantic and unchanged in behavior
[ ] Target conformance claim explicitly states "HPL Spec v2.0"

---

## Scheduler Conformance

[ ] Scheduler policy is declared and versioned
[ ] Tick authority is the sole ordering source for execution
[ ] Scheduler decisions are observable only via declared interfaces

---

## Execution Semantics Conformance

[ ] Program state definition is explicit and auditable
[ ] Evolution function is defined per tick
[ ] Observables are declared and bounded

---

## Measurement and Observation Conformance

[ ] Measurement events are scheduler-authorized
[ ] Observer capabilities are declared
[ ] Observation outcomes are auditable

---

## Determinism Policy Conformance

[ ] Determinism claims cite a declared scheduler policy
[ ] Nondeterministic operators are explicitly declared
[ ] Replayability requirements are met for certification claims

---

## Explicit Exclusions

Level-3 conformance does NOT certify:
- Runtime performance or throughput
- Hardware bindings or backend behavior
- External I/O semantics

---

## Notes

- This checklist is a skeleton; it must be completed before v2.0 freeze.
- Items should map directly to tests in the Level-3 test mapping.
