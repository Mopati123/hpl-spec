# Trading Paper-Mode Runbook

This runbook describes the deterministic, refusal-first trading paper-mode demo. It does not use broker APIs or network IO.

## Scope

- Paper-mode only (local fixtures, no external IO).
- Deterministic outputs under the Execution Semantics Kernel (ESK).
- Signed bundles optional locally; CI signs bundles by default.

## Inputs

- Market fixture: `tests/fixtures/trading/price_series_simple.json`
- Policy (safe): `tests/fixtures/trading/policy_safe.json`
- Policy (refusal): `tests/fixtures/trading/policy_forbidden.json`

## Command (safe run)

```
hpl demo trading-paper --out-dir .\out_trading \
  --market-fixture .\tests\fixtures\trading\price_series_simple.json \
  --policy .\tests\fixtures\trading\policy_safe.json \
  --signing-key .\tests\fixtures\keys\ci_ed25519_test.sk
```

Expected artifacts:
- `trade_report.json` and `trade_report.md`
- `bundle_manifest.json` and `bundle_manifest.sig`
- `runtime.json` with deterministic transcript

## Command (refusal path)

```
hpl demo trading-paper --out-dir .\out_trading_refuse \
  --market-fixture .\tests\fixtures\trading\price_series_simple.json \
  --policy .\tests\fixtures\trading\policy_forbidden.json \
  --signing-key .\tests\fixtures\keys\ci_ed25519_test.sk \
  --constraint-inversion-v1
```

Expected artifacts:
- `constraint_witness.json`
- `dual_proposal.json`
- Refusal recorded as `ok=false` in summary output

## Verification

Verify the bundle signature:

```
python -m hpl.cli bundle --out-dir .\out_trading --verify-bundle
```

## Determinism

Running the same command twice with the same fixture and policy must produce identical:
- `trade_report.json`
- `bundle_manifest.json`
- `bundle_manifest.sig`

## Notes

- This runbook validates refusal-first behavior and budget enforcement under paper-mode.
- It does not include broker IO or live order submission.