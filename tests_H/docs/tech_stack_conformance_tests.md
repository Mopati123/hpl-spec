# Tech Stack Conformance Tests (v2.4)

Required conformance tests include:
1. Backend lane declarations use only canonical targets.
2. Substrate usage (for example, Polars) is explicitly declared.
3. Evidence chain references CouplingEvent, DevChangeEvent, and AnchorEvent.
4. Epoch anchors include backend artifacts and lane metadata hashes.
5. Backend lowering references only declared operators and coupling edges.
6. Refusal evidence is emitted when determinism or legality cannot be proven.
