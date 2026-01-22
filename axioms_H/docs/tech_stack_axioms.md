# Tech Stack Axioms (v2.4)

## Axiom TS1 - Backend Target Taxonomy
Backend targets are fixed to: PYTHON, CYTHON, MOJO, JULIA, QASM.
Any new target requires a new SCR and freeze.

## Axiom TS2 - Evidence Chain Required
Certified runs MUST produce CouplingEvent, DevChangeEvent, and AnchorEvent
artifacts as applicable.

## Axiom TS3 - Registry-as-Linker
Backend lowering is lawful only for operators and edges declared in registries.

## Axiom TS4 - Papas Non-Authority
Papas MAY witness and explain but MUST NOT authorize collapse or alter
semantics.

## Axiom TS5 - Forbidden-Regions-First
If legality or determinism cannot be established, the system MUST refuse and
emit refusal evidence.
