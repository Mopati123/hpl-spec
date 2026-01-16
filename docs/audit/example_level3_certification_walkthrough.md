# EXAMPLE - NON-NORMATIVE - FOR WALKTHROUGH ONLY

# HPL v2.0 Certification Report (Walkthrough Example)

## 1. Certification Metadata

- **Implementation Name:** Example Implementation (Walkthrough)
- **Implementation Version:** N/A (walkthrough)
- **Certification Level:** Level-3 (Semantic)
- **Target Spec Version:** HPL v2.0
- **Report Version:** Example 1.0
- **Date:** 2026-01-16
- **Certifying Entity / Auditor:** Example Auditor (Walkthrough)

---

## 2. Scope Declaration

This report certifies conformance **only** to the following frozen specifications:

- HPL Spec v2.0
- Level-3 semantic requirements as defined in:
  - Scheduler Model
  - Execution Semantics
  - Measurement & Observation
  - Determinism Policy

Out-of-scope items are explicitly listed in Section 10.

---

## 3. Normative References

The following documents are authoritative for this certification:

- `docs/spec/00_spec_freeze_declaration_v2_0.md`
- `docs/spec/00n_conformance_checklist_level3_v2_0.md`
- `docs/spec/00o_conformance_test_mapping_level3_v2_0.md`
- `docs/spec/scr_level3_scheduler_model.md`
- `docs/spec/scr_level3_execution_semantics.md`
- `docs/spec/scr_level3_measurement_observation.md`
- `docs/spec/scr_level3_determinism_policy.md`

---

## 4. Scheduler Policy Declaration (Mandatory)

The implementation declares the following scheduler policy:

- **Scheduler Name / Identifier:** Example Deterministic Scheduler
- **Policy Type:** Deterministic (declared, not implemented)
- **Tick Authority:** Single declared scheduler authority (walkthrough)
- **Replay Guarantees:** Yes, conditional on declared policy and disclosures
- **Policy Reference:** N/A (walkthrough)

> Any determinism or replayability claim in this report depends on this declared policy.

---

## 5. Conformance Checklist Results (Level-3)

Each checklist item from
`00n_conformance_checklist_level3_v2_0.md`
MUST be reported here.

| Checklist ID | Description | Result (PASS/FAIL) | Evidence Reference |
|-------------|------------|--------------------|-------------------|
| L3-A-1 | Scheduler authority declared | PASS | Walkthrough declaration (Section 4) |
| L3-A-2 | Tick authority exclusive | PASS | Walkthrough declaration (Section 4) |
| L3-B-1 | Program state defined | PASS | Declared in walkthrough narrative |
| L3-B-2 | Evolution per tick | PASS | Declared in walkthrough narrative |
| L3-B-3 | Observables bounded | PASS | Declared in walkthrough narrative |
| L3-C-1 | Measurement authorized | PASS | Declared in walkthrough narrative |
| L3-C-2 | Observer capabilities declared | PASS | Declared in walkthrough narrative |
| L3-C-3 | Observation auditable | PASS | Declared in walkthrough narrative |
| L3-D-1 | Determinism claims policy-bound | PASS | Section 4 declaration |
| L3-D-2 | Nondeterminism declared | PASS | Walkthrough declaration |
| L3-D-3 | Replayability requirements | PASS | Walkthrough declaration |

(Values are illustrative; no implementation evidence provided.)

---

## 6. Test Mapping Evidence

For each checklist item, reference the corresponding test identifier(s)
from `00o_conformance_test_mapping_level3_v2_0.md`.

| Test ID | Description | Result | Evidence Artifact |
|-------|------------|--------|------------------|
| TEST_L3_SCHED_POLICY_DECLARED | Policy declared | PASS | N/A (walkthrough) |
| TEST_L3_SCHED_TICK_AUTHORITY | Tick authority exclusive | PASS | N/A (walkthrough) |
| TEST_L3_EXEC_STATE_DEFINED | Program state defined | PASS | N/A (walkthrough) |
| TEST_L3_EXEC_EVOLUTION_PER_TICK | Evolution per tick | PASS | N/A (walkthrough) |
| TEST_L3_EXEC_OBSERVABLES_DECLARED | Observables bounded | PASS | N/A (walkthrough) |
| TEST_L3_MEAS_AUTHORIZED | Measurement authorized | PASS | N/A (walkthrough) |
| TEST_L3_MEAS_CAPABILITIES_DECLARED | Capabilities declared | PASS | N/A (walkthrough) |
| TEST_L3_MEAS_AUDITABLE | Observation auditable | PASS | N/A (walkthrough) |
| TEST_L3_DET_POLICY_BOUND | Determinism policy bound | PASS | N/A (walkthrough) |
| TEST_L3_DET_ND_DECLARED | Nondeterminism declared | PASS | N/A (walkthrough) |
| TEST_L3_DET_REPLAY_REQUIREMENTS | Replayability requirements | PASS | N/A (walkthrough) |

---

## 7. Determinism & Replayability Claims

The implementation makes the following claims:

- **Deterministic Execution:** YES (declared, not implemented)
- **Replayable Execution:** YES (policy-dependent)
- **Nondeterministic Operators Declared:** YES (walkthrough declaration)

Operators (example only): NONE SPECIFIED (walkthrough)

---

## 8. Measurement & Observation Compliance

- **Measurement Events Are Explicit:** YES (declared)
- **Observers Are Authorized:** YES (declared)
- **Observation Side-Effects Declared:** YES (declared)

Evidence references are walkthrough-only and non-normative.

---

## 9. Deviations and Limitations

This is a walkthrough example. No implementation was evaluated.

---

## 10. Out-of-Scope Declarations

The following are explicitly NOT claimed:

- Performance guarantees
- Hardware or quantum backend fidelity
- Physical timing guarantees
- Economic or safety properties

---

## 11. Certification Decision

- **Certification Result:** PASS (walkthrough only)
- **Conditions (if any):** N/A
- **Validity Period:** N/A
- **Re-Certification Required Upon:** N/A

---

## 12. Sign-Off

- **Auditor / Authority Name:** Example Auditor (Walkthrough)
- **Signature:** N/A
- **Date:** 2026-01-16

---

## Appendix A - Evidence Index (Optional)

Walkthrough only; no evidence artifacts were produced.

---

*End of Report*
