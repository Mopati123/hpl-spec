# Conformance Restoration Patch — 2026-01-15

## Summary

A validator update was applied to enforce rejection of surface symbols post-expansion,
supporting Level 1 conformance requirements (L1.11 and L1.12).

## Scope

- File: `src/hpl/axioms/validator.py`
- Change: reject residual surface symbols and emit structured errors with a path

## Reason

Level-1 test `TEST_L1_VALIDATOR_NO_SURFACE_FORMS` initially failed. The patch restores
conformance by ensuring surface constructs cannot pass axiomatic validation.
