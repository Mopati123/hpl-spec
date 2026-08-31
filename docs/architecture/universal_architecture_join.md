# Universal Architecture Join

## Canonical pipeline

```text
Domain reality / repository model
        |
        v
ArchitectureSpec
        |
        | validate + normalize + digest
        v
ArchitectureIR
        |
        | deterministic lowering
        v
HPL ProgramIR
        |
        v
Scheduler / ExecutionToken
        |
        v
Governed effects -> evidence -> reconciliation
```

## Ownership boundaries

`ArchitectureSpec` is domain-facing and declarative. It describes state, observables, dynamics, proposals, constraints, invariants, authority requirements, effects, evidence, and reconciliation.

`ArchitectureIR` is domain-neutral. It normalizes those declarations into a deterministic pre-execution representation and records the source digest. ArchitectureIR cannot mint execution authority.

`ProgramIR` remains HPL-owned and frozen. The architecture join lowers into the existing ProgramIR schema rather than extending it with domain-specific fields.

The scheduler remains the sole execution-authority owner. A domain may declare that execution authority is required, but it cannot assign that authority to itself.

## Mandatory invariants

1. Scheduler sovereignty is preserved across lowering.
2. Architecture compilation never executes effects.
3. Evidence is mandatory for every executable architecture.
4. Reconciliation is mandatory for every executable architecture.
5. Invalid or incomplete architecture declarations refuse before ProgramIR emission.
6. Equivalent ArchitectureSpec inputs lower deterministically.
7. Domain-specific semantics remain in adapters/domain packs, not in the universal compiler.
8. Existing ProgramIR validation remains authoritative after lowering.

## Domain adapter rule

Each ecosystem repository should implement a thin adapter:

```text
native domain model -> ArchitectureSpec
```

The adapter may translate domain vocabulary but must not reimplement scheduler authority, evidence semantics, reconciliation semantics, or ProgramIR validation.

Initial target adapters:

- ApexQuantumICT -> market/trading ArchitectureSpec
- PulaFeed -> agriculture/marketplace ArchitectureSpec
- Easy Banking OS -> banking ArchitectureSpec
- QuantMuse / agent systems -> agent ArchitectureSpec
- Universal Hamiltonian Framework -> dynamical-system ArchitectureSpec

This creates one join point while preserving domain autonomy.
