# Quantum Proof Semantics - Dynamics (v2.4)

## D1 - Commutation Certificates
When commutation properties are claimed, the system MUST emit a commutation
certificate as evidence.

## D2 - Alternating Projections Fallback
If commutation cannot be established, alternating projections MAY be used only
with explicit nondeterminism markers and evidence records.

## D3 - Refusal Semantics
If determinism or legality cannot be established, the system MUST refuse
execution and emit refusal evidence.
