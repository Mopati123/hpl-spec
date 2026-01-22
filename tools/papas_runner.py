from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from hpl.audit.dev_change_event import build_dev_change_event, write_dev_change_event


def load_policy(path: Path) -> Dict[str, object]:
    if not path.exists():
        raise FileNotFoundError(f"Policy file not found: {path}")
    content = path.read_text(encoding="utf-8")
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Policy file must be JSON-compatible YAML: {exc}") from exc
    return data


def validate_mode(policy: Dict[str, object], mode: str) -> None:
    allowed = policy.get("allowed_modes", [])
    if mode not in allowed:
        raise ValueError(f"Mode '{mode}' not allowed by policy")


def check_paths_allowed(policy: Dict[str, object], paths: Iterable[str]) -> None:
    allowed = policy.get("allowed_paths", [])
    forbidden = policy.get("forbidden_paths", [])

    for path in paths:
        normalized = _normalize_path(path)
        if any(normalized.startswith(_normalize_path(item)) for item in forbidden):
            raise ValueError(f"Path '{path}' is forbidden by policy")
        if allowed and not any(normalized.startswith(_normalize_path(item)) for item in allowed):
            raise ValueError(f"Path '{path}' is not within allowed paths")


def resolve_command(policy: Dict[str, object], command_name: str) -> List[str]:
    whitelist = policy.get("command_whitelist", {})
    if command_name not in whitelist:
        raise ValueError(f"Command '{command_name}' is not whitelisted")
    cmd = whitelist[command_name]
    if not isinstance(cmd, list) or not all(isinstance(item, str) for item in cmd):
        raise ValueError(f"Command '{command_name}' must map to a list of strings")
    return cmd


def run_named_command(
    policy: Dict[str, object],
    mode: str,
    command_name: str,
    dry_run: bool = False,
) -> Dict[str, object]:
    validate_mode(policy, mode)
    if mode == "PR_BOT":
        raise ValueError("PR_BOT mode cannot execute commands")

    cmd = resolve_command(policy, command_name)
    if dry_run:
        return {"returncode": 0, "stdout": "", "stderr": ""}

    result = subprocess.run(cmd, check=False, capture_output=True, text=True, cwd=ROOT)
    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run whitelisted commands under Papas policy.")
    parser.add_argument("--policy", type=Path, default=ROOT / "config" / "papas_policy.yaml")
    parser.add_argument("--mode", required=True, choices=["PR_BOT", "NEAR_AUTONOMOUS"])
    parser.add_argument("--command", help="Whitelisted command name to execute.")
    parser.add_argument("--paths", nargs="*", default=[], help="Paths to validate against policy.")
    parser.add_argument("--branch", default="unknown")
    parser.add_argument("--ledger-item", default="unknown")
    parser.add_argument("--emit-event", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--timestamp", default=None)
    args = parser.parse_args()

    policy = load_policy(args.policy)
    validate_mode(policy, args.mode)
    if args.paths:
        check_paths_allowed(policy, args.paths)

    output = {"returncode": 0, "stdout": "", "stderr": ""}
    if args.command:
        output = run_named_command(policy, args.mode, args.command, dry_run=args.dry_run)

    if args.emit_event:
        policy_version = str(policy.get("policy_version", "unknown"))
        bundle = build_dev_change_event(
            mode=args.mode,
            branch=args.branch,
            target_ledger_item=args.ledger_item,
            files_changed=list(args.paths),
            test_results=output.get("stdout", ""),
            tool_outputs=output.get("stderr", ""),
            policy_version=policy_version,
            timestamp=args.timestamp or None,
        )
        write_dev_change_event(bundle.event, args.emit_event)

    return int(output.get("returncode", 0))


def _normalize_path(path: str) -> str:
    return path.replace("\\", "/")


if __name__ == "__main__":
    raise SystemExit(main())
