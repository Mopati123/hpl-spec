from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from hpl.audit.coupling_event import build_coupling_event_from_registry, write_event_json


DEFERRED_NOTES = [
    "Rule V1 (illegal cross-sector bypass detection) is deferred in this validator.",
]


def main() -> int:
    args = _parse_args()
    results = []
    all_ok = True

    for path in args.registry_paths:
        registry, load_errors = _load_registry(path)
        errors = list(load_errors)
        if registry:
            errors.extend(validate_coupling_registry_data(registry))
        ok = not errors
        all_ok = all_ok and ok
        results.append({"path": str(path), "ok": ok, "errors": errors})
        status = "PASS" if ok else "FAIL"
        print(f"{status}: {path}")
        for err in errors:
            print(f"  - {err}")

        if ok and registry:
            _emit_event_if_requested(registry, path, args)

    for note in DEFERRED_NOTES:
        print(f"NOTE: {note}")

    summary = {"ok": all_ok, "results": results, "notes": DEFERRED_NOTES}
    print(json.dumps(summary, indent=2))
    return 0 if all_ok else 1


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate coupling topology registries.")
    parser.add_argument("registry_paths", nargs="+", type=Path)
    parser.add_argument("--emit-event", type=Path, help="Write a CouplingEvent artifact.")
    parser.add_argument(
        "--emit-event-dir",
        type=Path,
        help="Write CouplingEvent artifacts into a directory.",
    )
    parser.add_argument("--timestamp", default=None, help="Deterministic timestamp override.")
    return parser.parse_args()


def _emit_event_if_requested(registry: Dict[str, object], path: Path, args: argparse.Namespace) -> None:
    if args.emit_event and args.emit_event_dir:
        raise SystemExit("Use only one of --emit-event or --emit-event-dir.")
    if not args.emit_event and not args.emit_event_dir:
        return

    bundle = build_coupling_event_from_registry(
        registry,
        timestamp=args.timestamp or None,
    )

    if args.emit_event:
        target = args.emit_event
        write_event_json(bundle.event, target)
        return

    if args.emit_event_dir:
        args.emit_event_dir.mkdir(parents=True, exist_ok=True)
        target = args.emit_event_dir / f"{path.stem}.coupling_event.json"
        write_event_json(bundle.event, target)


def _load_registry(path: Path) -> Tuple[Dict[str, object] | None, List[str]]:
    if not path.exists():
        return None, [f"Coupling registry not found: {path}"]

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"Invalid JSON: {exc}"]

    if not isinstance(data, dict):
        return None, ["Coupling registry: expected object at root"]

    return data, []


def validate_coupling_registry_file(path: Path) -> List[str]:
    registry, errors = _load_registry(path)
    if registry:
        errors.extend(validate_coupling_registry_data(registry))
    return errors


def validate_coupling_registry_data(data: Dict[str, object]) -> List[str]:
    errors: List[str] = []

    projectors, projector_errors = _load_projectors(data)
    errors.extend(projector_errors)

    edges, edge_errors = _load_edges(data)
    errors.extend(edge_errors)

    errors.extend(_validate_invocations(data, edges))
    errors.extend(_validate_edge_projectors(edges, projectors))
    errors.extend(_validate_audit_obligations(edges))

    return errors


def _load_projectors(data: Dict) -> Tuple[Dict[str, Dict], List[str]]:
    errors: List[str] = []
    projectors_list = data.get("projectors", [])
    if not isinstance(projectors_list, list):
        return {}, ["Coupling registry: 'projectors' must be a list"]

    projectors: Dict[str, Dict] = {}
    for idx, projector in enumerate(projectors_list):
        if not isinstance(projector, dict):
            errors.append(f"projectors[{idx}]: expected object")
            continue
        projector_id = projector.get("id")
        if not isinstance(projector_id, str) or not projector_id:
            errors.append(f"projectors[{idx}]: missing string id")
            continue
        if projector_id in projectors:
            errors.append(f"projectors[{idx}]: duplicate id '{projector_id}'")
            continue
        _validate_signature(projector, f"projectors[{idx}]", errors)
        projectors[projector_id] = projector

    return projectors, errors


def _load_edges(data: Dict) -> Tuple[List[Dict], List[str]]:
    errors: List[str] = []
    edges_list = data.get("edges", [])
    if not isinstance(edges_list, list):
        return [], ["Coupling registry: 'edges' must be a list"]

    edges: List[Dict] = []
    for idx, edge in enumerate(edges_list):
        if not isinstance(edge, dict):
            errors.append(f"edges[{idx}]: expected object")
            continue
        edge_id = edge.get("id")
        if not isinstance(edge_id, str) or not edge_id:
            errors.append(f"edges[{idx}]: missing string id")
            continue
        _validate_signature(edge, f"edges[{idx}]", errors)
        edges.append(edge)

    return edges, errors


def _validate_signature(entry: Dict, ctx: str, errors: List[str]) -> None:
    domain = entry.get("domain")
    codomain = entry.get("codomain")
    if not isinstance(domain, list) or not all(isinstance(item, str) for item in domain):
        errors.append(f"{ctx}: domain must be a list of strings")
    if not isinstance(codomain, list) or not all(isinstance(item, str) for item in codomain):
        errors.append(f"{ctx}: codomain must be a list of strings")


def _validate_invocations(data: Dict, edges: List[Dict]) -> List[str]:
    errors: List[str] = []
    invocations = data.get("invocations", [])
    if invocations is None:
        return errors
    if not isinstance(invocations, list):
        return ["Coupling registry: 'invocations' must be a list when present"]

    edge_ids = {edge.get("id") for edge in edges}
    for idx, invocation in enumerate(invocations):
        if not isinstance(invocation, dict):
            errors.append(f"invocations[{idx}]: expected object")
            continue
        edge_id = invocation.get("edge_id")
        if not isinstance(edge_id, str) or not edge_id:
            errors.append(f"invocations[{idx}]: missing string edge_id")
            continue
        if edge_id not in edge_ids:
            errors.append(f"invocations[{idx}]: edge_id '{edge_id}' not declared")

    return errors


def _validate_edge_projectors(edges: List[Dict], projectors: Dict[str, Dict]) -> List[str]:
    errors: List[str] = []
    for idx, edge in enumerate(edges):
        projector_id = edge.get("projector")
        if not isinstance(projector_id, str) or not projector_id:
            errors.append(f"edges[{idx}]: missing string projector id")
            continue
        projector = projectors.get(projector_id)
        if projector is None:
            errors.append(f"edges[{idx}]: projector '{projector_id}' not declared")
            continue

        edge_domain = edge.get("domain", [])
        edge_codomain = edge.get("codomain", [])
        proj_domain = projector.get("domain", [])
        proj_codomain = projector.get("codomain", [])
        if sorted(edge_domain) != sorted(proj_domain):
            errors.append(f"edges[{idx}]: domain does not match projector '{projector_id}'")
        if sorted(edge_codomain) != sorted(proj_codomain):
            errors.append(f"edges[{idx}]: codomain does not match projector '{projector_id}'")

    return errors


def _validate_audit_obligations(edges: List[Dict]) -> List[str]:
    errors: List[str] = []
    for idx, edge in enumerate(edges):
        audit = edge.get("audit")
        if not isinstance(audit, dict):
            errors.append(f"edges[{idx}]: missing audit obligation")
            continue
        requires = audit.get("requires")
        if not isinstance(requires, list) or not all(isinstance(item, str) for item in requires):
            errors.append(f"edges[{idx}]: audit.requires must be a list of strings")
            continue
        if "CouplingEvent" not in requires:
            errors.append(f"edges[{idx}]: audit.requires must include 'CouplingEvent'")

    return errors


if __name__ == "__main__":
    raise SystemExit(main())
