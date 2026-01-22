from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..trace import emit_witness_record


DEFAULT_TIMESTAMP = "1970-01-01T00:00:00Z"
DEFAULT_SCHEDULER_REF = "validator:coupling_topology"
DEFAULT_STAGE = "coupling_validation"


@dataclass(frozen=True)
class CouplingEventBundle:
    event: Dict[str, object]
    witness_record: Dict[str, object]
    entanglement_metadata: Dict[str, object]


def build_coupling_event_from_registry(
    registry: Dict[str, object],
    edge_index: int = 0,
    timestamp: str = DEFAULT_TIMESTAMP,
    scheduler_ref: str = DEFAULT_SCHEDULER_REF,
    stage: str = DEFAULT_STAGE,
    input_payload: Optional[object] = None,
    output_payload: Optional[object] = None,
) -> CouplingEventBundle:
    if not timestamp:
        timestamp = DEFAULT_TIMESTAMP
    edges = registry.get("edges", [])
    projectors = registry.get("projectors", [])
    if not isinstance(edges, list) or not edges:
        raise ValueError("Coupling registry: edges list is required")
    if not isinstance(projectors, list) or not projectors:
        raise ValueError("Coupling registry: projectors list is required")

    edge = edges[edge_index]
    projector_id = edge.get("projector")
    projector = _find_projector(projectors, projector_id)

    operator_name = _coerce_str(edge.get("operator_name"), "coupling_operator")
    sector_src = _coerce_str(edge.get("sector_src"), "unknown")
    sector_dst = _coerce_str(edge.get("sector_dst"), "unknown")
    invariants_checked = edge.get("invariants_checked")
    if not isinstance(invariants_checked, list):
        invariants_checked = []

    input_digest = _digest_payload(input_payload, f"{edge.get('id')}:input")
    output_digest = _digest_payload(output_payload, f"{edge.get('id')}:output")
    projector_versions = _projector_versions(projector)

    event_id = _digest_text(f"{edge.get('id')}|{timestamp}|{operator_name}")
    event_core = {
        "event_id": event_id,
        "timestamp": timestamp,
        "edge_id": _coerce_str(edge.get("id"), "unknown"),
        "sector_src": sector_src,
        "sector_dst": sector_dst,
        "operator_name": operator_name,
        "input_digest": input_digest,
        "output_digest": output_digest,
        "invariants_checked": list(invariants_checked),
        "scheduler_authorization_ref": scheduler_ref,
        "projector_versions": projector_versions,
    }

    event_core_digest = _digest_text(_canonical_json(event_core))

    witness_record = emit_witness_record(
        observer_id="papas",
        stage=stage,
        artifact_digests={"coupling_event": event_core_digest},
        timestamp=timestamp,
        attestation="coupling_event_witness",
    )
    witness_json = _canonical_json(witness_record)
    witness_digest = _digest_text(witness_json)

    entanglement_metadata = _build_entanglement_metadata(edge, projector)
    entanglement_json = _canonical_json(entanglement_metadata)
    entanglement_digest = _digest_text(entanglement_json)

    evidence_artifacts = {
        "coupling_event_core_digest": event_core_digest,
        "papas_witness_record": witness_json,
        "papas_witness_digest": witness_digest,
        "entanglement_metadata": entanglement_json,
        "entanglement_metadata_digest": entanglement_digest,
    }

    event = dict(event_core)
    event["evidence_artifacts"] = evidence_artifacts

    return CouplingEventBundle(
        event=event,
        witness_record=witness_record,
        entanglement_metadata=entanglement_metadata,
    )


def write_event_json(event: Dict[str, object], path: Path) -> None:
    path.write_text(json.dumps(event, indent=2), encoding="utf-8")


def _find_projector(projectors: List[Dict[str, object]], projector_id: Optional[str]) -> Dict[str, object]:
    if not projector_id:
        raise ValueError("Coupling registry: edge missing projector id")
    for projector in projectors:
        if projector.get("id") == projector_id:
            return projector
    raise ValueError(f"Coupling registry: projector '{projector_id}' not found")


def _projector_versions(projector: Dict[str, object]) -> Dict[str, str]:
    projector_id = _coerce_str(projector.get("id"), "unknown")
    version = _coerce_str(projector.get("version"), "unknown")
    return {projector_id: version}


def _build_entanglement_metadata(edge: Dict[str, object], projector: Dict[str, object]) -> Dict[str, object]:
    return {
        "edge_id": _coerce_str(edge.get("id"), "unknown"),
        "sector_src": _coerce_str(edge.get("sector_src"), "unknown"),
        "sector_dst": _coerce_str(edge.get("sector_dst"), "unknown"),
        "operator_name": _coerce_str(edge.get("operator_name"), "coupling_operator"),
        "projector_id": _coerce_str(projector.get("id"), "unknown"),
        "projector_version": _coerce_str(projector.get("version"), "unknown"),
        "symmetric_capable": bool(edge.get("symmetric_capable", False)),
    }


def _canonical_json(data: object) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def _digest_payload(payload: Optional[object], fallback_seed: str) -> str:
    if payload is None:
        return _digest_text(fallback_seed)
    return _digest_text(_canonical_json(payload))


def _digest_text(value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _coerce_str(value: Optional[object], fallback: str) -> str:
    if isinstance(value, str) and value:
        return value
    return fallback
