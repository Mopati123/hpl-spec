# Coupling Topology Validation Rules (v2.2)

## V1 - Illegal Cross-Sector Access
Reject any cross-sector coupling invocation that bypasses its declared Interface Projector.

A declared edge is cross-sector when both `sector_src` and `sector_dst` are non-empty strings and differ. For every invocation of such an edge:

- `edge_id` MUST resolve to a declared coupling edge;
- the invocation MUST declare `projector`;
- invocation `projector` MUST equal the projector bound to that declared edge.

Same-sector invocations are not subject to the invocation-level projector-binding requirement.

## V2 - Registry Completeness
Reject any coupling invocation not declared in the registry.

## V3 - Contract Consistency
Projector domain/codomain must match registry declarations.

## V4 - Audit Obligation
Every declared coupling edge MUST specify required audit outputs.
