# HPL Capability Matrix

Validation baseline SHA: d878e95c4b4adb64a6f080eb8b8fa4dbbd655aaf  
Current tip command: `git rev-parse HEAD`  
Date: 2026-02-16

Status legend:
- Implemented
- Implemented (governed)
- Implemented (gated)
- Demo-only
- Spec-only
- Out of scope

## Core
- Spec grammar: Implemented
- Macro boundary: Implemented
- IR pipeline: Implemented
- Scheduler: Implemented (governed)
- Runtime engine: Implemented (governed)
- General unconstrained runtime: Out of scope

## Governance
- ExecutionToken authority: Implemented
- Refusal-first semantics: Implemented
- Delta-S gate (measurement closure): Implemented (gated)
- Operator registry enforcement: Implemented (gated)
- Papas observer reports: Implemented (governed)

## IO Lane
- IO three-gate enablement: Implemented
- Tokenized IO scopes/allowlist/budgets: Implemented
- Deterministic IOTimeout refusal: Implemented
- Redaction refusal gate: Implemented
- Reconcile/rollback semantics: Implemented
- Remediation plan emission + bundle enforcement: Implemented
- Guarded MT5 adapter: Implemented (gated)
- Guarded Deriv adapter: Implemented (gated)
- Live IO by default: Out of scope

## NET Lane
- NET three-gate enablement: Implemented
- Tokenized NET caps/allowlist/budgets: Implemented
- Deterministic NetTimeout refusal: Implemented
- NET stabilizer gate (deferred collapse): Implemented (gated)
- NET adapter contract + mock adapter: Implemented (gated)
- Live NET by default: Out of scope

## Evidence and Anchoring
- Role-complete bundles: Implemented
- Bundle signing + verification: Implemented
- Phase-1 anchor generator + verifier: Implemented
- Multi-machine reproducibility proof process: Implemented (demo workflow)

## Domain Packs (Demo)
- CI governance demo: Demo-only
- Agent governance demo: Demo-only
- Trading paper-mode: Demo-only
- Trading shadow-mode: Demo-only
- Trading IO shadow/live-min tracks: Demo-only (gated)
- Navier-Stokes pack: Demo-only
- NET shadow pack: Demo-only (gated)