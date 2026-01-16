# HPL v2.0 Certification Report Template

## 1. Certification Metadata

- **Implementation Name:**
- **Implementation Version:**
- **Certification Level:** Level-3 (Semantic)
- **Target Spec Version:** HPL v2.0
- **Report Version:**
- **Date:**
- **Certifying Entity / Auditor:**

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

- **Scheduler Name / Identifier:**
- **Policy Type:** (e.g., deterministic, bounded-nondeterministic)
- **Tick Authority:** (who advances time)
- **Replay Guarantees:** (yes/no, conditions)
- **Policy Reference:** (document or code location)

> Any determinism or replayability claim in this report depends on this declared policy.

---

## 5. Conformance Checklist Results (Level-3)

Each checklist item from
`00n_conformance_checklist_level3_v2_0.md`
MUST be reported here.

| Checklist ID | Description | Result (PASS/FAIL) | Evidence Reference |
|-------------|------------|--------------------|-------------------|
| L3-A-1 | Scheduler authority declared | | |
| L3-B-2 | Execution state model | | |
| L3-C-1 | Measurement authorization | | |
| L3-D-3 | Determinism claim consistency | | |

(Extend table as needed.)

---

## 6. Test Mapping Evidence

For each checklist item, reference the corresponding test identifier(s)
from `00o_conformance_test_mapping_level3_v2_0.md`.

| Test ID | Description | Result | Evidence Artifact |
|-------|------------|--------|------------------|
| L3-TEST-SCH-01 | Scheduler declaration present | | |
| L3-TEST-DET-02 | Replayability consistency | | |

---

## 7. Determinism & Replayability Claims

The implementation makes the following claims:

- **Deterministic Execution:** YES / NO
- **Replayable Execution:** YES / NO
- **Nondeterministic Operators Declared:** YES / NO

If YES, list operators and justification.

---

## 8. Measurement & Observation Compliance

- **Measurement Events Are Explicit:** YES / NO
- **Observers Are Authorized:** YES / NO
- **Observation Side-Effects Declared:** YES / NO

Evidence references required for each YES.

---

## 9. Deviations and Limitations

List any known deviations, constraints, or partial implementations.

> Deviations MUST NOT contradict frozen semantics.

---

## 10. Out-of-Scope Declarations

The following are explicitly NOT claimed:

- Performance guarantees
- Hardware or quantum backend fidelity
- Physical timing guarantees
- Economic or safety properties

---

## 11. Certification Decision

- **Certification Result:** PASS / FAIL
- **Conditions (if any):**
- **Validity Period:**
- **Re-Certification Required Upon:** (spec change, policy change, etc.)

---

## 12. Sign-Off

- **Auditor / Authority Name:**
- **Signature:**
- **Date:**

---

## Appendix A - Evidence Index (Optional)

List all logs, traces, test outputs, and artifacts referenced above.

---

*End of Report*
