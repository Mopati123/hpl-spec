from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools import phase1_track_a_run


def test_extract_json_line_finds_first_json_object() -> None:
    output = "line one\n{\"ok\":true}\nline two\n{\"ok\":false}\n"
    payload = phase1_track_a_run._extract_json_line(output)
    assert payload == {"ok": True}


def test_validate_reference_folder_name_matches_commit_prefix() -> None:
    phase1_track_a_run._validate_reference_folder_name(
        "machine_a_f06023a", "f06023ac75d7bddb75d3ecb038b5cd5beae80a6b"
    )


def test_validate_reference_folder_name_rejects_mismatch() -> None:
    with pytest.raises(ValueError, match="does not match git_commit"):
        phase1_track_a_run._validate_reference_folder_name(
            "machine_a_d878e95", "f06023ac75d7bddb75d3ecb038b5cd5beae80a6b"
        )


def test_load_reference_contract_requires_git_commit(tmp_path: Path) -> None:
    manifest = tmp_path / "machine_a_f06023a" / "anchor_manifest.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({"leaf_count": 12}), encoding="utf-8")
    with pytest.raises(ValueError, match="missing git_commit"):
        phase1_track_a_run._load_reference_contract(manifest)
