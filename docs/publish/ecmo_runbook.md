# ECMO Runbook (Measurement Track Selection)

This runbook documents how to use the ExternalConstraintMeasurementOperator (ECMO)
in HPL. ECMO **selects** a collapse track based on explicit boundary-condition
inputs. It does **not** authorize execution; the scheduler remains sovereign.

## Inputs

ECMO reads a boundary-conditions JSON file. No network probes are used.

Minimal examples:

```json
{"ci_available": true}
```

```json
{"regulator_request_id": "REQ-001"}
```

```json
{"market_window_open": true, "risk_mode": "shadow"}
```

If multiple conditions select multiple tracks, ECMO produces a lawful refusal.

## Lifecycle (Kernel Default)

Run a full lifecycle with ECMO input:

```bash
hpl lifecycle examples/momentum_trade.hpl \
  --backend classical \
  --out-dir out/ecmo_demo \
  --ecmo-input tests/fixtures/ecmo_boundary_ci.json \
  --quantum-semantics-v1 \
  --constraint-inversion-v1
```

Outputs:

- `out/ecmo_demo/work/measurement_selection.json`
- `out/ecmo_demo/bundle_<id>/bundle_manifest.json`

The bundle includes `measurement_selection` as a first-class role when ECMO
selection succeeds.

## Refusal Behavior

If inputs are missing or ambiguous, ECMO yields a lawful refusal. The runtime
emits a `ConstraintWitness` (and a `DualProposal` if `--constraint-inversion-v1`
is set). Refusal is a **lawful output**, not a crash.

Example ambiguous inputs:

```json
{"ci_available": true, "regulator_request_id": "REQ-AMBIG"}
```

## Bundling and Signing

Bundles remain signable and verifiable as before:

```bash
hpl bundle --out-dir out/ecmo_demo --plan out/ecmo_demo/work/plan.json \
  --runtime-result out/ecmo_demo/work/runtime.json \
  --backend-ir out/ecmo_demo/work/backend.ir.json \
  --quantum-semantics-v1 \
  --sign-bundle --signing-key /path/to/test.key
```

The signed payload is `bundle_manifest.json`, with signature written to
`bundle_manifest.sig`.

## Success Criteria

Success:

- `measurement_selection.json` exists
- bundle includes role `measurement_selection`
- bundle verification passes (if signature used)

Lawful refusal:

- lifecycle returns `ok=false`
- constraint witness is present
- evidence bundle is still produced
