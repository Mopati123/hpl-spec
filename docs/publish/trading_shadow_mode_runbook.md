# HPL Trading Shadow-Mode Runbook

This runbook describes the **shadow-mode trading** demo pack. It is **paper-only** and does **not** touch broker APIs or real accounts. The goal is to exercise latency, partial fills, slippage, regime shifts, and deterministic reconciliation under the kernel while preserving refusal-first behavior and evidence signing.

## What Shadow-Mode Is

Shadow-mode is a **deterministic realism bridge**:

- Simulates latency and staleness windows
- Models partial fills and slippage
- Applies regime-shift adjustments
- Refuses when uncertainty or staleness exceed policy
- Reconciles signal, fill, risk, ledger, and report state before completion
- Emits deterministic evidence and a signed bundle

## What Shadow-Mode Is Not

- No broker or network IO
- No real accounts or credentials
- No stochastic randomness (all effects are seeded and deterministic)

## Required Inputs

- **Market fixture**: `tests/fixtures/trading/price_series_simple.json`
- **Policy**: `tests/fixtures/trading/shadow_policy_safe.json`
- **Shadow model**: `tests/fixtures/trading/shadow_model.json`
- **Signing key**: test key or CI key for bundle signing

## Run the Demo

```bash
hpl demo trading-shadow \
  --out-dir out/shadow \
  --market-fixture tests/fixtures/trading/price_series_simple.json \
  --policy tests/fixtures/trading/shadow_policy_safe.json \
  --shadow-model tests/fixtures/trading/shadow_model.json \
  --signing-key tests/fixtures/keys/ci_ed25519_test.sk
```

### Expected Outputs

The output directory will include:

- `trade_report.json` / `trade_report.md`
- `shadow_model.json` + `shadow_seed.json`
- `shadow_execution_log.json`
- `shadow_trade_ledger.json`
- `shadow_reconciliation.json`
- Signed bundle artifacts:
  - `bundle_manifest.json`
  - `bundle_manifest.sig`

### Reconciliation Stage

The scheduler appends `SIM_RECONCILE_TRADE` after `EMIT_TRADE_REPORT`. The reconciliation effect is simulation-native: it does not use broker or network IO and it does not gain execution authority outside the scheduler-selected plan.

`shadow_reconciliation.json` records:

- the reconciliation schema version
- the ArchitectureIR reconciliation operators
- deterministic comparisons across signal, fill, risk, ledger, and report state
- SHA-256 digests of the source artifact bytes
- refusal reasons when canonical bytes or derived state do not reconcile

A successful run requires the witness to report `ok=true`. Semantic mutation of derived trade state or non-canonical rewriting of a source artifact causes reconciliation refusal rather than silent completion.

## Verify Bundle Signature

```bash
hpl bundle --out-dir out/shadow \
  --verify-bundle \
  --pub tests/fixtures/keys/ci_ed25519_test.pub
```

## Refusal Path (Safe Failure)

Use the forbidden policy to trigger refusal (staleness/uncertainty or partial-fill failure):

```bash
hpl demo trading-shadow \
  --out-dir out/shadow_refusal \
  --market-fixture tests/fixtures/trading/price_series_simple.json \
  --policy tests/fixtures/trading/shadow_policy_forbidden.json \
  --shadow-model tests/fixtures/trading/shadow_model.json \
  --signing-key tests/fixtures/keys/ci_ed25519_test.sk \
  --constraint-inversion-v1
```

Expected refusal outcomes:

- `ok=false` summary
- `constraint_witness.json` + `dual_proposal.json`
- Signed bundle with refusal evidence

## Determinism Checklist

Shadow-mode is **deterministic** when:

- The same fixtures + policy + model are used
- The same token/budget is applied
- The same seed is recorded in `shadow_seed.json`

Two runs with identical inputs must yield identical bundle IDs, report bytes, and reconciliation witness bytes.

## ECMO Integration (Optional)

Shadow-mode can be selected by ECMO boundary conditions in future tracks.
When ECMO selects the shadow track, the lifecycle will:

- emit `measurement_selection.json`
- run the shadow-mode steps
- reconcile the resulting shadow state
- bundle and sign evidence

This preserves “external constraints force measurement” without live IO.
