# First Live Instantiation Plan

This plan is an implementation guide using the current codebase (B1 + B2 + anchoring + signing). It introduces no new law.

## Chosen MVP: CI Governance Instantiation

Rationale: The CI governance instantiation is already closest to completion and exercises the full evidence chain.

### Goals
- Produce an ExecutionPlan from ProgramIR
- Enforce runtime gate (contracted steps only)
- Emit evidence (CouplingEvent/DevChangeEvent/AnchorEvent)
- Anchor and sign the universe state

### Exact Steps (Commands)

1) Generate ProgramIR from an example surface program:
- parse -> expand -> validate -> ir_emit

2) Produce an ExecutionPlan (planner-only):
- `python -c "from hpl import scheduler; ..."` (use scheduler.plan)

3) Run runtime gate (no execution yet):
- `python -c "from hpl.runtime.engine import RuntimeEngine; ..."`

4) Emit evidence artifacts:
- CouplingEvent: `src/hpl/audit/coupling_event.py`
- DevChangeEvent: `src/hpl/audit/dev_change_event.py`

5) Anchor and sign:
- `python tools/anchor_epoch.py --epoch-id ci --out artifacts/epoch_ci.anchor.json`
- `python tools/sign_anchor.py --anchor artifacts/epoch_ci.anchor.json --out artifacts/epoch_ci.anchor.sig`
- `python tools/verify_anchor_signature.py --anchor artifacts/epoch_ci.anchor.json --sig artifacts/epoch_ci.anchor.sig --pub config/keys/ci_ed25519.pub`

### Artifacts Produced
- ExecutionPlan (JSON via `ExecutionPlan.to_dict`)
- RuntimeResult (JSON via `RuntimeResult.to_dict`)
- Evidence artifacts (CouplingEvent, DevChangeEvent)
- Epoch anchor + signature (AnchorEvent equivalent)

### Acceptance Criteria
- ExecutionPlan is deterministic (stable plan_id)
- Runtime gate refuses any step not in contract
- Evidence artifacts are deterministic and schema-shaped
- Anchor verification passes using the CI public key

### Refusal / Failure Modes (Expected)
- Missing or invalid epoch anchor => plan/runtime denial
- Signature verification failure => denial
- Step not in allowed contract => refusal with evidence
- Missing evidence emission => reject as incomplete run

### Security Boundaries
- No secrets committed; signing key in GitHub Secrets only
- Papas can witness, cannot authorize or execute
- CI signing is the authoritative proof boundary

## Alternative MVPs (Queued)

1) Trading pilot (domain instantiation)
- Requires backend lowering and domain-specific registries

2) Agent governance pilot
- Requires CLI and policy enforcement for agent actions

Both are deferred until B3 backend lowering or CLI scaffolding is completed.

## Follow-on Tasks (If Needed)
- Minimal CLI: `hpl plan`, `hpl gate`, `hpl anchor`
- B3 backend lowering modules
- CI attestation reporting bundle
