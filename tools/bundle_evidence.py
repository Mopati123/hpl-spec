from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from tools import verify_epoch
from tools import verify_anchor_signature


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PUBLIC_KEY = ROOT / "config" / "keys" / "ci_ed25519.pub"


@dataclass(frozen=True)
class Artifact:
    role: str
    source: Path
    filename: str
    digest: str


def main() -> int:
    args = _parse_args()
    artifacts = _collect_artifacts(args)
    bundle_dir, manifest = build_bundle(
        out_dir=args.out_dir,
        artifacts=artifacts,
        epoch_anchor=args.epoch_anchor,
        epoch_sig=args.epoch_sig,
        public_key=args.pub,
    )
    manifest_path = bundle_dir / "bundle_manifest.json"
    manifest_path.write_text(_canonical_json(manifest), encoding="utf-8")
    return 0


def build_bundle(
    out_dir: Path,
    artifacts: List[Artifact],
    epoch_anchor: Optional[Path],
    epoch_sig: Optional[Path],
    public_key: Optional[Path],
) -> Tuple[Path, Dict[str, object]]:
    if not artifacts:
        raise ValueError("no artifacts provided")

    bundle_id = _bundle_id(artifacts)
    bundle_dir = out_dir / f"bundle_{bundle_id}"
    bundle_dir.mkdir(parents=True, exist_ok=True)

    for artifact in artifacts:
        shutil.copyfile(artifact.source, bundle_dir / artifact.filename)

    git_commit = _git_commit()
    verification = _verify_epoch_and_signature(epoch_anchor, epoch_sig, public_key, git_commit)

    manifest = {
        "bundle_id": bundle_id,
        "git_commit": git_commit,
        "verification": verification,
        "artifacts": [
            {
                "role": artifact.role,
                "filename": artifact.filename,
                "digest": artifact.digest,
            }
            for artifact in artifacts
        ],
    }

    return bundle_dir, manifest


def _collect_artifacts(args: argparse.Namespace) -> List[Artifact]:
    mapping: Dict[str, Optional[Path]] = {
        "program_ir": args.program_ir,
        "plan": args.plan,
        "runtime_result": args.runtime_result,
        "backend_ir": args.backend_ir,
        "qasm": args.qasm,
        "epoch_anchor": args.epoch_anchor,
        "epoch_sig": args.epoch_sig,
    }

    artifacts: List[Artifact] = []
    for role, path in mapping.items():
        if not path:
            continue
        artifacts.append(_artifact(role, path))

    extras = sorted(args.extra or [], key=lambda p: str(p))
    for idx, path in enumerate(extras):
        artifacts.append(_artifact(f"extra_{idx}", path))

    artifacts.sort(key=lambda item: (item.role, item.filename))
    return artifacts


def _artifact(role: str, path: Path) -> Artifact:
    digest = _digest_bytes(path.read_bytes())
    filename = f"{role}_{path.name}"
    return Artifact(role=role, source=path, filename=filename, digest=digest)


def _bundle_id(artifacts: List[Artifact]) -> str:
    core = [
        {"role": artifact.role, "digest": artifact.digest}
        for artifact in artifacts
    ]
    return _digest_hex(_canonical_json(core))


def _verify_epoch_and_signature(
    anchor: Optional[Path],
    signature: Optional[Path],
    public_key: Optional[Path],
    git_commit: Optional[str],
) -> Dict[str, object]:
    epoch_ok = None
    epoch_errors: List[str] = []
    signature_ok = None
    signature_errors: List[str] = []

    if anchor:
        anchor_data = json.loads(anchor.read_text(encoding="utf-8"))
        epoch_ok, epoch_errors = verify_epoch.verify_epoch_anchor(
            anchor_data,
            root=ROOT,
            git_commit_override=git_commit,
        )

    if signature and anchor:
        verify_key = verify_anchor_signature._load_verify_key(
            public_key or DEFAULT_PUBLIC_KEY,
            "UNUSED",
        )
        signature_ok, signature_errors = verify_anchor_signature.verify_anchor_signature(
            anchor,
            signature,
            verify_key,
        )

    return {
        "epoch_ok": epoch_ok,
        "epoch_errors": list(epoch_errors),
        "signature_ok": signature_ok,
        "signature_errors": list(signature_errors),
    }


def _git_commit() -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip() or None
    except Exception:
        return None


def _canonical_json(data: object) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def _digest_bytes(data: bytes) -> str:
    digest = hashlib.sha256(data).hexdigest()
    return f"sha256:{digest}"


def _digest_text(value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _digest_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bundle evidence artifacts.")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--program-ir", type=Path)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--runtime-result", type=Path)
    parser.add_argument("--backend-ir", type=Path)
    parser.add_argument("--qasm", type=Path)
    parser.add_argument("--epoch-anchor", type=Path)
    parser.add_argument("--epoch-sig", type=Path)
    parser.add_argument("--pub", type=Path, default=DEFAULT_PUBLIC_KEY)
    parser.add_argument("--extra", type=Path, action="append", default=[])
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(main())
