# Coupling Operator Semantics (v2.2)

## D1 - Couple
Couple(edge_id, payload):
- validates domain/codomain against projector contracts
- applies the declared coupling transformation
- emits a CouplingEvent

## D2 - Commute (Optional)
Commute(edge_a, edge_b, payload):
- evaluates paired application under deterministic ordering
- produces a dual trace for symmetry or interference analysis
- MUST be explicitly declared if supported

## D3 - Local Evolution Independence
Sector internals may evolve freely provided projector contracts remain satisfied.
