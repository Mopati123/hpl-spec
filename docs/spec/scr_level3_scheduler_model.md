# SCR — Level-3 Scheduler Model

## Target Version
- Proposed: v2.0 (Level-3 semantics)

## Change Category
- New semantic layer (breaking; requires major version)

## Motivation
Define the authoritative execution scheduler for HPL programs. This establishes
how evolution, ordering, and determinism are governed without prescribing runtime code.

## Scope
IN SCOPE:
- Scheduler responsibilities and invariants
- Determinism vs nondeterminism boundaries
- Ordering guarantees (or lack thereof)

OUT OF SCOPE:
- Runtime implementation
- Performance optimizations
- Hardware bindings

## Definitions
- **Scheduler:** The semantic authority that orders and authorizes program evolution.
- **Tick:** A logical scheduling step (not wall-clock time).

## Proposed Semantics (Draft)
- Programs advance only via scheduler-authorized ticks.
- Scheduler is the sole source of ordering.
- Scheduler decisions are observable only via declared interfaces.

## Invariants
- No implicit execution outside scheduler control.
- Same inputs + same scheduler policy ⇒ same observable outcomes.

## Compatibility & Migration
- Not backward compatible with v1/v1.1 (introduces execution semantics).
- Requires v2.0 freeze.

## Conformance Impact
- New Level-3 conformance checklist required.
- No impact on v1/v1.1 certification.

## Alternatives Considered
- Implicit execution (rejected)
- External host scheduling (rejected)

## Open Questions
- Deterministic replay requirements?
- Pluggable vs fixed scheduler policies?

## Review Record
(To be completed)
