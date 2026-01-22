# HPL Spec Freeze Declaration - v2.2

## Status

**DECLARED - FROZEN (Normative)**

This document formally declares **HPL Spec v2.2** as frozen and authoritative,
subject to the scope, constraints, and prohibitions defined herein.

---

## Scope of the Freeze

HPL Spec **v2.2** incorporates the following amendment:

1. **Coupling Topology / Sector Isolation / Interface Projectors**
   - Source: `docs/spec/scr_v2_2_coupling_topology.md`
   - Effect: Introduces explicit coupling topology, scheduler-gated coupling,
     and audit requirements for cross-sector interaction.

No other changes are included in this freeze.

---

## Frozen Artifacts

- `axioms_H/docs/coupling_topology_axioms.md`
- `dynamics_H/docs/coupling_operator_semantics.md`
- `runtime_H/docs/scheduler_gated_coupling.md`
- `audit_H/docs/coupling_event_schema.md`
- `audit_H/manifests/coupling_event_manifest.yaml`
- `tools_H/docs/coupling_topology_validation.md`
- `tests_H/docs/coupling_conformance_tests.md`

---

## Compatibility Statement

- **HPL Spec v2.2 is a backward-compatible amendment** to v2.1.
- v2.0 and v2.1 remain valid and frozen.
- v2.2 adds explicit coupling law and audit obligations.

---

## Prohibitions Under This Freeze

While this freeze is in effect:

- No changes may be made to:
  - Scheduler semantics (v2.0/v2.1)
  - Execution semantics (v2.0/v2.1)
  - Measurement or observation rules (v2.0/v2.1)
  - Determinism policy definitions (v2.0/v2.1)

- No reinterpretation of v2.2 semantics is permitted without:
  1. A new Spec Change Request (SCR), and
  2. A subsequent freeze declaration (v2.3 or v3.0).

---

## Declaration

By issuing this document, the maintainers declare that:

- HPL Spec v2.2 is a minimal, governance-compliant amendment.
- Coupling topology is now frozen law.
- The specification is frozen until superseded by a future declared version.

**Effective Date:** 2026-01-16
