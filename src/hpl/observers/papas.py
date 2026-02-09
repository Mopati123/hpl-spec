"""Papas observer report builder (no collapse authority)."""

from __future__ import annotations

import hashlib
import json
from typing import Dict, Iterable, List, Optional

from ..audit.constraint_inversion import invert_constraints


def is_enabled(observers: Optional[Iterable[str]]) -> bool:
    if observers is None:
        return True
    return any(str(observer).lower() == "papas" for observer in observers)


def build_papas_report(
    witness: Dict[str, object],
    allow_dual_proposal: bool = False,
) -> Dict[str, object]:
    witness_id = str(witness.get("witness_id", ""))
    stage = str(witness.get("stage", "unknown"))
    refusal_reasons = witness.get("refusal_reasons", [])
    reasons = _normalize_reasons(refusal_reasons)
    summary = "refusal_reasons:" + ",".join(reasons) if reasons else "refusal_reasons:none"

    report: Dict[str, object] = {
        "observer_id": "papas",
        "witness_id": witness_id,
        "stage": stage,
        "refusal_reasons": reasons,
        "summary": summary,
    }

    if allow_dual_proposal:
        report["dual_proposal"] = invert_constraints(witness)

    report_id = _digest_text(_canonical_json(report))
    return {"report_id": report_id, **report}


def _normalize_reasons(refusal_reasons: object) -> List[str]:
    if isinstance(refusal_reasons, list):
        return sorted(str(reason) for reason in refusal_reasons)
    if refusal_reasons is None:
        return []
    return [str(refusal_reasons)]


def _canonical_json(data: object) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def _digest_text(value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"
