from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional


def main() -> int:
    args = _parse_args()
    result = validate_quantum_execution_semantics(
        program_ir=args.program_ir,
        plan=args.plan,
        runtime_result=args.runtime_result,
        backend_ir=args.backend_ir,
        qasm=args.qasm,
        bundle_manifest=args.bundle_manifest,
    )
    status = "PASS" if result["ok"] else "FAIL"
    print(status)
    for err in result["errors"]:
        print(f"  - {err}")
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


def validate_quantum_execution_semantics(
    program_ir: Optional[Path],
    plan: Optional[Path],
    runtime_result: Optional[Path],
    backend_ir: Optional[Path],
    qasm: Optional[Path],
    bundle_manifest: Optional[Path],
) -> Dict[str, object]:
    errors: List[str] = []
    present: List[str] = []

    _require_path("program_ir", program_ir, present, errors)
    _require_path("plan", plan, present, errors)
    _require_path("runtime_result", runtime_result, present, errors)

    if backend_ir and backend_ir.exists():
        present.append("backend_ir")
    if qasm and qasm.exists():
        present.append("qasm")
    if "backend_ir" not in present and "qasm" not in present:
        errors.append("missing backend projection (backend_ir or qasm)")

    _require_path("bundle_manifest", bundle_manifest, present, errors)

    required = ["program_ir", "plan", "runtime_result", "bundle_manifest"]
    missing_required = sorted({role for role in required if role not in present})
    if missing_required:
        errors.append(f"missing required roles: {', '.join(missing_required)}")

    result = {
        "ok": not errors,
        "required_roles": required,
        "present_roles": sorted(set(present)),
        "errors": errors,
    }
    return result


def _require_path(role: str, path: Optional[Path], present: List[str], errors: List[str]) -> None:
    if path is None:
        errors.append(f"missing {role} path")
        return
    if not path.exists():
        errors.append(f"{role} not found: {path}")
        return
    present.append(role)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate quantum execution semantics artifacts.")
    parser.add_argument("--program-ir", type=Path)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--runtime-result", type=Path)
    parser.add_argument("--backend-ir", type=Path)
    parser.add_argument("--qasm", type=Path)
    parser.add_argument("--bundle-manifest", type=Path)
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(main())
