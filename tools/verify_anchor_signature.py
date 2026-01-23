from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import List, Optional, Tuple

from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey


def main() -> int:
    args = _parse_args()
    verify_key = _load_verify_key(args.public_key, args.public_key_env)
    ok, errors = verify_anchor_signature(args.anchor, args.signature, verify_key)
    result = {"ok": ok, "errors": errors}
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if ok else 1


def verify_anchor_signature(
    anchor_path: Path,
    signature_path: Path,
    verify_key: VerifyKey,
) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    payload = anchor_path.read_bytes()
    signature_hex = signature_path.read_text(encoding="utf-8").strip()
    if not signature_hex:
        return False, ["signature file is empty"]

    try:
        signature = bytes.fromhex(signature_hex)
    except ValueError:
        return False, ["signature is not valid hex"]

    try:
        verify_key.verify(payload, signature)
    except BadSignatureError:
        errors.append("signature verification failed")

    return not errors, errors


def _load_verify_key(path: Optional[Path], env_var: str) -> VerifyKey:
    if path:
        key_hex = _read_hex(path)
    else:
        key_hex = os.environ.get(env_var, "").strip()

    if not key_hex:
        raise ValueError(
            f"missing public key; provide --public-key or set {env_var}"
        )

    key_bytes = bytes.fromhex(key_hex)
    if len(key_bytes) != 32:
        raise ValueError("public key must be 32 bytes (64 hex chars)")

    return VerifyKey(key_bytes)


def _read_hex(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify an Ed25519 anchor signature.")
    parser.add_argument("anchor", type=Path)
    parser.add_argument("signature", type=Path)
    parser.add_argument("--public-key", type=Path)
    parser.add_argument(
        "--public-key-env",
        default="HPL_CI_ED25519_PUBLIC_KEY",
        help="Environment variable containing hex public key",
    )
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(main())
