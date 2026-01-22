# Tech Stack and Quantum Proof Semantics (v2.4)

## Scope
This module defines backend lane taxonomy and proof obligations for HPL. It is
normative and does not introduce runtime implementation requirements.

## Backend Target Taxonomy
The canonical backend targets are:
- PYTHON
- CYTHON
- MOJO
- JULIA
- QASM

Rules:
- Implementations MUST declare supported targets in a backend lane registry.
- Lowering for a given target MUST be deterministic for identical inputs.
- Any target outside this list requires a new SCR and freeze.

## Permitted Substrates
Polars is a permitted substrate for the PYTHON lane only. Use of Polars MUST be
explicitly declared in backend lane metadata. Undeclared substrate use is
forbidden for certified runs.

## Evidence Chain Requirements
Certified implementations MUST produce an evidence chain that includes:
- CouplingEvent for cross-sector interactions.
- DevChangeEvent for development changes that affect certified artifacts.
- AnchorEvent for each epoch anchor.

Evidence artifacts MUST be deterministic for identical inputs and MUST include
hash links to the epoch anchor that governs the run.

## Anchoring Requirements
Epoch anchors MUST include hashes for:
- Spec schemas and registries used by the run.
- Validator and gate tooling.
- Backend lowering artifacts and lane metadata.
- Evidence bundles generated during the run.

Signatures are optional at v2.4 but MUST be recorded when present.

## Registry-as-Linker Legality
Backend lowering is lawful only when:
- Operators are declared in registries, and
- Coupling edges are declared where cross-sector interaction occurs.

Undeclared operators or edges MUST be rejected.

## Determinism and Refusal Semantics
If determinism cannot be proven for a target:
- The implementation MUST refuse execution, or
- The implementation MUST emit a commutation certificate or an explicit
  nondeterminism declaration and mark the run as non-replayable.

Alternating projections are permitted only as a refusal fallback with explicit
nondeterminism markers and evidence records.

## Forbidden-Regions-First Control
When legality, determinism, or evidence requirements are not satisfied, the
system MUST refuse execution and emit refusal evidence. This is a survivability
control principle, not a performance choice.

## Papas Role
Papas MAY act as a witness, explainer, or development-mode assistant. Papas
MUST NOT authorize collapse, change semantics, or bypass governance gates.

## Non-Claims
This module does not claim experimental physics validity or hardware
performance. It defines software proof obligations only.
