# HPL Level-3 Conformance Test Mapping - v2.0 (Skeleton)

## Purpose

This document maps Level-3 conformance checklist items to named test
identifiers. It is a skeleton for v2.0 certification planning.

---

## Naming Convention

TEST_L3_<AREA>_<SHORT_DESCRIPTION>

---

## Scheduler Conformance

| Checklist Item | Test Identifier | Pass / Fail Criteria |
| --- | --- | --- |
| Scheduler policy declared | TEST_L3_SCHED_POLICY_DECLARED | Policy identifier/version is present in evidence. |
| Tick authority exclusive | TEST_L3_SCHED_TICK_AUTHORITY | No ordering outside declared scheduler policy. |
| Observable interfaces only | TEST_L3_SCHED_DECLARED_INTERFACES | Evidence shows only declared interfaces expose ordering. |

---

## Execution Semantics Conformance

| Checklist Item | Test Identifier | Pass / Fail Criteria |
| --- | --- | --- |
| Program state defined | TEST_L3_EXEC_STATE_DEFINED | State model is defined in spec evidence. |
| Evolution per tick | TEST_L3_EXEC_EVOLUTION_PER_TICK | Evolution function is defined for each tick. |
| Observables bounded | TEST_L3_EXEC_OBSERVABLES_DECLARED | Observables are explicitly listed and bounded. |

---

## Measurement and Observation Conformance

| Checklist Item | Test Identifier | Pass / Fail Criteria |
| --- | --- | --- |
| Measurement authorized | TEST_L3_MEAS_AUTHORIZED | Evidence ties measurement to scheduler authority. |
| Observer capabilities declared | TEST_L3_MEAS_CAPABILITIES_DECLARED | Capabilities are declared and scoped. |
| Observation auditable | TEST_L3_MEAS_AUDITABLE | Audit trail exists for observations. |

---

## Determinism Policy Conformance

| Checklist Item | Test Identifier | Pass / Fail Criteria |
| --- | --- | --- |
| Determinism claims policy-bound | TEST_L3_DET_POLICY_BOUND | Claims cite declared scheduler policy. |
| Nondeterminism declared | TEST_L3_DET_ND_DECLARED | Nondeterministic operators are explicitly listed. |
| Replayability requirements | TEST_L3_DET_REPLAY_REQUIREMENTS | Required artifacts are present for replay. |

---

## Test Classification

- Policy declaration tests: evidence-only, structural compliance.
- Semantic assertion tests: verify declared invariants, not runtime behavior.

---

## Notes

- This mapping is a skeleton; pass/fail criteria must be finalized before v2.0 freeze.
- No runtime or backend assumptions are implied by these tests.
