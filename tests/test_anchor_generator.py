from __future__ import annotations

from pathlib import Path

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
