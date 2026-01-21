# Witness Attestation Model (Normative)

## Purpose

Define a witness record for audit evidence. Witness records are evidence
artifacts and do not grant execution authority.

## Required Fields

- observer_id
- stage
- artifact_digests
- timestamp
- attestation

## Optional Fields

- notes

## Constraints

- observer_id MUST be a registered observer identity.
- Witness records do not authorize collapse or execution.
- Witness records are additive and non-semantic.
