# Coupling Topology Axioms (v2.2)

## Axiom A1 - Sector Isolation
A sector is a closed semantic region.
No internal symbol of a sector is addressable from outside that sector except via
Interface Projectors.

## Axiom A2 - Interface Projector Law
Every sector SHALL expose one or more Interface Projectors.
A projector defines:
- externally visible value types
- externally callable operator signatures
No internal execution semantics are implied.

## Axiom A3 - No Undocumented Coupling
Cross-sector influence exists if and only if a coupling edge is declared in the
Coupling Registry. Undeclared coupling is semantically nonexistent.

## Axiom A4 - No Authority by Import
Import reachability confers zero execution authority.
Authority is granted only by (Registry AND Projector Contract AND Scheduler Authorization).
