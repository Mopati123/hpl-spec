from __future__ import annotations

from pathlib import Path

import pytest
from nacl.signing import SigningKey

from tools import anchor_generator, verify_anchor


def test_anchor_generator_determinism(tmp_path: Path) -> None:
    bundle_dir = tmp_path / "bundle"
    bundle_dir.mkdir()
    (bundle_dir / "a.txt").write_text("alpha", encoding="utf-8")
    nested = bundle_dir / "nested"
    nested.mkdir()
    (nested / "b.txt").write_text("beta", encoding="utf-8")

    seed_hex = "01" * 32
    key_path = tmp_path / "signing_key.hex"
    key_path.write_text(seed_hex, encoding="utf-8")
    signing_key = SigningKey(bytes.fromhex(seed_hex))
    pub_hex = signing_key.verify_key.encode().hex()
    pub_path = tmp_path / "signing_key.pub"
    pub_path.write_text(pub_hex, encoding="utf-8")

    out_one = tmp_path / "out1"
    out_two = tmp_path / "out2"

    inputs_common = dict(
        bundle_dir=bundle_dir,
        manifest_name="anchor_manifest.json",
        leaves_name="anchor_leaves.json",
        signature_name="anchor_manifest.sig",
        repo="test/repo",
        git_commit="deadbeef",
        challenge_window_mode="blocks",
        challenge_window_value="10",
        challenge_window_chain="testnet",
        challenge_window_policy="P1",
        signing_key=key_path,
        signing_key_env="HPL_CI_ED25519_PRIVATE_KEY",
        public_key=pub_path,
        exclude=(),
    )

    inputs_one = anchor_generator.AnchorInputs(out_dir=out_one, **inputs_common)
    inputs_two = anchor_generator.AnchorInputs(out_dir=out_two, **inputs_common)

    anchor_generator.generate_anchor(inputs_one)
    anchor_generator.generate_anchor(inputs_two)

    manifest_one = (out_one / "anchor_manifest.json").read_text(encoding="utf-8")
    manifest_two = (out_two / "anchor_manifest.json").read_text(encoding="utf-8")
    assert manifest_one == manifest_two

    result = verify_anchor.verify_anchor(
        bundle_dir=bundle_dir,
        manifest_path=out_one / "anchor_manifest.json",
        leaves_path=out_one / "anchor_leaves.json",
        signature_path=out_one / "anchor_manifest.sig",
        public_key=pub_path,
    )
    assert result["ok"] is True


def test_commit_detection_gitdir_file(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    gitdir = tmp_path / "gitdir"
    (gitdir / "refs" / "heads").mkdir(parents=True)
    commit = "f06023ac75d7bddb75d3ecb038b5cd5beae80a6b"

    (repo_root / ".git").write_text("gitdir: ../gitdir\n", encoding="utf-8")
    (gitdir / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    (gitdir / "refs" / "heads" / "main").write_text(f"{commit}\n", encoding="utf-8")

    assert anchor_generator._read_git_commit(repo_root) == commit


def test_requires_git_commit_when_unknown(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".git").write_text("gitdir: missing-gitdir\n", encoding="utf-8")

    with pytest.raises(ValueError, match="unable to determine git_commit; provide --git-commit"):
        anchor_generator._resolve_required_git_commit(None, repo_root)

    explicit = "f06023ac75d7bddb75d3ecb038b5cd5beae80a6b"
    assert anchor_generator._resolve_required_git_commit(explicit, repo_root) == explicit
