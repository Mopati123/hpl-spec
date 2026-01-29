# HPL Production Readiness Checklist and Runbook

This runbook provides a minimal, repeatable path to demonstrate HPL as a
production-grade execution sovereignty platform. It assumes you are in the
repo root and have Python 3.11+ available.

## 0) Preconditions

- CI signing key is set in GitHub Secrets as HPL_CI_ED25519_PRIVATE_KEY.
- Local working tree is clean: `git status -sb` shows no untracked artifacts.
- You are on the latest main: `git pull --ff-only`.

## 1) Install / Entry Point Check

- [ ] Create a fresh virtual environment.
- [ ] Install the package:

```
pip install .
```

- [ ] Verify CLI is available and versioned:

```
hpl --version
hpl --help
```

## 2) Local Lifecycle (Kernel Default)

This produces a full, deterministic run bundle using the canonical entrypoint.

- [ ] Create a temp output directory:

```
mkdir .\out_run
```

- [ ] Run lifecycle on a minimal example:

```
hpl lifecycle .\examples\momentum_trade.hpl --backend classical --out-dir .\out_run
```

Expected:
- `out_run` contains plan, runtime result, backend artifacts, evidence JSONs,
  and a bundle folder with `bundle_manifest.json`.
- Exit code is 0, even on lawful refusal.

## 3) Bundle Signing (Local)

If you have a local dev signing key (test key) and want to validate signing,
use the bundle command to sign and verify the manifest.

- [ ] Sign and verify the bundle manifest:

```
hpl bundle --out-dir .\out_run --sign-bundle --signing-key .\tests\fixtures\keys\ci_ed25519_test.sk --verify-bundle
```

Expected:
- `bundle_manifest.sig` appears alongside `bundle_manifest.json`.
- Verification passes; no errors in output.

## 4) CI Artifact Verification

CI runs lifecycle, signs the bundle, verifies the signature, and uploads the
bundle as an artifact.

- [ ] Trigger CI with a no-op commit (if needed):

```
git commit --allow-empty -m "CI: verify bundle signing"
git push
```

- [ ] In GitHub Actions, confirm:
  - lifecycle step ran
  - bundle was signed and verified
  - artifact was uploaded (bundle directory)

## 5) CI Governance Demo (Domain Pack)

The CI governance demo pack is the first domain instantiation. It validates
registries and coupling topology and produces a signed bundle.

- [ ] Run the demo locally:

```
hpl demo ci-governance --out-dir .\out_demo --signing-key .\tests\fixtures\keys\ci_ed25519_test.sk
```

Expected:
- `out_demo` includes a signed bundle and a report JSON.
- Deterministic outputs across repeated runs.

## 6) ECMO Track Selection (External Constraints)

ECMO selects a track from explicit boundary-condition inputs.

- [ ] Run ECMO-driven lifecycle (CI available case):

```
hpl lifecycle .\examples\momentum_trade.hpl --backend classical --out-dir .\out_ecmo_ci --ecmo .\tests\fixtures\ecmo_boundary_ci.json
```

- [ ] Run ECMO-driven lifecycle (regulator request case):

```
hpl lifecycle .\examples\momentum_trade.hpl --backend classical --out-dir .\out_ecmo_reg --ecmo .\tests\fixtures\ecmo_boundary_regulator.json
```

- [ ] Run ECMO-driven lifecycle (ambiguous inputs -> refusal):

```
hpl lifecycle .\examples\momentum_trade.hpl --backend classical --out-dir .\out_ecmo_amb --ecmo .\tests\fixtures\ecmo_boundary_ambiguous.json
```

Expected:
- MeasurementSelection artifact is bundled when selection is valid.
- Ambiguous inputs produce lawful refusal with ConstraintWitness.

## 7) Verification Checklist

- [ ] Bundle manifest is deterministic across repeated runs (same inputs).
- [ ] Signature verification fails on manifest tamper.
- [ ] Runtime refusal always includes ConstraintWitness.
- [ ] ExecutionToken is included in evidence bundles.
- [ ] Budget exhaustion triggers lawful refusal with witness.

## 8) Minimal Public Claims (Accurate)

You can claim the platform is production-grade as an execution sovereignty
system with:

- deterministic kernel execution
- refusal-first evidence
- token- and budget-gated runtime
- signed bundle non-repudiation
- ECMO external-constraint selection
- a working domain demo pack (CI governance)

You should avoid claiming production-grade domain IO (trading/agents) until a
real domain pack with IO policies is implemented and tested.

## 9) Clean Up

- [ ] Remove local output directories if they are not needed:

```
Remove-Item -Recurse -Force .\out_run, .\out_demo, .\out_ecmo_ci, .\out_ecmo_reg, .\out_ecmo_amb
```

- [ ] Ensure no new artifacts are tracked:

```
git status -sb
```