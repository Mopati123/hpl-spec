# Constraint Inversion Runbook (v1)

## Purpose

This runbook describes the refusal-driven discovery loop:

refusal -> ConstraintWitness -> DualProposal -> bundle

It is operational guidance only. It introduces no new semantics and does not modify the
spec or freeze artifacts.

---

## Core artifacts

- ConstraintWitness: typed refusal evidence emitted by the runtime gate.
- DualProposal: deterministic alternatives derived from a witness.
- Evidence bundle: role-complete package containing both artifacts.

---

## Lifecycle command (automatic path)

### Refusal-driven lifecycle

```
hpl lifecycle examples/momentum_trade.hpl \
  --backend classical \
  --out-dir ./runs/run_001 \
  --require-epoch --anchor ./epoch.anchor.json --sig ./epoch.anchor.sig \
  --constraint-inversion-v1
```

Expected outcomes:
- ok=false is lawful when refusal occurs.
- The bundle contains constraint_witness + dual_proposal roles.
- Deterministic artifacts (same inputs -> same bundle_id).

---

## Manual inversion (explicit path)

### 1) Invert a witness

```
hpl invert --witness ./constraint_witness.json --out ./dual_proposal.json
```

### 2) Bundle with enforcement

```
python tools/bundle_evidence.py \
  --out-dir ./runs/bundle \
  --program-ir ./program.ir.json \
  --plan ./plan.json \
  --runtime-result ./runtime.json \
  --backend-ir ./backend.ir.json \
  --constraint-witness ./constraint_witness.json \
  --dual-proposal ./dual_proposal.json \
  --constraint-inversion-v1
```

---

## Artifact locations

Typical lifecycle output layout (work dir + bundle):

- work/constraint_witness.json
- work/dual_proposal.json
- bundle_*/bundle_manifest.json

---

## Success vs refusal vs internal error

- Success: ok=true and bundle manifest role checks pass.
- Lawful refusal: ok=false with explicit errors and ConstraintWitness present.
- Internal error: nonzero exit code or missing witness on refusal.

---

## Determinism expectations

- No wall-clock timestamps in hashed artifacts.
- Same inputs produce identical witness_id and dual_proposal_id.
- Bundle manifest bytes remain identical across runs.

---

## Audit expectations

Every refusal must be evidenced and invertible. If it is not witnessed, it did not happen.

