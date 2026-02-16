Place canonical Machine A Track A reference artifacts in this folder:

- `anchor_manifest.json`
- `anchor_leaves.json`

This folder is used by `tools/phase1_track_a_verify.ps1` and should contain
the exact files exported from Machine A for commit
`d878e95c4b4adb64a6f080eb8b8fa4dbbd655aaf`.

The verifier will fail fast if either file is missing.
