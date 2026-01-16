# SCR — Level-3 Scheduler Model

## Target Version
- Proposed: v2.0 (Level-3 semantics)

## Change Category
- New semantic layer (breaking; requires major version)

## Motivation
Define the authoritative execution scheduler for HPL programs. This establishes
how evolution, ordering, and determinism are governed without prescribing runtime code.

## Scope
IN SCOPE:
- Scheduler responsibilities and invariants
- Determinism vs nondeterminism boundaries
- Ordering guarantees (or lack thereof)

OUT OF SCOPE:
- Runtime implementation
- Performance optimizations
- Hardware bindings

## Definitions
- **Scheduler:** The semantic authority that orders and authorizes program evolution.
- **Tick:** A logical scheduling step (not wall-clock time).

## Proposed Semantics (Draft)
- Programs advance only via scheduler-authorized ticks.
- Scheduler is the sole source of ordering.
- Scheduler decisions are observable only via declared interfaces.

## Invariants
- No implicit execution outside scheduler control.
- Same inputs + same scheduler policy ⇒ same observable outcomes.

## Compatibility & Migration
- Not backward compatible with v1/v1.1 (introduces execution semantics).
- Requires v2.0 freeze.

## Conformance Impact
- New Level-3 conformance checklist required.
- No impact on v1/v1.1 certification.

## Alternatives Considered
- Implicit execution (rejected)
- External host scheduling (rejected)

## Open Questions
- Deterministic replay requirements?
- Pluggable vs fixed scheduler policies?

## Review Record
(To be completed)

---

## REVIEW RECORD (v2.0)

- Checklist: `docs/spec/00j_scr_review_checklist_v1.md`
- Review date: 2026-01-16
- Reviewers: Codex execution (per user instruction)
- Stage results:
  - Stage 1 (Completeness): NEEDS REVISION
  - Stage 2 (Scope & Authority): PASS
  - Stage 3 (Compatibility): PASS
  - Stage 4 (Impact Analysis): NEEDS REVISION
  - Stage 5 (Conformance & Certification): NEEDS REVISION
  - Stage 6 (Migration, if breaking): NEEDS REVISION
  - Stage 7 (Alternatives & Risk): NEEDS REVISION
  - Stage 8 (Decision Readiness): NEEDS REVISION
- Disposition: Defer
- Conditions (if any):
  - Convert to the standard SCR template.
  - Add explicit impact statements (IR schema, operator classes, macro boundary).
  - Add conformance and test-mapping implications.
  - Add migration strategy (required for v2.0).
  - Add risks section (determinism guarantees, replay requirements, policy declaration).
- Reference summary: `docs/audit/scr_v1_1_review_summary.md`
