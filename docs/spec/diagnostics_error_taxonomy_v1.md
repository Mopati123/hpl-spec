# HPL Diagnostics Error Taxonomy — v1

## Purpose

This document defines a **tooling-only** taxonomy for normalizing errors.
It does not change language semantics or acceptance rules.

---

## Required Fields

All normalized errors MUST include these keys:

- `code` (string)
- `category` (string)
- `message` (string)
- `location` (object or null)
- `path` (array or null)
- `cause` (string)

---

## Categories and Codes

- `parse` → `PARSE_ERROR`
- `macro` → `MACRO_ERROR`
- `validation` → `VALIDATION_ERROR`
- `ir_schema` → `IR_SCHEMA_ERROR`
- `unknown` → `UNKNOWN_ERROR`

---

## Field Semantics

- `message`: human-readable description, unchanged from the exception.
- `location`: `{line, column}` when available, else null.
- `path`: structural path (list of indexes) when available, else null.
- `cause`: exception class name.

---

## Notes

This taxonomy is **non-normative** and must not alter pass/fail behavior.
