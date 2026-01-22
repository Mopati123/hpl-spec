# Epoch Anchoring (v2.3)

## Purpose
Epoch anchoring defines the immutable boundary for evidence and replay. An epoch
anchor captures the exact law, registries, and tooling used to validate a run.

## Requirements
1. An epoch anchor MUST include hashes of:
   - IR schema
   - operator registry schema
   - audit trace schema
   - coupling event manifest
   - all `_H` operator registries
   - enforcement tooling binaries/scripts
2. Anchors MUST be deterministic for identical inputs.
3. Anchors MUST be verifiable against the working tree.
4. Anchors MAY include witness attestations; such attestations have no execution authority.

## Notes
Anchoring is evidence-only. It does not execute or authorize runtime behavior.
