from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional


CONTRACT_FIELDS = [
    "git_commit",
    "leaf_rule",
    "leaf_count",
    "bundle_manifest_digest",
    "leaves_digest",
]


def _load_json(path: Path) -> Dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _emit_input_error(missing_paths: List[str]) -> int:
    output = {
        "CONTRACT_MATCH": False,
        "MERKLE_MATCH": False,
        "ROOT_CAUSE": "missing reference/candidate anchor artifacts",
        "NEXT_ACTION": "Provide existing manifest/leaves paths for both machines before comparison",
        "missing_paths": missing_paths,
    }
    print(json.dumps(output, sort_keys=True, separators=(",", ":")))
    return 2


def _contract(manifest: Dict[str, object]) -> Dict[str, object]:
    return {
        "git_commit": manifest.get("git_commit"),
        "leaf_rule": manifest.get("leaf_rule"),
        "leaf_count": manifest.get("leaf_count"),
        "bundle_manifest_digest": manifest.get("bundle_manifest_digest"),
        "leaves_digest": manifest.get("leaves_digest"),
        "merkle_root": manifest.get("merkle_root"),
    }


def _first_divergent_leaf(
    a_leaves: List[Dict[str, object]], b_leaves: List[Dict[str, object]]
) -> Optional[Dict[str, object]]:
    limit = min(len(a_leaves), len(b_leaves))
    for idx in range(limit):
        a = a_leaves[idx]
        b = b_leaves[idx]
        if a.get("path") != b.get("path") or a.get("leaf_hash") != b.get("leaf_hash"):
            return {
                "index": idx,
                "machine_a": {
                    "relpath": a.get("path"),
                    "file_hash": a.get("sha256"),
                    "leaf_hash": a.get("leaf_hash"),
                },
                "machine_b": {
                    "relpath": b.get("path"),
                    "file_hash": b.get("sha256"),
                    "leaf_hash": b.get("leaf_hash"),
                },
            }
    if len(a_leaves) != len(b_leaves):
        return {
            "index": limit,
            "machine_a": {
                "relpath": a_leaves[limit].get("path") if len(a_leaves) > limit else None,
                "file_hash": a_leaves[limit].get("sha256") if len(a_leaves) > limit else None,
                "leaf_hash": a_leaves[limit].get("leaf_hash") if len(a_leaves) > limit else None,
            },
            "machine_b": {
                "relpath": b_leaves[limit].get("path") if len(b_leaves) > limit else None,
                "file_hash": b_leaves[limit].get("sha256") if len(b_leaves) > limit else None,
                "leaf_hash": b_leaves[limit].get("leaf_hash") if len(b_leaves) > limit else None,
            },
        }
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare two anchor contract states.")
    parser.add_argument("--machine-a-manifest", type=Path, required=True)
    parser.add_argument("--machine-a-leaves", type=Path, required=True)
    parser.add_argument("--machine-b-manifest", type=Path, required=True)
    parser.add_argument("--machine-b-leaves", type=Path, required=True)
    args = parser.parse_args()

    required_paths = [
        args.machine_a_manifest,
        args.machine_a_leaves,
        args.machine_b_manifest,
        args.machine_b_leaves,
    ]
    missing_paths = [str(path) for path in required_paths if not path.exists()]
    if missing_paths:
        return _emit_input_error(missing_paths)

    a_manifest = _load_json(args.machine_a_manifest)
    b_manifest = _load_json(args.machine_b_manifest)
    a_contract = _contract(a_manifest)
    b_contract = _contract(b_manifest)

    contract_match = all(a_contract[field] == b_contract[field] for field in CONTRACT_FIELDS)
    merkle_match = False
    root_cause = "none"
    next_action = "none"
    first_divergent_leaf = None

    if not contract_match:
        root_cause = "Reference anchor is from a different contract state"
        next_action = "Align commit/rule/leaf set before comparing merkle"
        output = {
            "machine_a_contract": a_contract,
            "machine_b_contract": b_contract,
            "CONTRACT_MATCH": False,
            "MERKLE_MATCH": False,
            "ROOT_CAUSE": root_cause,
            "NEXT_ACTION": next_action,
        }
        print(json.dumps(output, sort_keys=True, separators=(",", ":")))
        print("Reference anchor is from a different contract state. Refusing comparison.")
        return 1

    merkle_match = a_contract["merkle_root"] == b_contract["merkle_root"]
    if merkle_match:
        root_cause = "contract matched and merkle matched"
        next_action = "Track A green"
    else:
        root_cause = "contract matched, merkle mismatched"
        next_action = "Run deterministic leaf diff"
        a_leaves = _load_json(args.machine_a_leaves).get("inputs", [])
        b_leaves = _load_json(args.machine_b_leaves).get("inputs", [])
        if isinstance(a_leaves, list) and isinstance(b_leaves, list):
            first_divergent_leaf = _first_divergent_leaf(a_leaves, b_leaves)

    output = {
        "machine_a_contract": a_contract,
        "machine_b_contract": b_contract,
        "CONTRACT_MATCH": contract_match,
        "MERKLE_MATCH": merkle_match,
        "ROOT_CAUSE": root_cause,
        "NEXT_ACTION": next_action,
        "first_divergent_leaf": first_divergent_leaf,
    }
    print(json.dumps(output, sort_keys=True, separators=(",", ":")))
    return 0 if merkle_match else 1


if __name__ == "__main__":
    raise SystemExit(main())
