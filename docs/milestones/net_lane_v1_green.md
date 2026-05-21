# NET Lane v1 Green Baseline

## Status

NET Lane v1 is frozen as a governed communication and evidence lane.

This milestone records the completed NET proof ladder from N1 through N14 and defines the freeze boundary for NET Lane v1.

## Final baseline

```text
Branch before N15: main
Latest verified merge before N15: 3ec6da3
Full proof before N15: 405 passed, 26 subtests passed
```

## Kernel meaning

NET Lane v1 proves that governed network communication can execute under HPL/ApexQuantumICT lawful-collapse semantics.

```text
valid authority   → authorized NET collapse
invalid authority → deterministic NET refusal
```

Both outcomes produce auditable, signed, anchor-ready evidence.

## Lawful-collapse semantics

NET effects follow the HPL execution law:

```text
proposal
→ token/policy gate
→ endpoint/capability/budget projection
→ epoch/authority verification
→ NET effect execution or refusal
→ deterministic evidence
→ bundle completeness
→ signature verification
→ anchor-ready commitment
```

No NET effect may bypass token policy, endpoint allowlists, runtime guards, evidence emission, or authority verification.

## NET effect lifecycle

NET Lane v1 covers the governed NET lifecycle:

```text
NET_CONNECT
→ NET_HANDSHAKE
→ NET_KEY_EXCHANGE
→ NET_SEND
→ NET_RECV
→ NET_CLOSE
```

The session lifecycle is correlated through deterministic evidence and `net_session_manifest`.

## Proof ladder

| Step | Proof file | Invariant |
| --- | --- | --- |
| N1 | `tests/test_net_token_gate.py` | permission/capability/endpoint/budget gate |
| N2 | `tests/test_net_evidence_bundle.py` | NET evidence bundle completeness |
| N3 | `tests/test_net_adapter_contract.py` | adapter response contract and request correlation |
| N4 | `tests/test_net_session_lifecycle.py` | full NET lifecycle evidence correlation |
| N5 | `tests/test_net_cli_plan_proof.py` | CLI → plan → runtime → evidence → bundle |
| N6 | `tests/test_net_signed_bundle_proof.py` | successful bundle signature verification |
| N7 | `tests/test_net_anchor_ready_proof.py` | successful bundle anchor-ready commitment |
| N8 | `tests/test_net_epoch_anchor_verification_proof.py` | valid epoch/anchor verification |
| N9 | `tests/test_net_epoch_refusal_proof.py` | invalid epoch signature refusal |
| N10 | `tests/test_net_refusal_bundle_completeness.py` | refusal bundle completeness |
| N11 | `tests/test_net_refusal_bundle_signature_proof.py` | refusal bundle signature verification |
| N12 | `tests/test_net_refusal_anchor_ready_proof.py` | refusal bundle anchor-ready commitment |
| N13 | `tests/test_net_valid_refusal_duality_proof.py` | valid/refusal evidence-contract duality |
| N14 | `tests/test_net_proof_ladder_regression_guard.py` | proof ladder regression guard |

## N1 — Token gate and refusal taxonomy

Proof file:

```text
tests/test_net_token_gate.py
```

Proves:

```text
NETPermissionDenied
NETEndpointNotAllowed
NETBudgetExceeded
```

Meaning:

```text
NET effects cannot execute without the required token capability, endpoint permission, and budget.
```

## N2 — Evidence bundle completeness

Proof file:

```text
tests/test_net_evidence_bundle.py
```

Proves:

```text
net_lane_v1
missing_required
required NET evidence roles
```

Meaning:

```text
NET evidence must be complete enough to be bundled and audited.
```

## N3 — Adapter response contract

Proof file:

```text
tests/test_net_adapter_contract.py
```

Proves:

```text
adapter response normalization
request_id correlation
mock adapter behavior
```

Meaning:

```text
NET adapter responses are normalized and correlated to deterministic request IDs.
```

## N4 — Session lifecycle correlation

Proof file:

```text
tests/test_net_session_lifecycle.py
```

Proves:

```text
NET_CONNECT
NET_HANDSHAKE
NET_KEY_EXCHANGE
NET_SEND
NET_RECV
NET_CLOSE
net_session_manifest
```

Meaning:

```text
A full NET session lifecycle is recorded as correlated evidence.
```

## N5 — CLI plan evidence path

Proof file:

```text
tests/test_net_cli_plan_proof.py
```

Proves:

```text
hpl demo net-shadow
→ plan
→ runtime
→ evidence
→ bundle_manifest.json
```

Meaning:

```text
The public CLI path can generate plan, runtime, evidence, and bundle artifacts.
```

## N6 — Signed bundle verification

Proof file:

```text
tests/test_net_signed_bundle_proof.py
```

Proves:

```text
bundle_manifest.json
bundle_manifest.sig
verify_bundle_manifest_signature
net_lane_v1.ok == true
```

Meaning:

```text
Successful NET bundles are signed and verifiable.
```

## N7 — Anchor-ready success commitment

Proof file:

```text
tests/test_net_anchor_ready_proof.py
```

Proves:

```text
successful NET bundle
→ signed
→ verifiable
→ stable anchor-ready commitment
```

Meaning:

```text
Successful NET evidence can be converted into a stable external commitment.
```

## N8 — Valid epoch/anchor verification

Proof file:

```text
tests/test_net_epoch_anchor_verification_proof.py
```

Proves:

```text
valid epoch anchor
valid anchor signature
--require-epoch
verification.epoch_ok == true
verification.signature_ok == true
lawful NET execution
```

Meaning:

```text
Valid epoch authority authorizes lawful NET shadow execution.
```

## N9 — Invalid epoch signature refusal

Proof file:

```text
tests/test_net_epoch_refusal_proof.py
```

Proves:

```text
valid epoch anchor
invalid anchor signature
→ deterministic refusal
→ no false successful NET collapse
```

Meaning:

```text
Invalid epoch authority is refused deterministically.
```

## N10 — Refusal bundle completeness

Proof file:

```text
tests/test_net_refusal_bundle_completeness.py
```

Proves:

```text
refusal path
→ deterministic evidence
→ refusal bundle artifacts
→ verification.epoch_ok == true
→ verification.signature_ok == false
```

Meaning:

```text
Refusal is not silent failure; refusal is an auditable runtime outcome.
```

## N11 — Refusal bundle signature verification

Proof file:

```text
tests/test_net_refusal_bundle_signature_proof.py
```

Proves:

```text
refusal bundle
→ bundle_manifest.json
→ bundle_manifest.sig
→ signature verifies
```

Meaning:

```text
Refusal bundles are also signed and verifiable.
```

## N12 — Refusal anchor-ready commitment

Proof file:

```text
tests/test_net_refusal_anchor_ready_proof.py
```

Proves:

```text
refusal bundle
→ signed
→ verifiable
→ stable anchor-ready commitment
```

Meaning:

```text
Refused NET authority also produces stable commitment-ready history.
```

## N13 — Valid/refusal duality proof

Proof file:

```text
tests/test_net_valid_refusal_duality_proof.py
```

Proves:

```text
valid authority   → summary.ok == true
invalid authority → summary.ok == false

valid and refusal paths share the same evidence contract shape
```

Meaning:

```text
Valid execution and deterministic refusal are two lawful outcomes of one evidence contract.
```

## N14 — Proof ladder regression guard

Proof file:

```text
tests/test_net_proof_ladder_regression_guard.py
```

Proves:

```text
N1 through N13 are represented in order
critical proof files exist
each proof file carries invariant tokens
future deletion or weakening is caught by tests
```

Meaning:

```text
The proof ladder itself is protected from accidental deletion, renaming, or hollowing out.
```

## Successful path contract

A valid authority path proves:

```text
summary.ok == true
runtime status == completed
bundle_manifest.json exists
bundle_manifest.sig exists
bundle signature verifies
verification.epoch_ok == true
verification.signature_ok == true
net_lane_v1.ok == true
net_lane_v1.missing_required == []
anchor-ready commitment exists
```

## Refusal path contract

An invalid authority path proves:

```text
summary.ok == false
denied_reason == refusal
bundle_manifest.json exists when bundle_path is emitted
bundle_manifest.sig exists when bundle_path is emitted
bundle signature verifies
verification.epoch_ok == true
verification.signature_ok == false
signature/verification failure is recorded
no false successful NET collapse is accepted
anchor-ready refusal commitment exists
```

## Symmetry theorem

NET Lane v1 proves:

```text
lawful execution → signed/verifiable/anchor-ready evidence
lawful refusal   → signed/verifiable/anchor-ready evidence
```

Therefore:

```text
valid authority   → authorized collapse
invalid authority → deterministic refusal
```

Both outcomes are auditable history.

## Governance invariants

NET Lane v1 preserves:

```text
Codex proposes only.
CPU-side gates own collapse authority.
ExecutionToken policy gates cannot be bypassed.
Endpoint allowlists cannot be bypassed.
NET runtime guard cannot be bypassed.
Secrets must not appear in evidence.
Successful bundles are signed.
Refusal bundles are signed.
Successful bundles are anchor-ready.
Refusal bundles are anchor-ready.
Regression guard protects the proof ladder.
```

## Freeze boundary

NET Lane v1 is considered complete when this document is merged and the final merge commit is tagged:

```text
net-lane-v1-green-<commit>
```

After this freeze, future NET changes must be treated as NET Lane v2 or as narrow maintenance patches that preserve all v1 invariants.

## What is left after NET Lane v1

NET Lane v1 completes the governed communication substrate. It does not complete the whole HPL/ApexQuantumICT system.

Remaining canonical lanes:

```text
Crypto lane
→ hybrid/PQ transcript hashing, key policy, no-secrets evidence

Trading shadow lane
→ MT5/Deriv/TradingView governed shadow execution

Hardware substrate lane
→ CPU/GPU authority validator

Codex governance lane
→ Codex task execution proof under AGENTS.md

Regulatory packet lane
→ regulator-readable evidence bundle and external audit packet
```

## Completion status

```text
NET Lane v1: complete after N15 merge and tag
System overall: not complete
Next recommended lane: Crypto lane or Trading shadow lane
```