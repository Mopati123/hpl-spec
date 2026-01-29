# HPL External Packet (v1)

This packet is a PDF-friendly external projection of the HPL execution-sovereignty platform.
It contains authoritative, human-readable artifacts derived from the current repository state.

## Contents
- Production Readiness Checklist: `docs/publish/production_readiness_checklist.md`
- Execution Lifecycle Diagram: `docs/publish/hpl_execution_lifecycle_diagram.md`
- Constitution / Whitepaper: `docs/publish/hpl_constitution_whitepaper_v1.md`
- ECMO Runbook: `docs/publish/ecmo_runbook.md`

---

# Production Readiness Checklist

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

<!-- pagebreak -->

# Execution Lifecycle Diagram

# HPL Execution Lifecycle (Canonical Diagram)

This is the single canonical lifecycle description. All outward-facing artifacts must conform to this flow.

## ASCII Flow (Canonical)

[Axioms/Law (_H)]
    |
    v
[Intent Source]
    |
    v
[Existence Projector]
  (Registry + Spec Gate)
    |
    v
[IR State Vector]
  (ProgramIR)
    |
    v
[Papas Observe]
  (witness only)
    |
    v
[Scheduler Gate]
  (epoch+sig verify, lambda grant/refuse)
   |  \
   |   \__ Refusal is success (evidence emitted)
   |
   v
[Runtime Gate]
  (contract enforcement)
   |  \
   |   \__ Refusal is success (evidence emitted)
   |
   v
[Backend Reaction Vessel]
  (lowering/execution target)
    |
    v
[Evidence Emission]
  (CouplingEvent / DevChangeEvent / AnchorEvent)
    |
    v
[Epoch Anchor]
  (anchor + sign + verify)
    |
    v
[Feedback]
  (auditable universe state)

Rule: if not evidenced, did not happen.

## Mermaid Flow (Canonical)

```mermaid
flowchart TD
  A[Axioms / Law (_H)] --> B[Intent Source]
  B --> C[Existence Projector<br/>Registry + Spec Gate]
  C --> D[IR State Vector<br/>ProgramIR]
  D --> E[Papas Observe<br/>Witness Only]
  E --> F[Scheduler Gate<br/>Epoch+Sig Verify<br/>Lambda Grant/Refuse]
  F -->|refuse| R1[Refusal = Success<br/>Evidence Emitted]
  F --> G[Runtime Gate<br/>Contract Enforcement]
  G -->|refuse| R2[Refusal = Success<br/>Evidence Emitted]
  G --> H[Backend Reaction Vessel<br/>Lowering / Execution Target]
  H --> I[Evidence Emission<br/>CouplingEvent / DevChangeEvent / AnchorEvent]
  I --> J[Epoch Anchor<br/>Anchor + Sign + Verify]
  J --> K[Feedback<br/>Auditable Universe State]

  classDef gate fill:#f7f7f7,stroke:#333,stroke-width:1px;
  class F,G gate;
```

## Repo Module Mapping (Canonical)

- Axioms/Law: `*_H/` (e.g., `axioms_H`, `dynamics_H`, `runtime_H`, `audit_H`, `tools_H`, `tests_H`)
- Intent Source: `examples/`, surface DSL inputs
- Existence Projector: registries + validators
  - `tools/validate_operator_registries.py`
  - `tools/validate_observer_registry.py`
  - `tools/validate_coupling_topology.py`
- IR State Vector: parser/macro/validator/IR emitter
  - `src/hpl/emergence/dsl/parser.py`
  - `src/hpl/emergence/macros/expander.py`
  - `src/hpl/axioms/validator.py`
  - `src/hpl/dynamics/ir_emitter.py`
- Papas Observe: witness emission
  - `src/hpl/trace.py` (witness records)
- Scheduler Gate: `src/hpl/scheduler.py`
- Runtime Gate: `src/hpl/runtime/context.py`, `src/hpl/runtime/contracts.py`, `src/hpl/runtime/engine.py`
- Evidence Emission:
  - CouplingEvent: `src/hpl/audit/coupling_event.py`
  - DevChangeEvent: `src/hpl/audit/dev_change_event.py`
- Epoch Anchor:
  - `tools/anchor_epoch.py`
  - `tools/sign_anchor.py`
  - `tools/verify_anchor_signature.py`
  - `tools/verify_epoch.py`

Status note: lowering/execution backends are planned under B3, not yet implemented.


<!-- pagebreak -->

# Constitution / Whitepaper

# HPL Constitution / Whitepaper v1

## 1) Problem Statement

Most software systems allow implicit execution and unverifiable behavior. This creates:
- unclear authority boundaries,
- unprovable claims about correctness or determinism,
- and audit trails that are optional rather than required.

HPL is designed to remove those failure modes by making authority, evidence, and evolution explicit and mandatory.

## 2) HPL Solution (Authority, Evidence, Anchoring)

HPL defines a governed computational universe where:
- authority is centralized (scheduler),
- evidence is mandatory (audit artifacts),
- and the universe state is anchored cryptographically.

Execution is not a right. It is a phase transition that must be earned.

## 3) Core Laws (v2.4 Summary)

This document summarizes the frozen law. See:
- `docs/spec/00_spec_freeze_declaration_v2_4.md`
- `docs/spec/11_tech_stack_quantum_proof_semantics.md`

Key laws:
- Coupling topology is explicit and registry-gated.
- Evidence chain is mandatory (CouplingEvent, DevChangeEvent, AnchorEvent).
- Epoch anchoring defines a verifiable universe state.
- Backend lanes are declared and non-authoritative.
- Papas is a witness and explainer, never a collapse authority.

## 4) Execution Lifecycle (Canonical)

See `docs/publish/hpl_execution_lifecycle_diagram.md`.

Lifecycle summary:
Axioms -> Intent -> Registry Gate -> ProgramIR -> Papas Observe -> Scheduler Gate
-> Runtime Gate -> Backend Reaction Vessel -> Evidence Emission -> Epoch Anchor -> Feedback

Refusal is success and is always evidenced. If not evidenced, it did not happen.

## 5) Security and Provenance

HPL requires epoch anchors and Ed25519 signatures for provenance:
- Anchor generation: `tools/anchor_epoch.py`
- Signature: `tools/sign_anchor.py`
- Verification: `tools/verify_anchor_signature.py`

The scheduler and runtime gates may refuse authorization if the universe identity
cannot be verified.

## 6) Compliance and Auditability

HPL is designed for auditability:
- explicit coupling edges,
- deterministic artifacts,
- and enforced evidence emission.

This supports compliance, regulated domains, and reproducibility.

## 7) Scope Disclaimers

HPL defines software proof semantics. It is not an experimental physics claim,
not a quantum device model, and not a trading system by itself.

## 8) Roadmap (Implementation)

Near-term execution milestones:
- B3: Backend lowering (BackendIR + deterministic lowerers)
- CLI scaffolding (plan + runtime gate)
- First live instantiation (CI governance or domain-specific pilot)

No new semantics are introduced here; this document is a narrative reference only.


<!-- pagebreak -->

# ECMO Runbook

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


<!-- pagebreak -->
