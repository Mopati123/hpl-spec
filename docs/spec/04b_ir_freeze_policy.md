# IR Freeze Policy (v1)

This document defines compatibility rules for the HPL IR schema.

## Policy

1. IR v1 is frozen; additions must be backward compatible.
2. Removals or renames require a version bump.
3. Unknown fields are forbidden.

## Bootstrap Allowance

Implementations MAY default `cls` to `C` only for surface-derived operators that have
not yet been classified. This allowance MUST be removed once operator classification
rules or registry annotations are frozen as normative specification.

## Errata

Erratum: enum value `?` was corrected to `Ω` to match the operator algebra. This is a
normative correction and does not constitute a breaking change; it restores intended
semantics.
