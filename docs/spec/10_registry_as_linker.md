# Registry as Linker (v2.3)

## Law
The operator registry is the sole linker of legal edges. A coupling edge exists
iff it is declared in the registry.

## Requirements
1. Undeclared edges MUST be rejected.
2. Declared edges MUST match projector contracts.
3. Registry ordering is non-authoritative; identity is by edge id.

## Notes
Registry-as-linker is a legality rule; it does not imply runtime execution.
