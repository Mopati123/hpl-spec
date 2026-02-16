# HPL Technical Spec Summary (Public)

Validation baseline SHA: d878e95c4b4adb64a6f080eb8b8fa4dbbd655aaf  
Current tip command: `git rev-parse HEAD`  
Date: 2026-02-16

This summary reflects implemented behavior at the validation baseline SHA.

---

## 1) Core Pipeline

parse -> expand -> validate -> ProgramIR -> ExecutionPlan -> Runtime (ESK) -> Bundle -> Signature -> Anchor

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
- net_policy
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

### net_policy (normalized)
- net_mode (dry_run | live)
- net_caps (list)
- net_endpoints_allowlist (list)
- net_budget_calls (optional int)
- net_timeout_ms (int)
- net_nonce_policy (string)
- net_redaction_policy_id (string)
- net_crypto_policy_id (string)

---

## 3) Runtime Semantics (ESK)

Typed effects are executed through handlers with explicit contracts.
Runtime guarantees:
- refusal-first outcomes,
- deterministic transcript,
- step budget enforcement,
- IO budget enforcement,
- NET budget enforcement,
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

## 6) NET Lane (Governed Sub-Universe)

Three-gate enablement:
- CLI: --enable-net
- ENV: HPL_NET_ENABLED=1
- Adapter readiness: HPL_NET_ADAPTER_READY=1

Handler safeguards:
- token cap check
- endpoint allowlist
- net_budget_calls
- stabilizer gate
- deterministic timeout/refusal semantics
- redaction-safe artifacts

Adapters:
- Mock (default)
- Local loopback (guarded)
- WebSocket (guarded)

---

## 7) Evidence Bundling

Bundles are role-complete and signed:
- bundle_manifest.json
- role-based artifacts (token, IO, NET, Delta-S, witness, etc.)
- signature + verification enforced
- refusal on missing required roles

---

## 8) Phase-1 Anchoring

Tools:
- tools/anchor_generator.py
- tools/verify_anchor.py

Outputs:
- anchor_manifest.json
- anchor_leaves.json
- anchor_manifest.sig

Root is deterministic for identical inputs and verified independently.

---

## 9) Operator Registry Enforcement

Registry loader:
- enforces META <-> registry bijection
- plan-time hard fail when enforcement enabled
- runtime re-validation as defense in depth

---

## 10) Observer/Witness (Papas)

Papas emits deterministic observer reports on refusal:
- summary + refusal reasons
- optional DualProposal (when enabled)
- zero collapse authority

---

## 11) Current Domain Packs

- CI governance demo
- Agent governance demo
- Trading paper-mode
- Trading shadow-mode
- Trading IO shadow / live-min demos
- Navier-Stokes demo
- NET shadow demo

---

## 12) Public Claims (Scope)

Supported:
- governed execution with refusal-first semantics
- deterministic evidence bundles with signatures
- IO lane with reconciliation/rollback and redaction guard
- NET lane with stabilizer gating and deterministic evidence
- Phase-1 anchoring and independent verification

Not claimed:
- live trading by default
- unbounded external IO/NET
- performance guarantees under adversarial conditions

---

## 13) Reproducibility Targets

Phase-1 proof requires:
- identical merkle_root across machines for identical inputs
- verify_anchor.py returns ok: true

Contract-state fields must match before merkle comparison:
- git_commit
- leaf_rule
- leaf_count
- bundle_manifest_digest
- leaves_digest