# Phase-1 Anchor Runbook (Bundle → Merkle Root → Signature)

This runbook defines the deterministic, refusal-first anchor loop for Phase-1 runs.
It is chain-agnostic and produces a mint-ready anchor manifest + signature.

## Preconditions

- A completed, role-complete evidence bundle directory (e.g., produced by `hpl lifecycle` or a demo track).
- Optional signing key (Ed25519 seed hex) for non-repudiation.

## Determinism Rules

- File paths are normalized with `/` separators and sorted lexicographically.
- Leaf hash rule: `sha256(relpath + ":" + sha256(file_bytes))`.
- Merkle tree pairing is deterministic; odd leaves are duplicated.
- No wall-clock timestamps are included in any hashed content.

## Generate Anchor Manifest

Example (signing via key file):

```
python tools/anchor_generator.py <bundle_dir> \
  --out-dir <bundle_dir> \
  --signing-key <path_to_ed25519_seed_hex>
```

Outputs (in `out-dir`):

- `anchor_manifest.json`
- `anchor_leaves.json`
- `anchor_manifest.sig` (if signing key provided)

## Verify Anchor

```
python tools/verify_anchor.py <bundle_dir> <bundle_dir>/anchor_manifest.json
```

Verification recomputes the leaves and Merkle root from bundle contents and verifies
the manifest signature if present.

## Canonical Track A Compare (Machine B)

Do not compare against ephemeral `artifacts/.../run_001` paths. Keep Machine A
reference artifacts in a stable, versioned folder.

Canonical reference folder:

- `references/phase1/navier_stokes/machine_a_f06023a/anchor_manifest.json`
- `references/phase1/navier_stokes/machine_a_f06023a/anchor_leaves.json`

Run the wrapper to enforce preflight checks and compare in one command:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools\phase1_track_a_verify.ps1
```

The runner creates a detached worktree pinned to the reference manifest's
`git_commit`, forces LF checkout during worktree creation, executes the demo and
anchor generation in that worktree, and then compares contracts deterministically.

It fails fast if required reference files are missing and emits:

- `CONTRACT_MATCH=true|false`
- `MERKLE_MATCH=true|false`
- `REPORT_PATH=<.../track_a_report.json>`

## Anchor Manifest Fields (Canonical)

The manifest includes:

- `hash_alg`: `sha256`
- `leaf_rule`: path-bound leaf rule
- `leaves_path` + `leaves_digest`
- `merkle_root`
- `bundle_id` + `bundle_manifest_digest` (when bundle_manifest.json exists)
- `challenge_window`: chain-agnostic metadata (no timestamps)
- `signing`: public key + signature + signed payload digest

## Challenge Window Metadata

Provide policy metadata without timestamps:

- `mode`: `blocks` or `time`
- `value`: integer or string (policy-defined)
- `chain`: network identifier (e.g., `testnet`)
- `policy_id`: policy label

## Security Posture

- Secrets must never be placed in bundle artifacts.
- The redaction gate should remain enabled for IO bundles.
- Signature payload is the canonical anchor manifest core (no self-reference).
