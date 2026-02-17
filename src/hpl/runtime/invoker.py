from __future__ import annotations

from typing import Dict, List, Optional

from ..operators.canonical_equations17 import apply_eq09, apply_eq15


CANONICAL_EQ09 = "CANONICAL_EQ09"
CANONICAL_EQ15 = "CANONICAL_EQ15"
DEFAULT_OPERATOR_ALLOWLIST = [CANONICAL_EQ09, CANONICAL_EQ15]


def invoke_operator(
    operator_id: str,
    payload: Dict[str, object],
    allowlist: Optional[List[str]] = None,
) -> Dict[str, object]:
    normalized_allowlist = _normalize_allowlist(allowlist)
    normalized_id = str(operator_id).upper()
    if normalized_allowlist and normalized_id not in normalized_allowlist:
        raise PermissionError(f"operator not allowlisted: {normalized_id}")

    if normalized_id == CANONICAL_EQ09:
        return apply_eq09(payload)
    if normalized_id == CANONICAL_EQ15:
        return apply_eq15(payload)
    raise ValueError(f"unknown canonical operator: {normalized_id}")


def _normalize_allowlist(allowlist: Optional[List[str]]) -> List[str]:
    if not allowlist:
        return []
    return sorted({str(item).upper() for item in allowlist if str(item).strip()})