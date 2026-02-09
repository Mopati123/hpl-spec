from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from nacl.signing import VerifyKey

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PUBLIC_KEY = ROOT / "config" / "keys" / "ci_ed25519.pub"


def main() -> int:
    args = _parse_args()
    result = verify_anchor(
        bundle_dir=args.bundle_dir.resolve(),
        manifest_path=args.manifest.resolve(),
        leaves_path=(args.leaves or args.manifest.with_name("anchor_leaves.json")).resolve(),
        signature_path=(args.signature or args.manifest.with_suffix(".sig")).resolve(),
        public_key=args.public_key or (DEFAULT_PUBLIC_KEY if DEFAULT_PUBLIC_KEY.exists() else None),
    )
    print(_canonical_json(result))
    return 0


def verify_anchor(
    bundle_dir: Path,
    manifest_path: Path,
    leaves_path: Path,
    signature_path: Path,
    public_key: Optional[Path],
) -> Dict[str, object]:
    errors: List[str] = []
    if not manifest_path.exists():
        return {"ok": False, "errors": [f"manifest not found: {manifest_path}"]}
    if not leaves_path.exists():
        return {"ok": False, "errors": [f"leaves not found: {leaves_path}"]}

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    leaves_payload = json.loads(leaves_path.read_text(encoding="utf-8"))
    inputs = leaves_payload.get("inputs", [])

    computed_leaves = _collect_leaves(bundle_dir, _exclude_names(manifest, leaves_path, signature_path, manifest_path))
    if inputs != computed_leaves:
        errors.append("leaves do not match bundle contents")

    leaves_bytes = _canonical_json({"inputs": computed_leaves, "hash_alg": "sha256", "leaf_rule": _leaf_rule()}).encode("utf-8")
    leaves_digest = _digest_bytes(leaves_bytes)
    if manifest.get("leaves_digest") != leaves_digest:
        errors.append("leaves_digest mismatch")

    computed_root = _build_merkle_root([entry["leaf_hash"] for entry in computed_leaves])
    if manifest.get("merkle_root") != computed_root:
        errors.append("merkle_root mismatch")

    signing = manifest.get("signing", {})
    signature_hex = signing.get("signature")
    payload_digest = signing.get("signed_payload_digest")

    if signature_hex:
        if public_key is None or not public_key.exists():
            errors.append("public key not found for signature verification")
        elif not signature_path.exists():
            errors.append("signature file not found")
        else:
            signature_file = signature_path.read_text(encoding="utf-8").strip()
            if signature_file != signature_hex:
                errors.append("signature file mismatch")
            payload = _canonical_json(_strip_signature(manifest)).encode("utf-8")
            if payload_digest and payload_digest != _digest_bytes(payload):
                errors.append("signed_payload_digest mismatch")
            else:
                ok, sig_errors = _verify_signature(payload, signature_hex, public_key)
                if not ok:
                    errors.extend(sig_errors)

    return {"ok": not errors, "errors": errors, "merkle_root": computed_root}


def _verify_signature(payload: bytes, signature_hex: str, public_key: Path) -> tuple[bool, List[str]]:
    errors: List[str] = []
    try:
        signature = bytes.fromhex(signature_hex)
    except ValueError:
        return False, ["signature is not valid hex"]

    verify_key = VerifyKey(bytes.fromhex(public_key.read_text(encoding="utf-8").strip()))
    try:
        verify_key.verify(payload, signature)
    except Exception:
        errors.append("signature verification failed")
    return not errors, errors


def _strip_signature(manifest: Dict[str, object]) -> Dict[str, object]:
    manifest_core = dict(manifest)
    manifest_core.pop("signing", None)
    return manifest_core


def _exclude_names(
    manifest: Dict[str, object],
    leaves_path: Path,
    signature_path: Path,
    manifest_path: Path,
) -> set[str]:
    excluded = {
        leaves_path.name,
        signature_path.name,
        manifest_path.name,
    }
    if isinstance(manifest.get("leaves_path"), str):
        excluded.add(str(manifest["leaves_path"]))
    return excluded


def _leaf_rule() -> str:
    return "sha256(relpath + ':' + sha256(file_bytes))"


def _collect_leaves(bundle_dir: Path, excluded: set[str]) -> List[Dict[str, object]]:
    files: List[tuple[str, Path]] = []
    for path in bundle_dir.rglob("*"):
        if path.is_dir():
            continue
        relpath = _normalize_relpath(path, bundle_dir)
        if relpath in excluded or relpath.startswith(".git/"):
            continue
        files.append((relpath, path))
    files.sort(key=lambda item: item[0])

    leaves: List[Dict[str, object]] = []
    for relpath, path in files:
        payload = path.read_bytes()
        file_digest = _digest_bytes(payload)
        leaf_hash = _digest_text(f"{relpath}:{file_digest}")
        leaves.append(
            {
                "path": relpath,
                "size": len(payload),
                "sha256": file_digest,
                "leaf_hash": leaf_hash,
            }
        )
    return leaves


def _build_merkle_root(leaf_hashes: Iterable[object]) -> str:
    nodes = [str(item) for item in leaf_hashes]
    nodes = [_strip_prefix(item) for item in nodes]
    if not nodes:
        return _digest_bytes(b"")

    level = nodes[:]
    while len(level) > 1:
        if len(level) % 2 == 1:
            level.append(level[-1])
        next_level: List[str] = []
        for idx in range(0, len(level), 2):
            left = bytes.fromhex(level[idx])
            right = bytes.fromhex(level[idx + 1])
            next_level.append(hashlib.sha256(left + right).hexdigest())
        level = next_level
    return f"sha256:{level[0]}"


def _strip_prefix(value: str) -> str:
    if value.startswith("sha256:"):
        return value.split("sha256:", 1)[1]
    return value


def _normalize_relpath(path: Path, root: Path) -> str:
    rel = path.relative_to(root)
    return rel.as_posix().replace("\\", "/")


def _digest_text(value: str) -> str:
    return _digest_bytes(value.encode("utf-8"))


def _digest_bytes(payload: bytes) -> str:
    digest = hashlib.sha256(payload).hexdigest()
    return f"sha256:{digest}"


def _canonical_json(data: object) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify a Phase-1 anchor manifest.")
    parser.add_argument("bundle_dir", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--leaves", type=Path)
    parser.add_argument("--signature", type=Path)
    parser.add_argument("--public-key", type=Path)
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(main())
