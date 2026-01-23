from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Optional

from nacl.signing import SigningKey


def main() -> int:
    args = _parse_args()
    signing_key = _load_signing_key(args.private_key, args.private_key_env)
    signature = sign_anchor_file(args.anchor, signing_key)

    signature_out = args.signature_out or args.anchor.with_suffix(
        args.anchor.suffix + ".sig"
    )
    signature_out.write_text(signature.hex(), encoding="utf-8")

    result = {
        "ok": True,
        "signature_path": str(signature_out),
        "signature_digest": _hash_bytes(signature),
    }
    print(json.dumps(result, sort_keys=True))
    return 0


def sign_anchor_file(anchor_path: Path, signing_key: SigningKey) -> bytes:
    payload = anchor_path.read_bytes()
    return signing_key.sign(payload).signature


def _load_signing_key(path: Optional[Path], env_var: str) -> SigningKey:
    if path:
        key_hex = _read_hex(path)
    else:
        key_hex = os.environ.get(env_var, "").strip()

    if not key_hex:
        raise ValueError(
            f"missing private key; provide --private-key or set {env_var}"
        )

    key_bytes = bytes.fromhex(key_hex)
    if len(key_bytes) != 32:
        raise ValueError("private key seed must be 32 bytes (64 hex chars)")

    return SigningKey(key_bytes)


def _read_hex(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def _hash_bytes(payload: bytes) -> str:
    digest = hashlib.sha256(payload).hexdigest()
    return f"sha256:{digest}"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sign an epoch anchor with Ed25519.")
    parser.add_argument("anchor", type=Path)
    parser.add_argument("--signature-out", type=Path)
    parser.add_argument("--private-key", type=Path)
    parser.add_argument(
        "--private-key-env",
        default="HPL_CI_ED25519_PRIVATE_KEY",
        help="Environment variable containing hex seed for signing key",
    )
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(main())
