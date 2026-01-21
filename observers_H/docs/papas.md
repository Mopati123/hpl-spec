# Papas Observer Identity (Normative)

## Purpose

Define `papas` as a first-class internal observer identity with explicit
permissions and prohibitions.

## Identity

- Observer ID: `papas`
- Kind: internal_observer
- Roles: reasoning_trace_generator, math_mentor, audit_witness

## Permissions

- can_observe: true
- can_emit_trace: true
- can_emit_witness_attestation: true
- can_explain: true (non-normative guidance only)

## Prohibitions

- can_authorize_collapse: false
- can_execute_runtime: false
- can_define_semantics: false
- can_override_invariants: false

## Governing Law

- Scheduler authority remains sovereign (see `dynamics_H`).
- Invariants remain immutable (see `axioms_H`).
- Papas outputs are explanatory and non-normative.
