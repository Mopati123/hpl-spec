# IO Lane v1 Green Baseline

Commit: ba44514  
Status: pushed to origin/main  
Test gate: 383 passed, 26 subtests passed

## What was restored

The IO lane now enforces:

- IO policy gate before effect execution
- token scope checks
- endpoint allowlist checks
- timeout bucket refusal evidence
- HPL_IO_ENABLED runtime guard
- IO reconciliation output
- io_outcome.json evidence
- reconciliation_report.json evidence
- io_lane_v1 bundle completeness

## Kernel meaning

IO effects now follow lawful-collapse semantics:

proposal → token/policy gate → effect execution/refusal → reconciliation → evidence bundle

No IO lane bundle passes without required IO evidence roles.

## Frozen milestone

This note records the green IO lane baseline after the repo returned to a clean, passing state.

The milestone is identified by:

- Git tag: io-lane-v1-green-ba44514
- Commit: ba44514
- Branch: main
- Test result: 383 passed, 26 subtests passed

This baseline becomes the stable checkpoint before NET lane N1 begins.