# IO Lane Runbook (Permissioned, Refusal-First)

This runbook defines how to use the **permissioned IO lane** in HPL without violating
kernel invariants. The IO lane is safe-by-default and requires **three explicit gates**
plus token authorization.

## 1) Enablement Gates (All Required)

**Gate A — CLI intent**
- Use `--enable-io` on commands that can execute IO effects (e.g., `hpl run`, `hpl lifecycle`, demo commands).

**Gate B — Environment intent**
- Set `HPL_IO_ENABLED=1` in the environment.

**Gate C — Adapter readiness**
- Set `HPL_IO_ADAPTER_READY=1` to explicitly allow adapter initialization.

If any gate is missing, the runtime **refuses** with a typed reason (e.g., `IOGuardNotEnabled`, `IOAdapterUnavailable`).

## 2) Token IO Policy (Scheduler Authority)

IO is only lawful when the **ExecutionToken** permits it. Required token fields:

- `io_allowed: true`
- `io_scopes: ["BROKER_CONNECT", "ORDER_SUBMIT", "ORDER_CANCEL", "ORDER_QUERY"]`
- `io_endpoints_allowed: ["broker://demo", ...]` (allowlist)
- `io_budget_calls: <int>`
- `io_requires_reconciliation: true`
- `io_requires_delta_s: true|false` (if IO is treated as irreversible)

If the token lacks permission, runtime refuses with:
- `IOPermissionDenied`
- `EndpointNotAllowed`
- `IOBudgetExceeded`

## 3) Adapter Selection (Mock by Default)

By default, HPL uses a deterministic mock adapter. To select a named adapter stub:

```
HPL_IO_ADAPTER=mt5|deriv|tradingview
HPL_IO_ADAPTER_READY=1
```

Adapters remain **non-live** until a real adapter implementation is installed and explicitly enabled.

## 4) Redaction Gate (Secrets Never Leave the Universe)

Before bundling, HPL runs a **redaction scan**. If secret-like patterns are detected,
**bundling is refused** and a `redaction_report.json` is emitted.

This ensures:
- no secrets in artifacts
- no secrets in bundle manifests
- no secrets in CI uploads

## 5) Reconciliation & Rollback (Reality Must Agree)

IO responses are **not** automatically committed. The kernel runs reconciliation:

- `IO_RECONCILE` emits:
  - `io_outcome.json`
  - `reconciliation_report.json`
- If outcome requires rollback, `IO_ROLLBACK` is the only lawful path.
- Rollback emits `rollback_record.json`.

Ambiguity → **refusal** (`IOAmbiguousResult`).

## 6) Required Bundle Roles (Non-Repudiation)

If IO occurred, bundles must include (role-complete or bundling refuses):

- `io_request_log`
- `io_response_log`
- `io_event_log`
- `io_outcome`
- `reconciliation_report`
- `redaction_report`
- `rollback_record` (required **only if** outcome says rollback)

Bundles are signed and verifiable (manifest signature).

## 7) Verification Steps

**Bundle signing + verification (at bundle creation time)**
```
python tools/bundle_evidence.py \
  --out-dir <bundle_out_dir> \
  --plan <plan.json> \
  --runtime-result <runtime_result.json> \
  --execution-token <execution_token.json> \
  --sign-bundle \
  --signing-key <signing_key.sk> \
  --verify-bundle \
  --pub config/keys/ci_ed25519.pub
```

**Anchor verification (post-bundle)**
```
python tools/verify_anchor.py <bundle_dir> <anchor_manifest.json> --public-key config/keys/ci_ed25519.pub
```

**CI artifacts**
- CI uploads signed bundles and anchors as workflow artifacts (when Actions runs).

## 8) Example Commands (Mock IO)

```powershell
# Enable IO lane locally (mock adapter)
$env:HPL_IO_ENABLED = "1"
$env:HPL_IO_ADAPTER_READY = "1"
$env:HPL_IO_ADAPTER = "mock"

# Run lifecycle with explicit backend + IO gate
hpl lifecycle examples/momentum_trade.hpl --backend classical --out-dir out --enable-io
```

If any gate is missing, the run **refuses** with typed evidence, and no IO artifacts
are bundled.

---

This runbook is a **production safety contract**. It ensures IO is permissioned,
budgeted, reconciled, redacted, and non-repudiable.
