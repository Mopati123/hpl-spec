# HPL (Hamiltonian Programming Language)

HPL is a governed execution substrate: a canonical specification plus a reference runtime kernel that executes only under explicit authority, emits deterministic evidence, and supports cryptographic anchoring.

Main SHA: `8a7925547d403521db5e7db6d34600314ad642de`

## What This Software Does

HPL provides a full pipeline from program parsing to verifiable execution evidence:

- Parse DSL source into AST.
- Expand macros into axiomatic forms.
- Validate program semantics.
- Emit deterministic ProgramIR.
- Build scheduler-controlled ExecutionPlans and ExecutionTokens.
- Execute effect steps in a governed runtime engine.
- Enforce refusal-first contracts and budget/capability gates.
- Produce role-complete evidence bundles.
- Sign and verify bundle manifests.
- Anchor bundles (Merkle root + Ed25519 signature) and verify anchors.

## Core Capabilities

- Deterministic pipeline: parser -> macro expander -> validator -> IR.
- Governed scheduler: token issuance with backend, IO, NET, and budget constraints.
- Runtime kernel: effect handlers with pre/post contract checks.
- Refusal-first semantics: typed refusals with witness artifacts.
- Constraint inversion: optional dual proposals from refusal state.
- IO lane (governed): connect/submit/query/cancel/reconcile/rollback/remediation with redaction and role enforcement.
- NET lane (governed): connect/handshake/key exchange/send/recv/close with stabilizer gating and deterministic evidence.
- Operator registry enforcement: plan-time hard fail (gated) plus runtime re-validation.
- Observer layer: Papas witness reports (zero execution/collapse authority).
- Anchoring: deterministic leaf set -> Merkle root -> signature -> verifier.
- Reproducibility contract checks: compare contract-state fields before merkle comparison.

## Architecture Layers

### 1) Spec Law (`*_H` folders)
Top-level sub-Hamiltonians define immutable or normative governance constraints:

- `axioms_H`
- `dynamics_H`
- `emergence_H`
- `backends_H`
- `observers_H`
- `audit_H`
- `runtime_H`
- `tools_H`
- `tests_H`
- `infra_H`
- `data_H`

### 2) Runtime and Tooling (`src/hpl`, `tools`)
Executable reference implementation and governance tooling:

- `src/hpl/`: parser, validator, scheduler, runtime engine, effects, observers, registry enforcement.
- `tools/`: bundling, validation gates, anchoring, verification, and reproducibility scripts.

### 3) Governance and Publication (`docs`)
Normative specs, audit artifacts, runbooks, capability statements, and index.

## Safety and Governance Model

HPL is intentionally not an unconstrained runtime.

- Scheduler sovereignty: authority is minted via ExecutionToken.
- Explicit gates: effects require policy/capability/allowlist/budget satisfaction.
- Refusal-first behavior: invalid state transitions are denied with evidence, not best-effort fallback.
- No ambient IO/NET authority: opt-in flags, env gates, policy gates, and adapter readiness.
- Secret hygiene: redaction gate refuses secret-like leakage before bundling.
- Reconciliation semantics: ambiguity/mismatch routes to refusal and remediation artifacts.

## Deterministic Evidence and Anchoring

HPL evidence is built for verification, not just logs.

- Bundle manifests include role inventories and digests.
- Signatures are Ed25519 over manifest payloads.
- Anchor pipeline creates deterministic leaf hashes and Merkle roots.
- Verifier recomputes leaf/merkle contracts independently.

Reproducibility rule:

A merkle root comparison is valid only when contract-state fields match:

- `git_commit`
- `leaf_rule`
- `leaf_count`
- `bundle_manifest_digest`
- `leaves_digest`

See `docs/audit/reproducibility_contract.md`.

## Domain Packs and Demo Tracks

Implemented demo tracks include:

- `ci-governance`
- `agent-governance`
- `trading-paper`
- `trading-shadow`
- `trading-io-shadow`
- `trading-io-live-min`
- `navier-stokes`
- `net-shadow`

These run under the same kernel contracts and evidence policy.

## Quickstart

### Install

```bash
pip install -e .
```

### Run tests

```bash
python -m pytest -q
```

### Example: anchor demo (PowerShell)

```powershell
./tools/phase1_anchor_demo.ps1 `
  -DemoName navier-stokes `
  -OutDir artifacts/phase1/navier_stokes/run_001 `
  -SigningKey tests/fixtures/keys/ci_ed25519_test.sk `
  -PublicKey tests/fixtures/keys/ci_ed25519_test.pub
```

### Compare anchor contracts

```bash
python tools/compare_anchor_contract.py \
  --machine-a-manifest artifacts/phase1/navier_stokes/run_001/anchor/anchor_manifest.json \
  --machine-a-leaves artifacts/phase1/navier_stokes/run_001/anchor/anchor_leaves.json \
  --machine-b-manifest artifacts/phase1/navier_stokes/run_002/anchor/anchor_manifest.json \
  --machine-b-leaves artifacts/phase1/navier_stokes/run_002/anchor/anchor_leaves.json
```

## Repository Navigation

- Universe index: `docs/UNIVERSE_INDEX.md`
- Full codebase overview: `docs/publish/hpl_codebase_overview.md`
- Capability matrix: `docs/publish/hpl_capability_matrix.md`
- Public capability statement: `docs/publish/hpl_public_capability_statement.md`
- Technical spec summary: `docs/publish/hpl_technical_spec_summary.md`
- Root architecture + full file manifest: `docs/publish/repo_root_architecture.md`

## Current Boundaries

- Live broker/network behavior is gated and policy-bound by design.
- Unconstrained general-purpose execution is out of scope.
- Runtime claims are restricted to implemented tracks and contract state.

## License and Change Discipline

- Specification freezes and SCR process govern semantics.
- Operational/runtime changes are additive unless freeze process says otherwise.
- Evidence-first and refusal-first invariants are non-negotiable.
