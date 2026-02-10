# HPL Public Capability Statement

Version: Phase-1 (public)  
Main SHA: ccac2e45490612d8f4ef69edaf4104b0a90ff8f4  
Date: 2026-02-10

## Executive Summary
Hamiltonian Programming Language (HPL) is a governance-native execution platform.
Execution is treated as a permissioned, evidence-producing state transition, not a default behavior.
Every run is deterministic, auditable, and cryptographically verifiable.

HPL provides:
- tokenized execution authority (no ambient execution),
- refusal-first outcomes with evidence,
- deterministic evidence bundles with signatures,
- a governed IO lane with reconcile/rollback,
- Phase-1 anchoring (Merkle root + signature + verification),
- formal observer/witness outputs (Papas) with zero collapse authority.

This is a production-grade execution sovereignty substrate, not a best-effort runtime.

---

## What HPL Guarantees Today

### 1) Execution Sovereignty
- Execution only occurs through scheduler-minted tokens.
- Runtime refuses any step not authorized by token policy or contracts.
- Refusal is a lawful output with evidence (ConstraintWitness).

### 2) Determinism
- Canonical JSON serialization for hashed artifacts.
- Stable identifiers (bundle_id, witness_id, delta_s IDs).
- Evidence bundling is deterministic and verifiable.

### 3) Evidence & Non-Repudiation
- Evidence bundles are role-complete and signed (Ed25519).
- Signature verification is required by policy in CI lanes.
- Redaction gate prevents secrets from entering bundles.

### 4) Governed IO Lane
- IO requires a three-gate turn:
  - CLI opt-in (--enable-io),
  - environment opt-in (HPL_IO_ENABLED=1),
  - adapter readiness (HPL_IO_ADAPTER_READY=1).
- IO is token-scoped (scopes, endpoint allowlist, call budgets).
- IO outcomes are reconciled and rollback is explicit.
- Bundles refuse if IO roles are incomplete.

### 5) Measurement / Delta-S Gate
- Irreversible steps can be policy-gated by admissibility + Delta-S evidence.
- Delta-S artifacts are evidence roles, signed and verifiable.

### 6) Phase-1 Anchoring
- Evidence bundles can be converted into a Merkle root + signed anchor.
- Independent verification is supported by tooling.

---

## What HPL Does Not Claim Yet

- Live trading by default.
- Unbounded external IO.
- Performance guarantees under adversarial workloads.
- Broker access without explicit operator and token authority.

These are explicitly gated and require opt-in permissions and policy.

---

## What HPL Can Do Now (Practical Capabilities)

### Regulated Automation
Produce verifiable execution proofs that include:
- token authority,
- admissibility decisions,
- refusal reasons,
- reconcile/rollback evidence,
- signed bundle manifest.

### Trading (Governed Ladder)
Supported ladder:
- IO shadow (connect/query only),
- IO live-min (tight caps + mandatory reconciliation),
- expansion only after reproducibility proof.

### Agent Governance

Agents can propose indefinitely but cannot execute without:
- token authority,
- admissibility/Delta-S (if required),
- explicit evidence roles.

### Scientific / PDE / CFD
Navier-Stokes pack demonstrates lawful evolution under:
- projection + barrier checks,
- refusal-first gating,
- deterministic evidence outputs.

---

## Independent Verification
Phase-1 anchor workflow enables:
- reproducible Merkle roots,
- signed anchor manifests,
- independent verification on any machine.

This provides external, cryptographically verifiable evidence of execution.

---

## Governance Roles (Papas Observer)
Papas is a first-class observer with zero collapse authority:
- emits deterministic observer reports,
- produces DualProposal when enabled,
- cannot mint tokens or authorize IO.

Papas serves as an audit witness and lawful explanation generator, not an executor.

---

## Production Status (Public Truth)
Main SHA: ccac2e45490612d8f4ef69edaf4104b0a90ff8f4

Public main includes:
- full P4 IO lane (C1–C3 tightening),
- Phase-1 anchor generator + verifier,
- operator registry enforcement,
- Papas observer reports.

---

## Next Proof Milestones
Recommended order:
1) Multi-machine reproducibility proof (same merkle_root across machines).
2) Anchor IO shadow run (IO lane + anchoring combined).
3) Publish Phase-1 proof bundle as an external certificate.

---

## Contact
For verification or audit requests, provide the bundle + anchor manifest and the verification tools in this repo.
