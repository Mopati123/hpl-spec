"""Runtime execution gate for scheduler-approved plans (no execution yet)."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..trace import emit_witness_record
from ..audit.constraint_witness import build_constraint_witness
from .context import RuntimeContext
from .contracts import ExecutionContract


ROOT = Path(__file__).resolve().parents[3]
VERIFY_EPOCH_PATH = ROOT / "tools" / "verify_epoch.py"
VERIFY_SIGNATURE_PATH = ROOT / "tools" / "verify_anchor_signature.py"
DEFAULT_TIMESTAMP = "1970-01-01T00:00:00Z"


@dataclass(frozen=True)
class RuntimeResult:
    result_id: str
    status: str
    reasons: List[str]
    steps: List[Dict[str, object]]
    verification: Optional[Dict[str, object]]
    witness_records: List[Dict[str, object]]
    constraint_witnesses: List[Dict[str, object]]

    def to_dict(self) -> Dict[str, object]:
        return {
            "result_id": self.result_id,
            "status": self.status,
            "reasons": list(self.reasons),
            "steps": list(self.steps),
            "verification": self.verification,
            "witness_records": list(self.witness_records),
            "constraint_witnesses": list(self.constraint_witnesses),
        }


class RuntimeEngine:
    def run(
        self,
        plan: object,
        ctx: RuntimeContext,
        contract: ExecutionContract,
    ) -> RuntimeResult:
        plan_dict = _plan_to_dict(plan)
        reasons: List[str] = []
        witness_records: List[Dict[str, object]] = []
        constraint_witnesses: List[Dict[str, object]] = []
        verification: Optional[Dict[str, object]] = None

        witness_records.append(
            _build_witness(
                stage="runtime_start",
                artifact_digests={"plan": _digest_text(_canonical_json(plan_dict))},
                timestamp=ctx.timestamp,
                attestation="runtime_start_witness",
            )
        )

        if plan_dict.get("status") != "planned":
            reasons.append("plan not approved")

        if contract.require_epoch_verification or contract.require_signature_verification:
            verification, verify_errors = _verify_epoch_and_signature(ctx, contract)
            reasons.extend(verify_errors)

            witness_records.append(
                _build_witness(
                    stage="epoch_verification",
                    artifact_digests={
                        "epoch_verification": _digest_text(_canonical_json(verification))
                    },
                    timestamp=ctx.timestamp,
                    attestation="epoch_verification_witness",
                )
            )

        steps = _steps_from_plan(plan_dict)
        for step in steps:
            ok, errors = contract.preconditions(step, ctx)
            if not ok:
                reasons.extend(errors)
                witness_records.append(
                    _build_witness(
                        stage="step_denied",
                        artifact_digests={"step": _digest_text(_canonical_json(step))},
                        timestamp=ctx.timestamp,
                        attestation="step_denied_witness",
                    )
                )
                break

            post_ok, post_errors = contract.postconditions(step, ctx)
            if not post_ok:
                reasons.extend(post_errors)
                witness_records.append(
                    _build_witness(
                        stage="step_denied",
                        artifact_digests={"step": _digest_text(_canonical_json(step))},
                        timestamp=ctx.timestamp,
                        attestation="step_denied_witness",
                    )
                )
                break

            witness_records.append(
                _build_witness(
                    stage="step_ok",
                    artifact_digests={"step": _digest_text(_canonical_json(step))},
                    timestamp=ctx.timestamp,
                    attestation="step_ok_witness",
                )
            )

        status = "completed" if not reasons else "denied"

        if status == "denied":
            constraint_witnesses.append(
                build_constraint_witness(
                    stage="runtime_refusal",
                    refusal_reasons=reasons,
                    artifact_digests={"plan": _digest_text(_canonical_json(plan_dict))},
                    observer_id="papas",
                    timestamp=None,
                )
            )
            if not constraint_witnesses:
                raise RuntimeError("internal_error: missing constraint witness for refusal")

        result_core = {
            "status": status,
            "reasons": list(reasons),
            "steps": steps,
            "verification": verification,
        }
        result_id = _digest_text(_canonical_json(result_core))

        witness_records.append(
            _build_witness(
                stage="runtime_complete",
                artifact_digests={"result_id": result_id},
                timestamp=ctx.timestamp,
                attestation="runtime_complete_witness",
            )
        )

        return RuntimeResult(
            result_id=result_id,
            status=status,
            reasons=reasons,
            steps=steps,
            verification=verification,
            witness_records=witness_records,
            constraint_witnesses=constraint_witnesses,
        )


def _plan_to_dict(plan: object) -> Dict[str, object]:
    if hasattr(plan, "to_dict"):
        return plan.to_dict()  # type: ignore[no-any-return]
    if isinstance(plan, dict):
        return plan
    raise TypeError("plan must be a dict or support to_dict")


def _steps_from_plan(plan: Dict[str, object]) -> List[Dict[str, object]]:
    steps = plan.get("steps", [])
    if isinstance(steps, list):
        return [step for step in steps if isinstance(step, dict)]
    return []


def _verify_epoch_and_signature(
    ctx: RuntimeContext,
    contract: ExecutionContract,
) -> Tuple[Dict[str, object], List[str]]:
    errors: List[str] = []

    if not ctx.epoch_anchor_path:
        return {"anchor_ok": False, "signature_ok": False}, [
            "epoch verification required but epoch_anchor_path missing"
        ]

    if not ctx.epoch_anchor_path.exists():
        return {"anchor_ok": False, "signature_ok": False}, [
            f"epoch anchor not found: {ctx.epoch_anchor_path}"
        ]

    anchor = json.loads(ctx.epoch_anchor_path.read_text(encoding="utf-8"))
    verify_epoch = _load_verify_epoch()
    anchor_ok, anchor_errors = verify_epoch.verify_epoch_anchor(
        anchor,
        root=ctx.epoch_anchor_path.parents[2],
        git_commit_override=None,
    )
    if not anchor_ok:
        errors.extend(["epoch verification failed"] + anchor_errors)

    signature_ok = True
    signature_errors: List[str] = []
    if contract.require_signature_verification:
        if not ctx.epoch_sig_path:
            signature_ok = False
            errors.append("signature verification required but epoch_sig_path missing")
        elif not ctx.epoch_sig_path.exists():
            signature_ok = False
            errors.append(f"epoch signature not found: {ctx.epoch_sig_path}")
        else:
            verify_sig = _load_verify_signature()
            verify_key = verify_sig._load_verify_key(ctx.ci_pubkey_path, "UNUSED")
            signature_ok, signature_errors = verify_sig.verify_anchor_signature(
                ctx.epoch_anchor_path,
                ctx.epoch_sig_path,
                verify_key,
            )
            if not signature_ok:
                errors.extend(["signature verification failed"] + signature_errors)

    return {
        "anchor_ok": anchor_ok,
        "signature_ok": signature_ok,
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
        timestamp=timestamp or DEFAULT_TIMESTAMP,
        attestation=attestation,
    )


def _canonical_json(data: object) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def _digest_text(value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"
