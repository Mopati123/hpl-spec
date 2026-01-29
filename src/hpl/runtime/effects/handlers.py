from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Dict, List, Optional

from ...audit.constraint_inversion import invert_constraints
from ...backends.classical_lowering import lower_program_ir_to_backend_ir
from ...backends.qasm_lowering import lower_backend_ir_to_qasm
from ..context import RuntimeContext
from .effect_step import EffectResult, EffectStep
from .measurement_selection import build_measurement_selection


ROOT = Path(__file__).resolve().parents[4]
VERIFY_EPOCH_PATH = ROOT / "tools" / "verify_epoch.py"
VERIFY_SIGNATURE_PATH = ROOT / "tools" / "verify_anchor_signature.py"
BUNDLE_EVIDENCE_PATH = ROOT / "tools" / "bundle_evidence.py"
VALIDATE_REGISTRIES_PATH = ROOT / "tools" / "validate_operator_registries.py"
VALIDATE_COUPLING_PATH = ROOT / "tools" / "validate_coupling_topology.py"
VALIDATE_QUANTUM_PATH = ROOT / "tools" / "validate_quantum_execution_semantics.py"


def handle_noop(step: EffectStep, ctx: RuntimeContext) -> EffectResult:
    return _ok(step, {})


def handle_emit_artifact(step: EffectStep, ctx: RuntimeContext) -> EffectResult:
    args = step.args
    path = _resolve_output_path(ctx, args)
    if path is None:
        return _refuse(step, "MissingArtifactPath", ["missing artifact path"])
    payload = args.get("payload", {})
    fmt = str(args.get("format", "json")).lower()
    if fmt == "text":
        content = str(payload)
        path.write_text(content, encoding="utf-8")
        digest = _digest_bytes(path.read_bytes())
    else:
        content = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        path.write_text(content, encoding="utf-8")
        digest = _digest_bytes(content.encode("utf-8"))
    return _ok(step, {path.name: digest})


def handle_assert_contract(step: EffectStep, ctx: RuntimeContext) -> EffectResult:
    ok = bool(step.args.get("ok", True))
    if ok:
        return _ok(step, {})
    reasons = step.args.get("errors", [])
    if not isinstance(reasons, list):
        reasons = [str(reasons)]
    return _refuse(step, "ContractViolation", [str(item) for item in reasons])


def handle_verify_epoch(step: EffectStep, ctx: RuntimeContext) -> EffectResult:
    anchor_path = _resolve_output_path(ctx, step.args, key="anchor_path")
    if anchor_path is None or not anchor_path.exists():
        return _refuse(step, "AnchorMissing", ["anchor not found"])
    anchor = json.loads(anchor_path.read_text(encoding="utf-8"))
    verify_epoch = _load_tool("verify_epoch", VERIFY_EPOCH_PATH)
    ok, errors = verify_epoch.verify_epoch_anchor(anchor, root=ROOT, git_commit_override=None)
    digest = _digest_bytes(anchor_path.read_bytes())
    if ok:
        return _ok(step, {anchor_path.name: digest})
    return _refuse(step, "EpochVerificationFailed", errors, {anchor_path.name: digest})


def handle_verify_signature(step: EffectStep, ctx: RuntimeContext) -> EffectResult:
    anchor_path = _resolve_output_path(ctx, step.args, key="anchor_path")
    sig_path = _resolve_output_path(ctx, step.args, key="sig_path")
    pub_path = _resolve_output_path(ctx, step.args, key="pub_path")
    if anchor_path is None or sig_path is None or pub_path is None:
        return _refuse(step, "SignatureInputsMissing", ["missing signature inputs"])
    if not anchor_path.exists() or not sig_path.exists() or not pub_path.exists():
        return _refuse(step, "SignatureInputsMissing", ["missing signature inputs"])
    verify_sig = _load_tool("verify_anchor_signature", VERIFY_SIGNATURE_PATH)
    verify_key = verify_sig._load_verify_key(pub_path, "UNUSED")
    ok, errors = verify_sig.verify_anchor_signature(anchor_path, sig_path, verify_key)
    digests = {
        anchor_path.name: _digest_bytes(anchor_path.read_bytes()),
        sig_path.name: _digest_bytes(sig_path.read_bytes()),
    }
    if ok:
        return _ok(step, digests)
    return _refuse(step, "SignatureVerificationFailed", errors, digests)


def handle_select_measurement_track(step: EffectStep, ctx: RuntimeContext) -> EffectResult:
    input_value = step.args.get("input_path") or step.args.get("boundary_conditions_path")
    if input_value is None:
        return _refuse(step, "BoundaryConditionsMissing", ["boundary conditions missing"])
    input_path = Path(str(input_value))
    if not input_path.is_absolute():
        candidate = ROOT / input_path
        if candidate.exists():
            input_path = candidate
    if not input_path.exists():
        return _refuse(step, "BoundaryConditionsMissing", [f"input not found: {input_path}"])

    try:
        boundary_conditions = json.loads(input_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return _refuse(step, "BoundaryConditionsInvalid", ["invalid boundary conditions json"])

    result = build_measurement_selection(boundary_conditions)
    input_digest = _digest_bytes(input_path.read_bytes())
    if not result.ok or not result.selection:
        return _refuse(
            step,
            "ECMOSelectionFailed",
            result.errors or ["selection failed"],
            {"boundary_conditions": input_digest},
        )

    out_path = _resolve_output_path(
        ctx,
        step.args,
        key="out_path",
        default_name="measurement_selection.json",
    )
    if out_path:
        out_path.write_text(_canonical_json(result.selection), encoding="utf-8")
        output_digest = _digest_bytes(out_path.read_bytes())
        return _ok(step, {out_path.name: output_digest, "boundary_conditions": input_digest})
    return _ok(step, {"measurement_selection": _digest_bytes(_canonical_json(result.selection).encode("utf-8")), "boundary_conditions": input_digest})


def handle_check_repo_state(step: EffectStep, ctx: RuntimeContext) -> EffectResult:
    state_path = _resolve_output_path(ctx, step.args, key="state_path")
    if state_path is None or not state_path.exists():
        return _refuse(step, "RepoStateMissing", ["repo state missing"])
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return _refuse(step, "RepoStateInvalid", ["repo state invalid json"])
    clean = state.get("clean")
    if clean is not True:
        return _refuse(step, "RepoStateNotClean", ["repo state not clean"], {state_path.name: _digest_bytes(state_path.read_bytes())})
    return _ok(step, {state_path.name: _digest_bytes(state_path.read_bytes())})


def handle_validate_registries(step: EffectStep, ctx: RuntimeContext) -> EffectResult:
    module = _load_tool("validate_operator_registries", VALIDATE_REGISTRIES_PATH)
    schema = module._load_schema()
    registry_paths = module._resolve_registry_paths([])
    errors: List[str] = []
    digests: Dict[str, str] = {}
    for path in registry_paths:
        errors.extend(module.validate_registry_file(path, schema))
        digests[path.name] = _digest_bytes(path.read_bytes())
    if errors:
        return _refuse(step, "RegistryValidationFailed", errors, digests)
    return _ok(step, digests)


def handle_validate_coupling_topology(step: EffectStep, ctx: RuntimeContext) -> EffectResult:
    registry_path = _resolve_output_path(ctx, step.args, key="registry_path")
    if registry_path is None or not registry_path.exists():
        return _refuse(step, "CouplingRegistryMissing", ["coupling registry missing"])
    module = _load_tool("validate_coupling_topology", VALIDATE_COUPLING_PATH)
    errors = module.validate_coupling_registry_file(registry_path)
    digest = _digest_bytes(registry_path.read_bytes())
    if errors:
        return _refuse(step, "CouplingTopologyInvalid", errors, {registry_path.name: digest})
    return _ok(step, {registry_path.name: digest})


def handle_validate_quantum_semantics(step: EffectStep, ctx: RuntimeContext) -> EffectResult:
    module = _load_tool("validate_quantum_execution_semantics", VALIDATE_QUANTUM_PATH)
    program_ir = _resolve_output_path(ctx, step.args, key="program_ir")
    plan = _resolve_output_path(ctx, step.args, key="plan")
    runtime_result = _resolve_output_path(ctx, step.args, key="runtime_result")
    backend_ir = _resolve_output_path(ctx, step.args, key="backend_ir")
    qasm = _resolve_output_path(ctx, step.args, key="qasm")
    bundle_manifest = _resolve_output_path(ctx, step.args, key="bundle_manifest")
    result = module.validate_quantum_execution_semantics(
        program_ir=program_ir,
        plan=plan,
        runtime_result=runtime_result,
        backend_ir=backend_ir,
        qasm=qasm,
        bundle_manifest=bundle_manifest,
    )
    digests = {}
    for path in [program_ir, plan, runtime_result, backend_ir, qasm, bundle_manifest]:
        if path and path.exists():
            digests[path.name] = _digest_bytes(path.read_bytes())
    if not result.get("ok", False):
        return _refuse(step, "QuantumSemanticsInvalid", result.get("errors", []), digests)
    return _ok(step, digests)


def handle_sign_bundle(step: EffectStep, ctx: RuntimeContext) -> EffectResult:
    manifest_path = _resolve_output_path(ctx, step.args, key="bundle_manifest")
    signing_key = _resolve_output_path(ctx, step.args, key="signing_key")
    if manifest_path is None or signing_key is None:
        return _refuse(step, "BundleSigningInputsMissing", ["bundle signing inputs missing"])
    if not manifest_path.exists() or not signing_key.exists():
        return _refuse(step, "BundleSigningInputsMissing", ["bundle signing inputs missing"])
    bundle_module = _load_tool("bundle_evidence", BUNDLE_EVIDENCE_PATH)
    signature_path = bundle_module.sign_bundle_manifest(manifest_path, signing_key)
    digests = {
        manifest_path.name: _digest_bytes(manifest_path.read_bytes()),
        signature_path.name: _digest_bytes(signature_path.read_bytes()),
    }
    return _ok(step, digests)


def handle_verify_bundle(step: EffectStep, ctx: RuntimeContext) -> EffectResult:
    manifest_path = _resolve_output_path(ctx, step.args, key="bundle_manifest")
    signature_path = _resolve_output_path(ctx, step.args, key="bundle_signature")
    public_key = _resolve_output_path(ctx, step.args, key="public_key")
    if manifest_path is None or signature_path is None or public_key is None:
        return _refuse(step, "BundleVerificationInputsMissing", ["bundle verification inputs missing"])
    if not manifest_path.exists() or not signature_path.exists() or not public_key.exists():
        return _refuse(step, "BundleVerificationInputsMissing", ["bundle verification inputs missing"])
    bundle_module = _load_tool("bundle_evidence", BUNDLE_EVIDENCE_PATH)
    ok, errors = bundle_module.verify_bundle_manifest_signature(
        manifest_path,
        signature_path,
        public_key,
    )
    digests = {
        manifest_path.name: _digest_bytes(manifest_path.read_bytes()),
        signature_path.name: _digest_bytes(signature_path.read_bytes()),
    }
    if not ok:
        return _refuse(step, "BundleSignatureInvalid", errors, digests)
    return _ok(step, digests)

def handle_lower_backend_ir(step: EffectStep, ctx: RuntimeContext) -> EffectResult:
    program_ir = _program_ir_from_args(step.args)
    if program_ir is None:
        return _refuse(step, "ProgramIrMissing", ["program_ir missing"])
    target = str(step.args.get("backend_target", "classical")).lower()
    backend_ir = lower_program_ir_to_backend_ir(program_ir, target=target).to_dict()
    payload = _canonical_json(backend_ir)
    out_path = _resolve_output_path(ctx, step.args, default_name="backend.ir.json")
    if out_path:
        out_path.write_text(payload, encoding="utf-8")
        digest = _digest_bytes(out_path.read_bytes())
    else:
        digest = _digest_bytes(payload.encode("utf-8"))
    return _ok(step, {"backend_ir": digest})


def handle_lower_qasm(step: EffectStep, ctx: RuntimeContext) -> EffectResult:
    program_ir = _program_ir_from_args(step.args)
    if program_ir is None:
        return _refuse(step, "ProgramIrMissing", ["program_ir missing"])
    backend_ir = lower_program_ir_to_backend_ir(program_ir, target="qasm").to_dict()
    qasm = lower_backend_ir_to_qasm(backend_ir)
    out_path = _resolve_output_path(ctx, step.args, default_name="program.qasm")
    if out_path:
        out_path.write_text(qasm, encoding="utf-8")
        digest = _digest_bytes(out_path.read_bytes())
    else:
        digest = _digest_bytes(qasm.encode("utf-8"))
    return _ok(step, {"qasm": digest})


def handle_bundle_evidence(step: EffectStep, ctx: RuntimeContext) -> EffectResult:
    out_dir = _resolve_output_path(ctx, step.args)
    if out_dir is None:
        return _refuse(step, "BundleOutDirMissing", ["out_dir missing"])
    artifacts_spec = step.args.get("artifacts", [])
    if not isinstance(artifacts_spec, list):
        return _refuse(step, "BundleArtifactsMissing", ["artifacts missing"])
    bundle_module = _load_tool("bundle_evidence", BUNDLE_EVIDENCE_PATH)
    artifacts = []
    errors: List[str] = []
    for entry in artifacts_spec:
        if not isinstance(entry, dict):
            continue
        role = entry.get("role")
        path_value = entry.get("path")
        if not role or not path_value:
            continue
        path_obj = _resolve_output_path(ctx, {"path": path_value})
        if not path_obj.exists():
            errors.append(f"artifact missing: {path_obj}")
            continue
        artifacts.append(bundle_module._artifact(role, path_obj))
    if errors or not artifacts:
        return _refuse(step, "BundleArtifactsMissing", errors or ["no artifacts provided"])
    bundle_dir, manifest = bundle_module.build_bundle(
        out_dir=out_dir,
        artifacts=artifacts,
        epoch_anchor=_resolve_output_path(ctx, step.args, key="epoch_anchor"),
        epoch_sig=_resolve_output_path(ctx, step.args, key="epoch_sig"),
        public_key=_resolve_output_path(ctx, step.args, key="pub"),
        quantum_semantics_v1=bool(step.args.get("quantum_semantics_v1", False)),
        constraint_inversion_v1=bool(step.args.get("constraint_inversion_v1", False)),
    )
    manifest_path = bundle_dir / "bundle_manifest.json"
    manifest_path.write_text(_canonical_json(manifest), encoding="utf-8")
    digest = _digest_bytes(manifest_path.read_bytes())
    return _ok(step, {manifest_path.name: digest})


def handle_invert_constraints(step: EffectStep, ctx: RuntimeContext) -> EffectResult:
    witness = step.args.get("constraint_witness")
    witness_path = _resolve_output_path(ctx, step.args, key="witness_path")
    if witness is None and witness_path is None:
        return _refuse(step, "WitnessMissing", ["constraint witness missing"])
    if witness is None and witness_path is not None:
        witness = json.loads(witness_path.read_text(encoding="utf-8"))
    if not isinstance(witness, dict):
        return _refuse(step, "WitnessInvalid", ["constraint witness invalid"])
    proposal = invert_constraints(witness)
    payload = _canonical_json(proposal)
    out_path = _resolve_output_path(ctx, step.args, default_name="dual_proposal.json")
    if out_path:
        out_path.write_text(payload, encoding="utf-8")
        digest = _digest_bytes(out_path.read_bytes())
    else:
        digest = _digest_bytes(payload.encode("utf-8"))
    return _ok(step, {"dual_proposal": digest})


def _program_ir_from_args(args: Dict[str, object]) -> Optional[Dict[str, object]]:
    program_ir = args.get("program_ir")
    if isinstance(program_ir, dict):
        return program_ir
    path = args.get("program_ir_path")
    if path:
        return json.loads(Path(str(path)).read_text(encoding="utf-8"))
    return None


def _resolve_output_path(
    ctx: RuntimeContext,
    args: Dict[str, object],
    key: str = "path",
    default_name: Optional[str] = None,
) -> Optional[Path]:
    value = args.get(key)
    if value is None and "artifact_name" in args:
        value = args.get("artifact_name")
    if value is None and default_name is not None:
        value = default_name
    if value is None:
        return None
    path = Path(str(value))
    if path.is_absolute():
        return path
    if key in {"pub", "epoch_anchor", "epoch_sig", "anchor_path", "sig_path", "witness_path", "registry_path"}:
        return ROOT / path
    if ctx.trace_sink is None:
        return path
    return ctx.trace_sink / path


def _load_tool(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_json(data: object) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def _digest_bytes(data: bytes) -> str:
    import hashlib

    digest = hashlib.sha256(data).hexdigest()
    return f"sha256:{digest}"


def _ok(step: EffectStep, digests: Dict[str, str]) -> EffectResult:
    return EffectResult(
        step_id=step.step_id,
        effect_type=step.effect_type,
        ok=True,
        refusal_type=None,
        refusal_reasons=[],
        artifact_digests=digests,
    )


def _refuse(
    step: EffectStep,
    refusal_type: str,
    refusal_reasons: List[str],
    digests: Optional[Dict[str, str]] = None,
) -> EffectResult:
    return EffectResult(
        step_id=step.step_id,
        effect_type=step.effect_type,
        ok=False,
        refusal_type=refusal_type,
        refusal_reasons=[str(item) for item in refusal_reasons],
        artifact_digests=digests or {},
    )
