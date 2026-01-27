# Quantum Execution Semantics v1 (Normative)

## Q0 Axiom
Execution exists only as a lawful phase transition. Any transition not authorized and evidenced is invalid.

## QM ? HPL Isomorphism Table
| Quantum Concept | HPL Construct |
| --- | --- |
| State | ProgramIR (|??) |
| Preparation | Parser ? Expander ? Validator |
| Measurement Authorization | Scheduler Gate (ExecutionPlan) |
| Projection | Backend Lowering (BackendIR/QASM) |
| Measurement | Runtime Gate (RuntimeResult) |
| Collapse | Scheduler-authorized transition |
| Evidence | CouplingEvent / DevChangeEvent / AnchorEvent |

## Execution State Machine (Normative)
PREPARE ? WAIT ? AUTHORIZE/REFUSE ? PROJECT ? MEASURE ? COMMIT ? EVIDENCE

Rules:
- REFUSE is a lawful terminal state and MUST emit evidence.
- COMMIT is valid only if PROJECT and MEASURE are authorized.
- If not evidenced, it did not happen.

## Backend Projection Law
All projections must be declared and deterministic.
- CPU projection: ProgramIR ? BackendIR (classical)
- QASM projection: BackendIR ? QASM
No backend may invent semantics.

## Refusal and Evidence Invariants
- Refusal is success when the universe is not authorized.
- Every phase transition MUST emit evidence or a refusal record.

## Governance Note
This module is an additive semantic mapping. It does not change the IR schema or grammar.
