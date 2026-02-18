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


def _make_manifest(git_commit: str) -> dict[str, object]:
    return {
        "git_commit": git_commit,
        "leaf_rule": "sha256(relpath + ':' + sha256(file_bytes))",
        "leaf_count": 1,
        "bundle_manifest_digest": "sha256:a",
        "leaves_digest": "sha256:b",
        "merkle_root": "sha256:c",
    }


def _make_leaves() -> dict[str, object]:
    return {
        "inputs": [
            {"path": "bundle_manifest.json", "sha256": "sha256:a", "leaf_hash": "sha256:leaf"},
        ]
    }


def _run_payload(a_manifest: Path, a_leaves: Path, b_manifest: Path, b_leaves: Path) -> tuple[int, dict[str, object]]:
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
    return result.returncode, json.loads(result.stdout.strip())


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


def test_compare_anchor_contract_match() -> None:
    ref_manifest = ROOT / "refs" / "io_shadow_machine_a" / "anchor_manifest.json"
    ref_leaves = ROOT / "refs" / "io_shadow_machine_a" / "anchor_leaves.json"
    cand_manifest = ROOT / "artifacts" / "phase1" / "trading_io_shadow" / "run_B" / "anchor" / "anchor_manifest.json"
    cand_leaves = ROOT / "artifacts" / "phase1" / "trading_io_shadow" / "run_B" / "anchor" / "anchor_leaves.json"
    if not (ref_manifest.exists() and ref_leaves.exists() and cand_manifest.exists() and cand_leaves.exists()):
        return

    code, payload = _run_payload(ref_manifest, ref_leaves, cand_manifest, cand_leaves)
    assert code == 0
    assert payload["CONTRACT_MATCH"] is True
    assert payload["MERKLE_MATCH"] is True


def test_git_commit_short_vs_full_prefix_passes(tmp_path: Path) -> None:
    leaves = _make_leaves()
    a_manifest = tmp_path / "a_manifest.json"
    b_manifest = tmp_path / "b_manifest.json"
    a_leaves = tmp_path / "a_leaves.json"
    b_leaves = tmp_path / "b_leaves.json"
    _write_json(a_manifest, _make_manifest("2436f81"))
    _write_json(b_manifest, _make_manifest("2436f81e0b8156161e6545d2c80e9de63671e029"))
    _write_json(a_leaves, leaves)
    _write_json(b_leaves, leaves)

    code, payload = _run_payload(a_manifest, a_leaves, b_manifest, b_leaves)
    assert code == 0
    assert payload["CONTRACT_MATCH"] is True
    assert payload["MERKLE_MATCH"] is True


def test_git_commit_non_prefix_fails(tmp_path: Path) -> None:
    leaves = _make_leaves()
    a_manifest = tmp_path / "a_manifest.json"
    b_manifest = tmp_path / "b_manifest.json"
    a_leaves = tmp_path / "a_leaves.json"
    b_leaves = tmp_path / "b_leaves.json"
    _write_json(a_manifest, _make_manifest("2436f81"))
    _write_json(b_manifest, _make_manifest("abcdef1e0b8156161e6545d2c80e9de63671e029"))
    _write_json(a_leaves, leaves)
    _write_json(b_leaves, leaves)

    code, payload = _run_payload(a_manifest, a_leaves, b_manifest, b_leaves)
    assert code == 1
    assert payload["CONTRACT_MATCH"] is False
    assert payload["MERKLE_MATCH"] is False
    assert "git_commit" in payload["mismatched_fields"]


def test_git_commit_case_insensitive_passes(tmp_path: Path) -> None:
    leaves = _make_leaves()
    a_manifest = tmp_path / "a_manifest.json"
    b_manifest = tmp_path / "b_manifest.json"
    a_leaves = tmp_path / "a_leaves.json"
    b_leaves = tmp_path / "b_leaves.json"
    _write_json(a_manifest, _make_manifest("2436F81E0B8156161E6545D2C80E9DE63671E029"))
    _write_json(b_manifest, _make_manifest("2436f81e0b8156161e6545d2c80e9de63671e029"))
    _write_json(a_leaves, leaves)
    _write_json(b_leaves, leaves)

    code, payload = _run_payload(a_manifest, a_leaves, b_manifest, b_leaves)
    assert code == 0
    assert payload["CONTRACT_MATCH"] is True
    assert payload["MERKLE_MATCH"] is True


def test_git_commit_too_short_is_strict(tmp_path: Path) -> None:
    leaves = _make_leaves()
    a_manifest = tmp_path / "a_manifest.json"
    b_manifest = tmp_path / "b_manifest.json"
    a_leaves = tmp_path / "a_leaves.json"
    b_leaves = tmp_path / "b_leaves.json"
    _write_json(a_manifest, _make_manifest("2436f8"))
    _write_json(b_manifest, _make_manifest("2436f81e0b8156161e6545d2c80e9de63671e029"))
    _write_json(a_leaves, leaves)
    _write_json(b_leaves, leaves)

    code, payload = _run_payload(a_manifest, a_leaves, b_manifest, b_leaves)
    assert code == 1
    assert payload["CONTRACT_MATCH"] is False
    assert payload["MERKLE_MATCH"] is False
    assert "git_commit" in payload["mismatched_fields"]
