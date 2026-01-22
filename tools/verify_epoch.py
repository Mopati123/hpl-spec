from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
TOOLS_PATH = ROOT / "tools" / "anchor_epoch.py"
SPEC = importlib.util.spec_from_file_location("anchor_epoch", TOOLS_PATH)
anchor_epoch = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(anchor_epoch)

build_epoch_anchor = anchor_epoch.build_epoch_anchor


def main() -> int:
    args = _parse_args()
    anchor = json.loads(args.anchor.read_text(encoding="utf-8"))
    ok, errors = verify_epoch_anchor(anchor, root=args.root, git_commit_override=args.git_commit)
    result = {"ok": ok, "errors": errors}
    print(json.dumps(result, indent=2))
    return 0 if ok else 1


def verify_epoch_anchor(
    anchor: Dict[str, object],
    root: Path,
    git_commit_override: Optional[str] = None,
) -> Tuple[bool, List[str]]:
    errors: List[str] = []

    epoch_id = anchor.get("epoch_id")
    timestamp = anchor.get("timestamp_utc")
    git_commit = git_commit_override or anchor.get("git_commit")
    emit_witness = "papas_witness_record" in anchor

    if not epoch_id:
        errors.append("anchor: missing epoch_id")
    if not timestamp:
        errors.append("anchor: missing timestamp_utc")

    if errors:
        return False, errors

    current = build_epoch_anchor(
        epoch_id=str(epoch_id),
        timestamp=str(timestamp),
        git_commit=str(git_commit) if git_commit else None,
        root=root,
        emit_witness=emit_witness,
    )

    errors.extend(_compare_field(anchor, current, "git_commit"))
    errors.extend(_compare_field(anchor, current, "schema_hashes"))
    errors.extend(_compare_field(anchor, current, "registry_hashes"))
    errors.extend(_compare_field(anchor, current, "tooling_hashes"))
    errors.extend(_compare_field(anchor, current, "callgraph_hash"))
    errors.extend(_compare_field(anchor, current, "scheduler_contract_hash"))

    if emit_witness:
        errors.extend(_compare_field(anchor, current, "papas_witness_digest"))

    return not errors, errors


def _compare_field(anchor: Dict[str, object], current: Dict[str, object], field: str) -> List[str]:
    if field not in anchor:
        return []
    if anchor.get(field) != current.get(field):
        return [f"{field} mismatch"]
    return []


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify an epoch anchor against the working tree.")
    parser.add_argument("anchor", type=Path)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--git-commit")
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(main())
