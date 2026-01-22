# Scheduler-Gated Coupling and Boot Semantics (v2.2)

## R1 - Scheduler Gate
Every coupling invocation requires explicit scheduler authorization.
The scheduler is the sole collapse authority for cross-sector execution.

## R2 - Deterministic Boot
Sector initialization and coupling availability MUST be explicitly ordered.
No coupling may occur before:
- registry load
- scheduler readiness

## R3 - Lazy Realization
Backend realization may be deferred until coupling invocation.
Deferred realization MUST be reflected in audit traces.
