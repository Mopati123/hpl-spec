# CouplingEvent Schema (v2.2)

A CouplingEvent is a mandatory audit artifact for every cross-sector interaction.

Required fields:
- event_id
- timestamp
- edge_id
- sector_src
- sector_dst
- operator_name
- input_digest
- output_digest
- invariants_checked
- scheduler_authorization_ref
- projector_versions
- evidence_artifacts

CouplingEvents MUST support deterministic replay at the semantic level.
