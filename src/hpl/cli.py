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
from . import __version__
from .runtime.context import RuntimeContext
from .runtime.contracts import ExecutionContract
from .runtime.engine import RuntimeEngine
from .audit.constraint_inversion import invert_constraints
from .audit.constraint_witness import build_constraint_witness
from .execution_token import ExecutionToken
from .scheduler import SchedulerContext, plan as plan_program
from .backends.classical_lowering import lower_program_ir_to_backend_ir
from .backends.qasm_lowering import lower_backend_ir_to_qasm
from .runtime.effects.measurement_selection import build_measurement_selection


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PUBLIC_KEY = Path("config/keys/ci_ed25519.pub")
BUNDLE_EVIDENCE_PATH = ROOT / "tools" / "bundle_evidence.py"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="hpl")
    parser.add_argument("--version", action="version", version=f"hpl {__version__}")
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
    bundle_parser.add_argument("--execution-token", type=Path)
    bundle_parser.add_argument("--constraint-witness", type=Path)
    bundle_parser.add_argument("--dual-proposal", type=Path)
    bundle_parser.add_argument("--delta-s-report", type=Path)
    bundle_parser.add_argument("--admissibility-certificate", type=Path)
    bundle_parser.add_argument("--measurement-trace", type=Path)
    bundle_parser.add_argument("--collapse-decision", type=Path)
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
    lifecycle_parser.add_argument("--ecmo-input", type=Path)
    lifecycle_parser.add_argument("--ecmo", type=Path)
    lifecycle_parser.add_argument("--allowed-backends", type=str, default="PYTHON,CLASSICAL,QASM")
    lifecycle_parser.add_argument("--budget-steps", type=int, default=100)
    lifecycle_parser.add_argument("--legacy", action="store_true")

    demo_parser = subparsers.add_parser("demo")
    demo_subparsers = demo_parser.add_subparsers(dest="demo_name", required=True)
    ci_demo = demo_subparsers.add_parser("ci-governance")
    ci_demo.add_argument("--out-dir", type=Path, required=True)
    ci_demo.add_argument("--input", type=Path, default=Path("examples/momentum_trade.hpl"))
    ci_demo.add_argument("--backend", choices=["classical", "qasm"], default="classical")
    ci_demo.add_argument("--coupling-registry", type=Path, default=Path("tests/fixtures/coupling_registry_valid.json"))
    ci_demo.add_argument("--signing-key", type=Path)
    ci_demo.add_argument("--pub", type=Path, default=DEFAULT_PUBLIC_KEY)
    ci_demo.add_argument("--require-epoch", action="store_true")
    ci_demo.add_argument("--anchor", type=Path)
    ci_demo.add_argument("--sig", type=Path)
    ci_demo.add_argument("--quantum-semantics-v1", action="store_true")
    agent_demo = demo_subparsers.add_parser("agent-governance")
    agent_demo.add_argument("--out-dir", type=Path, required=True)
    agent_demo.add_argument("--input", type=Path, default=Path("examples/momentum_trade.hpl"))
    agent_demo.add_argument("--proposal", type=Path, default=Path("tests/fixtures/agent_proposal_allow.json"))
    agent_demo.add_argument("--policy", type=Path, default=Path("tests/fixtures/agent_policy.json"))
    agent_demo.add_argument("--signing-key", type=Path)
    agent_demo.add_argument("--pub", type=Path, default=DEFAULT_PUBLIC_KEY)
    agent_demo.add_argument("--require-epoch", action="store_true")
    agent_demo.add_argument("--anchor", type=Path)
    agent_demo.add_argument("--sig", type=Path)
    trading_demo = demo_subparsers.add_parser("trading-paper")
    trading_demo.add_argument("--out-dir", type=Path, required=True)
    trading_demo.add_argument("--input", type=Path, default=Path("examples/momentum_trade.hpl"))
    trading_demo.add_argument("--market-fixture", type=Path, default=Path("tests/fixtures/trading/price_series_simple.json"))
    trading_demo.add_argument("--policy", type=Path, default=Path("tests/fixtures/trading/policy_safe.json"))
    trading_demo.add_argument("--signing-key", type=Path)
    trading_demo.add_argument("--pub", type=Path, default=DEFAULT_PUBLIC_KEY)
    trading_demo.add_argument("--require-epoch", action="store_true")
    trading_demo.add_argument("--anchor", type=Path)
    trading_demo.add_argument("--sig", type=Path)
    trading_demo.add_argument("--allowed-backends", type=str, default="PYTHON,CLASSICAL")
    trading_demo.add_argument("--budget-steps", type=int, default=100)
    trading_demo.add_argument("--constraint-inversion-v1", action="store_true")
    trading_shadow_demo = demo_subparsers.add_parser("trading-shadow")
    trading_shadow_demo.add_argument("--out-dir", type=Path, required=True)
    trading_shadow_demo.add_argument("--input", type=Path, default=Path("examples/momentum_trade.hpl"))
    trading_shadow_demo.add_argument("--market-fixture", type=Path, default=Path("tests/fixtures/trading/price_series_simple.json"))
    trading_shadow_demo.add_argument("--policy", type=Path, default=Path("tests/fixtures/trading/shadow_policy_safe.json"))
    trading_shadow_demo.add_argument("--shadow-model", type=Path, default=Path("tests/fixtures/trading/shadow_model.json"))
    trading_shadow_demo.add_argument("--signing-key", type=Path)
    trading_shadow_demo.add_argument("--pub", type=Path, default=DEFAULT_PUBLIC_KEY)
    trading_shadow_demo.add_argument("--require-epoch", action="store_true")
    trading_shadow_demo.add_argument("--anchor", type=Path)
    trading_shadow_demo.add_argument("--sig", type=Path)
    trading_shadow_demo.add_argument("--allowed-backends", type=str, default="PYTHON,CLASSICAL")
    trading_shadow_demo.add_argument("--budget-steps", type=int, default=100)
    trading_shadow_demo.add_argument("--constraint-inversion-v1", action="store_true")
    ns_demo = demo_subparsers.add_parser("navier-stokes")
    ns_demo.add_argument("--out-dir", type=Path, required=True)
    ns_demo.add_argument("--input", type=Path, default=Path("examples/momentum_trade.hpl"))
    ns_demo.add_argument("--state", type=Path, default=Path("tests/fixtures/pde/ns_state_initial.json"))
    ns_demo.add_argument("--policy", type=Path, default=Path("tests/fixtures/pde/ns_policy_safe.json"))
    ns_demo.add_argument("--signing-key", type=Path)
    ns_demo.add_argument("--pub", type=Path, default=DEFAULT_PUBLIC_KEY)
    ns_demo.add_argument("--require-epoch", action="store_true")
    ns_demo.add_argument("--anchor", type=Path)
    ns_demo.add_argument("--sig", type=Path)
    ns_demo.add_argument("--allowed-backends", type=str, default="PYTHON,CLASSICAL")
    ns_demo.add_argument("--budget-steps", type=int, default=100)
    ns_demo.add_argument("--constraint-inversion-v1", action="store_true")

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
        if args.command == "demo":
            return _cmd_demo(args)
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
    add_artifact("execution_token", args.execution_token)
    add_artifact("constraint_witness", args.constraint_witness)
    add_artifact("dual_proposal", args.dual_proposal)
    add_artifact("delta_s_report", args.delta_s_report)
    add_artifact("admissibility_certificate", args.admissibility_certificate)
    add_artifact("measurement_trace", args.measurement_trace)
    add_artifact("collapse_decision", args.collapse_decision)

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
    measurement_selection_path = work_dir / "measurement_selection.json"

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

        # ECMO selection (optional)
        ecmo_input = args.ecmo or args.ecmo_input
        selected_track = None
        ecmo_errors: List[str] = []
        require_epoch = args.require_epoch
        backend = args.backend
        constraint_inversion = args.constraint_inversion_v1
        if ecmo_input:
            if not ecmo_input.exists():
                ecmo_errors.append(f"ecmo input not found: {ecmo_input}")
            else:
                boundary_conditions = json.loads(ecmo_input.read_text(encoding="utf-8"))
                selection_result = build_measurement_selection(boundary_conditions)
                if selection_result.ok and selection_result.selection:
                    selected_track = selection_result.selection.get("selected_track")
                    _write_json(measurement_selection_path, selection_result.selection)
                    if selected_track == "B":
                        require_epoch = True
                    elif selected_track == "C":
                        backend = "classical"
                        constraint_inversion = True
                else:
                    ecmo_errors.extend(selection_result.errors)

        # Plan
        use_kernel = not args.legacy
        if ecmo_errors:
            plan_ok = False
            plan_errors = list(ecmo_errors)
            plan_core = {
                "program_id": args.input.stem,
                "status": "denied",
                "steps": [],
                "reasons": list(plan_errors),
            }
            plan_dict = {
                "plan_id": _digest_text(_canonical_json(plan_core)),
                "program_id": args.input.stem,
                "status": "denied",
                "steps": [],
                "reasons": list(plan_errors),
                "verification": None,
                "witness_records": [],
                "execution_token": None,
            }
            _write_json(plan_path, plan_dict)
        else:
            ctx = SchedulerContext(
                require_epoch_verification=require_epoch,
                anchor_path=args.anchor,
                signature_path=args.sig,
                public_key_path=args.pub,
                allowed_backends=_parse_backends(args.allowed_backends),
                budget_steps=args.budget_steps,
                emit_effect_steps=use_kernel,
                backend_target=backend,
                artifact_paths=None,
                ecmo_input_path=args.ecmo_input,
                measurement_selection_path=measurement_selection_path,
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
        if ecmo_errors:
            run_ok = False
            runtime_errors = list(plan_errors)
            runtime_dict = {
                "result_id": _digest_text(_canonical_json({"status": "denied", "reasons": runtime_errors})),
                "status": "denied",
                "reasons": list(runtime_errors),
                "steps": [],
                "verification": None,
                "witness_records": [],
                "constraint_witnesses": [],
                "transcript": [],
            }
        else:
            token_dict = plan_dict.get("execution_token")
            execution_token = None
            if isinstance(token_dict, dict):
                execution_token = ExecutionToken.from_dict(token_dict)
            runtime_ctx = RuntimeContext(
                epoch_anchor_path=args.anchor,
                epoch_sig_path=args.sig,
                ci_pubkey_path=args.pub,
                execution_token=execution_token,
                requested_backend=_normalize_backend(backend),
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
                require_epoch_verification=False if use_kernel else require_epoch,
                require_signature_verification=False if use_kernel else bool(args.sig) if require_epoch else False,
                required_backend=None if use_kernel else _normalize_backend(backend),
            )
            runtime_result = RuntimeEngine().run(plan_dict, runtime_ctx, contract)
            runtime_dict = runtime_result.to_dict()
            run_ok = runtime_result.status == "completed"
            runtime_errors = list(runtime_result.reasons)

        _write_json(runtime_path, runtime_dict)
        _write_evidence(
            work_dir / "run_evidence.json",
            command="run",
            ok=run_ok,
            errors=list(runtime_errors),
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
            constraint_list = runtime_dict.get("constraint_witnesses", [])
            if isinstance(constraint_list, list) and constraint_list:
                constraint_witness = constraint_list[0]
        if constraint_witness:
            dual_proposal = invert_constraints(constraint_witness)
            _write_json(work_dir / "constraint_witness.json", constraint_witness)
            _write_json(work_dir / "dual_proposal.json", dual_proposal)

        # Lower
        if not use_kernel:
            backend_ir = lower_program_ir_to_backend_ir(program_ir, target=backend).to_dict()
            _write_json(backend_ir_path, backend_ir)
            output_digests = {"backend_ir": _digest_text_value(_canonical_json(backend_ir))}
            if backend == "qasm":
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
        if backend == "qasm":
            if qasm_path.exists():
                artifacts.append(bundle_module._artifact("qasm", qasm_path))
        if measurement_selection_path.exists():
            artifacts.append(
                bundle_module._artifact("measurement_selection", measurement_selection_path)
            )
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
        delta_s_report = work_dir / "delta_s_report.json"
        admissibility_certificate = work_dir / "admissibility_certificate.json"
        measurement_trace = work_dir / "measurement_trace.json"
        collapse_decision = work_dir / "collapse_decision.json"
        if delta_s_report.exists():
            artifacts.append(bundle_module._artifact("delta_s_report", delta_s_report))
        if admissibility_certificate.exists():
            artifacts.append(bundle_module._artifact("admissibility_certificate", admissibility_certificate))
        if measurement_trace.exists():
            artifacts.append(bundle_module._artifact("measurement_trace", measurement_trace))
        if collapse_decision.exists():
            artifacts.append(bundle_module._artifact("collapse_decision", collapse_decision))

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
        if runtime_errors:
            errors.extend(runtime_errors)
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


def _cmd_demo(args: argparse.Namespace) -> int:
    if args.demo_name == "ci-governance":
        return _cmd_demo_ci_governance(args)
    if args.demo_name == "agent-governance":
        return _cmd_demo_agent_governance(args)
    if args.demo_name == "trading-paper":
        return _cmd_demo_trading_paper(args)
    if args.demo_name == "trading-shadow":
        return _cmd_demo_trading_shadow(args)
    if args.demo_name == "navier-stokes":
        return _cmd_demo_navier_stokes(args)
    print(_canonical_json({"ok": False, "errors": ["unknown demo"]}))
    return 0


def _cmd_demo_ci_governance(args: argparse.Namespace) -> int:
    out_dir = args.out_dir
    work_dir = out_dir / "work"
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    repo_state_path = work_dir / "repo_state.json"
    repo_state_path.write_text(_canonical_json({"clean": True}), encoding="utf-8")
    repo_state_rel = Path("repo_state.json")

    program_ir_path = work_dir / "program.ir.json"
    plan_path = work_dir / "plan.json"
    runtime_path = work_dir / "runtime.json"
    backend_ir_path = work_dir / "backend.ir.json"

    bundle_module = _load_bundle_module()
    errors: List[str] = []

    try:
        program = parse_file(str(args.input))
        expanded = expand_program(program)
        validate_program(expanded)
        program_ir = emit_program_ir(expanded, program_id=args.input.stem)
        _write_json(program_ir_path, program_ir)

        coupling_registry = _relative_to_root(args.coupling_registry)
        ctx = SchedulerContext(
            require_epoch_verification=args.require_epoch,
            anchor_path=args.anchor,
            signature_path=args.sig,
            public_key_path=args.pub,
            allowed_backends=_parse_backends("PYTHON,CLASSICAL,QASM"),
            budget_steps=100,
            emit_effect_steps=True,
            backend_target=args.backend,
            artifact_paths={
                "backend_ir": "backend.ir.json",
            },
            track="ci_governance",
            ci_repo_state_path=repo_state_rel,
            ci_coupling_registry_path=coupling_registry,
        )
        plan_obj = plan_program(program_ir, ctx)
        plan_dict = plan_obj.to_dict()
        _write_json(plan_path, plan_dict)

        plan_ok = plan_obj.status == "planned"
        if not plan_ok:
            errors.extend(plan_obj.reasons)

        token_dict = plan_dict.get("execution_token")
        execution_token = ExecutionToken.from_dict(token_dict) if isinstance(token_dict, dict) else None
        runtime_ctx = RuntimeContext(
            epoch_anchor_path=args.anchor,
            epoch_sig_path=args.sig,
            ci_pubkey_path=args.pub,
            execution_token=execution_token,
            requested_backend=_normalize_backend(args.backend),
            trace_sink=work_dir,
        )
        allowed_steps = {str(step.get("step_id")) for step in plan_dict.get("steps", []) if isinstance(step, dict) and step.get("step_id")}
        contract = ExecutionContract(allowed_steps=allowed_steps)
        runtime_result = RuntimeEngine().run(plan_dict, runtime_ctx, contract)
        runtime_dict = runtime_result.to_dict()
        _write_json(runtime_path, runtime_dict)

        run_ok = runtime_result.status == "completed"
        if runtime_result.reasons:
            errors.extend(runtime_result.reasons)

        artifacts = [
            bundle_module._artifact("program_ir", program_ir_path),
            bundle_module._artifact("plan", plan_path),
            bundle_module._artifact("runtime_result", runtime_path),
        ]
        if backend_ir_path.exists():
            artifacts.append(bundle_module._artifact("backend_ir", backend_ir_path))
        if token_dict:
            token_path = work_dir / "execution_token.json"
            _write_json(token_path, token_dict)
            artifacts.append(bundle_module._artifact("execution_token", token_path))

        bundle_dir, manifest = bundle_module.build_bundle(
            out_dir=out_dir,
            artifacts=artifacts,
            epoch_anchor=args.anchor if args.anchor and args.anchor.exists() else None,
            epoch_sig=args.sig if args.sig and args.sig.exists() else None,
            public_key=args.pub,
            quantum_semantics_v1=args.quantum_semantics_v1,
        )
        manifest_path = bundle_dir / "bundle_manifest.json"
        manifest_path.write_text(bundle_module._canonical_json(manifest), encoding="utf-8")

        if not args.signing_key:
            errors.append("signing_key required for ci-governance demo")
        else:
            sig_path = bundle_module.sign_bundle_manifest(manifest_path, args.signing_key)
            ok, sig_errors = bundle_module.verify_bundle_manifest_signature(
                manifest_path,
                sig_path,
                args.pub,
            )
            if not ok:
                errors.extend(sig_errors)

        if args.quantum_semantics_v1:
            quantum_module = _load_tool_module("validate_quantum_execution_semantics", ROOT / "tools" / "validate_quantum_execution_semantics.py")
            quantum_result = quantum_module.validate_quantum_execution_semantics(
                program_ir=program_ir_path,
                plan=plan_path,
                runtime_result=runtime_path,
                backend_ir=backend_ir_path if backend_ir_path.exists() else None,
                qasm=None,
                bundle_manifest=manifest_path,
            )
            if not quantum_result.get("ok", False):
                errors.extend(quantum_result.get("errors", []))

        ok = plan_ok and run_ok and not errors
        constraint_witness = None
        dual_proposal = None
        if not ok:
            constraint_witness = build_constraint_witness(
                stage="ci_governance_refusal",
                refusal_reasons=errors,
                artifact_digests={"plan": _digest_text(_canonical_json(plan_dict))},
                observer_id="papas",
                timestamp=None,
            )
            dual_proposal = invert_constraints(constraint_witness)
            _write_json(work_dir / "constraint_witness.json", constraint_witness)
            _write_json(work_dir / "dual_proposal.json", dual_proposal)

            artifacts.append(bundle_module._artifact("constraint_witness", work_dir / "constraint_witness.json"))
            artifacts.append(bundle_module._artifact("dual_proposal", work_dir / "dual_proposal.json"))

            bundle_dir, manifest = bundle_module.build_bundle(
                out_dir=out_dir,
                artifacts=artifacts,
                epoch_anchor=args.anchor if args.anchor and args.anchor.exists() else None,
                epoch_sig=args.sig if args.sig and args.sig.exists() else None,
                public_key=args.pub,
                quantum_semantics_v1=args.quantum_semantics_v1,
            )
            manifest_path = bundle_dir / "bundle_manifest.json"
            manifest_path.write_text(bundle_module._canonical_json(manifest), encoding="utf-8")
            if args.signing_key:
                sig_path = bundle_module.sign_bundle_manifest(manifest_path, args.signing_key)
                ok_sig, sig_errors = bundle_module.verify_bundle_manifest_signature(
                    manifest_path,
                    sig_path,
                    args.pub,
                )
                if not ok_sig:
                    errors.extend(sig_errors)

        summary = {
            "ok": ok,
            "bundle_path": str(bundle_dir),
            "bundle_id": manifest.get("bundle_id"),
            "errors": list(errors),
            "denied_reason": None if ok else "refusal",
        }
        print(_canonical_json(summary))
        return 0
    except HplError as exc:
        summary = {"ok": False, "errors": [str(exc)], "bundle_path": None, "bundle_id": None}
        print(_canonical_json(summary))
        return 0


def _cmd_demo_agent_governance(args: argparse.Namespace) -> int:
    out_dir = args.out_dir
    work_dir = out_dir / "work"
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    proposal_path = work_dir / "agent_proposal.json"
    policy_path = work_dir / "agent_policy.json"
    decision_path = work_dir / "agent_decision.json"

    program_ir_path = work_dir / "program.ir.json"
    plan_path = work_dir / "plan.json"
    runtime_path = work_dir / "runtime.json"

    bundle_module = _load_bundle_module()
    errors: List[str] = []

    try:
        program = parse_file(str(args.input))
        expanded = expand_program(program)
        validate_program(expanded)
        program_ir = emit_program_ir(expanded, program_id=args.input.stem)
        _write_json(program_ir_path, program_ir)

        try:
            proposal = json.loads(args.proposal.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise HplError(f"proposal invalid json: {args.proposal}") from exc
        try:
            policy = json.loads(args.policy.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise HplError(f"policy invalid json: {args.policy}") from exc
        proposal_path.write_text(_canonical_json(proposal), encoding="utf-8")
        policy_path.write_text(_canonical_json(policy), encoding="utf-8")

        ctx = SchedulerContext(
            require_epoch_verification=args.require_epoch,
            anchor_path=args.anchor,
            signature_path=args.sig,
            public_key_path=args.pub,
            allowed_backends=_parse_backends("PYTHON,CLASSICAL,QASM"),
            budget_steps=100,
            emit_effect_steps=True,
            track="agent_governance",
            agent_proposal_path=Path("agent_proposal.json"),
            agent_policy_path=Path("agent_policy.json"),
            agent_decision_path=Path("agent_decision.json"),
        )
        plan_obj = plan_program(program_ir, ctx)
        plan_dict = plan_obj.to_dict()
        _write_json(plan_path, plan_dict)

        plan_ok = plan_obj.status == "planned"
        if not plan_ok:
            errors.extend(plan_obj.reasons)

        token_dict = plan_dict.get("execution_token")
        execution_token = ExecutionToken.from_dict(token_dict) if isinstance(token_dict, dict) else None
        runtime_ctx = RuntimeContext(
            epoch_anchor_path=args.anchor,
            epoch_sig_path=args.sig,
            ci_pubkey_path=args.pub,
            execution_token=execution_token,
            trace_sink=work_dir,
        )
        allowed_steps = {
            str(step.get("step_id"))
            for step in plan_dict.get("steps", [])
            if isinstance(step, dict) and step.get("step_id")
        }
        contract = ExecutionContract(allowed_steps=allowed_steps)
        runtime_result = RuntimeEngine().run(plan_dict, runtime_ctx, contract)
        runtime_dict = runtime_result.to_dict()
        _write_json(runtime_path, runtime_dict)

        run_ok = runtime_result.status == "completed"
        if runtime_result.reasons:
            errors.extend(runtime_result.reasons)

        artifacts = [
            bundle_module._artifact("program_ir", program_ir_path),
            bundle_module._artifact("plan", plan_path),
            bundle_module._artifact("runtime_result", runtime_path),
            bundle_module._artifact("agent_proposal", proposal_path),
            bundle_module._artifact("agent_policy", policy_path),
        ]
        if decision_path.exists():
            artifacts.append(bundle_module._artifact("agent_decision", decision_path))
        if token_dict:
            token_path = work_dir / "execution_token.json"
            _write_json(token_path, token_dict)
            artifacts.append(bundle_module._artifact("execution_token", token_path))

        bundle_dir, manifest = bundle_module.build_bundle(
            out_dir=out_dir,
            artifacts=artifacts,
            epoch_anchor=args.anchor if args.anchor and args.anchor.exists() else None,
            epoch_sig=args.sig if args.sig and args.sig.exists() else None,
            public_key=args.pub,
        )
        manifest_path = bundle_dir / "bundle_manifest.json"
        manifest_path.write_text(bundle_module._canonical_json(manifest), encoding="utf-8")

        if not args.signing_key:
            errors.append("signing_key required for agent-governance demo")
        else:
            sig_path = bundle_module.sign_bundle_manifest(manifest_path, args.signing_key)
            ok, sig_errors = bundle_module.verify_bundle_manifest_signature(
                manifest_path,
                sig_path,
                args.pub,
            )
            if not ok:
                errors.extend(sig_errors)

        ok = plan_ok and run_ok and not errors
        constraint_witness = None
        dual_proposal = None
        if not ok:
            constraint_witness = build_constraint_witness(
                stage="agent_governance_refusal",
                refusal_reasons=errors,
                artifact_digests={"plan": _digest_text(_canonical_json(plan_dict))},
                observer_id="papas",
                timestamp=None,
            )
            dual_proposal = invert_constraints(constraint_witness)
            _write_json(work_dir / "constraint_witness.json", constraint_witness)
            _write_json(work_dir / "dual_proposal.json", dual_proposal)

            artifacts.append(bundle_module._artifact("constraint_witness", work_dir / "constraint_witness.json"))
            artifacts.append(bundle_module._artifact("dual_proposal", work_dir / "dual_proposal.json"))

            bundle_dir, manifest = bundle_module.build_bundle(
                out_dir=out_dir,
                artifacts=artifacts,
                epoch_anchor=args.anchor if args.anchor and args.anchor.exists() else None,
                epoch_sig=args.sig if args.sig and args.sig.exists() else None,
                public_key=args.pub,
            )
            manifest_path = bundle_dir / "bundle_manifest.json"
            manifest_path.write_text(bundle_module._canonical_json(manifest), encoding="utf-8")
            if args.signing_key:
                sig_path = bundle_module.sign_bundle_manifest(manifest_path, args.signing_key)
                ok_sig, sig_errors = bundle_module.verify_bundle_manifest_signature(
                    manifest_path,
                    sig_path,
                    args.pub,
                )
                if not ok_sig:
                    errors.extend(sig_errors)

        summary = {
            "ok": ok,
            "bundle_path": str(bundle_dir),
            "bundle_id": manifest.get("bundle_id"),
            "errors": list(errors),
            "denied_reason": None if ok else "refusal",
        }
        print(_canonical_json(summary))
        return 0
    except HplError as exc:
        summary = {"ok": False, "errors": [str(exc)], "bundle_path": None, "bundle_id": None}
        print(_canonical_json(summary))
        return 0


def _cmd_demo_trading_paper(args: argparse.Namespace) -> int:
    out_dir = args.out_dir
    work_dir = out_dir / "work"
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    program_ir_path = work_dir / "program.ir.json"
    plan_path = work_dir / "plan.json"
    runtime_path = work_dir / "runtime.json"
    report_json_path = work_dir / "trade_report.json"
    report_md_path = work_dir / "trade_report.md"

    bundle_module = _load_bundle_module()
    errors: List[str] = []

    try:
        program = parse_file(str(args.input))
        expanded = expand_program(program)
        validate_program(expanded)
        program_ir = emit_program_ir(expanded, program_id=args.input.stem)
        _write_json(program_ir_path, program_ir)

        fixture_path = _relative_to_root(args.market_fixture)
        policy_path = _relative_to_root(args.policy)

        ctx = SchedulerContext(
            require_epoch_verification=args.require_epoch,
            anchor_path=args.anchor,
            signature_path=args.sig,
            public_key_path=args.pub,
            allowed_backends=_parse_backends(args.allowed_backends),
            budget_steps=args.budget_steps,
            emit_effect_steps=True,
            track="trading_paper_mode",
            trading_fixture_path=fixture_path,
            trading_policy_path=policy_path,
            trading_report_json_path=Path("trade_report.json"),
            trading_report_md_path=Path("trade_report.md"),
        )
        plan_obj = plan_program(program_ir, ctx)
        plan_dict = plan_obj.to_dict()
        _write_json(plan_path, plan_dict)

        plan_ok = plan_obj.status == "planned"
        if not plan_ok:
            errors.extend(plan_obj.reasons)

        token_dict = plan_dict.get("execution_token")
        execution_token = ExecutionToken.from_dict(token_dict) if isinstance(token_dict, dict) else None
        runtime_ctx = RuntimeContext(
            epoch_anchor_path=args.anchor,
            epoch_sig_path=args.sig,
            ci_pubkey_path=args.pub,
            execution_token=execution_token,
            trace_sink=work_dir,
        )
        allowed_steps = {
            str(step.get("step_id"))
            for step in plan_dict.get("steps", [])
            if isinstance(step, dict) and step.get("step_id")
        }
        contract = ExecutionContract(allowed_steps=allowed_steps)
        runtime_result = RuntimeEngine().run(plan_dict, runtime_ctx, contract)
        runtime_dict = runtime_result.to_dict()
        _write_json(runtime_path, runtime_dict)

        run_ok = runtime_result.status == "completed"
        if runtime_result.reasons:
            errors.extend(runtime_result.reasons)

        artifacts = [
            bundle_module._artifact("program_ir", program_ir_path),
            bundle_module._artifact("plan", plan_path),
            bundle_module._artifact("runtime_result", runtime_path),
            bundle_module._artifact("market_fixture", args.market_fixture),
            bundle_module._artifact("trade_policy", args.policy),
        ]
        if report_json_path.exists():
            artifacts.append(bundle_module._artifact("trade_report", report_json_path))
        if report_md_path.exists():
            artifacts.append(bundle_module._artifact("trade_report_md", report_md_path))
        if token_dict:
            token_path = work_dir / "execution_token.json"
            _write_json(token_path, token_dict)
            artifacts.append(bundle_module._artifact("execution_token", token_path))

        bundle_dir, manifest = bundle_module.build_bundle(
            out_dir=out_dir,
            artifacts=artifacts,
            epoch_anchor=args.anchor if args.anchor and args.anchor.exists() else None,
            epoch_sig=args.sig if args.sig and args.sig.exists() else None,
            public_key=args.pub,
            constraint_inversion_v1=args.constraint_inversion_v1,
        )
        manifest_path = bundle_dir / "bundle_manifest.json"
        manifest_path.write_text(bundle_module._canonical_json(manifest), encoding="utf-8")

        if not args.signing_key:
            errors.append("signing_key required for trading-paper demo")
        else:
            sig_path = bundle_module.sign_bundle_manifest(manifest_path, args.signing_key)
            ok, sig_errors = bundle_module.verify_bundle_manifest_signature(
                manifest_path,
                sig_path,
                args.pub,
            )
            if not ok:
                errors.extend(sig_errors)

        ok = plan_ok and run_ok and not errors
        constraint_witness = None
        dual_proposal = None
        if not ok:
            constraint_witness = build_constraint_witness(
                stage="trading_paper_refusal",
                refusal_reasons=errors,
                artifact_digests={"plan": _digest_text(_canonical_json(plan_dict))},
                observer_id="papas",
                timestamp=None,
            )
            dual_proposal = invert_constraints(constraint_witness)
            _write_json(work_dir / "constraint_witness.json", constraint_witness)
            _write_json(work_dir / "dual_proposal.json", dual_proposal)

            artifacts.append(bundle_module._artifact("constraint_witness", work_dir / "constraint_witness.json"))
            artifacts.append(bundle_module._artifact("dual_proposal", work_dir / "dual_proposal.json"))

            bundle_dir, manifest = bundle_module.build_bundle(
                out_dir=out_dir,
                artifacts=artifacts,
                epoch_anchor=args.anchor if args.anchor and args.anchor.exists() else None,
                epoch_sig=args.sig if args.sig and args.sig.exists() else None,
                public_key=args.pub,
                constraint_inversion_v1=args.constraint_inversion_v1,
            )
            manifest_path = bundle_dir / "bundle_manifest.json"
            manifest_path.write_text(bundle_module._canonical_json(manifest), encoding="utf-8")
            if args.signing_key:
                sig_path = bundle_module.sign_bundle_manifest(manifest_path, args.signing_key)
                ok_sig, sig_errors = bundle_module.verify_bundle_manifest_signature(
                    manifest_path,
                    sig_path,
                    args.pub,
                )
                if not ok_sig:
                    errors.extend(sig_errors)

        summary = {
            "ok": ok,
            "bundle_path": str(bundle_dir),
            "bundle_id": manifest.get("bundle_id"),
            "errors": list(errors),
            "denied_reason": None if ok else "refusal",
        }
        print(_canonical_json(summary))
        return 0
    except HplError as exc:
        summary = {"ok": False, "errors": [str(exc)], "bundle_path": None, "bundle_id": None}
        print(_canonical_json(summary))
        return 0


def _cmd_demo_trading_shadow(args: argparse.Namespace) -> int:
    out_dir = args.out_dir
    work_dir = out_dir / "work"
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    program_ir_path = work_dir / "program.ir.json"
    plan_path = work_dir / "plan.json"
    runtime_path = work_dir / "runtime.json"
    report_json_path = work_dir / "trade_report.json"
    report_md_path = work_dir / "trade_report.md"
    shadow_model_path = work_dir / "shadow_model.json"
    shadow_seed_path = work_dir / "shadow_seed.json"
    shadow_log_path = work_dir / "shadow_execution_log.json"
    shadow_ledger_path = work_dir / "shadow_trade_ledger.json"

    bundle_module = _load_bundle_module()
    errors: List[str] = []

    try:
        program = parse_file(str(args.input))
        expanded = expand_program(program)
        validate_program(expanded)
        program_ir = emit_program_ir(expanded, program_id=args.input.stem)
        _write_json(program_ir_path, program_ir)

        fixture_path = _relative_to_root(args.market_fixture)
        policy_path = _relative_to_root(args.policy)
        model_path = _relative_to_root(args.shadow_model)

        ctx = SchedulerContext(
            require_epoch_verification=args.require_epoch,
            anchor_path=args.anchor,
            signature_path=args.sig,
            public_key_path=args.pub,
            allowed_backends=_parse_backends(args.allowed_backends),
            budget_steps=args.budget_steps,
            emit_effect_steps=True,
            track="trading_shadow_mode",
            trading_fixture_path=fixture_path,
            trading_policy_path=policy_path,
            trading_shadow_model_path=model_path,
            trading_report_json_path=Path("trade_report.json"),
            trading_report_md_path=Path("trade_report.md"),
        )
        plan_obj = plan_program(program_ir, ctx)
        plan_dict = plan_obj.to_dict()
        _write_json(plan_path, plan_dict)

        plan_ok = plan_obj.status == "planned"
        if not plan_ok:
            errors.extend(plan_obj.reasons)

        token_dict = plan_dict.get("execution_token")
        execution_token = ExecutionToken.from_dict(token_dict) if isinstance(token_dict, dict) else None
        runtime_ctx = RuntimeContext(
            epoch_anchor_path=args.anchor,
            epoch_sig_path=args.sig,
            ci_pubkey_path=args.pub,
            execution_token=execution_token,
            trace_sink=work_dir,
        )
        allowed_steps = {
            str(step.get("step_id"))
            for step in plan_dict.get("steps", [])
            if isinstance(step, dict) and step.get("step_id")
        }
        contract = ExecutionContract(allowed_steps=allowed_steps)
        runtime_result = RuntimeEngine().run(plan_dict, runtime_ctx, contract)
        runtime_dict = runtime_result.to_dict()
        _write_json(runtime_path, runtime_dict)

        run_ok = runtime_result.status == "completed"
        if runtime_result.reasons:
            errors.extend(runtime_result.reasons)

        artifacts = [
            bundle_module._artifact("program_ir", program_ir_path),
            bundle_module._artifact("plan", plan_path),
            bundle_module._artifact("runtime_result", runtime_path),
            bundle_module._artifact("market_fixture", args.market_fixture),
            bundle_module._artifact("trade_policy", args.policy),
            bundle_module._artifact("shadow_model", args.shadow_model),
        ]
        if shadow_model_path.exists():
            artifacts.append(bundle_module._artifact("shadow_model_output", shadow_model_path))
        if shadow_seed_path.exists():
            artifacts.append(bundle_module._artifact("shadow_seed", shadow_seed_path))
        if shadow_log_path.exists():
            artifacts.append(bundle_module._artifact("shadow_execution_log", shadow_log_path))
        if shadow_ledger_path.exists():
            artifacts.append(bundle_module._artifact("shadow_trade_ledger", shadow_ledger_path))
        if report_json_path.exists():
            artifacts.append(bundle_module._artifact("trade_report", report_json_path))
        if report_md_path.exists():
            artifacts.append(bundle_module._artifact("trade_report_md", report_md_path))
        if token_dict:
            token_path = work_dir / "execution_token.json"
            _write_json(token_path, token_dict)
            artifacts.append(bundle_module._artifact("execution_token", token_path))

        bundle_dir, manifest = bundle_module.build_bundle(
            out_dir=out_dir,
            artifacts=artifacts,
            epoch_anchor=args.anchor if args.anchor and args.anchor.exists() else None,
            epoch_sig=args.sig if args.sig and args.sig.exists() else None,
            public_key=args.pub,
            constraint_inversion_v1=args.constraint_inversion_v1,
        )
        manifest_path = bundle_dir / "bundle_manifest.json"
        manifest_path.write_text(bundle_module._canonical_json(manifest), encoding="utf-8")

        if not args.signing_key:
            errors.append("signing_key required for trading-shadow demo")
        else:
            sig_path = bundle_module.sign_bundle_manifest(manifest_path, args.signing_key)
            ok, sig_errors = bundle_module.verify_bundle_manifest_signature(
                manifest_path,
                sig_path,
                args.pub,
            )
            if not ok:
                errors.extend(sig_errors)

        ok = plan_ok and run_ok and not errors
        constraint_witness = None
        dual_proposal = None
        if not ok:
            constraint_witness = build_constraint_witness(
                stage="trading_shadow_refusal",
                refusal_reasons=errors,
                artifact_digests={"plan": _digest_text(_canonical_json(plan_dict))},
                observer_id="papas",
                timestamp=None,
            )
            dual_proposal = invert_constraints(constraint_witness)
            _write_json(work_dir / "constraint_witness.json", constraint_witness)
            _write_json(work_dir / "dual_proposal.json", dual_proposal)

            artifacts.append(bundle_module._artifact("constraint_witness", work_dir / "constraint_witness.json"))
            artifacts.append(bundle_module._artifact("dual_proposal", work_dir / "dual_proposal.json"))

            bundle_dir, manifest = bundle_module.build_bundle(
                out_dir=out_dir,
                artifacts=artifacts,
                epoch_anchor=args.anchor if args.anchor and args.anchor.exists() else None,
                epoch_sig=args.sig if args.sig and args.sig.exists() else None,
                public_key=args.pub,
                constraint_inversion_v1=args.constraint_inversion_v1,
            )
            manifest_path = bundle_dir / "bundle_manifest.json"
            manifest_path.write_text(bundle_module._canonical_json(manifest), encoding="utf-8")
            if args.signing_key:
                sig_path = bundle_module.sign_bundle_manifest(manifest_path, args.signing_key)
                ok_sig, sig_errors = bundle_module.verify_bundle_manifest_signature(
                    manifest_path,
                    sig_path,
                    args.pub,
                )
                if not ok_sig:
                    errors.extend(sig_errors)

        summary = {
            "ok": ok,
            "bundle_path": str(bundle_dir),
            "bundle_id": manifest.get("bundle_id"),
            "errors": list(errors),
            "denied_reason": None if ok else "refusal",
        }
        print(_canonical_json(summary))
        return 0
    except HplError as exc:
        summary = {"ok": False, "errors": [str(exc)], "bundle_path": None, "bundle_id": None}
        print(_canonical_json(summary))
        return 0


def _cmd_demo_navier_stokes(args: argparse.Namespace) -> int:
    out_dir = args.out_dir
    work_dir = out_dir / "work"
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    program_ir_path = work_dir / "program.ir.json"
    plan_path = work_dir / "plan.json"
    runtime_path = work_dir / "runtime.json"
    state_final_path = work_dir / "ns_state_final.json"
    observables_path = work_dir / "ns_observables.json"
    pressure_path = work_dir / "ns_pressure.json"
    gate_path = work_dir / "ns_gate_certificate.json"

    bundle_module = _load_bundle_module()
    errors: List[str] = []

    try:
        program = parse_file(str(args.input))
        expanded = expand_program(program)
        validate_program(expanded)
        program_ir = emit_program_ir(expanded, program_id=args.input.stem)
        _write_json(program_ir_path, program_ir)

        state_path = _relative_to_root(args.state)
        policy_path = _relative_to_root(args.policy)

        ctx = SchedulerContext(
            require_epoch_verification=args.require_epoch,
            anchor_path=args.anchor,
            signature_path=args.sig,
            public_key_path=args.pub,
            allowed_backends=_parse_backends(args.allowed_backends),
            budget_steps=args.budget_steps,
            emit_effect_steps=True,
            track="navier_stokes",
            ns_state_path=state_path,
            ns_policy_path=policy_path,
            ns_state_final_path=Path("ns_state_final.json"),
            ns_observables_path=Path("ns_observables.json"),
            ns_pressure_path=Path("ns_pressure.json"),
            ns_gate_certificate_path=Path("ns_gate_certificate.json"),
        )
        plan_obj = plan_program(program_ir, ctx)
        plan_dict = plan_obj.to_dict()
        _write_json(plan_path, plan_dict)

        plan_ok = plan_obj.status == "planned"
        if not plan_ok:
            errors.extend(plan_obj.reasons)

        token_dict = plan_dict.get("execution_token")
        execution_token = ExecutionToken.from_dict(token_dict) if isinstance(token_dict, dict) else None
        runtime_ctx = RuntimeContext(
            epoch_anchor_path=args.anchor,
            epoch_sig_path=args.sig,
            ci_pubkey_path=args.pub,
            execution_token=execution_token,
            trace_sink=work_dir,
        )
        allowed_steps = {
            str(step.get("step_id"))
            for step in plan_dict.get("steps", [])
            if isinstance(step, dict) and step.get("step_id")
        }
        contract = ExecutionContract(allowed_steps=allowed_steps)
        runtime_result = RuntimeEngine().run(plan_dict, runtime_ctx, contract)
        runtime_dict = runtime_result.to_dict()
        _write_json(runtime_path, runtime_dict)

        run_ok = runtime_result.status == "completed"
        if runtime_result.reasons:
            errors.extend(runtime_result.reasons)

        artifacts = [
            bundle_module._artifact("program_ir", program_ir_path),
            bundle_module._artifact("plan", plan_path),
            bundle_module._artifact("runtime_result", runtime_path),
            bundle_module._artifact("pde_state", args.state),
            bundle_module._artifact("pde_policy", args.policy),
        ]
        if state_final_path.exists():
            artifacts.append(bundle_module._artifact("pde_state_final", state_final_path))
        if observables_path.exists():
            artifacts.append(bundle_module._artifact("pde_observables", observables_path))
        if pressure_path.exists():
            artifacts.append(bundle_module._artifact("pde_pressure", pressure_path))
        if gate_path.exists():
            artifacts.append(bundle_module._artifact("pde_gate_certificate", gate_path))
        if token_dict:
            token_path = work_dir / "execution_token.json"
            _write_json(token_path, token_dict)
            artifacts.append(bundle_module._artifact("execution_token", token_path))

        bundle_dir, manifest = bundle_module.build_bundle(
            out_dir=out_dir,
            artifacts=artifacts,
            epoch_anchor=args.anchor if args.anchor and args.anchor.exists() else None,
            epoch_sig=args.sig if args.sig and args.sig.exists() else None,
            public_key=args.pub,
            constraint_inversion_v1=args.constraint_inversion_v1,
        )
        manifest_path = bundle_dir / "bundle_manifest.json"
        manifest_path.write_text(bundle_module._canonical_json(manifest), encoding="utf-8")

        if not args.signing_key:
            errors.append("signing_key required for navier-stokes demo")
        else:
            sig_path = bundle_module.sign_bundle_manifest(manifest_path, args.signing_key)
            ok, sig_errors = bundle_module.verify_bundle_manifest_signature(
                manifest_path,
                sig_path,
                args.pub,
            )
            if not ok:
                errors.extend(sig_errors)

        ok = plan_ok and run_ok and not errors
        constraint_witness = None
        dual_proposal = None
        if not ok:
            constraint_witness = build_constraint_witness(
                stage="navier_stokes_refusal",
                refusal_reasons=errors,
                artifact_digests={"plan": _digest_text(_canonical_json(plan_dict))},
                observer_id="papas",
                timestamp=None,
            )
            dual_proposal = invert_constraints(constraint_witness)
            _write_json(work_dir / "constraint_witness.json", constraint_witness)
            _write_json(work_dir / "dual_proposal.json", dual_proposal)

            artifacts.append(bundle_module._artifact("constraint_witness", work_dir / "constraint_witness.json"))
            artifacts.append(bundle_module._artifact("dual_proposal", work_dir / "dual_proposal.json"))

            bundle_dir, manifest = bundle_module.build_bundle(
                out_dir=out_dir,
                artifacts=artifacts,
                epoch_anchor=args.anchor if args.anchor and args.anchor.exists() else None,
                epoch_sig=args.sig if args.sig and args.sig.exists() else None,
                public_key=args.pub,
                constraint_inversion_v1=args.constraint_inversion_v1,
            )
            manifest_path = bundle_dir / "bundle_manifest.json"
            manifest_path.write_text(bundle_module._canonical_json(manifest), encoding="utf-8")
            if args.signing_key:
                sig_path = bundle_module.sign_bundle_manifest(manifest_path, args.signing_key)
                ok_sig, sig_errors = bundle_module.verify_bundle_manifest_signature(
                    manifest_path,
                    sig_path,
                    args.pub,
                )
                if not ok_sig:
                    errors.extend(sig_errors)

        summary = {
            "ok": ok,
            "bundle_path": str(bundle_dir),
            "bundle_id": manifest.get("bundle_id"),
            "errors": list(errors),
            "denied_reason": None if ok else "refusal",
        }
        print(_canonical_json(summary))
        return 0
    except HplError as exc:
        summary = {"ok": False, "errors": [str(exc)], "bundle_path": None, "bundle_id": None}
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


def _load_tool_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
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


def _relative_to_root(path: Path) -> Path:
    try:
        return path.relative_to(ROOT)
    except ValueError:
        return path


if __name__ == "__main__":
    raise SystemExit(main())
