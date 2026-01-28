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


ROOT = Path(__file__).resolve().parents[4]
VERIFY_EPOCH_PATH = ROOT / "tools" / "verify_epoch.py"
VERIFY_SIGNATURE_PATH = ROOT / "tools" / "verify_anchor_signature.py"
BUNDLE_EVIDENCE_PATH = ROOT / "tools" / "bundle_evidence.py"


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
    anchor_path = _path_arg(step, "anchor_path")
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
    anchor_path = _path_arg(step, "anchor_path")
    sig_path = _path_arg(step, "sig_path")
    pub_path = _path_arg(step, "pub_path")
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
    if key in {"pub", "epoch_anchor", "epoch_sig", "anchor_path", "sig_path", "witness_path"}:
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
