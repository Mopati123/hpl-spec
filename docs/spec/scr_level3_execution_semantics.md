# SCR — Level-3 Execution Semantics

## Target Version
- Proposed: v2.0

## Change Category
- New semantic layer (breaking)

## Motivation
Specify how axiomatic programs *execute*: state, evolution, and observables,
without binding to a runtime.

## Scope
IN SCOPE:
- Program state model
- Evolution rules
- Observability boundaries

OUT OF SCOPE:
- Concrete runtimes
- Performance, threading, I/O

## Proposed Semantics (Draft)
- Execution is a sequence of scheduler ticks.
- Each tick applies a well-defined evolution function.
- Only declared observables may expose state.

## Invariants
- No hidden state transitions.
- Evolution is total or fails explicitly.

## Compatibility & Migration
- Requires v2.0.
- v1/v1.1 remain front-end–only.

## Conformance Impact
- New semantic conformance tests.
- Existing tooling remains valid.

## Open Questions
- Pure vs effectful evolution?
- Error handling during evolution?

## Review Record
(To be completed)
