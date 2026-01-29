from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Dict, List, Optional


TRACK_PUBLISH = "A"
TRACK_REGULATOR = "B"
TRACK_SHADOW = "C"


@dataclass(frozen=True)
class MeasurementSelectionResult:
    ok: bool
    selection: Optional[Dict[str, object]]
    errors: List[str]


def build_measurement_selection(
    boundary_conditions: Dict[str, object],
) -> MeasurementSelectionResult:
    if not isinstance(boundary_conditions, dict):
        return MeasurementSelectionResult(False, None, ["boundary_conditions_invalid"])

    candidates: Dict[str, List[str]] = {}
    _add_candidate(candidates, TRACK_REGULATOR, boundary_conditions.get("regulator_request_id"), "regulator_request_id")
    _add_candidate(candidates, TRACK_REGULATOR, boundary_conditions.get("regulator_request"), "regulator_request")
    _add_candidate(candidates, TRACK_PUBLISH, boundary_conditions.get("ci_available"), "ci_available")
    _add_candidate(
        candidates,
        TRACK_SHADOW,
        boundary_conditions.get("market_window_open"),
        "market_window_open",
    )
    risk_mode = str(boundary_conditions.get("risk_mode", "")).lower()
    if risk_mode in {"shadow", "live"}:
        candidates.setdefault(TRACK_SHADOW, []).append(f"risk_mode={risk_mode}")

    tracks = sorted(candidates.keys())
    if not tracks:
        return MeasurementSelectionResult(False, None, ["no_selection"])
    if len(tracks) > 1:
        return MeasurementSelectionResult(
            False,
            None,
            [f"ambiguous_selection={','.join(tracks)}"],
        )

    selected_track = tracks[0]
    reasons = sorted(candidates.get(selected_track, []))
    requested_constraints = boundary_conditions.get("requested_constraints")
    if not isinstance(requested_constraints, dict):
        requested_constraints = {}

    boundary_digest = _digest_text(_canonical_json(boundary_conditions))
    selection_core = {
        "boundary_conditions_digest": boundary_digest,
        "selected_track": selected_track,
        "reasons": reasons,
        "requested_constraints": requested_constraints,
    }
    selection_id = _digest_text(_canonical_json(selection_core))

    selection = {
        "selection_id": selection_id,
        "selected_track": selected_track,
        "reasons": reasons,
        "boundary_conditions_digest": boundary_digest,
        "requested_constraints": requested_constraints,
        "boundary_conditions": boundary_conditions,
    }
    return MeasurementSelectionResult(True, selection, [])


def _add_candidate(
    candidates: Dict[str, List[str]],
    track: str,
    value: object,
    reason: str,
) -> None:
    if value is True or (isinstance(value, str) and value.strip()):
        candidates.setdefault(track, []).append(reason)


def _canonical_json(data: object) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def _digest_text(value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"
