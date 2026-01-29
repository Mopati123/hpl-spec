# HPL Quickstart (Install and Run)

This quickstart installs the HPL toolchain and runs a deterministic lifecycle
to produce a signed evidence bundle.

## Install

```bash
pip install .
```

Verify the CLI is available:

```bash
hpl --version
```

## Run a deterministic lifecycle

```bash
hpl lifecycle examples/momentum_trade.hpl \
  --backend classical \
  --out-dir out/quickstart \
  --quantum-semantics-v1 \
  --constraint-inversion-v1
```

Outputs:

- `out/quickstart/work/program.ir.json`
- `out/quickstart/work/plan.json`
- `out/quickstart/work/runtime.json`
- `out/quickstart/bundle_<id>/bundle_manifest.json`
- `out/quickstart/bundle_<id>/bundle_manifest.sig` (if signed)

## Verify the bundle signature

If a signature exists, verify it with the public key:

```bash
hpl bundle --out-dir out/quickstart \
  --verify-bundle \
  --pub config/keys/ci_ed25519.pub
```

This returns a refusal-style JSON if verification fails.
