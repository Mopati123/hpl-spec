# HPL Primitives — Evolve / Collapse / Anchor (v2.3)

## Evolve
`evolve(ETO, λ, state, dt)` defines time evolution under a declared effect type.
Evolve MUST be deterministic given the same ETO, λ, state, and dt.

## Collapse
`collapse(scheduler, measurement)` defines the scheduler-gated measurement event.
Collapse MUST be authorized by the scheduler and MUST emit audit evidence.

## Anchor
`anchor(epoch_hash, signatures)` records the epoch boundary for verification.
Anchor MUST be a pure evidence primitive and MUST NOT alter semantics.

## Notes
These primitives are semantic declarations, not runtime implementations.
