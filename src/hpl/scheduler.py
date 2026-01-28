"""Scheduler authority for deterministic execution planning."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .trace import emit_witness_record
from .execution_token import ExecutionToken


ROOT = Path(__file__).resolve().parents[2]
VERIFY_EPOCH_PATH = ROOT / "tools" / "verify_epoch.py"
VERIFY_SIGNATURE_PATH = ROOT / "tools" / "verify_anchor_signature.py"
DEFAULT_PUBLIC_KEY = ROOT / "config" / "keys" / "ci_ed25519.pub"
DEFAULT_TIMESTAMP = "1970-01-01T00:00:00Z"
DEFAULT_ALLOWED_BACKENDS = ["PYTHON", "CLASSICAL", "QASM"]


@dataclass(frozen=True)
class SchedulerContext:
    require_epoch_verification: bool = False
    anchor_path: Optional[Path] = None
    signature_path: Optional[Path] = None
    public_key_path: Path = DEFAULT_PUBLIC_KEY
    root: Path = ROOT
    git_commit_override: Optional[str] = None
    timestamp: str = DEFAULT_TIMESTAMP
    allowed_backends: Optional[List[str]] = None
    budget_steps: int = 100
    determinism_mode: str = "deterministic"


@dataclass(frozen=True)
class ExecutionPlan:
    plan_id: str
    program_id: str
    status: str
    steps: List[Dict[str, object]]
    reasons: List[str]
    verification: Optional[Dict[str, object]]
    witness_records: List[Dict[str, object]]
    execution_token: Optional[Dict[str, object]] = None

    def to_dict(self) -> Dict[str, object]:
        return {
            "plan_id": self.plan_id,
            "program_id": self.program_id,
            "status": self.status,
            "steps": list(self.steps),
            "reasons": list(self.reasons),
            "verification": self.verification,
            "witness_records": list(self.witness_records),
            "execution_token": self.execution_token,
        }


def plan(program_ir: Dict[str, object], ctx: SchedulerContext) -> ExecutionPlan:
    program_id = str(program_ir.get("program_id", "unknown"))
    reasons: List[str] = []
    witness_records: List[Dict[str, object]] = []
    verification: Optional[Dict[str, object]] = None
    allowed_backends = ctx.allowed_backends or list(DEFAULT_ALLOWED_BACKENDS)
    token = ExecutionToken.build(
        allowed_backends=allowed_backends,
        budget_steps=ctx.budget_steps,
        determinism_mode=ctx.determinism_mode,
    )

    if ctx.require_epoch_verification:
        verification, verification_errors = _verify_epoch_and_signature(ctx)
        reasons.extend(verification_errors)

        witness_records.append(
            _build_witness(
                stage="epoch_verification",
                artifact_digests={
                    "anchor_verification": _digest_text(
                        _canonical_json(verification)
                    )
                },
                timestamp=ctx.timestamp,
                attestation="epoch_verification_witness",
            )
        )

    steps = _build_steps(program_ir)
    status = "planned" if not reasons else "denied"

    plan_core = {
        "program_id": program_id,
        "status": status,
        "steps": steps,
        "reasons": list(reasons),
        "verification": verification,
        "execution_token": token.to_dict(),
    }
    plan_id = _digest_text(_canonical_json(plan_core))

    witness_records.append(
        _build_witness(
            stage="scheduler_plan",
            artifact_digests={"plan_id": plan_id},
            timestamp=ctx.timestamp,
            attestation="scheduler_plan_witness",
        )
    )

    return ExecutionPlan(
        plan_id=plan_id,
        program_id=program_id,
        status=status,
        steps=steps,
        reasons=reasons,
        verification=verification,
        witness_records=witness_records,
        execution_token=token.to_dict(),
    )


def _build_steps(program_ir: Dict[str, object]) -> List[Dict[str, object]]:
    hamiltonian = program_ir.get("hamiltonian", {})
    terms = hamiltonian.get("terms", []) if isinstance(hamiltonian, dict) else []
    steps: List[Dict[str, object]] = []
    if not isinstance(terms, list):
        return steps
    for idx, term in enumerate(terms):
        if not isinstance(term, dict):
            continue
        steps.append(
            {
                "index": idx,
                "operator_id": str(term.get("operator_id", "unknown")),
                "cls": str(term.get("cls", "unknown")),
                "coefficient": term.get("coefficient", 0.0),
            }
        )
    return steps


def _verify_epoch_and_signature(ctx: SchedulerContext) -> Tuple[Dict[str, object], List[str]]:
    errors: List[str] = []

    if not ctx.anchor_path:
        return {"anchor_ok": False, "signature_ok": False}, [
            "epoch verification required but anchor_path missing"
        ]

    if not ctx.anchor_path.exists():
        return {"anchor_ok": False, "signature_ok": False}, [
            f"anchor not found: {ctx.anchor_path}"
        ]

    anchor = json.loads(ctx.anchor_path.read_text(encoding="utf-8"))
    verify_epoch = _load_verify_epoch()
    ok, epoch_errors = verify_epoch.verify_epoch_anchor(
        anchor,
        root=ctx.root,
        git_commit_override=ctx.git_commit_override,
    )
    if not ok:
        errors.extend(["epoch verification failed"] + epoch_errors)

    sig_ok = True
    sig_errors: List[str] = []
    if ctx.signature_path:
        if ctx.signature_path.exists():
            verify_sig = _load_verify_signature()
            verify_key = verify_sig._load_verify_key(ctx.public_key_path, "UNUSED")
            sig_ok, sig_errors = verify_sig.verify_anchor_signature(
                ctx.anchor_path,
                ctx.signature_path,
                verify_key,
            )
            if not sig_ok:
                errors.extend(["signature verification failed"] + sig_errors)
        else:
            sig_ok = False
            errors.append(f"signature not found: {ctx.signature_path}")
    else:
        sig_ok = False
        errors.append("signature verification required but signature_path missing")

    return {
        "anchor_ok": ok,
        "signature_ok": sig_ok,
        "errors": list(errors),
    }, errors


def _load_verify_epoch():
    spec = importlib.util.spec_from_file_location("verify_epoch", VERIFY_EPOCH_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_verify_signature():
    spec = importlib.util.spec_from_file_location(
        "verify_anchor_signature", VERIFY_SIGNATURE_PATH
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _build_witness(
    stage: str,
    artifact_digests: Dict[str, str],
    timestamp: str,
    attestation: str,
) -> Dict[str, object]:
    return emit_witness_record(
        observer_id="papas",
        stage=stage,
        artifact_digests=artifact_digests,
        timestamp=timestamp,
        attestation=attestation,
    )


def _canonical_json(data: object) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def _digest_text(value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"
