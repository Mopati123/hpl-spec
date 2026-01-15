# HPL Release & Versioning Policy — v1

## Purpose

This document defines how **HPL specifications and implementations** are versioned,
released, and evolved after the **v1 freeze**.

The policy ensures:
- Predictable evolution
- Backward compatibility guarantees
- Clear separation between spec versions and implementation releases

This document introduces **no new language semantics**.

---

## Normative References

This policy operates under:

- `docs/spec/00_spec_freeze_declaration_v1.md`
- `docs/spec/00b_conformance_checklist_v1.md`
- `docs/spec/00c_conformance_test_mapping_v1.md`
- `docs/spec/00d_certification_report_template_v1.md`
- `docs/spec/00e_implementation_intake_checklist_v1.md`
- `docs/spec/00f_ci_gate_policy_v1.md`

---

## Versioning Model

### Specification Versions

HPL specifications use **semantic versioning**:

MAJOR.MINOR

- **MAJOR**: Breaking changes to language law, IR schema, or axiomatic grammar
- **MINOR**: Backward-compatible extensions or clarifications

Examples:
- `v1.0` — Initial frozen specification
- `v1.1` — Backward-compatible clarifications or additions
- `v2.0` — Breaking semantic changes

---

### Implementation Versions

Implementations may use independent versioning schemes, but MUST declare:
- The **HPL Spec version** they target (e.g., `HPL Spec v1.0`)
- The **conformance level** achieved (Level 0 / 1 / 2)

---

## Compatibility Rules

### Backward-Compatible Changes (MINOR)

Allowed under `v1.x`:
- Additional surface DSL macros (provided they expand into axiomatic core)
- Additional operator registry entries (schema-compliant)
- Clarifications to spec text that do not alter meaning
- Additional non-runtime tooling or diagnostics

Not allowed:
- New axiomatic grammar constructs
- New operator classes
- Changes to IR field meaning or requirements

---

### Breaking Changes (MAJOR)

Require a new MAJOR version (`v2.0`), including:
- Modifications to `02_bnf.md`
- Changes to operator class set `{U, M, Ω, C, I, A}`
- Changes to IR schema that remove or rename fields
- Semantic changes to macro boundary rules

Breaking changes MUST be accompanied by:
- A new spec freeze declaration
- Updated conformance checklist and test mapping

---

## Release Process (Spec)

For any new spec release:

1. Draft changes under a new version identifier.
2. Update or add a **Spec Freeze Declaration** for the new version.
3. Update conformance checklist and mappings if required.
4. Record changes in a release notes document.
5. Declare the new version frozen.

No implementation MAY claim conformance until the new version is frozen.

---

## Release Process (Implementation)

For implementation releases claiming conformance:

1. Run CI gates defined in `00f_ci_gate_policy_v1.md`.
2. Complete a Certification Report for the target spec version.
3. Declare:
   - Target spec version
   - Conformance level
4. Tag or mark the release accordingly.

---

## Deprecation Policy

- Deprecated features MUST be marked in the spec with a target removal version.
- Deprecated features remain valid until the next MAJOR version.
- Implementations MAY warn but MUST NOT reject deprecated constructs prior to removal.

---

## Policy Status

- Applies to: **HPL Spec v1.x**
- Authority: **Specification First**
- Scope: **Specification and Conformance Governance**

Any modification to this policy requires a spec version increment.
