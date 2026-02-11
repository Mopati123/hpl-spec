# NET Lane Runbook

## Purpose
The NET lane provides governed, refusal-first communication effects under HPL. It is a sibling of the IO lane, but scoped to message-oriented network actions. No network effect occurs without explicit enablement, token authority, and evidence capture.

## Enablement Gates
All NET effects require the following gates to be satisfied:

- CLI flag: `--enable-net`
- Environment gate: `HPL_NET_ENABLED=1`
- Adapter readiness gate for non-mock adapters: `HPL_NET_ADAPTER_READY=1`
- Token authority: `ExecutionToken.net_policy` must allow the requested capability

If any gate is missing, the runtime refuses with a typed refusal (for example, `NetGuardNotEnabled` or `NetPermissionDenied`).

## Token Policy (net_policy)
The `ExecutionToken.net_policy` block defines the NET authority surface:

- `net_mode`: `dry_run` or `live`
- `net_caps`: allowed capabilities (for example `NET_CONNECT`, `NET_SEND`)
- `net_budget_calls`: per-run call budget
- `net_endpoints_allowlist`: explicit endpoints that may be contacted
- `net_timeout_ms`: timeout policy (deterministic bucket)
- `net_nonce_policy`: deterministic nonce derivation policy
- `net_redaction_policy_id`: redaction policy identifier
- `net_crypto_policy_id`: crypto policy identifier (for example `QKX1`)

## Effects
NET actions are expressed as effect steps and run through handlers:

- `NET_CONNECT`
- `NET_HANDSHAKE`
- `NET_KEY_EXCHANGE`
- `NET_SEND`
- `NET_RECV`
- `NET_CLOSE`

Each effect is request/response logged with deterministic identifiers and redaction-safe payloads.

## Evidence and Bundle Roles
If any NET effects occur, the bundle must contain:

- `net_request_log`
- `net_response_log`
- `net_event_log`
- `net_session_manifest`
- `redaction_report`

Bundling refuses if required NET roles are missing.

## Refusal Taxonomy
Typical NET refusals include:

- `NetGuardNotEnabled`
- `NetPermissionDenied`
- `NetEndpointNotAllowed`
- `NetBudgetExceeded`
- `NetTimeout`

Refusals emit witnesses and are eligible for dual proposals when enabled.

## Demo Track: net-shadow
The demo track `net_shadow` executes a deterministic NET flow using the mock adapter. It is safe for local reproducibility tests and produces role-complete evidence bundles.

Example:

```
hpl demo net-shadow \
  --out-dir artifacts/phase1/net_shadow/run_001 \
  --endpoint net://demo \
  --message "hello" \
  --signing-key tests/fixtures/keys/ci_ed25519_test.sk \
  --pub tests/fixtures/keys/ci_ed25519_test.pub \
  --enable-net
```

## Anchoring
After bundling, the anchor generator can produce a Merkle root and signature for the bundle. See `docs/publish/phase1_anchor_runbook.md` for the full procedure.
