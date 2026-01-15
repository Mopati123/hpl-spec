from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "hpl"
FORBIDDEN_DIRS = {
    "runtime",
    "scheduler",
    "observers",
    "backends",
    "simulator",
}


def main() -> int:
    violations = []
    if SRC.exists():
        for name in FORBIDDEN_DIRS:
            candidate = SRC / name
            if candidate.exists() and any(candidate.rglob("*")):
                violations.append(str(candidate.relative_to(ROOT)))

    if violations:
        print("Gate C failed: prohibited implementation areas detected.")
        for path in violations:
            print(f"- {path}")
        return 1

    print("Gate C passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
