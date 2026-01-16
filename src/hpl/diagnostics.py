"""Diagnostics normalization (tooling-only)."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from .errors import ParseError, MacroExpansionError, ValidationError


CATEGORY_CODES = {
    "parse": "PARSE_ERROR",
    "macro": "MACRO_ERROR",
    "validation": "VALIDATION_ERROR",
    "ir_schema": "IR_SCHEMA_ERROR",
    "unknown": "UNKNOWN_ERROR",
}


def normalize_error(
    exc: Exception,
    category_override: Optional[str] = None,
    code_override: Optional[str] = None,
) -> Dict[str, Any]:
    category = category_override or _category_for_exception(exc)
    code = code_override or CATEGORY_CODES.get(category, CATEGORY_CODES["unknown"])
    message = getattr(exc, "message", str(exc))

    location = None
    if hasattr(exc, "location") and exc.location:
        location = {"line": exc.location.line, "column": exc.location.column}

    path = getattr(exc, "path", None)

    return {
        "code": code,
        "category": category,
        "message": message,
        "location": location,
        "path": path,
        "cause": exc.__class__.__name__,
    }


def format_error_json(
    exc: Exception,
    category_override: Optional[str] = None,
    code_override: Optional[str] = None,
) -> str:
    payload = normalize_error(exc, category_override, code_override)
    return json.dumps(payload, sort_keys=True)


def _category_for_exception(exc: Exception) -> str:
    if isinstance(exc, ParseError):
        return "parse"
    if isinstance(exc, MacroExpansionError):
        return "macro"
    if isinstance(exc, ValidationError):
        return "validation"
    return "unknown"
