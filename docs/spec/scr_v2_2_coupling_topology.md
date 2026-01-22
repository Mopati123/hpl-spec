# SCR v2.2 - Coupling Topology / Sector Isolation / Interface Projectors

## Status
Proposed

## Version Target
v2.2

## Motivation
HPL currently allows implicit coupling via import reachability and undeclared
execution paths. This SCR introduces an explicit coupling topology so that all
cross-sector interaction is declared, scheduler-gated, auditable, and replayable.

## Scope (Additive)
This amendment introduces new semantic law in the following areas:
- Sector Isolation
- Interface Projectors
- Declared Coupling Registry
- Coupling Operator Semantics
- Scheduler-gated coupling
- Coupling audit event schema
- Validator and conformance rules

## Non-Changes
- No grammar changes
- No IR schema changes
- No modification of frozen v2.0 / v2.1 semantics
- No breaking change to existing Level-1 pipeline or Level-2 tooling

## Acceptance Criteria
- New axioms exist for sector isolation and projector-only coupling
- Coupling semantics (Couple / optional Commute) are specified
- Runtime rules define scheduler-gated coupling and deterministic boot
- Audit schema defines CouplingEvent with replay guarantees
- Validator rules reject undeclared or illegal couplings
- Conformance test intent is specified
- v2.2 freeze declaration is issued

## Rationale
This amendment converts integration discipline into enforceable law.

## REVIEW RECORD (v2.2)

- Checklist: `docs/spec/00j_scr_review_checklist_v1.md`
- Review date:
- Reviewers:
- Stage results:
  - Stage 1 (Completeness):
  - Stage 2 (Scope & Authority):
  - Stage 3 (Compatibility):
  - Stage 4 (Impact Analysis):
  - Stage 5 (Conformance & Certification):
  - Stage 6 (Migration, if breaking):
  - Stage 7 (Alternatives & Risk):
  - Stage 8 (Decision Readiness):
- Disposition:
- Conditions (if any):
- Reference summary:
