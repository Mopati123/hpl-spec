# SCR: Papas Observer Identity (v2.1)

## Status
Ready

## Target Release
v2.1

## Summary
Introduce `papas` as a first-class internal observer identity with:
- no collapse authority
- no semantic authority
- permitted outputs limited to trace reasoning, mentorship explanations
  (non-normative), and audit witness attestations

Extend the audit trace schema to support witness records.

## Motivation
A formally bounded internal observer agent is needed to generate reasoning
traces and provide audit witness attestations without any execution or collapse
authority.

## Normative Changes
1. observers_H: add observer identity `papas` and its permission set.
2. audit_H: add witness record schema and allow `papas` as a witness signer.

## Non-Changes (Explicit)
- No changes to scheduler authority semantics.
- No changes to grammar, macro semantics, IR semantics, or backend lowering.

## Compatibility / Migration
v2.0 programs remain valid. Evidence output may include an additional witness
record when enabled.

## Security / Safety
Papas is explicitly prohibited from:
- authorizing collapse
- inventing semantics
- overriding invariants

## Acceptance Criteria
- Observer registry validation passes.
- Tests prove `papas` has no collapse authority.
- Trace schema validates witness records.

## Sign-off
- Spec maintainer:
- Tooling maintainer:
- Audit maintainer:

## REVIEW RECORD (v2.1)

- Checklist: `docs/spec/00j_scr_review_checklist_v1.md`
- Review date: 2026-01-16
- Reviewers: Codex execution (per user instruction)
- Stage results:
  - Stage 1 (Completeness): PASS
  - Stage 2 (Scope & Authority): PASS
  - Stage 3 (Compatibility): PASS
  - Stage 4 (Impact Analysis): PASS
  - Stage 5 (Conformance & Certification): PASS
  - Stage 6 (Migration, if breaking): N/A
  - Stage 7 (Alternatives & Risk): PASS
  - Stage 8 (Decision Readiness): PASS
- Disposition: Ready
- Conditions (if any): None
- Reference summary: None
