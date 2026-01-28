from __future__ import annotations

import hashlib
import json
from typing import Dict, List


def invert_constraints(witness: Dict[str, object]) -> Dict[str, object]:
    refusal_reasons = witness.get("refusal_reasons", [])
    if isinstance(refusal_reasons, list):
        reasons = sorted(str(reason) for reason in refusal_reasons)
    else:
        reasons = [str(refusal_reasons)]

    proposal = {
        "source_witness_id": witness.get("witness_id"),
        "stage": witness.get("stage"),
        "refusal_reasons": reasons,
        "dual_actions": [
            {"action": "relax", "target": reason} for reason in reasons
        ],
    }
    proposal_id = _digest_text(_canonical_json(proposal))
    proposal["dual_proposal_id"] = proposal_id
    return proposal


def _canonical_json(data: object) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def _digest_text(value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"
