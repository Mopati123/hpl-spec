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
    emit_effect_steps: bool = False
    backend_target: Optional[str] = None
    artifact_paths: Optional[Dict[str, str]] = None
    ecmo_input_path: Optional[Path] = None
    measurement_selection_path: Optional[Path] = None
    track: Optional[str] = None
    ci_repo_state_path: Optional[Path] = None
    ci_coupling_registry_path: Optional[Path] = None
    ci_bundle_out_dir: Optional[Path] = None
    ci_bundle_signing_key_path: Optional[Path] = None
    agent_policy_path: Optional[Path] = None
    agent_proposal_path: Optional[Path] = None
    agent_decision_path: Optional[Path] = None
    trading_fixture_path: Optional[Path] = None
    trading_policy_path: Optional[Path] = None
    trading_shadow_model_path: Optional[Path] = None
    trading_report_json_path: Optional[Path] = None
    trading_report_md_path: Optional[Path] = None
    ns_state_path: Optional[Path] = None
    ns_policy_path: Optional[Path] = None
    ns_state_final_path: Optional[Path] = None
    ns_observables_path: Optional[Path] = None
    ns_pressure_path: Optional[Path] = None
    ns_gate_certificate_path: Optional[Path] = None


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

    if ctx.emit_effect_steps:
        steps = _build_effect_steps(program_ir, ctx)
    else:
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


def _build_effect_steps(program_ir: Dict[str, object], ctx: SchedulerContext) -> List[Dict[str, object]]:
    steps: List[Dict[str, object]] = []
    index = 0

    def add_step(step: Dict[str, object]) -> None:
        nonlocal index
        steps.append(step)
        index += 1

    if ctx.track == "ci_governance":
        return _build_ci_governance_steps(program_ir, ctx)
    if ctx.track == "agent_governance":
        return _build_agent_governance_steps(program_ir, ctx)
    if ctx.track == "trading_paper_mode":
        return _build_trading_paper_steps(program_ir, ctx)
    if ctx.track == "trading_shadow_mode":
        return _build_trading_shadow_steps(program_ir, ctx)
    if ctx.track == "navier_stokes":
        return _build_navier_stokes_steps(program_ir, ctx)

    if ctx.ecmo_input_path:
        selection_args: Dict[str, object] = {"input_path": str(ctx.ecmo_input_path)}
        if ctx.measurement_selection_path:
            selection_args["out_path"] = str(ctx.measurement_selection_path)
        add_step(
            {
                "step_id": f"select_measurement_track_{index}",
                "effect_type": "SELECT_MEASUREMENT_TRACK",
                "args": selection_args,
                "requires": {},
            }
        )

    if ctx.require_epoch_verification and ctx.anchor_path:
        add_step(
            {
                "step_id": f"verify_epoch_{index}",
                "effect_type": "VERIFY_EPOCH",
                "args": {"anchor_path": str(ctx.anchor_path)},
                "requires": {},
            }
        )
        if ctx.signature_path:
            add_step(
                {
                    "step_id": f"verify_signature_{index}",
                    "effect_type": "VERIFY_SIGNATURE",
                    "args": {
                        "anchor_path": str(ctx.anchor_path),
                        "sig_path": str(ctx.signature_path),
                        "pub_path": str(ctx.public_key_path),
                    },
                    "requires": {},
                }
            )

    backend_target = (ctx.backend_target or "classical").upper()
    artifact_paths = ctx.artifact_paths or {}
    backend_ir_path = artifact_paths.get("backend_ir")
    qasm_path = artifact_paths.get("qasm")

    backend_args: Dict[str, object] = {
        "program_ir": program_ir,
        "backend_target": backend_target,
    }
    if backend_ir_path:
        backend_args["out_path"] = backend_ir_path
    add_step(
        {
            "step_id": f"lower_backend_ir_{index}",
            "effect_type": "LOWER_BACKEND_IR",
            "args": backend_args,
            "requires": {"backend": backend_target},
        }
    )

    if backend_target == "QASM":
        qasm_args: Dict[str, object] = {"program_ir": program_ir}
        if qasm_path:
            qasm_args["out_path"] = qasm_path
        add_step(
            {
                "step_id": f"lower_qasm_{index}",
                "effect_type": "LOWER_QASM",
                "args": qasm_args,
                "requires": {"backend": backend_target},
            }
        )

    return steps


def _build_ci_governance_steps(program_ir: Dict[str, object], ctx: SchedulerContext) -> List[Dict[str, object]]:
    steps: List[Dict[str, object]] = []
    index = 0

    def add_step(step: Dict[str, object]) -> None:
        nonlocal index
        steps.append(step)
        index += 1

    if ctx.ci_repo_state_path:
        add_step(
            {
                "step_id": f"check_repo_state_{index}",
                "effect_type": "CHECK_REPO_STATE",
                "args": {"state_path": str(ctx.ci_repo_state_path)},
                "requires": {},
            }
        )

    add_step(
        {
            "step_id": f"validate_registries_{index}",
            "effect_type": "VALIDATE_REGISTRIES",
            "args": {},
            "requires": {},
        }
    )

    if ctx.ci_coupling_registry_path:
        add_step(
            {
                "step_id": f"validate_coupling_{index}",
                "effect_type": "VALIDATE_COUPLING_TOPOLOGY",
                "args": {"registry_path": str(ctx.ci_coupling_registry_path)},
                "requires": {},
            }
        )

    if ctx.require_epoch_verification and ctx.anchor_path:
        add_step(
            {
                "step_id": f"verify_epoch_{index}",
                "effect_type": "VERIFY_EPOCH",
                "args": {"anchor_path": str(ctx.anchor_path)},
                "requires": {},
            }
        )
        if ctx.signature_path:
            add_step(
                {
                    "step_id": f"verify_signature_{index}",
                    "effect_type": "VERIFY_SIGNATURE",
                    "args": {
                        "anchor_path": str(ctx.anchor_path),
                        "sig_path": str(ctx.signature_path),
                        "pub_path": str(ctx.public_key_path),
                    },
                    "requires": {},
                }
            )

    backend_target = (ctx.backend_target or "classical").upper()
    artifact_paths = ctx.artifact_paths or {}
    backend_ir_path = artifact_paths.get("backend_ir")
    backend_args: Dict[str, object] = {
        "program_ir": program_ir,
        "backend_target": backend_target,
    }
    if backend_ir_path:
        backend_args["out_path"] = backend_ir_path
    add_step(
        {
            "step_id": f"lower_backend_ir_{index}",
            "effect_type": "LOWER_BACKEND_IR",
            "args": backend_args,
            "requires": {"backend": backend_target},
        }
    )

    return steps


def _build_agent_governance_steps(program_ir: Dict[str, object], ctx: SchedulerContext) -> List[Dict[str, object]]:
    steps: List[Dict[str, object]] = []
    index = 0

    def add_step(step: Dict[str, object]) -> None:
        nonlocal index
        steps.append(step)
        index += 1

    if ctx.require_epoch_verification and ctx.anchor_path:
        add_step(
            {
                "step_id": f"verify_epoch_{index}",
                "effect_type": "VERIFY_EPOCH",
                "args": {"anchor_path": str(ctx.anchor_path)},
                "requires": {},
            }
        )
        if ctx.signature_path:
            add_step(
                {
                    "step_id": f"verify_signature_{index}",
                    "effect_type": "VERIFY_SIGNATURE",
                    "args": {
                        "anchor_path": str(ctx.anchor_path),
                        "sig_path": str(ctx.signature_path),
                        "pub_path": str(ctx.public_key_path),
                    },
                    "requires": {},
                }
            )

    proposal_path = str(ctx.agent_proposal_path) if ctx.agent_proposal_path else None
    policy_path = str(ctx.agent_policy_path) if ctx.agent_policy_path else None
    decision_path = str(ctx.agent_decision_path) if ctx.agent_decision_path else None
    args: Dict[str, object] = {}
    if proposal_path:
        args["proposal_path"] = proposal_path
    if policy_path:
        args["policy_path"] = policy_path
    if decision_path:
        args["decision_path"] = decision_path
    add_step(
        {
            "step_id": f"evaluate_agent_proposal_{index}",
            "effect_type": "EVALUATE_AGENT_PROPOSAL",
            "args": args,
            "requires": {},
        }
    )

    return steps


def _build_trading_paper_steps(program_ir: Dict[str, object], ctx: SchedulerContext) -> List[Dict[str, object]]:
    steps: List[Dict[str, object]] = []
    index = 0

    def add_step(step: Dict[str, object]) -> None:
        nonlocal index
        steps.append(step)
        index += 1

    if ctx.require_epoch_verification and ctx.anchor_path:
        add_step(
            {
                "step_id": f"verify_epoch_{index}",
                "effect_type": "VERIFY_EPOCH",
                "args": {"anchor_path": str(ctx.anchor_path)},
                "requires": {},
            }
        )
        if ctx.signature_path:
            add_step(
                {
                    "step_id": f"verify_signature_{index}",
                    "effect_type": "VERIFY_SIGNATURE",
                    "args": {
                        "anchor_path": str(ctx.anchor_path),
                        "sig_path": str(ctx.signature_path),
                        "pub_path": str(ctx.public_key_path),
                    },
                    "requires": {},
                }
            )

    fixture_path = str(ctx.trading_fixture_path) if ctx.trading_fixture_path else None
    policy_path = str(ctx.trading_policy_path) if ctx.trading_policy_path else None
    report_json = str(ctx.trading_report_json_path) if ctx.trading_report_json_path else "trade_report.json"
    report_md = str(ctx.trading_report_md_path) if ctx.trading_report_md_path else "trade_report.md"

    add_step(
        {
            "step_id": f"ingest_market_{index}",
            "effect_type": "INGEST_MARKET_FIXTURE",
            "args": {
                "fixture_path": fixture_path,
                "out_path": "market_snapshot.json",
            },
            "requires": {"backend": "CLASSICAL"},
        }
    )
    add_step(
        {
            "step_id": f"compute_signal_{index}",
            "effect_type": "COMPUTE_SIGNAL",
            "args": {
                "market_snapshot_path": "market_snapshot.json",
                "policy_path": policy_path,
                "out_path": "signal.json",
            },
            "requires": {"backend": "CLASSICAL"},
        }
    )
    add_step(
        {
            "step_id": f"simulate_order_{index}",
            "effect_type": "SIMULATE_ORDER",
            "args": {
                "market_snapshot_path": "market_snapshot.json",
                "signal_path": "signal.json",
                "policy_path": policy_path,
                "out_path": "trade_fill.json",
            },
            "requires": {"backend": "CLASSICAL"},
        }
    )
    add_step(
        {
            "step_id": f"update_risk_{index}",
            "effect_type": "UPDATE_RISK_ENVELOPE",
            "args": {
                "trade_fill_path": "trade_fill.json",
                "policy_path": policy_path,
                "out_path": "risk_envelope.json",
            },
            "requires": {"backend": "CLASSICAL"},
        }
    )
    add_step(
        {
            "step_id": f"emit_trade_report_{index}",
            "effect_type": "EMIT_TRADE_REPORT",
            "args": {
                "market_snapshot_path": "market_snapshot.json",
                "signal_path": "signal.json",
                "trade_fill_path": "trade_fill.json",
                "risk_envelope_path": "risk_envelope.json",
                "report_json_path": report_json,
                "report_md_path": report_md,
            },
            "requires": {"backend": "CLASSICAL"},
        }
    )

    return steps


def _build_trading_shadow_steps(program_ir: Dict[str, object], ctx: SchedulerContext) -> List[Dict[str, object]]:
    steps: List[Dict[str, object]] = []
    index = 0

    def add_step(step: Dict[str, object]) -> None:
        nonlocal index
        steps.append(step)
        index += 1

    if ctx.require_epoch_verification and ctx.anchor_path:
        add_step(
            {
                "step_id": f"verify_epoch_{index}",
                "effect_type": "VERIFY_EPOCH",
                "args": {"anchor_path": str(ctx.anchor_path)},
                "requires": {},
            }
        )
        if ctx.signature_path:
            add_step(
                {
                    "step_id": f"verify_signature_{index}",
                    "effect_type": "VERIFY_SIGNATURE",
                    "args": {
                        "anchor_path": str(ctx.anchor_path),
                        "sig_path": str(ctx.signature_path),
                        "pub_path": str(ctx.public_key_path),
                    },
                    "requires": {},
                }
            )

    fixture_path = str(ctx.trading_fixture_path) if ctx.trading_fixture_path else None
    policy_path = str(ctx.trading_policy_path) if ctx.trading_policy_path else None
    model_path = str(ctx.trading_shadow_model_path) if ctx.trading_shadow_model_path else None
    report_json = str(ctx.trading_report_json_path) if ctx.trading_report_json_path else "trade_report.json"
    report_md = str(ctx.trading_report_md_path) if ctx.trading_report_md_path else "trade_report.md"

    add_step(
        {
            "step_id": f"load_shadow_model_{index}",
            "effect_type": "SIM_MARKET_MODEL_LOAD",
            "args": {
                "model_path": model_path,
                "out_path": "shadow_model.json",
                "seed_out_path": "shadow_seed.json",
            },
            "requires": {"backend": "CLASSICAL"},
        }
    )
    add_step(
        {
            "step_id": f"ingest_market_{index}",
            "effect_type": "INGEST_MARKET_FIXTURE",
            "args": {
                "fixture_path": fixture_path,
                "out_path": "market_snapshot.json",
            },
            "requires": {"backend": "CLASSICAL"},
        }
    )
    add_step(
        {
            "step_id": f"regime_shift_{index}",
            "effect_type": "SIM_REGIME_SHIFT_STEP",
            "args": {
                "market_snapshot_path": "market_snapshot.json",
                "model_path": model_path,
                "out_path": "regime_snapshot.json",
            },
            "requires": {"backend": "CLASSICAL"},
        }
    )
    add_step(
        {
            "step_id": f"apply_latency_{index}",
            "effect_type": "SIM_LATENCY_APPLY",
            "args": {
                "market_snapshot_path": "regime_snapshot.json",
                "model_path": model_path,
                "policy_path": policy_path,
                "out_path": "latency_snapshot.json",
            },
            "requires": {"backend": "CLASSICAL"},
        }
    )
    add_step(
        {
            "step_id": f"compute_signal_{index}",
            "effect_type": "COMPUTE_SIGNAL",
            "args": {
                "market_snapshot_path": "latency_snapshot.json",
                "policy_path": policy_path,
                "out_path": "signal.json",
            },
            "requires": {"backend": "CLASSICAL"},
        }
    )
    add_step(
        {
            "step_id": f"simulate_order_{index}",
            "effect_type": "SIMULATE_ORDER",
            "args": {
                "market_snapshot_path": "latency_snapshot.json",
                "signal_path": "signal.json",
                "policy_path": policy_path,
                "model_path": model_path,
                "out_path": "trade_fill.json",
            },
            "requires": {"backend": "CLASSICAL"},
        }
    )
    add_step(
        {
            "step_id": f"apply_partial_fill_{index}",
            "effect_type": "SIM_PARTIAL_FILL_MODEL",
            "args": {
                "trade_fill_path": "trade_fill.json",
                "policy_path": policy_path,
                "model_path": model_path,
                "out_path": "shadow_fill.json",
            },
            "requires": {"backend": "CLASSICAL"},
        }
    )
    add_step(
        {
            "step_id": f"update_risk_{index}",
            "effect_type": "UPDATE_RISK_ENVELOPE",
            "args": {
                "trade_fill_path": "shadow_fill.json",
                "policy_path": policy_path,
                "out_path": "risk_envelope.json",
            },
            "requires": {"backend": "CLASSICAL"},
        }
    )
    add_step(
        {
            "step_id": f"order_lifecycle_{index}",
            "effect_type": "SIM_ORDER_LIFECYCLE",
            "args": {
                "shadow_fill_path": "shadow_fill.json",
                "model_path": model_path,
                "out_path": "shadow_execution_log.json",
            },
            "requires": {"backend": "CLASSICAL"},
        }
    )
    add_step(
        {
            "step_id": f"emit_ledger_{index}",
            "effect_type": "SIM_EMIT_TRADE_LEDGER",
            "args": {
                "shadow_fill_path": "shadow_fill.json",
                "risk_envelope_path": "risk_envelope.json",
                "signal_path": "signal.json",
                "out_path": "shadow_trade_ledger.json",
            },
            "requires": {"backend": "CLASSICAL"},
        }
    )
    add_step(
        {
            "step_id": f"emit_trade_report_{index}",
            "effect_type": "EMIT_TRADE_REPORT",
            "args": {
                "market_snapshot_path": "latency_snapshot.json",
                "signal_path": "signal.json",
                "trade_fill_path": "shadow_fill.json",
                "risk_envelope_path": "risk_envelope.json",
                "report_json_path": report_json,
                "report_md_path": report_md,
            },
            "requires": {"backend": "CLASSICAL"},
        }
    )

    return steps


def _build_navier_stokes_steps(program_ir: Dict[str, object], ctx: SchedulerContext) -> List[Dict[str, object]]:
    steps: List[Dict[str, object]] = []
    index = 0

    def add_step(step: Dict[str, object]) -> None:
        nonlocal index
        steps.append(step)
        index += 1

    if ctx.require_epoch_verification and ctx.anchor_path:
        add_step(
            {
                "step_id": f"verify_epoch_{index}",
                "effect_type": "VERIFY_EPOCH",
                "args": {"anchor_path": str(ctx.anchor_path)},
                "requires": {},
            }
        )
        if ctx.signature_path:
            add_step(
                {
                    "step_id": f"verify_signature_{index}",
                    "effect_type": "VERIFY_SIGNATURE",
                    "args": {
                        "anchor_path": str(ctx.anchor_path),
                        "sig_path": str(ctx.signature_path),
                        "pub_path": str(ctx.public_key_path),
                    },
                    "requires": {},
                }
            )

    state_path = str(ctx.ns_state_path) if ctx.ns_state_path else None
    policy_path = str(ctx.ns_policy_path) if ctx.ns_policy_path else None
    state_final = str(ctx.ns_state_final_path) if ctx.ns_state_final_path else "ns_state_final.json"
    observables_path = str(ctx.ns_observables_path) if ctx.ns_observables_path else "ns_observables.json"
    pressure_path = str(ctx.ns_pressure_path) if ctx.ns_pressure_path else "ns_pressure.json"
    gate_path = str(ctx.ns_gate_certificate_path) if ctx.ns_gate_certificate_path else "ns_gate_certificate.json"

    add_step(
        {
            "step_id": f"ns_evolve_linear_{index}",
            "effect_type": "NS_EVOLVE_LINEAR",
            "args": {"state_path": state_path, "out_path": "ns_state_linear.json"},
            "requires": {"backend": "CLASSICAL"},
        }
    )
    add_step(
        {
            "step_id": f"ns_apply_duhamel_{index}",
            "effect_type": "NS_APPLY_DUHAMEL",
            "args": {
                "state_path": "ns_state_linear.json",
                "policy_path": policy_path,
                "out_path": "ns_state_nonlinear.json",
            },
            "requires": {"backend": "CLASSICAL"},
        }
    )
    add_step(
        {
            "step_id": f"ns_project_leray_{index}",
            "effect_type": "NS_PROJECT_LERAY",
            "args": {"state_path": "ns_state_nonlinear.json", "out_path": "ns_state_projected.json"},
            "requires": {"backend": "CLASSICAL"},
        }
    )
    add_step(
        {
            "step_id": f"ns_pressure_recover_{index}",
            "effect_type": "NS_PRESSURE_RECOVER",
            "args": {"state_path": "ns_state_projected.json", "out_path": pressure_path},
            "requires": {"backend": "CLASSICAL"},
        }
    )
    add_step(
        {
            "step_id": f"ns_measure_obs_{index}",
            "effect_type": "NS_MEASURE_OBSERVABLES",
            "args": {
                "state_path": "ns_state_projected.json",
                "policy_path": policy_path,
                "out_path": observables_path,
            },
            "requires": {"backend": "CLASSICAL"},
        }
    )
    add_step(
        {
            "step_id": f"ns_check_barrier_{index}",
            "effect_type": "NS_CHECK_BARRIER",
            "args": {
                "observables_path": observables_path,
                "policy_path": policy_path,
                "out_path": gate_path,
            },
            "requires": {"backend": "CLASSICAL"},
        }
    )
    add_step(
        {
            "step_id": f"ns_emit_state_{index}",
            "effect_type": "NS_EMIT_STATE",
            "args": {"state_path": "ns_state_projected.json", "out_path": state_final},
            "requires": {"backend": "CLASSICAL"},
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
