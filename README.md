# hpl-spec - HPL Specification and Governance

This repository is the canonical, frozen specification and governance source
for Hamiltonian Programming Language (HPL) v1 -> v2.1. It is spec-first, with a
partial reference implementation for the Level-1 pipeline and Level-2 tooling.

## What this repo contains

- Spec law and governance artifacts (freeze declarations, SCRs, checklists)
- Sub-Hamiltonians (`*_H`) that define the ontology and constraints
- Level-1 front-end pipeline (parser -> macro -> validator -> IR)
- Level-2 tooling (registry validation, traceability, diagnostics)

## What this repo does NOT contain

- No runtime execution engine or scheduler implementation
- No backend execution runtime

## Quick navigation

- `docs/spec/`: normative specs and freezes
- `docs/audit/`: audit artifacts and walkthroughs
- `docs/publish/`: external overviews
- `src/hpl/`: partial reference implementation (Level-1 + Level-2)
- `_H` folders: spec-only sub-Hamiltonians
