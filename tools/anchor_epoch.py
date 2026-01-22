from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = ROOT / "src"

import sys

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from hpl.trace import emit_witness_record


DEFAULT_TIMESTAMP = "1970-01-01T00:00:00Z"
DEFAULT_EPOCH_ID = "epoch-0"


SCHEMA_FILES = [
    Path("docs/spec/04_ir_schema.json"),
    Path("docs/spec/06_operator_registry_schema.json"),
    Path("audit_H/manifests/trace_schema.json"),
    Path("audit_H/manifests/coupling_event_manifest.yaml"),
]

TOOL_FILES = [
    Path("tools/validate_ir_schema.py"),
    Path("tools/validate_operator_registries.py"),
    Path("tools/validate_observer_registry.py"),
    Path("tools/validate_coupling_topology.py"),
    Path("tools/ci_gate_spec_integrity.py"),
    Path("tools/ci_gate_prohibited_behavior.py"),
]

SCHEDULER_SPEC = Path("docs/spec/scr_level3_scheduler_model.md")


def main() -> int:
    args = _parse_args()
    anchor = build_epoch_anchor(
        epoch_id=args.epoch_id,
        timestamp=args.timestamp,
        git_commit=args.git_commit,
        root=args.root,
        emit_witness=args.emit_witness,
    )

    output = _anchor_to_json(anchor, pretty=args.pretty)
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output)
    return 0


def build_epoch_anchor(
    epoch_id: str,
    timestamp: Optional[str],
    git_commit: Optional[str],
    root: Path = ROOT,
    emit_witness: bool = False,
) -> Dict[str, object]:
    epoch_id = epoch_id or DEFAULT_EPOCH_ID
    timestamp = timestamp or DEFAULT_TIMESTAMP

    commit = git_commit or _resolve_git_commit(root)
    notes: List[str] = []
    if commit is None:
        commit = "unknown"
        notes.append("git_commit unavailable; set to 'unknown'")

    schema_hashes = _hash_files([root / path for path in SCHEMA_FILES], root)
    registry_paths = _collect_registry_paths(root)
    registry_hashes = _hash_files(registry_paths, root)
    tooling_hashes = _hash_files([root / path for path in TOOL_FILES], root)

    callgraph_hash, callgraph_note = _compute_callgraph_hash(registry_paths)
    if callgraph_note:
        notes.append(callgraph_note)

    scheduler_hash, scheduler_note = _scheduler_contract_hash(root)
    if scheduler_note:
        notes.append(scheduler_note)

    anchor: Dict[str, object] = {
        "epoch_id": epoch_id,
        "timestamp_utc": timestamp,
        "git_commit": commit,
        "schema_hashes": schema_hashes,
        "registry_hashes": registry_hashes,
        "tooling_hashes": tooling_hashes,
        "callgraph_hash": callgraph_hash,
        "scheduler_contract_hash": scheduler_hash,
        "signatures": [],
    }

    if notes:
        anchor["notes"] = list(notes)

    if emit_witness:
        witness_record = emit_witness_record(
            observer_id="papas",
            stage="epoch_anchor",
            artifact_digests={"epoch_anchor": _digest_text(_canonical_json(anchor))},
            timestamp=timestamp,
            attestation="epoch_anchor_witness",
        )
        witness_digest = _digest_text(_canonical_json(witness_record))
        anchor["papas_witness_record"] = witness_record
        anchor["papas_witness_digest"] = witness_digest

    return anchor


def collect_required_paths(root: Path = ROOT) -> Dict[str, List[Path]]:
    return {
        "schemas": [root / path for path in SCHEMA_FILES],
        "registries": _collect_registry_paths(root),
        "tooling": [root / path for path in TOOL_FILES],
        "scheduler_spec": [root / SCHEDULER_SPEC] if (root / SCHEDULER_SPEC).exists() else [],
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate an epoch anchor JSON artifact.")
    parser.add_argument("--epoch-id", default=DEFAULT_EPOCH_ID)
    parser.add_argument("--timestamp", default=DEFAULT_TIMESTAMP)
    parser.add_argument("--git-commit")
    parser.add_argument("--emit-witness", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--root", type=Path, default=ROOT)
    return parser.parse_args()


def _resolve_git_commit(root: Path) -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
            cwd=root,
        )
        if result.returncode != 0:
            return None
        return result.stdout.strip() or None
    except OSError:
        return None


def _hash_files(paths: Iterable[Path], root: Path) -> Dict[str, str]:
    hashes: Dict[str, str] = {}
    for path in sorted(paths):
        if not path.exists():
            raise FileNotFoundError(f"Required file not found: {path}")
        rel = str(path.relative_to(root)).replace("\\", "/")
        hashes[rel] = _hash_bytes(path.read_bytes())
    return hashes


def _collect_registry_paths(root: Path) -> List[Path]:
    registries = []
    for folder in root.iterdir():
        if folder.is_dir() and folder.name.endswith("_H"):
            candidate = folder / "operators" / "registry.json"
            if candidate.exists():
                registries.append(candidate)
    return sorted(registries)


def _compute_callgraph_hash(registry_paths: List[Path]) -> Tuple[str, Optional[str]]:
    edges: List[Dict[str, str]] = []
    for path in registry_paths:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        for edge in data.get("edges", []) if isinstance(data, dict) else []:
            if isinstance(edge, dict) and edge.get("id"):
                edges.append({"edge_id": str(edge.get("id"))})

    if not edges:
        placeholder_hash = _digest_text(_canonical_json([]))
        return placeholder_hash, "callgraph_hash computed from empty edge list placeholder"

    edges_sorted = sorted(edges, key=lambda item: item["edge_id"])
    return _digest_text(_canonical_json(edges_sorted)), None


def _scheduler_contract_hash(root: Path) -> Tuple[Optional[str], Optional[str]]:
    path = root / SCHEDULER_SPEC
    if not path.exists():
        return None, "scheduler_contract_hash unavailable; scheduler spec not found"
    return _hash_bytes(path.read_bytes()), None


def _hash_bytes(payload: bytes) -> str:
    digest = hashlib.sha256(payload).hexdigest()
    return f"sha256:{digest}"


def _digest_text(text: str) -> str:
    return _hash_bytes(text.encode("utf-8"))


def _canonical_json(data: object) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def _anchor_to_json(anchor: Dict[str, object], pretty: bool = False) -> str:
    if pretty:
        return json.dumps(anchor, sort_keys=True, indent=2)
    return _canonical_json(anchor)


if __name__ == "__main__":
    raise SystemExit(main())
