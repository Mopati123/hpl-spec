from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from nacl.exceptions import BadSignatureError
from nacl.signing import SigningKey, VerifyKey

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import verify_epoch
from tools import verify_anchor_signature


DEFAULT_PUBLIC_KEY = ROOT / "config" / "keys" / "ci_ed25519.pub"


@dataclass(frozen=True)
class Artifact:
    role: str
    source: Path
    filename: str
    digest: str


def main() -> int:
    args = _parse_args()
    artifacts = _collect_artifacts(args)
    bundle_dir, manifest = build_bundle(
        out_dir=args.out_dir,
        artifacts=artifacts,
        epoch_anchor=args.epoch_anchor,
        epoch_sig=args.epoch_sig,
        public_key=args.pub,
        quantum_semantics_v1=args.quantum_semantics_v1,
        constraint_inversion_v1=args.constraint_inversion_v1,
    )
    manifest_path = bundle_dir / "bundle_manifest.json"
    manifest_path.write_text(_canonical_json(manifest), encoding="utf-8")
    signature_path: Optional[Path] = None
    bundle_verify_ok = True
    bundle_verify_errors: List[str] = []

    if args.sign_bundle:
        if not args.signing_key:
            raise ValueError("sign_bundle requires --signing-key")
        signature_path = sign_bundle_manifest(manifest_path, args.signing_key)

    if args.verify_bundle:
        if signature_path is None:
            signature_path = manifest_path.with_suffix(".sig")
        bundle_verify_ok, bundle_verify_errors = verify_bundle_manifest_signature(
            manifest_path,
            signature_path,
            args.pub,
        )
    overall_ok = True
    quantum_section = manifest.get("quantum_semantics_v1")
    if isinstance(quantum_section, dict):
        overall_ok = overall_ok and bool(quantum_section.get("ok", True))
    constraint_section = manifest.get("constraint_inversion_v1")
    if isinstance(constraint_section, dict):
        overall_ok = overall_ok and bool(constraint_section.get("ok", True))
    delta_section = manifest.get("delta_s_v1")
    if isinstance(delta_section, dict):
        overall_ok = overall_ok and bool(delta_section.get("ok", True))
    io_section = manifest.get("io_lane_v1")
    if isinstance(io_section, dict):
        overall_ok = overall_ok and bool(io_section.get("ok", True))
    net_section = manifest.get("net_lane_v1")
    if isinstance(net_section, dict):
        overall_ok = overall_ok and bool(net_section.get("ok", True))
    overall_ok = overall_ok and bundle_verify_ok
    if args.verify_bundle and not bundle_verify_ok:
        print(_canonical_json({"ok": False, "errors": bundle_verify_errors}))
    return 0 if overall_ok else 1


def build_bundle(
    out_dir: Path,
    artifacts: List[Artifact],
    epoch_anchor: Optional[Path],
    epoch_sig: Optional[Path],
    public_key: Optional[Path],
    quantum_semantics_v1: bool = False,
    constraint_inversion_v1: bool = False,
) -> Tuple[Path, Dict[str, object]]:
    if not artifacts:
        raise ValueError("no artifacts provided")

    artifacts_sorted = sorted(artifacts, key=lambda item: (item.role, item.filename))
    bundle_id = _bundle_id(artifacts_sorted)
    bundle_dir = out_dir / f"bundle_{bundle_id}"
    bundle_dir.mkdir(parents=True, exist_ok=True)

    for artifact in artifacts_sorted:
        shutil.copyfile(artifact.source, bundle_dir / artifact.filename)

    git_commit = _git_commit()
    verification = _verify_epoch_and_signature(epoch_anchor, epoch_sig, public_key, git_commit)

    manifest: Dict[str, object] = {
        "bundle_id": bundle_id,
        "git_commit": git_commit,
        "verification": verification,
        "artifacts": [
            {
                "role": artifact.role,
                "filename": artifact.filename,
                "digest": artifact.digest,
            }
            for artifact in artifacts_sorted
        ],
    }

    if quantum_semantics_v1:
        manifest["quantum_semantics_v1"] = _quantum_semantics_section(artifacts)
        manifest["quantum_semantics_v1"]["evidence_manifest"] = "bundle_manifest.json"

    if constraint_inversion_v1:
        manifest["constraint_inversion_v1"] = _constraint_inversion_section(artifacts)
        manifest["constraint_inversion_v1"]["evidence_manifest"] = "bundle_manifest.json"

    token_data = _load_execution_token(artifacts)
    if token_data and token_data.get("collapse_requires_delta_s"):
        manifest["delta_s_v1"] = _delta_s_section(artifacts)
        manifest["delta_s_v1"]["evidence_manifest"] = "bundle_manifest.json"

    canonical_section = _canonical_invoke_section(artifacts)
    if canonical_section.get("canonical_present"):
        manifest["canonical_invoke_v1"] = canonical_section
        manifest["canonical_invoke_v1"]["evidence_manifest"] = "bundle_manifest.json"

    io_section = _io_section(artifacts)
    if io_section.get("io_present"):
        manifest["io_lane_v1"] = io_section
        manifest["io_lane_v1"]["evidence_manifest"] = "bundle_manifest.json"

    net_section = _net_section(artifacts)
    if net_section.get("net_present"):
        manifest["net_lane_v1"] = net_section
        manifest["net_lane_v1"]["evidence_manifest"] = "bundle_manifest.json"

    return bundle_dir, manifest


def _collect_artifacts(args: argparse.Namespace) -> List[Artifact]:
    execution_token = args.execution_token
    if execution_token is None and args.plan is not None:
        execution_token = _extract_execution_token(args.plan, args.out_dir)
    mapping: Dict[str, Optional[Path]] = {
        "program_ir": args.program_ir,
        "plan": args.plan,
        "runtime_result": args.runtime_result,
        "backend_ir": args.backend_ir,
        "qasm": args.qasm,
        "epoch_anchor": args.epoch_anchor,
        "epoch_sig": args.epoch_sig,
        "execution_token": execution_token,
        "constraint_witness": args.constraint_witness,
        "dual_proposal": args.dual_proposal,
        "delta_s_report": args.delta_s_report,
        "admissibility_certificate": args.admissibility_certificate,
        "measurement_trace": args.measurement_trace,
        "collapse_decision": args.collapse_decision,
        "io_request_log": args.io_request_log,
        "io_response_log": args.io_response_log,
        "io_event_log": args.io_event_log,
        "io_outcome": args.io_outcome,
        "reconciliation_report": args.reconciliation_report,
        "rollback_record": args.rollback_record,
        "remediation_plan": args.remediation_plan,
        "redaction_report": args.redaction_report,
        "net_request_log": args.net_request_log,
        "net_response_log": args.net_response_log,
        "net_event_log": args.net_event_log,
        "net_session_manifest": args.net_session_manifest,
    }

    artifacts: List[Artifact] = []
    for role, path in mapping.items():
        if not path:
            continue
        artifacts.append(_artifact(role, path))

    extras = sorted(args.extra or [], key=lambda p: str(p))
    for idx, path in enumerate(extras):
        artifacts.append(_artifact(f"extra_{idx}", path))

    artifacts.sort(key=lambda item: (item.role, item.filename))
    return artifacts


def _artifact(role: str, path: Path) -> Artifact:
    digest = _digest_bytes(path.read_bytes())
    filename = f"{role}_{path.name}"
    return Artifact(role=role, source=path, filename=filename, digest=digest)


def _extract_execution_token(plan_path: Path, out_dir: Path) -> Optional[Path]:
    try:
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    token = plan.get("execution_token")
    if not isinstance(token, dict):
        return None
    out_dir.mkdir(parents=True, exist_ok=True)
    token_path = out_dir / "execution_token.json"
    token_path.write_text(_canonical_json(token), encoding="utf-8")
    return token_path


def sign_bundle_manifest(manifest_path: Path, signing_key_path: Path) -> Path:
    signing_key = _load_signing_key(signing_key_path)
    payload = manifest_path.read_bytes()
    signature = signing_key.sign(payload).signature
    signature_path = manifest_path.with_suffix(".sig")
    signature_path.write_text(signature.hex(), encoding="utf-8")
    return signature_path


def verify_bundle_manifest_signature(
    manifest_path: Path,
    signature_path: Path,
    public_key_path: Path,
) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    if not signature_path.exists():
        return False, [f"signature not found: {signature_path}"]
    payload = manifest_path.read_bytes()
    signature_hex = signature_path.read_text(encoding="utf-8").strip()
    if not signature_hex:
        return False, ["signature file is empty"]
    try:
        signature = bytes.fromhex(signature_hex)
    except ValueError:
        return False, ["signature is not valid hex"]
    try:
        verify_key = _load_verify_key(public_key_path)
        verify_key.verify(payload, signature)
    except BadSignatureError:
        errors.append("signature verification failed")
    return not errors, errors


def _bundle_id(artifacts: List[Artifact]) -> str:
    core = [
        {"role": artifact.role, "digest": artifact.digest}
        for artifact in artifacts
    ]
    return _digest_hex(_canonical_json(core))


def _quantum_semantics_section(artifacts: List[Artifact]) -> Dict[str, object]:
    required_roles = ["program_ir", "plan", "runtime_result"]
    projection_roles = ["backend_ir", "qasm"]
    present_roles = sorted({artifact.role for artifact in artifacts})

    missing_required = sorted([role for role in required_roles if role not in present_roles])
    projection_present = [role for role in projection_roles if role in present_roles]
    missing_projection = not projection_present
    ok = not missing_required and not missing_projection

    return {
        "ok": ok,
        "required_roles": required_roles,
        "projection_roles": projection_roles,
        "present_roles": present_roles,
        "missing_required": missing_required,
        "projection_present": projection_present,
    }


def _constraint_inversion_section(artifacts: List[Artifact]) -> Dict[str, object]:
    required_roles = ["constraint_witness", "dual_proposal"]
    present_roles = sorted({artifact.role for artifact in artifacts})
    missing_required = sorted([role for role in required_roles if role not in present_roles])
    ok = not missing_required

    return {
        "ok": ok,
        "required_roles": required_roles,
        "present_roles": present_roles,
        "missing_required": missing_required,
    }


def _delta_s_section(artifacts: List[Artifact]) -> Dict[str, object]:
    required_roles = ["delta_s_report", "admissibility_certificate", "collapse_decision"]
    present_roles = sorted({artifact.role for artifact in artifacts})
    missing_required = sorted([role for role in required_roles if role not in present_roles])
    ok = not missing_required
    return {
        "ok": ok,
        "required_roles": required_roles,
        "present_roles": present_roles,
        "missing_required": missing_required,
    }


def _canonical_invoke_section(artifacts: List[Artifact]) -> Dict[str, object]:
    present_roles = sorted({artifact.role for artifact in artifacts})
    canonical_detect_roles = {
        "canonical_eq09_report",
        "canonical_eq15_report",
        "admissibility_certificate",
        "delta_s_report",
        "collapse_decision",
    }
    canonical_present = any(role in canonical_detect_roles for role in present_roles)
    if not canonical_present:
        return {
            "ok": True,
            "canonical_present": False,
            "required_roles": [],
            "present_roles": present_roles,
            "missing_required": [],
        }
    required_roles = ["canonical_eq09_report", "canonical_eq15_report"]
    missing_required = sorted([role for role in required_roles if role not in present_roles])
    ok = not missing_required
    return {
        "ok": ok,
        "canonical_present": True,
        "required_roles": required_roles,
        "present_roles": present_roles,
        "missing_required": missing_required,
    }


def _io_section(artifacts: List[Artifact]) -> Dict[str, object]:
    present_roles = sorted({artifact.role for artifact in artifacts})
    io_detect_roles = {
        "io_request_log",
        "io_response_log",
        "io_event_log",
        "io_outcome",
        "reconciliation_report",
        "rollback_record",
    }
    io_present = any(role in io_detect_roles for role in present_roles)
    if not io_present:
        return {
            "ok": True,
            "io_present": False,
            "required_roles": [],
            "present_roles": present_roles,
            "missing_required": [],
            "rollback_required": False,
        }

    required_roles = [
        "io_request_log",
        "io_response_log",
        "reconciliation_report",
        "io_outcome",
        "redaction_report",
    ]
    missing_required = sorted([role for role in required_roles if role not in present_roles])
    rollback_required = False
    remediation_required = False
    outcome = _load_role_json(artifacts, "io_outcome")
    if isinstance(outcome, dict) and str(outcome.get("action", "")).lower() == "rollback":
        rollback_required = True
        if "rollback_record" not in present_roles:
            missing_required.append("rollback_record")
    if isinstance(outcome, dict):
        action = str(outcome.get("action", "")).lower()
        if action in {"rollback", "refuse"} or outcome.get("ok") is False:
            remediation_required = True
            if "remediation_plan" not in present_roles:
                missing_required.append("remediation_plan")
    ok = not missing_required
    return {
        "ok": ok,
        "io_present": True,
        "required_roles": required_roles,
        "present_roles": present_roles,
        "missing_required": sorted(set(missing_required)),
        "rollback_required": rollback_required,
        "remediation_required": remediation_required,
    }


def _net_section(artifacts: List[Artifact]) -> Dict[str, object]:
    present_roles = sorted({artifact.role for artifact in artifacts})
    net_detect_roles = {
        "net_request_log",
        "net_response_log",
        "net_event_log",
        "net_session_manifest",
    }
    net_present = any(role in net_detect_roles for role in present_roles)
    if not net_present:
        return {
            "ok": True,
            "net_present": False,
            "required_roles": [],
            "present_roles": present_roles,
            "missing_required": [],
        }

    required_roles = [
        "net_request_log",
        "net_response_log",
        "net_event_log",
        "net_session_manifest",
        "redaction_report",
    ]
    missing_required = sorted([role for role in required_roles if role not in present_roles])
    ok = not missing_required
    return {
        "ok": ok,
        "net_present": True,
        "required_roles": required_roles,
        "present_roles": present_roles,
        "missing_required": missing_required,
    }


def _load_execution_token(artifacts: List[Artifact]) -> Optional[Dict[str, object]]:
    for artifact in artifacts:
        if artifact.role != "execution_token":
            continue
        try:
            return json.loads(artifact.source.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
    return None


def _load_role_json(artifacts: List[Artifact], role: str) -> Optional[Dict[str, object]]:
    for artifact in artifacts:
        if artifact.role != role:
            continue
        try:
            data = json.loads(artifact.source.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if isinstance(data, dict):
            return data
        return None
    return None


def _verify_epoch_and_signature(
    anchor: Optional[Path],
    signature: Optional[Path],
    public_key: Optional[Path],
    git_commit: Optional[str],
) -> Dict[str, object]:
    epoch_ok = None
    epoch_errors: List[str] = []
    signature_ok = None
    signature_errors: List[str] = []

    if anchor:
        anchor_data = json.loads(anchor.read_text(encoding="utf-8"))
        epoch_ok, epoch_errors = verify_epoch.verify_epoch_anchor(
            anchor_data,
            root=ROOT,
            git_commit_override=git_commit,
        )

    if signature and anchor:
        verify_key = verify_anchor_signature._load_verify_key(
            public_key or DEFAULT_PUBLIC_KEY,
            "UNUSED",
        )
        signature_ok, signature_errors = verify_anchor_signature.verify_anchor_signature(
            anchor,
            signature,
            verify_key,
        )

    return {
        "epoch_ok": epoch_ok,
        "epoch_errors": list(epoch_errors),
        "signature_ok": signature_ok,
        "signature_errors": list(signature_errors),
    }


def _git_commit() -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip() or None
    except Exception:
        return None


def _canonical_json(data: object) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def _digest_bytes(data: bytes) -> str:
    digest = hashlib.sha256(data).hexdigest()
    return f"sha256:{digest}"


def _digest_text(value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _digest_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _load_signing_key(path: Path) -> SigningKey:
    key_hex = path.read_text(encoding="utf-8").strip()
    if not key_hex:
        raise ValueError("signing key file is empty")
    key_bytes = bytes.fromhex(key_hex)
    if len(key_bytes) != 32:
        raise ValueError("private key seed must be 32 bytes (64 hex chars)")
    return SigningKey(key_bytes)


def _load_verify_key(path: Path) -> VerifyKey:
    key_hex = path.read_text(encoding="utf-8").strip()
    if not key_hex:
        raise ValueError("public key file is empty")
    key_bytes = bytes.fromhex(key_hex)
    if len(key_bytes) != 32:
        raise ValueError("public key must be 32 bytes (64 hex chars)")
    return VerifyKey(key_bytes)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bundle evidence artifacts.")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--program-ir", type=Path)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--runtime-result", type=Path)
    parser.add_argument("--backend-ir", type=Path)
    parser.add_argument("--qasm", type=Path)
    parser.add_argument("--epoch-anchor", type=Path)
    parser.add_argument("--epoch-sig", type=Path)
    parser.add_argument("--execution-token", type=Path)
    parser.add_argument("--constraint-witness", type=Path)
    parser.add_argument("--dual-proposal", type=Path)
    parser.add_argument("--delta-s-report", type=Path)
    parser.add_argument("--admissibility-certificate", type=Path)
    parser.add_argument("--measurement-trace", type=Path)
    parser.add_argument("--collapse-decision", type=Path)
    parser.add_argument("--io-request-log", type=Path)
    parser.add_argument("--io-response-log", type=Path)
    parser.add_argument("--io-event-log", type=Path)
    parser.add_argument("--io-outcome", type=Path)
    parser.add_argument("--reconciliation-report", type=Path)
    parser.add_argument("--rollback-record", type=Path)
    parser.add_argument("--remediation-plan", type=Path)
    parser.add_argument("--redaction-report", type=Path)
    parser.add_argument("--net-request-log", type=Path)
    parser.add_argument("--net-response-log", type=Path)
    parser.add_argument("--net-event-log", type=Path)
    parser.add_argument("--net-session-manifest", type=Path)
    parser.add_argument("--pub", type=Path, default=DEFAULT_PUBLIC_KEY)
    parser.add_argument("--extra", type=Path, action="append", default=[])
    parser.add_argument("--quantum-semantics-v1", action="store_true")
    parser.add_argument("--constraint-inversion-v1", action="store_true")
    parser.add_argument("--sign-bundle", action="store_true")
    parser.add_argument("--signing-key", type=Path)
    parser.add_argument("--verify-bundle", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(main())
