# HPL Delta-S Kernel Runbook

This runbook describes the **Delta-S kernel integration**. It makes irreversible effects lawful only when admissibility evidence and a Delta-S gate are present and signed. It does **not** change spec/freeze documents; it is an operational usage guide for the kernel and bundler.

## What Delta-S Kernel Enforcement Is

- A **kernel rule**: irreversible effects require admissibility + Delta-S evidence
- Deterministic Delta-S computation from prior/posterior artifacts
- Refusal-first enforcement when evidence is missing or the gate fails
- Signed bundle roles for Delta-S artifacts

## Required Artifacts

When `collapse_requires_delta_s=true` in the ExecutionToken, bundles must include:

- `delta_s_report.json`
- `admissibility_certificate.json`
- `collapse_decision.json`

Optional but recommended:

- `measurement_trace.json`

## Minimal Flow (Effect-Level)

1) **MEASURE_CONDITION** ? emits `measurement_trace.json`
2) **COMPUTE_DELTA_S** ? emits `delta_s_report.json`
3) **DELTA_S_GATE** ? emits `collapse_decision.json`
4) Irreversible effect may proceed **only if** gate passes

## Bundle Roles Enforcement

When the token requires Delta-S, bundling enforces roles automatically:

```bash
hpl bundle --out-dir out/bundle \
  --execution-token work/execution_token.json \
  --delta-s-report work/delta_s_report.json \
  --admissibility-certificate work/admissibility_certificate.json \
  --collapse-decision work/collapse_decision.json \
  --sign-bundle --signing-key tests/fixtures/keys/ci_ed25519_test.sk
```

If any required role is missing, bundling returns `ok=false` and the manifest includes `delta_s_v1.ok=false`.

## Refusal Behavior

Refusal is a lawful output. If Delta-S evidence is missing or the gate fails:

- runtime returns `ok=false`
- a `ConstraintWitness` is emitted
- (optional) `DualProposal` can be produced

## Determinism Checklist

- Delta-S computed from **prior/posterior artifacts only**
- No wall-clock timestamps in hashed content
- Canonical JSON ordering in artifacts
- Same inputs ? same Delta-S report and same bundle manifest

## Notes on Domain Packs

Domain packs may emit their own admissibility certificates (e.g., barrier checks).
If a pack uses irreversible effects, it must also emit the Delta-S artifacts above.

This makes **collapse authorization** provable and non-repudiable.
