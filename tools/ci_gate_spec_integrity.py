from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Iterable, Set


ROOT = Path(__file__).resolve().parents[1]
FREEZE_DECLARATION = ROOT / "docs" / "spec" / "00_spec_freeze_declaration_v1.md"
DISALLOWED_EXTS = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".rs",
    ".go",
    ".java",
    ".cs",
    ".cpp",
    ".c",
    ".h",
    ".sh",
    ".ps1",
}


def main() -> int:
    changed = _git_changed_files()
    normative = _read_normative_files()

    if normative:
        touched_normative = [path for path in changed if path in normative]
        if touched_normative and str(FREEZE_DECLARATION.relative_to(ROOT)) not in changed:
            print("Gate A failed: normative spec files changed without freeze declaration update.")
            for path in touched_normative:
                print(f"- {path}")
            return 1

    violations = _scan_h_folders_for_executables()
    if violations:
        print("Gate A failed: executable files found in _H folders.")
        for path in violations:
            print(f"- {path}")
        return 1

    print("Gate A passed.")
    return 0


def _git_changed_files() -> Set[str]:
    base = os.getenv("BASE_SHA") or os.getenv("GITHUB_BASE_SHA")
    head = os.getenv("HEAD_SHA") or os.getenv("GITHUB_SHA")
    if not base:
        base = "HEAD~1"
    if not head:
        head = "HEAD"

    result = subprocess.run(
        ["git", "diff", "--name-only", base, head],
        check=False,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    if result.returncode != 0:
        print(result.stderr.strip())
        raise SystemExit("Unable to determine changed files for Gate A.")
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def _read_normative_files() -> Set[str]:
    if not FREEZE_DECLARATION.exists():
        return set()
    content = FREEZE_DECLARATION.read_text(encoding="utf-8")
    matches = re.findall(r"`(docs/[^`]+)`", content)
    return set(matches)


def _scan_h_folders_for_executables() -> Iterable[str]:
    violations = []
    for folder in ROOT.iterdir():
        if folder.is_dir() and folder.name.endswith("_H"):
            for path in folder.rglob("*"):
                if path.is_file() and path.suffix.lower() in DISALLOWED_EXTS:
                    violations.append(str(path.relative_to(ROOT)))
    return violations


if __name__ == "__main__":
    raise SystemExit(main())
