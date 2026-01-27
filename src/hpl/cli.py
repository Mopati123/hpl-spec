"""Canonical CLI entrypoint for the HPL pipeline."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

from .axioms.validator import validate_program
from .dynamics.ir_emitter import emit_program_ir
from .emergence.dsl.parser import parse_file
from .emergence.macros.expander import expand_program
from .errors import HplError
from .runtime.context import RuntimeContext
from .runtime.contracts import ExecutionContract
from .runtime.engine import RuntimeEngine
from .scheduler import SchedulerContext, plan as plan_program
from .backends.classical_lowering import lower_program_ir_to_backend_ir
from .backends.qasm_lowering import lower_backend_ir_to_qasm


DEFAULT_PUBLIC_KEY = Path("config/keys/ci_ed25519.pub")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="hpl")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ir_parser = subparsers.add_parser("ir")
    ir_parser.add_argument("input", type=Path)
    ir_parser.add_argument("--out", type=Path, required=True)

    plan_parser = subparsers.add_parser("plan")
    plan_parser.add_argument("program_ir", type=Path)
    plan_parser.add_argument("--out", type=Path, required=True)
    plan_parser.add_argument("--require-epoch", action="store_true")
    plan_parser.add_argument("--anchor", type=Path)
    plan_parser.add_argument("--sig", type=Path)
    plan_parser.add_argument("--pub", type=Path, default=DEFAULT_PUBLIC_KEY)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("plan", type=Path)
    run_parser.add_argument("--out", type=Path, required=True)
    run_parser.add_argument("--contract", type=Path)
    run_parser.add_argument("--anchor", type=Path)
    run_parser.add_argument("--sig", type=Path)
    run_parser.add_argument("--pub", type=Path, default=DEFAULT_PUBLIC_KEY)

    lower_parser = subparsers.add_parser("lower")
    lower_parser.add_argument("--backend", choices=["classical", "qasm"], required=True)
    lower_parser.add_argument("--ir", type=Path, required=True)
    lower_parser.add_argument("--out", type=Path, required=True)

    args = parser.parse_args(argv)

    try:
        if args.command == "ir":
            return _cmd_ir(args)
        if args.command == "plan":
            return _cmd_plan(args)
        if args.command == "run":
            return _cmd_run(args)
        if args.command == "lower":
            return _cmd_lower(args)
    except HplError as exc:
        _write_refusal_evidence(
            command=args.command,
            inputs={"input": str(args.input)} if hasattr(args, "input") else {},
            errors=[str(exc)],
            evidence_path=_default_evidence_path(args.out, args.command)
            if hasattr(args, "out")
            else None,
        )
        return 0
    except Exception as exc:  # programming errors
        print(f"error: {exc}", file=sys.stderr)
        return 1

    return 1


def _cmd_ir(args: argparse.Namespace) -> int:
    program = parse_file(str(args.input))
    expanded = expand_program(program)
    validate_program(expanded)
    program_ir = emit_program_ir(expanded, program_id=args.input.stem)

    _write_json(args.out, program_ir)
    evidence_path = _default_evidence_path(args.out, "ir")
    _write_evidence(
        evidence_path,
        command="ir",
        ok=True,
        errors=[],
        inputs={"input": _digest_file(args.input)},
        outputs={"program_ir": _digest_file(args.out)},
    )
    return 0


def _cmd_plan(args: argparse.Namespace) -> int:
    program_ir = json.loads(args.program_ir.read_text(encoding="utf-8"))
    ctx = SchedulerContext(
        require_epoch_verification=args.require_epoch,
        anchor_path=args.anchor,
        signature_path=args.sig,
        public_key_path=args.pub,
    )
    execution_plan = plan_program(program_ir, ctx)
    plan_dict = execution_plan.to_dict()
    _write_json(args.out, plan_dict)

    ok = execution_plan.status == "planned"
    errors = list(execution_plan.reasons)
    evidence_path = _default_evidence_path(args.out, "plan")
    _write_evidence(
        evidence_path,
        command="plan",
        ok=ok,
        errors=errors,
        inputs={"program_ir": _digest_file(args.program_ir)},
        outputs={"plan": _digest_file(args.out)},
    )
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    plan_dict = json.loads(args.plan.read_text(encoding="utf-8"))
    ctx = RuntimeContext(
        epoch_anchor_path=args.anchor,
        epoch_sig_path=args.sig,
        ci_pubkey_path=args.pub,
    )
    contract = _load_contract(args.contract, plan_dict)
    result = RuntimeEngine().run(plan_dict, ctx, contract)
    result_dict = result.to_dict()
    _write_json(args.out, result_dict)

    ok = result.status == "completed"
    evidence_path = _default_evidence_path(args.out, "run")
    _write_evidence(
        evidence_path,
        command="run",
        ok=ok,
        errors=list(result.reasons),
        inputs={"plan": _digest_file(args.plan)},
        outputs={"runtime_result": _digest_file(args.out)},
    )
    return 0


def _cmd_lower(args: argparse.Namespace) -> int:
    program_ir = json.loads(args.ir.read_text(encoding="utf-8"))
    backend_ir = lower_program_ir_to_backend_ir(program_ir, target=args.backend)
    backend_ir_dict = backend_ir.to_dict()

    if args.backend == "classical":
        _write_json(args.out, backend_ir_dict)
        output_digest = _digest_file(args.out)
    else:
        qasm = lower_backend_ir_to_qasm(backend_ir_dict)
        args.out.write_text(qasm, encoding="utf-8")
        output_digest = _digest_text_value(qasm)

    evidence_path = _default_evidence_path(args.out, "lower")
    _write_evidence(
        evidence_path,
        command="lower",
        ok=True,
        errors=[],
        inputs={"program_ir": _digest_file(args.ir)},
        outputs={
            "backend_ir": _digest_text_value(_canonical_json(backend_ir_dict)),
            "output": output_digest,
        },
    )
    return 0


def _load_contract(contract_path: Optional[Path], plan_dict: Dict[str, object]) -> ExecutionContract:
    if contract_path and contract_path.exists():
        data = json.loads(contract_path.read_text(encoding="utf-8"))
        allowed_steps = set(map(str, data.get("allowed_steps", [])))
        return ExecutionContract(
            allowed_steps=allowed_steps,
            require_epoch_verification=bool(data.get("require_epoch_verification", False)),
            require_signature_verification=bool(data.get("require_signature_verification", False)),
        )

    plan_steps = plan_dict.get("steps", [])
    allowed = {str(step.get("operator_id")) for step in plan_steps if isinstance(step, dict)}
    return ExecutionContract(allowed_steps=allowed)


def _write_json(path: Path, payload: Dict[str, object]) -> None:
    path.write_text(_canonical_json(payload), encoding="utf-8")


def _write_refusal_evidence(
    command: str,
    inputs: Dict[str, str],
    errors: List[str],
    evidence_path: Optional[Path],
) -> None:
    if not evidence_path:
        return
    _write_evidence(
        evidence_path,
        command=command,
        ok=False,
        errors=errors,
        inputs={key: {"path": Path(value).name, "digest": "unavailable"} for key, value in inputs.items()},
        outputs={},
    )


def _write_evidence(
    path: Path,
    command: str,
    ok: bool,
    errors: List[str],
    inputs: Dict[str, Dict[str, str]] | Dict[str, str],
    outputs: Dict[str, Dict[str, str]] | Dict[str, str],
) -> None:
    def normalize(obj: Dict[str, Dict[str, str]] | Dict[str, str]) -> Dict[str, Dict[str, str]]:
        if not obj:
            return {}
        sample = next(iter(obj.values()))
        if isinstance(sample, dict):
            return obj  # type: ignore[return-value]
        return {key: {"path": key, "digest": value} for key, value in obj.items()}

    evidence = {
        "command": command,
        "ok": ok,
        "errors": list(errors),
        "inputs": normalize(inputs),
        "outputs": normalize(outputs),
    }
    path.write_text(_canonical_json(evidence), encoding="utf-8")


def _default_evidence_path(out_path: Path, command: str) -> Path:
    name = f"{command}_evidence.json"
    return out_path.with_name(name)


def _canonical_json(data: object) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def _digest_text_value(value: str) -> Dict[str, str]:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return {"path": "inline", "digest": f"sha256:{digest}"}


def _digest_file(path: Path) -> Dict[str, str]:
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    return {"path": path.name, "digest": f"sha256:{digest}"}


if __name__ == "__main__":
    raise SystemExit(main())
