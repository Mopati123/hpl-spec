# Anchor Event Schema (v2.3)

An AnchorEvent is the audit artifact that records epoch anchoring.

Required fields:
- epoch_id
- timestamp_utc
- git_commit
- schema_hashes
- registry_hashes
- tooling_hashes
- callgraph_hash
- scheduler_contract_hash
- signatures

Anchors MAY include witness attestations as evidence only.
