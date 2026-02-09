from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Dict, Iterable, List, Optional, Tuple

from nacl.signing import SigningKey

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PUBLIC_KEY = ROOT / "config" / "keys" / "ci_ed25519.pub"


@dataclass(frozen=True)
class AnchorInputs:
    bundle_dir: Path
    out_dir: Path
    manifest_name: str
    leaves_name: str
    signature_name: str
    repo: Optional[str]
    git_commit: Optional[str]
    challenge_window_mode: str
    challenge_window_value: str
    challenge_window_chain: str
    challenge_window_policy: str
    signing_key: Optional[Path]
    signing_key_env: str
    public_key: Optional[Path]
    exclude: Tuple[str, ...]


def main() -> int:
    args = _parse_args()
    inputs = AnchorInputs(
        bundle_dir=args.bundle_dir.resolve(),
        out_dir=(args.out_dir or args.bundle_dir).resolve(),
        manifest_name=args.manifest_name,
        leaves_name=args.leaves_name,
        signature_name=args.signature_name,
        repo=args.repo,
        git_commit=args.git_commit or _read_git_commit(args.repo_root),
        challenge_window_mode=args.challenge_window_mode,
        challenge_window_value=str(args.challenge_window_value),
        challenge_window_chain=args.challenge_window_chain,
        challenge_window_policy=args.challenge_window_policy,
        signing_key=args.signing_key,
        signing_key_env=args.signing_key_env,
        public_key=args.public_key or (DEFAULT_PUBLIC_KEY if DEFAULT_PUBLIC_KEY.exists() else None),
        exclude=tuple(args.exclude or ()),
    )
    result = generate_anchor(inputs)
    print(_canonical_json(result))
    return 0


def generate_anchor(inputs: AnchorInputs) -> Dict[str, object]:
    inputs.out_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = inputs.out_dir / inputs.manifest_name
    leaves_path = inputs.out_dir / inputs.leaves_name
    signature_path = inputs.out_dir / inputs.signature_name

    excluded = set(inputs.exclude)
    excluded.update(
        {
            inputs.manifest_name,
            inputs.leaves_name,
            inputs.signature_name,
        }
    )

    leaves = _collect_leaves(inputs.bundle_dir, excluded)
    leaves_payload = {"inputs": leaves, "hash_alg": "sha256", "leaf_rule": _leaf_rule()}
    leaves_bytes = _canonical_json(leaves_payload).encode("utf-8")
    leaves_path.write_text(leaves_bytes.decode("utf-8"), encoding="utf-8")
    leaves_digest = _digest_bytes(leaves_bytes)

    leaf_hashes = [entry["leaf_hash"] for entry in leaves]
    merkle_root = _build_merkle_root(leaf_hashes)

    bundle_id, bundle_manifest_digest = _bundle_metadata(inputs.bundle_dir)
    manifest_core = _drop_none(
        {
            "repo": inputs.repo,
            "git_commit": inputs.git_commit,
            "hash_alg": "sha256",
            "leaf_rule": _leaf_rule(),
            "leaves_path": leaves_path.name,
            "leaves_digest": leaves_digest,
            "leaf_count": len(leaves),
            "merkle_root": merkle_root,
            "bundle_id": bundle_id,
            "bundle_manifest_digest": bundle_manifest_digest,
            "challenge_window": {
                "mode": inputs.challenge_window_mode,
                "value": inputs.challenge_window_value,
                "chain": inputs.challenge_window_chain,
                "policy_id": inputs.challenge_window_policy,
            },
        }
    )

    payload = _canonical_json(manifest_core).encode("utf-8")
    payload_digest = _digest_bytes(payload)
    signature_hex = None
    public_key_hex = _read_hex(inputs.public_key) if inputs.public_key else None

    if inputs.signing_key or os.environ.get(inputs.signing_key_env, "").strip():
        signing_key = _load_signing_key(inputs.signing_key, inputs.signing_key_env)
        signature = signing_key.sign(payload).signature
        signature_hex = signature.hex()
        signature_path.write_text(signature_hex, encoding="utf-8")

    signing = _drop_none(
        {
            "alg": "ed25519",
            "public_key": public_key_hex,
            "signature": signature_hex,
            "signed_payload_digest": payload_digest,
            "signature_path": signature_path.name if signature_hex else None,
        }
    )

    manifest = dict(manifest_core)
    manifest["signing"] = signing
    manifest_bytes = _canonical_json(manifest).encode("utf-8")
    manifest_path.write_text(manifest_bytes.decode("utf-8"), encoding="utf-8")

    return _drop_none(
        {
            "ok": True,
            "bundle_dir": inputs.bundle_dir.as_posix(),
            "manifest_path": str(manifest_path),
            "leaves_path": str(leaves_path),
            "signature_path": str(signature_path) if signature_hex else None,
            "merkle_root": merkle_root,
            "leaf_count": len(leaves),
        }
    )


def _leaf_rule() -> str:
    return "sha256(relpath + ':' + sha256(file_bytes))"


def _bundle_metadata(bundle_dir: Path) -> Tuple[Optional[str], Optional[str]]:
    manifest_path = bundle_dir / "bundle_manifest.json"
    if not manifest_path.exists():
        return None, None
    payload = manifest_path.read_bytes()
    digest = _digest_bytes(payload)
    try:
        data = json.loads(payload.decode("utf-8"))
    except json.JSONDecodeError:
        return None, digest
    bundle_id = data.get("bundle_id")
    return str(bundle_id) if bundle_id else None, digest


def _collect_leaves(bundle_dir: Path, excluded: set[str]) -> List[Dict[str, object]]:
    files: List[Tuple[str, Path]] = []
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
    return PurePosixPath(rel.as_posix()).as_posix()


def _digest_text(value: str) -> str:
    return _digest_bytes(value.encode("utf-8"))


def _digest_bytes(payload: bytes) -> str:
    digest = hashlib.sha256(payload).hexdigest()
    return f"sha256:{digest}"


def _canonical_json(data: object) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _drop_none(data: Dict[str, object]) -> Dict[str, object]:
    return {key: value for key, value in data.items() if value is not None}


def _load_signing_key(path: Optional[Path], env_var: str) -> SigningKey:
    key_hex = _read_hex(path) if path else os.environ.get(env_var, "").strip()
    if not key_hex:
        raise ValueError(f"missing signing key; provide --signing-key or set {env_var}")
    key_bytes = bytes.fromhex(key_hex)
    if len(key_bytes) != 32:
        raise ValueError("signing key seed must be 32 bytes (64 hex chars)")
    return SigningKey(key_bytes)


def _read_hex(path: Optional[Path]) -> Optional[str]:
    if path is None or not path.exists():
        return None
    return path.read_text(encoding="utf-8").strip()


def _read_git_commit(repo_root: Optional[Path]) -> Optional[str]:
    if repo_root is None:
        return None
    git_dir = repo_root / ".git"
    head_path = git_dir / "HEAD"
    if not head_path.exists():
        return None
    head = head_path.read_text(encoding="utf-8").strip()
    if head.startswith("ref:"):
        ref = head.split("ref:", 1)[1].strip()
        ref_path = git_dir / ref
        if ref_path.exists():
            return ref_path.read_text(encoding="utf-8").strip()
        packed = git_dir / "packed-refs"
        if packed.exists():
            for line in packed.read_text(encoding="utf-8").splitlines():
                if line.startswith("#") or line.startswith("^"):
                    continue
                sha, ref_name = line.split(" ", 1)
                if ref_name.strip() == ref:
                    return sha.strip()
        return None
    return head or None


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a deterministic anchor manifest.")
    parser.add_argument("bundle_dir", type=Path)
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--manifest-name", default="anchor_manifest.json")
    parser.add_argument("--leaves-name", default="anchor_leaves.json")
    parser.add_argument("--signature-name", default="anchor_manifest.sig")
    parser.add_argument("--repo")
    parser.add_argument("--git-commit")
    parser.add_argument("--challenge-window-mode", default="blocks")
    parser.add_argument("--challenge-window-value", default="0")
    parser.add_argument("--challenge-window-chain", default="unspecified")
    parser.add_argument("--challenge-window-policy", default="unspecified")
    parser.add_argument("--signing-key", type=Path)
    parser.add_argument(
        "--signing-key-env",
        default="HPL_CI_ED25519_PRIVATE_KEY",
        help="Environment variable containing hex seed for signing key",
    )
    parser.add_argument("--public-key", type=Path)
    parser.add_argument("--exclude", action="append")
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(main())
