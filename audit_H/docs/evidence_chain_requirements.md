# Evidence Chain Requirements (v2.4)

## Required Artifacts
Certified implementations MUST produce the following artifacts:
- CouplingEvent for cross-sector interactions.
- DevChangeEvent for development changes affecting certified artifacts.
- AnchorEvent for each epoch anchor.

## Determinism
Evidence artifacts MUST be deterministic for identical inputs.

## Linking
Evidence artifacts MUST include hash references to the governing epoch anchor.
