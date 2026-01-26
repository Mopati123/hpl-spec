# HPL Constitution / Whitepaper v1

## 1) Problem Statement

Most software systems allow implicit execution and unverifiable behavior. This creates:
- unclear authority boundaries,
- unprovable claims about correctness or determinism,
- and audit trails that are optional rather than required.

HPL is designed to remove those failure modes by making authority, evidence, and evolution explicit and mandatory.

## 2) HPL Solution (Authority, Evidence, Anchoring)

HPL defines a governed computational universe where:
- authority is centralized (scheduler),
- evidence is mandatory (audit artifacts),
- and the universe state is anchored cryptographically.

Execution is not a right. It is a phase transition that must be earned.

## 3) Core Laws (v2.4 Summary)

This document summarizes the frozen law. See:
- `docs/spec/00_spec_freeze_declaration_v2_4.md`
- `docs/spec/11_tech_stack_quantum_proof_semantics.md`

Key laws:
- Coupling topology is explicit and registry-gated.
- Evidence chain is mandatory (CouplingEvent, DevChangeEvent, AnchorEvent).
- Epoch anchoring defines a verifiable universe state.
- Backend lanes are declared and non-authoritative.
- Papas is a witness and explainer, never a collapse authority.

## 4) Execution Lifecycle (Canonical)

See `docs/publish/hpl_execution_lifecycle_diagram.md`.

Lifecycle summary:
Axioms -> Intent -> Registry Gate -> ProgramIR -> Papas Observe -> Scheduler Gate
-> Runtime Gate -> Backend Reaction Vessel -> Evidence Emission -> Epoch Anchor -> Feedback

Refusal is success and is always evidenced. If not evidenced, it did not happen.

## 5) Security and Provenance

HPL requires epoch anchors and Ed25519 signatures for provenance:
- Anchor generation: `tools/anchor_epoch.py`
- Signature: `tools/sign_anchor.py`
- Verification: `tools/verify_anchor_signature.py`

The scheduler and runtime gates may refuse authorization if the universe identity
cannot be verified.

## 6) Compliance and Auditability

HPL is designed for auditability:
- explicit coupling edges,
- deterministic artifacts,
- and enforced evidence emission.

This supports compliance, regulated domains, and reproducibility.

## 7) Scope Disclaimers

HPL defines software proof semantics. It is not an experimental physics claim,
not a quantum device model, and not a trading system by itself.

## 8) Roadmap (Implementation)

Near-term execution milestones:
- B3: Backend lowering (BackendIR + deterministic lowerers)
- CLI scaffolding (plan + runtime gate)
- First live instantiation (CI governance or domain-specific pilot)

No new semantics are introduced here; this document is a narrative reference only.
