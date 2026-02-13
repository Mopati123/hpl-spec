# Reproducibility Contract

## Invariant
A Merkle root comparison is valid only if both runs share the same contract state:

- `git_commit`
- `leaf_rule`
- `leaf_count`
- `bundle_manifest_digest`
- `leaves_digest`

Only after these fields match may `merkle_root` be compared.

## Contract Object
Each anchored run must emit `machine_contract.json` with:

- `git_commit`
- `leaf_rule`
- `leaf_count`
- `bundle_manifest_digest`
- `leaves_digest`
- `merkle_root`

## Refusal Rule
If any contract-state field differs, the comparison must fail with:

`Reference anchor is from a different contract state. Refusing comparison.`

No `merkle_root` decision is permitted in that case.

## Root-Cause Flow
1. Compare contract-state fields.
2. If mismatch: align commit/rules/leaf set and rerun.
3. If contract matches but merkle differs: perform deterministic leaf diff and report first divergent leaf (`index`, `relpath`, `file_hash`).

## Output Contract
Comparisons must report:

- `CONTRACT_MATCH: true|false`
- `MERKLE_MATCH: true|false`
- `ROOT_CAUSE: <text>`
- `NEXT_ACTION: <text>`
