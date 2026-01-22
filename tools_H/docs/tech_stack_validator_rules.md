# Tech Stack Validator Rules (v2.4)

## VTS1 - Backend Target Taxonomy
Reject any backend lane declaration that uses targets outside the canonical
list: PYTHON, CYTHON, MOJO, JULIA, QASM.

## VTS2 - Substrate Declaration
If a permitted substrate is used (for example, Polars), it MUST be explicitly
declared in backend lane metadata.

## VTS3 - Evidence Chain Presence
Certified builds MUST include references to CouplingEvent, DevChangeEvent, and
AnchorEvent artifacts.

## VTS4 - Anchor Coverage
Epoch anchors MUST include hashes for backend artifacts and lane metadata.

## VTS5 - Registry-as-Linker Legality
Backend lowering MUST reference only declared operators and coupling edges.
