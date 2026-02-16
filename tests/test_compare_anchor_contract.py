from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
TOOL = ROOT / "tools" / "compare_anchor_contract.py"


def _run_compare(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, str(TOOL), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, sort_keys=True, separators=(",", ":")), encoding="utf-8")


def test_compare_anchor_contract_preflight_missing_paths(tmp_path: Path) -> None:
    result = _run_compare(
        [
            "--machine-a-manifest",
            str(tmp_path / "a_manifest.json"),
            "--machine-a-leaves",
            str(tmp_path / "a_leaves.json"),
            "--machine-b-manifest",
            str(tmp_path / "b_manifest.json"),
            "--machine-b-leaves",
            str(tmp_path / "b_leaves.json"),
        ]
    )
    assert result.returncode == 2
    payload = json.loads(result.stdout.strip())
    assert payload["CONTRACT_MATCH"] is False
    assert payload["MERKLE_MATCH"] is False
    assert payload["ROOT_CAUSE"] == "missing reference/candidate anchor artifacts"
    assert len(payload["missing_paths"]) == 4


def test_compare_anchor_contract_match(tmp_path: Path) -> None:
    manifest = {
        "git_commit": "d878e95c4b4adb64a6f080eb8b8fa4dbbd655aaf",
        "leaf_rule": "sha256(relpath + ':' + sha256(file_bytes))",
        "leaf_count": 1,
        "bundle_manifest_digest": "sha256:a",
        "leaves_digest": "sha256:b",
        "merkle_root": "sha256:c",
    }
    leaves = {
        "inputs": [
            {"path": "bundle_manifest.json", "sha256": "sha256:a", "leaf_hash": "sha256:leaf"},
        ]
    }

    a_manifest = tmp_path / "a_manifest.json"
    a_leaves = tmp_path / "a_leaves.json"
    b_manifest = tmp_path / "b_manifest.json"
    b_leaves = tmp_path / "b_leaves.json"
    _write_json(a_manifest, manifest)
    _write_json(a_leaves, leaves)
    _write_json(b_manifest, manifest)
    _write_json(b_leaves, leaves)

    result = _run_compare(
        [
            "--machine-a-manifest",
            str(a_manifest),
            "--machine-a-leaves",
            str(a_leaves),
            "--machine-b-manifest",
            str(b_manifest),
            "--machine-b-leaves",
            str(b_leaves),
        ]
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout.strip())
    assert payload["CONTRACT_MATCH"] is True
    assert payload["MERKLE_MATCH"] is True
