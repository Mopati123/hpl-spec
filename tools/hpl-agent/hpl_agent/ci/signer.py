from __future__ import annotations
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization

class Ed25519Signer:
    def __init__(self, private_key_path: Path | None = None):
        if private_key_path and private_key_path.exists():
            pem = private_key_path.read_bytes()
            self._private_key: Ed25519PrivateKey = serialization.load_pem_private_key(pem, password=None)
            self._public_key: Ed25519PublicKey = self._private_key.public_key()
        else:
            self._private_key = Ed25519PrivateKey.generate()
            self._public_key = self._private_key.public_key()

    def sign(self, payload: bytes) -> str:
        return self._private_key.sign(payload).hex()

    def verify(self, payload: bytes, signature_hex: str) -> bool:
        try:
            self._public_key.verify(bytes.fromhex(signature_hex), payload)
            return True
        except Exception:
            return False

    def public_key_hex(self) -> str:
        raw = self._public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return raw.hex()

    @classmethod
    def generate_keypair(cls, output_dir: Path) -> tuple[Path, Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        key = Ed25519PrivateKey.generate()
        priv_path = output_dir / "private_key.pem"
        pub_path = output_dir / "public_key.pem"
        priv_path.write_bytes(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ))
        pub = key.public_key()
        pub_path.write_bytes(pub.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ))
        return priv_path, pub_path
