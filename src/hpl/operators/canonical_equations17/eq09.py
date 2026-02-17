from __future__ import annotations

import hashlib
import json
from typing import Dict


def apply(payload: Dict[str, object]) -> Dict[str, object]:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    spectral_energy = _unit_from_hex(digest[0:16])
    spectral_norm = _unit_from_hex(digest[16:32])
    return {
        "equation_id": "EQ09",
        "equation_label": "deterministic_fourier_observable",
        "equation_version": "canonical_equations17.v1",
        "input_digest": f"sha256:{digest}",
        "spectral_energy": _round(spectral_energy),
        "spectral_norm": _round(spectral_norm),
    }


def _unit_from_hex(value: str) -> float:
    as_int = int(value, 16)
    max_int = (1 << (len(value) * 4)) - 1
    return as_int / max_int if max_int else 0.0


def _round(value: float) -> float:
    return float(f"{value:.8f}")