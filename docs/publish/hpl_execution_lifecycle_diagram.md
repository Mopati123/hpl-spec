# HPL Execution Lifecycle (Canonical Diagram)

This is the single canonical lifecycle description. All outward-facing artifacts must conform to this flow.

## ASCII Flow (Canonical)

[Axioms/Law (_H)]
    |
    v
[Intent Source]
    |
    v
[Existence Projector]
  (Registry + Spec Gate)
    |
    v
[IR State Vector]
  (ProgramIR)
    |
    v
[Papas Observe]
  (witness only)
    |
    v
[Scheduler Gate]
  (epoch+sig verify, lambda grant/refuse)
   |  \
   |   \__ Refusal is success (evidence emitted)
   |
   v
[Runtime Gate]
  (contract enforcement)
   |  \
   |   \__ Refusal is success (evidence emitted)
   |
   v
[Backend Reaction Vessel]
  (lowering/execution target)
    |
    v
[Evidence Emission]
  (CouplingEvent / DevChangeEvent / AnchorEvent)
    |
    v
[Epoch Anchor]
  (anchor + sign + verify)
    |
    v
[Feedback]
  (auditable universe state)

Rule: if not evidenced, did not happen.

## Mermaid Flow (Canonical)

```mermaid
flowchart TD
  A[Axioms / Law (_H)] --> B[Intent Source]
  B --> C[Existence Projector<br/>Registry + Spec Gate]
  C --> D[IR State Vector<br/>ProgramIR]
  D --> E[Papas Observe<br/>Witness Only]
  E --> F[Scheduler Gate<br/>Epoch+Sig Verify<br/>Lambda Grant/Refuse]
  F -->|refuse| R1[Refusal = Success<br/>Evidence Emitted]
  F --> G[Runtime Gate<br/>Contract Enforcement]
  G -->|refuse| R2[Refusal = Success<br/>Evidence Emitted]
  G --> H[Backend Reaction Vessel<br/>Lowering / Execution Target]
  H --> I[Evidence Emission<br/>CouplingEvent / DevChangeEvent / AnchorEvent]
  I --> J[Epoch Anchor<br/>Anchor + Sign + Verify]
  J --> K[Feedback<br/>Auditable Universe State]

  classDef gate fill:#f7f7f7,stroke:#333,stroke-width:1px;
  class F,G gate;
```

## Repo Module Mapping (Canonical)

- Axioms/Law: `*_H/` (e.g., `axioms_H`, `dynamics_H`, `runtime_H`, `audit_H`, `tools_H`, `tests_H`)
- Intent Source: `examples/`, surface DSL inputs
- Existence Projector: registries + validators
  - `tools/validate_operator_registries.py`
  - `tools/validate_observer_registry.py`
  - `tools/validate_coupling_topology.py`
- IR State Vector: parser/macro/validator/IR emitter
  - `src/hpl/emergence/dsl/parser.py`
  - `src/hpl/emergence/macros/expander.py`
  - `src/hpl/axioms/validator.py`
  - `src/hpl/dynamics/ir_emitter.py`
- Papas Observe: witness emission
  - `src/hpl/trace.py` (witness records)
- Scheduler Gate: `src/hpl/scheduler.py`
- Runtime Gate: `src/hpl/runtime/context.py`, `src/hpl/runtime/contracts.py`, `src/hpl/runtime/engine.py`
- Evidence Emission:
  - CouplingEvent: `src/hpl/audit/coupling_event.py`
  - DevChangeEvent: `src/hpl/audit/dev_change_event.py`
- Epoch Anchor:
  - `tools/anchor_epoch.py`
  - `tools/sign_anchor.py`
  - `tools/verify_anchor_signature.py`
  - `tools/verify_epoch.py`

Status note: lowering/execution backends are planned under B3, not yet implemented.
