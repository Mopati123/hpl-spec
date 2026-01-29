"""Canonical CLI entrypoint for the HPL pipeline."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
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
from .audit.constraint_inversion import invert_constraints
from .audit.constraint_witness import build_constraint_witness
from .execution_token import ExecutionToken
from .scheduler import SchedulerContext, plan as plan_program
from .backends.classical_lowering import lower_program_ir_to_backend_ir
from .backends.qasm_lowering import lower_backend_ir_to_qasm


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PUBLIC_KEY = Path("config/keys/ci_ed25519.pub")
BUNDLE_EVIDENCE_PATH = ROOT / "tools" / "bundle_evidence.py"


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
    plan_parser.add_argument("--allowed-backends", type=str, default="PYTHON,CLASSICAL,QASM")
    plan_parser.add_argument("--budget-steps", type=int, default=100)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("plan", type=Path)
    run_parser.add_argument("--out", type=Path, required=True)
    run_parser.add_argument("--contract", type=Path)
    run_parser.add_argument("--anchor", type=Path)
    run_parser.add_argument("--sig", type=Path)
    run_parser.add_argument("--pub", type=Path, default=DEFAULT_PUBLIC_KEY)
    run_parser.add_argument("--backend", choices=["classical", "qasm"])

    lower_parser = subparsers.add_parser("lower")
    lower_parser.add_argument("--backend", choices=["classical", "qasm"], required=True)
    lower_parser.add_argument("--ir", type=Path, required=True)
    lower_parser.add_argument("--out", type=Path, required=True)

    bundle_parser = subparsers.add_parser("bundle")
    bundle_parser.add_argument("--out-dir", type=Path, required=True)
    bundle_parser.add_argument("--program-ir", type=Path)
    bundle_parser.add_argument("--plan", type=Path)
    bundle_parser.add_argument("--runtime-result", type=Path)
    bundle_parser.add_argument("--backend-ir", type=Path)
    bundle_parser.add_argument("--qasm", type=Path)
    bundle_parser.add_argument("--epoch-anchor", type=Path)
    bundle_parser.add_argument("--epoch-sig", type=Path)
    bundle_parser.add_argument("--pub", type=Path, default=DEFAULT_PUBLIC_KEY)
    bundle_parser.add_argument("--extra", type=Path, action="append", default=[])
    bundle_parser.add_argument("--quantum-semantics-v1", action="store_true")
    bundle_parser.add_argument("--sign-bundle", action="store_true")
    bundle_parser.add_argument("--signing-key", type=Path)
    bundle_parser.add_argument("--verify-bundle", action="store_true")

    lifecycle_parser = subparsers.add_parser("lifecycle")
    lifecycle_parser.add_argument("input", type=Path)
    lifecycle_parser.add_argument("--backend", choices=["classical", "qasm"], required=True)
    lifecycle_parser.add_argument("--out-dir", type=Path, required=True)
    lifecycle_parser.add_argument("--require-epoch", action="store_true")
    lifecycle_parser.add_argument("--anchor", type=Path)
    lifecycle_parser.add_argument("--sig", type=Path)
    lifecycle_parser.add_argument("--pub", type=Path, default=DEFAULT_PUBLIC_KEY)
    lifecycle_parser.add_argument("--quantum-semantics-v1", action="store_true")
    lifecycle_parser.add_argument("--constraint-inversion-v1", action="store_true")
    lifecycle_parser.add_argument("--allowed-backends", type=str, default="PYTHON,CLASSICAL,QASM")
    lifecycle_parser.add_argument("--budget-steps", type=int, default=100)
    lifecycle_parser.add_argument("--legacy", action="store_true")

    invert_parser = subparsers.add_parser("invert")
    invert_parser.add_argument("--witness", type=Path, required=True)
    invert_parser.add_argument("--out", type=Path, required=True)
    invert_parser.add_argument("--pretty", action="store_true")

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
        if args.command == "bundle":
            return _cmd_bundle(args)
        if args.command == "lifecycle":
            return _cmd_lifecycle(args)
        if args.command == "invert":
            return _cmd_invert(args)
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
        allowed_backends=_parse_backends(args.allowed_backends),
        budget_steps=args.budget_steps,
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
    token_dict = plan_dict.get("execution_token")
    execution_token = None
    if isinstance(token_dict, dict):
        execution_token = ExecutionToken.from_dict(token_dict)
    ctx = RuntimeContext(
        epoch_anchor_path=args.anchor,
        epoch_sig_path=args.sig,
        ci_pubkey_path=args.pub,
        execution_token=execution_token,
        requested_backend=_normalize_backend(args.backend) if args.backend else None,
    )
    contract = _load_contract(args.contract, plan_dict)
    if args.backend:
        contract = ExecutionContract(
            allowed_steps=contract.allowed_steps,
            require_epoch_verification=contract.require_epoch_verification,
            require_signature_verification=contract.require_signature_verification,
            required_backend=_normalize_backend(args.backend),
        )
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


def _cmd_bundle(args: argparse.Namespace) -> int:
    bundle_module = _load_bundle_module()
    errors: List[str] = []
    artifacts: List[object] = []

    args.out_dir.mkdir(parents=True, exist_ok=True)

    def add_artifact(role: str, path: Optional[Path]) -> None:
        if not path:
            return
        if not path.exists():
            errors.append(f"{role} not found: {path}")
            return
        artifacts.append(bundle_module._artifact(role, path))

    add_artifact("program_ir", args.program_ir)
    add_artifact("plan", args.plan)
    add_artifact("runtime_result", args.runtime_result)
    add_artifact("backend_ir", args.backend_ir)
    add_artifact("qasm", args.qasm)
    add_artifact("epoch_anchor", args.epoch_anchor)
    add_artifact("epoch_sig", args.epoch_sig)

    extras = sorted(args.extra or [], key=lambda p: str(p))
    for idx, path in enumerate(extras):
        add_artifact(f"extra_{idx}", path)

    if errors or not artifacts:
        summary = {
            "ok": False,
            "bundle_path": None,
            "bundle_id": None,
            "errors": errors or ["no artifacts provided"],
        }
        evidence_path = args.out_dir / "bundle_evidence.json"
        _write_evidence(
            evidence_path,
            command="bundle",
            ok=False,
            errors=summary["errors"],
            inputs={},
            outputs={},
        )
        print(_canonical_json(summary))
        return 0

    bundle_dir, manifest = bundle_module.build_bundle(
        out_dir=args.out_dir,
        artifacts=artifacts,
        epoch_anchor=args.epoch_anchor,
        epoch_sig=args.epoch_sig,
        public_key=args.pub,
        quantum_semantics_v1=args.quantum_semantics_v1,
    )
    manifest_path = bundle_dir / "bundle_manifest.json"
    manifest_path.write_text(bundle_module._canonical_json(manifest), encoding="utf-8")

    quantum_errors: List[str] = []
    bundle_sig_errors: List[str] = []
    signature_path = None
    ok = True
    if args.quantum_semantics_v1:
        quantum = manifest.get("quantum_semantics_v1", {})
        ok = bool(quantum.get("ok", False))
        if not ok:
            quantum_errors.append("quantum semantics roles incomplete")
            missing_required = quantum.get("missing_required", [])
            if missing_required:
                quantum_errors.append(f"missing_required={','.join(missing_required)}")
            if not quantum.get("projection_present"):
                quantum_errors.append("missing backend projection")

    if args.sign_bundle:
        if not args.signing_key:
            ok = False
            bundle_sig_errors.append("sign_bundle requires --signing-key")
        else:
            signature_path = bundle_module.sign_bundle_manifest(
                manifest_path,
                args.signing_key,
            )

    if args.verify_bundle:
        if signature_path is None:
            signature_path = manifest_path.with_suffix(".sig")
        verify_ok, verify_errors = bundle_module.verify_bundle_manifest_signature(
            manifest_path,
            signature_path,
            args.pub,
        )
        if not verify_ok:
            ok = False
            bundle_sig_errors.extend(verify_errors)

    evidence_inputs = {item.role: _digest_file(item.source) for item in artifacts}
    evidence_path = args.out_dir / "bundle_evidence.json"
    _write_evidence(
        evidence_path,
        command="bundle",
        ok=ok,
        errors=quantum_errors + bundle_sig_errors,
        inputs=evidence_inputs,
        outputs={"bundle_manifest": _digest_file(manifest_path)},
    )

    summary = {
        "ok": ok,
        "bundle_path": str(bundle_dir),
        "bundle_id": manifest.get("bundle_id"),
        "errors": quantum_errors + bundle_sig_errors,
    }
    print(_canonical_json(summary))
    return 0


def _cmd_invert(args: argparse.Namespace) -> int:
    errors: List[str] = []
    if not args.witness.exists():
        errors.append(f"witness not found: {args.witness}")
        summary = {"ok": False, "errors": errors}
        _write_json(args.out, summary)
        print(_canonical_json(summary))
        return 0

    witness = json.loads(args.witness.read_text(encoding="utf-8"))
    if not isinstance(witness, dict):
        errors.append("invalid witness: expected object")
    if "refusal_reasons" not in witness:
        errors.append("invalid witness: missing refusal_reasons")

    if errors:
        summary = {"ok": False, "errors": errors}
        _write_json(args.out, summary)
        print(_canonical_json(summary))
        return 0

    proposal = invert_constraints(witness)
    _write_json(args.out, proposal)
    if args.pretty:
        print(json.dumps(proposal, indent=2, sort_keys=True))
    else:
        print(_canonical_json(proposal))
    return 0


def _cmd_lifecycle(args: argparse.Namespace) -> int:
    out_dir = args.out_dir
    work_dir = out_dir / "work"
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    program_ir_path = work_dir / "program.ir.json"
    plan_path = work_dir / "plan.json"
    runtime_path = work_dir / "runtime.json"
    backend_ir_path = work_dir / "backend.ir.json"
    qasm_path = work_dir / "program.qasm"

    try:
        # IR
        program = parse_file(str(args.input))
        expanded = expand_program(program)
        validate_program(expanded)
        program_ir = emit_program_ir(expanded, program_id=args.input.stem)
        _write_json(program_ir_path, program_ir)
        _write_evidence(
            work_dir / "ir_evidence.json",
            command="ir",
            ok=True,
            errors=[],
            inputs={"input": _digest_file(args.input)},
            outputs={"program_ir": _digest_file(program_ir_path)},
        )

        # Plan
        use_kernel = not args.legacy
        ctx = SchedulerContext(
            require_epoch_verification=args.require_epoch,
            anchor_path=args.anchor,
            signature_path=args.sig,
            public_key_path=args.pub,
            allowed_backends=_parse_backends(args.allowed_backends),
            budget_steps=args.budget_steps,
            emit_effect_steps=use_kernel,
            backend_target=args.backend,
            artifact_paths=None,
        )
        plan_obj = plan_program(program_ir, ctx)
        plan_dict = plan_obj.to_dict()
        _write_json(plan_path, plan_dict)
        plan_ok = plan_obj.status == "planned"
        plan_errors = list(plan_obj.reasons)
        _write_evidence(
            work_dir / "plan_evidence.json",
            command="plan",
            ok=plan_ok,
            errors=plan_errors,
            inputs={"program_ir": _digest_file(program_ir_path)},
            outputs={"plan": _digest_file(plan_path)},
        )

        # Runtime
        token_dict = plan_dict.get("execution_token")
        execution_token = None
        if isinstance(token_dict, dict):
            execution_token = ExecutionToken.from_dict(token_dict)
        runtime_ctx = RuntimeContext(
            epoch_anchor_path=args.anchor,
            epoch_sig_path=args.sig,
            ci_pubkey_path=args.pub,
            execution_token=execution_token,
            requested_backend=_normalize_backend(args.backend),
            trace_sink=work_dir if use_kernel else None,
        )
        allowed_steps = set()
        for step in plan_dict.get("steps", []):
            if not isinstance(step, dict):
                continue
            step_id = step.get("step_id") or step.get("operator_id")
            if step_id:
                allowed_steps.add(str(step_id))
        contract = ExecutionContract(
            allowed_steps=allowed_steps,
            require_epoch_verification=False if use_kernel else args.require_epoch,
            require_signature_verification=False if use_kernel else bool(args.sig) if args.require_epoch else False,
            required_backend=None if use_kernel else _normalize_backend(args.backend),
        )
        runtime_result = RuntimeEngine().run(plan_dict, runtime_ctx, contract)
        runtime_dict = runtime_result.to_dict()
        _write_json(runtime_path, runtime_dict)
        run_ok = runtime_result.status == "completed"
        _write_evidence(
            work_dir / "run_evidence.json",
            command="run",
            ok=run_ok,
            errors=list(runtime_result.reasons),
            inputs={"plan": _digest_file(plan_path)},
            outputs={"runtime_result": _digest_file(runtime_path)},
        )

        # Constraint inversion artifacts
        constraint_witness: Optional[Dict[str, object]] = None
        dual_proposal: Optional[Dict[str, object]] = None
        if not plan_ok:
            constraint_witness = build_constraint_witness(
                stage="plan_refusal",
                refusal_reasons=plan_errors,
                artifact_digests={"plan": _digest_text(_canonical_json(plan_dict))},
                observer_id="papas",
                timestamp=None,
            )
        elif not run_ok:
            if runtime_result.constraint_witnesses:
                constraint_witness = runtime_result.constraint_witnesses[0]
        if constraint_witness:
            dual_proposal = invert_constraints(constraint_witness)
            _write_json(work_dir / "constraint_witness.json", constraint_witness)
            _write_json(work_dir / "dual_proposal.json", dual_proposal)

        # Lower
        if not use_kernel:
            backend_ir = lower_program_ir_to_backend_ir(program_ir, target=args.backend).to_dict()
            _write_json(backend_ir_path, backend_ir)
            output_digests = {"backend_ir": _digest_text_value(_canonical_json(backend_ir))}
            if args.backend == "qasm":
                qasm = lower_backend_ir_to_qasm(backend_ir)
                qasm_path.write_text(qasm, encoding="utf-8")
                output_digests["qasm"] = _digest_text_value(qasm)
            _write_evidence(
                work_dir / "lower_evidence.json",
                command="lower",
                ok=True,
                errors=[],
                inputs={"program_ir": _digest_file(program_ir_path)},
                outputs=output_digests,
            )

        # Bundle
        bundle_module = _load_bundle_module()
        artifacts = [
            bundle_module._artifact("program_ir", program_ir_path),
            bundle_module._artifact("plan", plan_path),
            bundle_module._artifact("runtime_result", runtime_path),
        ]
        if plan_dict.get("execution_token"):
            token_path = work_dir / "execution_token.json"
            _write_json(token_path, plan_dict.get("execution_token", {}))
            artifacts.append(bundle_module._artifact("execution_token", token_path))
        if backend_ir_path.exists():
            artifacts.append(bundle_module._artifact("backend_ir", backend_ir_path))
        if args.backend == "qasm":
            if qasm_path.exists():
                artifacts.append(bundle_module._artifact("qasm", qasm_path))
        bundle_errors: List[str] = []
        if args.anchor:
            if args.anchor.exists():
                artifacts.append(bundle_module._artifact("epoch_anchor", args.anchor))
            else:
                bundle_errors.append(f"anchor not found: {args.anchor}")
        if args.sig:
            if args.sig.exists():
                artifacts.append(bundle_module._artifact("epoch_sig", args.sig))
            else:
                bundle_errors.append(f"signature not found: {args.sig}")

        if constraint_witness:
            artifacts.append(
                bundle_module._artifact("constraint_witness", work_dir / "constraint_witness.json")
            )
        if dual_proposal:
            artifacts.append(
                bundle_module._artifact("dual_proposal", work_dir / "dual_proposal.json")
            )

        anchor_for_bundle = args.anchor if args.anchor and args.anchor.exists() else None
        sig_for_bundle = args.sig if args.sig and args.sig.exists() else None

        bundle_dir, manifest = bundle_module.build_bundle(
            out_dir=out_dir,
            artifacts=artifacts,
            epoch_anchor=anchor_for_bundle,
            epoch_sig=sig_for_bundle,
            public_key=args.pub,
            quantum_semantics_v1=args.quantum_semantics_v1,
            constraint_inversion_v1=args.constraint_inversion_v1,
        )
        manifest_path = bundle_dir / "bundle_manifest.json"
        manifest_path.write_text(bundle_module._canonical_json(manifest), encoding="utf-8")

        errors: List[str] = []
        ok = plan_ok and run_ok
        if plan_errors:
            errors.extend(plan_errors)
        if runtime_result.reasons:
            errors.extend(runtime_result.reasons)
        if bundle_errors:
            ok = False
            errors.extend(bundle_errors)

        if args.quantum_semantics_v1:
            quantum = manifest.get("quantum_semantics_v1", {})
            if not quantum.get("ok", False):
                ok = False
                errors.append("quantum semantics roles incomplete")
                missing_required = quantum.get("missing_required", [])
                if missing_required:
                    errors.append(f"missing_required={','.join(missing_required)}")
                if not quantum.get("projection_present"):
                    errors.append("missing backend projection")

        if args.constraint_inversion_v1:
            inversion = manifest.get("constraint_inversion_v1", {})
            if not inversion.get("ok", False):
                ok = False
                errors.append("constraint inversion roles incomplete")
                missing_required = inversion.get("missing_required", [])
                if missing_required:
                    errors.append(f"missing_required={','.join(missing_required)}")

        _write_evidence(
            out_dir / "lifecycle_evidence.json",
            command="lifecycle",
            ok=ok,
            errors=errors,
            inputs={"input": _digest_file(args.input)},
            outputs={"bundle_manifest": _digest_file(manifest_path)},
        )

        summary = {
            "ok": ok,
            "bundle_path": str(bundle_dir),
            "bundle_id": manifest.get("bundle_id"),
            "errors": errors,
            "denied_reason": None if ok else "refusal",
        }
        print(_canonical_json(summary))
        return 0
    except HplError as exc:
        errors = [str(exc)]
        _write_evidence(
            out_dir / "lifecycle_evidence.json",
            command="lifecycle",
            ok=False,
            errors=errors,
            inputs={"input": _digest_file(args.input)} if args.input.exists() else {},
            outputs={},
        )
        summary = {
            "ok": False,
            "bundle_path": None,
            "bundle_id": None,
            "errors": errors,
            "denied_reason": "refusal",
        }
        print(_canonical_json(summary))
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


def _load_bundle_module():
    spec = importlib.util.spec_from_file_location("bundle_evidence", BUNDLE_EVIDENCE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


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


def _parse_backends(value: str) -> List[str]:
    parts = [item.strip() for item in value.split(",") if item.strip()]
    return sorted({item.upper() for item in parts}) or ["PYTHON", "CLASSICAL", "QASM"]


def _normalize_backend(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    return value.upper()


def _digest_text(value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _digest_file(path: Path) -> Dict[str, str]:
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    return {"path": path.name, "digest": f"sha256:{digest}"}


if __name__ == "__main__":
    raise SystemExit(main())
