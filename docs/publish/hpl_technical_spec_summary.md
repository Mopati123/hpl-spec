# HPL Technical Spec Summary (Public)

Main SHA: ccac2e45490612d8f4ef69edaf4104b0a90ff8f4  
Date: 2026-02-10

This summary is tied to the current main commit and lists only implemented behavior.

---

## 1) Core Pipeline

parse → expand → validate → ProgramIR → ExecutionPlan → Runtime (ESK) → Bundle → Signature → Anchor

- ProgramIR is deterministic.
- Scheduler issues ExecutionPlan + ExecutionToken.
- Runtime executes typed effects and emits a deterministic transcript.
- Refusals yield ConstraintWitness evidence.

---

## 2) ExecutionToken Policy

Token fields are deterministic and normalized:
- allowed_backends
- preferred_backend
- budget_steps
- determinism_mode
- io_policy
- delta_s_policy
- delta_s_budget
- measurement_modes_allowed
- collapse_requires_delta_s

### io_policy (normalized)
- io_allowed (bool)
- io_scopes (list)
- io_endpoints_allowed (list)
- io_budget_calls (optional int)
- io_requires_reconciliation (bool)
- io_requires_delta_s (bool)
- io_mode (dry_run | live)
- io_timeout_ms (int)
- io_nonce_policy (string)
- io_redaction_policy_id (string)

---

## 3) Runtime Semantics (ESK)

Typed effects are executed through handlers with explicit contracts.
Runtime guarantees:
- refusal-first outcomes,
- deterministic transcript,
- step budget enforcement,
- IO budget enforcement,
- Delta-S budget enforcement (when configured).

---

## 4) Delta-S Gate (Measurement Closure)

Irreversible steps can require:
- admissibility certificate,
- delta_s_report,
- collapse_decision.

Missing evidence yields refusal. Evidence is role-complete in bundles.

---

## 5) IO Lane (Governed Sub-Universe)

Three-gate enablement:
- CLI: --enable-io
- ENV: HPL_IO_ENABLED=1
- Adapter readiness: HPL_IO_ADAPTER_READY=1

Handler safeguards:
- token scope check
- endpoint allowlist
- io_budget_calls
- redaction refusal gate
- reconciliation + rollback
- remediation_plan on rollback/ambiguity

Adapters:
- Mock (default)
- MT5 (guarded)
- Deriv (guarded)
- TradingView (guarded)

---

## 6) Evidence Bundling

Bundles are role-complete and signed:
- bundle_manifest.json
- role-based artifacts (token, IO, Delta-S, witness, etc.)
- signature + verification enforced
- refusal on missing required roles

---

## 7) Phase-1 Anchoring

Tools:
- tools/anchor_generator.py
- tools/verify_anchor.py

Outputs:
- anchor_manifest.json
- anchor_leaves.json
- anchor_manifest.sig

Root is deterministic for identical inputs and verified independently.

---

## 8) Operator Registry Enforcement

Registry loader:
- enforces META ↔ registry bijection
- plan-time hard fail when enforcement enabled
- runtime re-validation as defense in depth

---

## 9) Observer/Witness (Papas)

Papas emits deterministic observer reports on refusal:
- summary + refusal reasons
- optional DualProposal (when enabled)
- zero collapse authority

---

## 10) Current Domain Packs

- CI governance demo
- Agent governance demo
- Trading paper-mode
- Trading shadow-mode
- Trading IO shadow / live-min demos
- Navier–Stokes demo

---

## 11) Public Claims (Scope)

Supported:
- governed execution with refusal-first semantics
- deterministic evidence bundles with signatures
- IO lane with reconciliation/rollback and redaction guard
- Phase-1 anchoring and independent verification

Not claimed:
- live trading by default
- unbounded external IO
- performance guarantees under adversarial conditions

---

## 12) Reproducibility Targets

Phase-1 proof requires:
- identical merkle_root across machines for identical inputs
- verify_anchor.py returns ok: true

If bundle_id diverges due to path normalization, merkle_root is the canonical truth.
