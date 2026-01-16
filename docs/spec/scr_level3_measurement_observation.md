# SCR — Level-3 Measurement & Observation

## Target Version
- Proposed: v2.0

## Change Category
- New semantic layer (breaking)

## Motivation
Define how measurements and observers interact with execution,
including visibility, collapse, and auditability.

## Scope
IN SCOPE:
- Measurement authorization
- Observer capabilities
- Audit trails

OUT OF SCOPE:
- Physical measurement models
- External I/O semantics

## Proposed Semantics (Draft)
- Measurements are explicit, scheduler-authorized events.
- Observers have declared capabilities.
- Measurements may affect future evolution only via declared rules.

## Invariants
- No implicit measurement.
- All observations are auditable.

## Compatibility & Migration
- Requires v2.0.
- No effect on v1/v1.1.

## Open Questions
- Multiple observers coordination?
- Deterministic vs probabilistic observation?

## Review Record
(To be completed)
