from __future__ import annotations

import hashlib
import json
from typing import Dict


def apply(payload: Dict[str, object]) -> Dict[str, object]:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    entropy_proxy = _unit_from_hex(digest[0:16])
    threshold = float(payload.get("entropy_threshold", 0.95))
    ok = entropy_proxy <= threshold
    admissibility_certificate = {
        "ok": ok,
        "threshold": _round(threshold),
        "comparator": "lte",
        "entropy_proxy": _round(entropy_proxy),
    }
    return {
        "equation_id": "EQ15",
        "equation_label": "deterministic_entropy_observable",
        "equation_version": "canonical_equations17.v1",
        "input_digest": f"sha256:{digest}",
        "entropy_proxy": _round(entropy_proxy),
        "admissibility_certificate": admissibility_certificate,
    }


def _unit_from_hex(value: str) -> float:
    as_int = int(value, 16)
    max_int = (1 << (len(value) * 4)) - 1
    return as_int / max_int if max_int else 0.0


def _round(value: float) -> float:
    return float(f"{value:.8f}")