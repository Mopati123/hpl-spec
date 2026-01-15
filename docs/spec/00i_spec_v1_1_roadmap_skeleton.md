# HPL Spec v1.1 Roadmap — Skeleton (Informational)

## Purpose

This document collects **candidate ideas** for a future **HPL Spec v1.1** without
affecting the frozen **v1** specification.

This roadmap is:
- Informational only
- Non-normative
- Non-binding
- Subject to the Spec Change Request (SCR) process

Nothing listed here is approved until accepted via an SCR and frozen in a new version.

---

## Status

- Current spec: **HPL Spec v1 (Frozen)**
- Roadmap target: **v1.1 (Backward-compatible)**
- Authority: Ideas only; no implementation mandate

---

## Candidate Themes (Non-Exhaustive)

### 1. Operator Classification Tightening
- Deterministic rules for assigning `{U, M, Ω, C, I, A}`
- Removal of bootstrap `cls = C` allowance

### 2. Operator Registry Semantics
- Optional semantic annotations (still schema-compliant)
- Formal linkage between registry entries and operator algebra

### 3. Macro System Extensions
- Additional surface macros expanding into axiomatic core
- Improved traceability metadata (still pure and deterministic)

### 4. Diagnostics & Tooling
- Standardized error codes
- Canonical source-map format for macro expansion

### 5. IR Clarifications
- Clarifying notes on optional fields
- Strengthened invariants (no schema breaking changes)

---

## Explicitly Out of Scope for v1.1

- Runtime or scheduler semantics
- Simulator execution models
- Backend execution (including QASM execution)
- Economic or market semantics

---

## Process

1. Propose changes using:
   - `docs/spec/00h_spec_change_request_template_v1.md`
2. Classify as backward-compatible (v1.1) or breaking (v2.0).
3. Review, accept, and freeze via a new Spec Freeze Declaration.

---

## Notes

- This roadmap exists to **capture intent without breaking the freeze**.
- Implementations MUST ignore this document unless a change is formally accepted.
