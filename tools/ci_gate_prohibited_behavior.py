from __future__ import annotations

from pathlib import Path
from typing import Iterable, List


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "hpl"
RUNTIME = SRC / "runtime"
RUNTIME_ENGINE = RUNTIME / "engine.py"
SCHEDULER = SRC / "scheduler.py"
EXECUTION_TOKEN = SRC / "execution_token.py"

# Gate C originally prohibited runtime implementation entirely. That was valid for
# the Level-1 front-end-only certification stage, but it is not the current HPL
# architecture. Gate C now protects the authority boundary itself: runtime code is
# lawful, but effect dispatch must remain inside the governed runtime and the
# runtime must preserve its refusal-first execution guards.
REQUIRED_RUNTIME_SENTINELS = {
    '"execution token missing"': "runtime must refuse execution without an ExecutionToken",
    '"plan not approved"': "runtime must refuse execution of a non-approved plan",
    'raise RuntimeError("effect execution requires context")': (
        "raw effect execution must require governed runtime context"
    ),
}


def validate_authority_boundaries(root: Path = ROOT) -> List[str]:
    """Return constitutional authority-boundary violations for a repository tree."""
    src = root / "src" / "hpl"
    runtime = src / "runtime"
    runtime_engine = runtime / "engine.py"
    scheduler = src / "scheduler.py"
    execution_token = src / "execution_token.py"

    violations: List[str] = []

    required_paths = {
        scheduler: "scheduler authority implementation missing",
        execution_token: "ExecutionToken authority contract missing",
        runtime_engine: "governed runtime execution gate missing",
    }
    for path, reason in required_paths.items():
        if not path.is_file():
            violations.append(f"{_relative(path, root)}: {reason}")

    if runtime_engine.is_file():
        engine_source = runtime_engine.read_text(encoding="utf-8")
        for sentinel, reason in REQUIRED_RUNTIME_SENTINELS.items():
            if sentinel not in engine_source:
                violations.append(f"{_relative(runtime_engine, root)}: {reason}")

    if src.is_dir():
        for path in _production_python_files(src):
            # Runtime owns effect dispatch. Other production layers may construct
            # plans, compile IR, or invoke RuntimeEngine, but may not fetch effect
            # handlers directly and thereby create a second execution authority.
            if _is_within(path, runtime):
                continue
            source = path.read_text(encoding="utf-8")
            if "get_handler(" in source:
                violations.append(
                    f"{_relative(path, root)}: effect dispatch outside governed runtime"
                )

    return violations


def _production_python_files(src: Path) -> Iterable[Path]:
    return sorted(path for path in src.rglob("*.py") if path.is_file())


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def main() -> int:
    violations = validate_authority_boundaries(ROOT)

    if violations:
        print("Gate C failed: execution-authority boundary violations detected.")
        for violation in violations:
            print(f"- {violation}")
        return 1

    print("Gate C passed: scheduler/runtime authority boundaries preserved.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
