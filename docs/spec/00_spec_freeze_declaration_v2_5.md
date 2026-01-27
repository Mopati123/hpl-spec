# HPL Spec Freeze Declaration ? v2.5

## Status
**DECLARED ? FROZEN (Normative)**

## Scope of the Freeze
HPL Spec v2.5 incorporates the following accepted SCR:

1. **Quantum Execution Semantics (Q0)**
   - Source: `docs/spec/scr_v2_5_quantum_execution_semantics.md`
   - Effect: introduces a normative mapping between HPL execution phases and a quantum-style
     execution state machine, including refusal/evidence invariants and backend projection law.

No other SCRs are included in this freeze.

## Normative References (v2.5)
- `docs/spec/12_quantum_execution_semantics_v1.md`
- `docs/spec/11_tech_stack_quantum_proof_semantics.md`
- `docs/spec/00_spec_freeze_declaration_v2_4.md`

## Compatibility Statement
- v2.5 is additive at the syntax/IR level.
- v1?v2.4 remain valid and frozen.

## Prohibitions Under This Freeze
No changes MAY be made to Q0, the state machine, backend projection law, or refusal/evidence invariants
without a new SCR and subsequent freeze.

## Declaration
HPL Spec v2.5 is complete, coherent, and review-closed.

**Effective Date:** 2026-01-27
