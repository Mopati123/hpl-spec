# SCR v2.3 — Epoch Anchoring + Evolve/Collapse/Anchor Primitives

## Status
Proposed

## Version Target
v2.3

## Summary
Introduce epoch anchoring as a normative requirement and freeze three primitives:
`evolve`, `collapse`, and `anchor`. Define ETO + lambda (λ) effect obligations and
registry-as-linker legality for cross-sector edges.

## Scope (Additive)
- Epoch anchoring semantics and verification obligations
- Evolve/collapse/anchor primitives
- ETO + λ effect obligations
- Registry-as-linker legality and refusal of undeclared edges

## Non-Changes
- No grammar changes
- No IR schema changes
- No modification to frozen v2.2 artifacts

## Acceptance Criteria
- Spec docs define anchor, evolve, collapse primitives
- Effect obligations (ETO + λ) are formalized
- Registry-as-linker semantics are specified
- _H mappings exist for axioms, dynamics, runtime, audit, tools, tests
- v2.3 freeze declaration is issued

## Rationale
Anchoring creates a deterministic boundary for evidence and replay. Primitive
definitions provide formal semantics without requiring runtime implementation.
