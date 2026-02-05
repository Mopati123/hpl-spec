# HPL Navier–Stokes Runbook

This runbook describes the **Navier–Stokes (NS) demo pack**. It is **non-IO** and exists as a deterministic, refusal-first physics lab for the kernel. It does **not** claim physical regularity or solve the Millennium problem; it demonstrates lawful fixed-point evolution under admissibility gates.

## What the NS Pack Is

- A deterministic effect sequence for a mild fixed-point evolution
- A stress test of projection, gating, and refusal-first behavior
- Fully auditable and bundle-signed artifacts

## What the NS Pack Is Not

- No external IO
- No real-world PDE claims
- No stochastic randomness

## Required Inputs

- **State fixture**: `tests/fixtures/pde/ns_state_initial.json`
- **Policy**: `tests/fixtures/pde/ns_policy_safe.json`
- **Signing key**: test key or CI key for bundle signing

## Run the Demo

```bash
hpl demo navier-stokes \
  --out-dir out/ns \
  --state tests/fixtures/pde/ns_state_initial.json \
  --policy tests/fixtures/pde/ns_policy_safe.json \
  --signing-key tests/fixtures/keys/ci_ed25519_test.sk
```

## Expected Outputs

The output directory will include:

- `ns_state_final.json`
- `ns_observables.json`
- `ns_pressure.json`
- `ns_gate_certificate.json`
- Signed bundle artifacts:
  - `bundle_manifest.json`
  - `bundle_manifest.sig`

## Verify Bundle Signature

```bash
hpl bundle --out-dir out/ns \
  --verify-bundle \
  --pub tests/fixtures/keys/ci_ed25519_test.pub
```

## Refusal Path (Safe Failure)

Use the forbidden policy to trigger refusal (energy/divergence/CFL gates):

```bash
hpl demo navier-stokes \
  --out-dir out/ns_refusal \
  --state tests/fixtures/pde/ns_state_initial.json \
  --policy tests/fixtures/pde/ns_policy_forbidden.json \
  --signing-key tests/fixtures/keys/ci_ed25519_test.sk \
  --constraint-inversion-v1
```

Expected refusal outcomes:

- `ok=false` summary
- `constraint_witness.json` + `dual_proposal.json`
- Signed bundle with refusal evidence

## Determinism Checklist

NS demo is **deterministic** when:

- Same state + policy inputs are used
- Same token/budget is applied
- No wall-clock values are injected

Two runs with identical inputs must yield identical bundle IDs and identical artifact bytes.

## ECMO Integration (Optional)

ECMO can select NS as a track in future workflows:

- emit `measurement_selection.json`
- run NS steps
- bundle and sign evidence

This keeps “external constraints force measurement” aligned with the physics lab pack.
