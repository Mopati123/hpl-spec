from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "docs" / "spec" / "04_ir_schema.json"


def main() -> int:
    if not SCHEMA_PATH.exists():
        raise SystemExit(f"Schema not found: {SCHEMA_PATH}")

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    required_top = {"program_id", "hamiltonian", "operators", "invariants", "scheduler"}
    missing = required_top.difference(schema.get("required", []))
    if missing:
        print("Schema check failed: missing required top-level fields.")
        for field in sorted(missing):
            print(f"- {field}")
        return 1

    print("Schema check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
