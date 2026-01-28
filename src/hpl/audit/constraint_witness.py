from __future__ import annotations

import hashlib
import json
from typing import Dict, List, Optional


DEFAULT_OBSERVER = "papas"


def build_constraint_witness(
    stage: str,
    refusal_reasons: List[str],
    artifact_digests: Dict[str, str],
    observer_id: str = DEFAULT_OBSERVER,
    timestamp: Optional[str] = None,
) -> Dict[str, object]:
    reasons = sorted(str(reason) for reason in refusal_reasons)
    core = {
        "stage": stage,
        "observer_id": observer_id,
        "refusal_reasons": reasons,
        "artifact_digests": dict(artifact_digests),
    }
    witness_id = _digest_text(_canonical_json(core))

    record: Dict[str, object] = {
        "witness_id": witness_id,
        **core,
    }
    if timestamp is not None:
        record["timestamp"] = timestamp
    return record


def _canonical_json(data: object) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def _digest_text(value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"
