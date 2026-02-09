from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from ...audit.constraint_inversion import invert_constraints
from ...backends.classical_lowering import lower_program_ir_to_backend_ir
from ...backends.qasm_lowering import lower_backend_ir_to_qasm
from ..context import RuntimeContext
from ..io.adapter import load_adapter
from ..redaction import scan_artifacts
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


def handle_measure_condition(step: EffectStep, ctx: RuntimeContext) -> EffectResult:
    prior_path = _resolve_input_path(ctx, step.args.get("prior_path"))
    posterior_path = _resolve_input_path(ctx, step.args.get("posterior_path"))
    if prior_path is None or posterior_path is None:
        return _refuse(step, "MeasurementInputsMissing", ["prior or posterior missing"])
    if not prior_path.exists() or not posterior_path.exists():
        return _refuse(step, "MeasurementInputsMissing", ["prior or posterior missing"])

    mode = str(step.args.get("mode", "deterministic"))
    trace = {
        "mode": mode,
        "prior_digest": _digest_bytes(prior_path.read_bytes()),
        "posterior_digest": _digest_bytes(posterior_path.read_bytes()),
    }
    out_path = _resolve_output_path(
        ctx,
        step.args,
        key="out_path",
        default_name="measurement_trace.json",
    )
    payload = _canonical_json(trace)
    digests = {
        prior_path.name: _digest_bytes(prior_path.read_bytes()),
        posterior_path.name: _digest_bytes(posterior_path.read_bytes()),
    }
    if out_path:
        out_path.write_text(payload, encoding="utf-8")
        digests[out_path.name] = _digest_bytes(out_path.read_bytes())
    else:
        digests["measurement_trace"] = _digest_bytes(payload.encode("utf-8"))
    return _ok(step, digests)


def handle_compute_delta_s(step: EffectStep, ctx: RuntimeContext) -> EffectResult:
    prior_path = _resolve_input_path(ctx, step.args.get("prior_path"))
    posterior_path = _resolve_input_path(ctx, step.args.get("posterior_path"))
    if prior_path is None or posterior_path is None:
        return _refuse(step, "MeasurementInputsMissing", ["prior or posterior missing"])
    if not prior_path.exists() or not posterior_path.exists():
        return _refuse(step, "MeasurementInputsMissing", ["prior or posterior missing"])
    prior_bytes = prior_path.read_bytes()
    posterior_bytes = posterior_path.read_bytes()
    prior_digest = _digest_bytes(prior_bytes)
    posterior_digest = _digest_bytes(posterior_bytes)
    prior_hash = _hash_to_unit(prior_bytes)
    posterior_hash = _hash_to_unit(posterior_bytes)
    delta_s = _round_delta(abs(posterior_hash - prior_hash))
    report = {
        "method": str(step.args.get("method", "hash_diff")),
        "delta_s": delta_s,
        "prior_digest": prior_digest,
        "posterior_digest": posterior_digest,
    }
    out_path = _resolve_output_path(
        ctx,
        step.args,
        key="out_path",
        default_name="delta_s_report.json",
    )
    payload = _canonical_json(report)
    digests = {
        prior_path.name: prior_digest,
        posterior_path.name: posterior_digest,
    }
    if out_path:
        out_path.write_text(payload, encoding="utf-8")
        digests[out_path.name] = _digest_bytes(out_path.read_bytes())
    else:
        digests["delta_s_report"] = _digest_bytes(payload.encode("utf-8"))
    return _ok(step, digests)


def handle_delta_s_gate(step: EffectStep, ctx: RuntimeContext) -> EffectResult:
    report_path = _resolve_input_path(ctx, step.args.get("delta_s_report_path"))
    if report_path is None or not report_path.exists():
        return _refuse(step, "DeltaSReportMissing", ["delta_s_report missing"])
    report = json.loads(report_path.read_text(encoding="utf-8"))
    token = ctx.execution_token
    policy = None
    if token is not None and token.delta_s_policy:
        policy = token.delta_s_policy
    if policy is None:
        policy = step.args.get("policy", {})
    if not isinstance(policy, dict):
        policy = {}
    threshold = float(policy.get("threshold", 0.0))
    comparator = str(policy.get("comparator", "gte"))
    delta_s_value = float(report.get("delta_s", 0.0))
    ok = delta_s_value >= threshold if comparator == "gte" else delta_s_value <= threshold
    decision = {
        "ok": ok,
        "delta_s": _round_delta(delta_s_value),
        "threshold": _round_delta(threshold),
        "comparator": comparator,
        "token_id": token.token_id if token else None,
    }
    out_path = _resolve_output_path(
        ctx,
        step.args,
        key="out_path",
        default_name="collapse_decision.json",
    )
    digests = {report_path.name: _digest_bytes(report_path.read_bytes())}
    if out_path:
        out_path.write_text(_canonical_json(decision), encoding="utf-8")
        digests[out_path.name] = _digest_bytes(out_path.read_bytes())
    else:
        digests["collapse_decision"] = _digest_bytes(_canonical_json(decision).encode("utf-8"))
    if not ok:
        return _refuse(step, "DeltaSGateFailed", ["delta_s gate failed"], digests)
    return _ok(step, digests)


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


def handle_ingest_market_fixture(step: EffectStep, ctx: RuntimeContext) -> EffectResult:
    fixture_path = _resolve_input_path(ctx, step.args.get("fixture_path"))
    if fixture_path is None or not fixture_path.exists():
        return _refuse(step, "MarketFixtureMissing", ["market fixture missing"])
    try:
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return _refuse(step, "MarketFixtureInvalid", ["market fixture invalid json"])
    if not isinstance(fixture, dict):
        return _refuse(step, "MarketFixtureInvalid", ["market fixture must be an object"])
    prices = fixture.get("prices")
    if not isinstance(prices, list) or not prices:
        return _refuse(step, "MarketFixtureInvalid", ["prices missing or empty"])
    prices = [float(value) for value in prices]
    snapshot = {
        "symbol": fixture.get("symbol", "UNKNOWN"),
        "prices": prices,
        "count": len(prices),
        "first_price": _round_price(prices[0]),
        "last_price": _round_price(prices[-1]),
    }
    out_path = _resolve_output_path(
        ctx,
        step.args,
        key="out_path",
        default_name="market_snapshot.json",
    )
    payload = _canonical_json(snapshot)
    if out_path:
        out_path.write_text(payload, encoding="utf-8")
        digest = _digest_bytes(out_path.read_bytes())
    else:
        digest = _digest_bytes(payload.encode("utf-8"))
    return _ok(step, {fixture_path.name: _digest_bytes(fixture_path.read_bytes()), "market_snapshot": digest})


def handle_compute_signal(step: EffectStep, ctx: RuntimeContext) -> EffectResult:
    snapshot_path = _resolve_output_path(ctx, step.args, key="market_snapshot_path")
    policy_path = _resolve_input_path(ctx, step.args.get("policy_path"))
    if snapshot_path is None or policy_path is None:
        return _refuse(step, "SignalInputsMissing", ["market snapshot or policy missing"])
    if not snapshot_path.exists() or not policy_path.exists():
        return _refuse(step, "SignalInputsMissing", ["market snapshot or policy missing"])
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    prices = snapshot.get("prices", [])
    if not isinstance(prices, list) or not prices:
        return _refuse(step, "SignalInputsMissing", ["prices missing"])
    first_price = float(prices[0])
    last_price = float(prices[-1])
    threshold = float(policy.get("signal_threshold", 0.0))
    change = last_price - first_price
    change_pct = change / first_price if first_price else 0.0
    action = "HOLD"
    if change_pct >= threshold:
        action = "BUY"
    elif change_pct <= -threshold:
        action = "SELL"
    signal = {
        "action": action,
        "threshold": _round_price(threshold),
        "price_change": _round_price(change),
        "price_change_pct": _round_price(change_pct),
    }
    out_path = _resolve_output_path(
        ctx,
        step.args,
        key="out_path",
        default_name="signal.json",
    )
    payload = _canonical_json(signal)
    if out_path:
        out_path.write_text(payload, encoding="utf-8")
        digest = _digest_bytes(out_path.read_bytes())
    else:
        digest = _digest_bytes(payload.encode("utf-8"))
    return _ok(
        step,
        {
            snapshot_path.name: _digest_bytes(snapshot_path.read_bytes()),
            policy_path.name: _digest_bytes(policy_path.read_bytes()),
            "signal": digest,
        },
    )


def handle_simulate_order(step: EffectStep, ctx: RuntimeContext) -> EffectResult:
    signal_path = _resolve_output_path(ctx, step.args, key="signal_path")
    snapshot_path = _resolve_output_path(ctx, step.args, key="market_snapshot_path")
    policy_path = _resolve_input_path(ctx, step.args.get("policy_path"))
    model_path = _resolve_input_path(ctx, step.args.get("model_path"))
    if signal_path is None or snapshot_path is None or policy_path is None:
        return _refuse(step, "OrderInputsMissing", ["signal or inputs missing"])
    if not signal_path.exists() or not snapshot_path.exists() or not policy_path.exists():
        return _refuse(step, "OrderInputsMissing", ["signal or inputs missing"])
    signal = json.loads(signal_path.read_text(encoding="utf-8"))
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    prices = snapshot.get("prices", [])
    if not isinstance(prices, list) or not prices:
        return _refuse(step, "OrderInputsMissing", ["prices missing"])
    last_price = float(prices[-1])
    action = str(signal.get("action", "HOLD"))
    spread_bps = float(policy.get("spread_bps", 0.0))
    slippage_bps = float(policy.get("slippage_bps", 0.0))
    if model_path is not None and model_path.exists():
        model = json.loads(model_path.read_text(encoding="utf-8"))
        spread_bps += float(model.get("spread_bps", 0.0))
        slippage_bps += float(model.get("slippage_bps", 0.0))
        max_slippage = policy.get("max_slippage_bps")
        if max_slippage is not None and slippage_bps > float(max_slippage):
            return _refuse(step, "SlippageExceedsMax", ["slippage exceeds max_slippage_bps"])
    order_size = float(policy.get("order_size", 1.0))

    executed = action in {"BUY", "SELL"}
    direction = action
    fill_price = last_price
    if executed:
        adjustment = (spread_bps + slippage_bps) / 10000.0
        if action == "BUY":
            fill_price = last_price * (1.0 + adjustment)
        else:
            fill_price = last_price * (1.0 - adjustment)
    fill = {
        "action": action,
        "executed": executed,
        "direction": direction,
        "order_size": _round_price(order_size),
        "last_price": _round_price(last_price),
        "fill_price": _round_price(fill_price),
    }
    out_path = _resolve_output_path(
        ctx,
        step.args,
        key="out_path",
        default_name="trade_fill.json",
    )
    payload = _canonical_json(fill)
    if out_path:
        out_path.write_text(payload, encoding="utf-8")
        digest = _digest_bytes(out_path.read_bytes())
    else:
        digest = _digest_bytes(payload.encode("utf-8"))
    return _ok(step, {out_path.name if out_path else "trade_fill": digest})


def handle_update_risk_envelope(step: EffectStep, ctx: RuntimeContext) -> EffectResult:
    fill_path = _resolve_output_path(ctx, step.args, key="trade_fill_path")
    policy_path = _resolve_input_path(ctx, step.args.get("policy_path"))
    if fill_path is None or policy_path is None:
        return _refuse(step, "RiskInputsMissing", ["trade fill or policy missing"])
    if not fill_path.exists() or not policy_path.exists():
        return _refuse(step, "RiskInputsMissing", ["trade fill or policy missing"])
    fill = json.loads(fill_path.read_text(encoding="utf-8"))
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    initial_equity = float(policy.get("initial_equity", 10000.0))
    max_drawdown = float(policy.get("max_drawdown", 0.0))
    order_size = float(fill.get("order_size", 1.0))
    last_price = float(fill.get("last_price", 0.0))
    fill_price = float(fill.get("fill_price", last_price))
    action = str(fill.get("action", "HOLD"))
    pnl = 0.0
    if fill.get("executed"):
        if action == "BUY":
            pnl = (last_price - fill_price) * order_size
        elif action == "SELL":
            pnl = (fill_price - last_price) * order_size
    equity = initial_equity + pnl
    drawdown = (initial_equity - equity) / initial_equity if initial_equity else 0.0
    envelope = {
        "initial_equity": _round_price(initial_equity),
        "equity": _round_price(equity),
        "drawdown": _round_price(drawdown),
        "max_drawdown": _round_price(max_drawdown),
        "pnl": _round_price(pnl),
    }
    out_path = _resolve_output_path(
        ctx,
        step.args,
        key="out_path",
        default_name="risk_envelope.json",
    )
    payload = _canonical_json(envelope)
    digests = {fill_path.name: _digest_bytes(fill_path.read_bytes())}
    if out_path:
        out_path.write_text(payload, encoding="utf-8")
        digests[out_path.name] = _digest_bytes(out_path.read_bytes())
    else:
        digests["risk_envelope"] = _digest_bytes(payload.encode("utf-8"))
    if drawdown > max_drawdown:
        return _refuse(step, "RiskEnvelopeViolation", ["drawdown exceeds max_drawdown"], digests)
    return _ok(step, digests)


def handle_emit_trade_report(step: EffectStep, ctx: RuntimeContext) -> EffectResult:
    snapshot_path = _resolve_output_path(ctx, step.args, key="market_snapshot_path")
    signal_path = _resolve_output_path(ctx, step.args, key="signal_path")
    fill_path = _resolve_output_path(ctx, step.args, key="trade_fill_path")
    risk_path = _resolve_output_path(ctx, step.args, key="risk_envelope_path")
    if snapshot_path is None or signal_path is None or fill_path is None or risk_path is None:
        return _refuse(step, "ReportInputsMissing", ["trade report inputs missing"])
    for path in [snapshot_path, signal_path, fill_path, risk_path]:
        if not path.exists():
            return _refuse(step, "ReportInputsMissing", [f"missing: {path}"])
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    signal = json.loads(signal_path.read_text(encoding="utf-8"))
    fill = json.loads(fill_path.read_text(encoding="utf-8"))
    risk = json.loads(risk_path.read_text(encoding="utf-8"))
    report = {
        "symbol": snapshot.get("symbol"),
        "action": signal.get("action"),
        "executed": fill.get("executed"),
        "fill_price": fill.get("fill_price"),
        "fill_fraction": fill.get("fill_fraction"),
        "equity": risk.get("equity"),
        "drawdown": risk.get("drawdown"),
        "max_drawdown": risk.get("max_drawdown"),
        "pnl": risk.get("pnl"),
    }
    report_json_path = _resolve_output_path(
        ctx,
        step.args,
        key="report_json_path",
        default_name="trade_report.json",
    )
    report_md_path = _resolve_output_path(
        ctx,
        step.args,
        key="report_md_path",
        default_name="trade_report.md",
    )
    payload = _canonical_json(report)
    digests = {}
    if report_json_path:
        report_json_path.write_text(payload, encoding="utf-8")
        digests[report_json_path.name] = _digest_bytes(report_json_path.read_bytes())
    if report_md_path:
        lines = [
            "# Trade Report",
            f"symbol: {report.get('symbol')}",
            f"action: {report.get('action')}",
            f"executed: {report.get('executed')}",
            f"fill_price: {report.get('fill_price')}",
            f"equity: {report.get('equity')}",
            f"drawdown: {report.get('drawdown')}",
            f"max_drawdown: {report.get('max_drawdown')}",
            f"pnl: {report.get('pnl')}",
        ]
        report_md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        digests[report_md_path.name] = _digest_bytes(report_md_path.read_bytes())
    return _ok(step, digests)


def handle_sim_market_model_load(step: EffectStep, ctx: RuntimeContext) -> EffectResult:
    model_path = _resolve_input_path(ctx, step.args.get("model_path"))
    if model_path is None or not model_path.exists():
        return _refuse(step, "ShadowModelMissing", ["shadow model missing"])
    try:
        model = json.loads(model_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return _refuse(step, "ShadowModelInvalid", ["shadow model invalid json"])
    seed = str(model.get("seed", "")).strip()
    if not seed or len(seed) != 64:
        return _refuse(step, "ShadowModelInvalid", ["seed missing or invalid"])
    model_core = {
        "model_id": str(model.get("model_id", "shadow_v1")),
        "seed": seed,
        "latency_steps": int(model.get("latency_steps", 0)),
        "spread_bps": float(model.get("spread_bps", 0.0)),
        "slippage_bps": float(model.get("slippage_bps", 0.0)),
        "partial_fill_ratio": float(model.get("partial_fill_ratio", 1.0)),
        "regime_shift_bps": float(model.get("regime_shift_bps", 0.0)),
        "seed_jitter_bps": float(model.get("seed_jitter_bps", 0.0)),
    }
    jitter = _seeded_float(seed, "slippage_jitter") * model_core["seed_jitter_bps"]
    model_core["slippage_bps"] = _round_price(model_core["slippage_bps"] + jitter)
    seed_id = _digest_bytes(_canonical_json(model_core).encode("utf-8"))
    model_out = dict(model_core)
    model_out["seed_id"] = seed_id

    out_path = _resolve_output_path(
        ctx,
        step.args,
        key="out_path",
        default_name="shadow_model.json",
    )
    seed_path = _resolve_output_path(
        ctx,
        step.args,
        key="seed_out_path",
        default_name="shadow_seed.json",
    )
    digests = {model_path.name: _digest_bytes(model_path.read_bytes())}
    if out_path:
        out_path.write_text(_canonical_json(model_out), encoding="utf-8")
        digests[out_path.name] = _digest_bytes(out_path.read_bytes())
    if seed_path:
        seed_payload = _canonical_json({"seed": seed, "seed_id": seed_id})
        seed_path.write_text(seed_payload, encoding="utf-8")
        digests[seed_path.name] = _digest_bytes(seed_path.read_bytes())
    return _ok(step, digests)


def handle_sim_regime_shift_step(step: EffectStep, ctx: RuntimeContext) -> EffectResult:
    snapshot_path = _resolve_output_path(ctx, step.args, key="market_snapshot_path")
    model_path = _resolve_input_path(ctx, step.args.get("model_path"))
    if snapshot_path is None or model_path is None:
        return _refuse(step, "ShadowInputsMissing", ["snapshot or model missing"])
    if not snapshot_path.exists() or not model_path.exists():
        return _refuse(step, "ShadowInputsMissing", ["snapshot or model missing"])
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    model = json.loads(model_path.read_text(encoding="utf-8"))
    prices = snapshot.get("prices", [])
    if not isinstance(prices, list) or not prices:
        return _refuse(step, "ShadowInputsMissing", ["prices missing"])
    shift_bps = float(model.get("regime_shift_bps", 0.0))
    factor = 1.0 + shift_bps / 10000.0
    adjusted = [_round_price(float(price) * factor) for price in prices]
    regime_snapshot = {
        "symbol": snapshot.get("symbol"),
        "prices": adjusted,
        "count": len(adjusted),
        "first_price": _round_price(adjusted[0]),
        "last_price": _round_price(adjusted[-1]),
        "regime_shift_bps": _round_price(shift_bps),
    }
    out_path = _resolve_output_path(
        ctx,
        step.args,
        key="out_path",
        default_name="regime_snapshot.json",
    )
    payload = _canonical_json(regime_snapshot)
    if out_path:
        out_path.write_text(payload, encoding="utf-8")
        digest = _digest_bytes(out_path.read_bytes())
    else:
        digest = _digest_bytes(payload.encode("utf-8"))
    return _ok(step, {snapshot_path.name: _digest_bytes(snapshot_path.read_bytes()), "regime_snapshot": digest})


def handle_sim_latency_apply(step: EffectStep, ctx: RuntimeContext) -> EffectResult:
    snapshot_path = _resolve_output_path(ctx, step.args, key="market_snapshot_path")
    model_path = _resolve_input_path(ctx, step.args.get("model_path"))
    policy_path = _resolve_input_path(ctx, step.args.get("policy_path"))
    if snapshot_path is None or model_path is None or policy_path is None:
        return _refuse(step, "LatencyInputsMissing", ["latency inputs missing"])
    if not snapshot_path.exists() or not model_path.exists() or not policy_path.exists():
        return _refuse(step, "LatencyInputsMissing", ["latency inputs missing"])
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    model = json.loads(model_path.read_text(encoding="utf-8"))
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    prices = snapshot.get("prices", [])
    if not isinstance(prices, list) or not prices:
        return _refuse(step, "LatencyInputsMissing", ["prices missing"])
    latency_steps = int(model.get("latency_steps", 0))
    max_staleness = int(policy.get("max_staleness_steps", latency_steps))
    staleness_steps = min(latency_steps, max(0, len(prices) - 1))
    if staleness_steps > max_staleness:
        return _refuse(step, "StalenessViolation", ["staleness exceeds max_staleness_steps"])
    spread_bps = float(model.get("spread_bps", 0.0))
    slippage_bps = float(model.get("slippage_bps", 0.0))
    partial_fill = float(model.get("partial_fill_ratio", 1.0))
    uncertainty_score = latency_steps + (spread_bps + slippage_bps) / 10.0 + (1.0 - partial_fill) * 10.0
    max_uncertainty = policy.get("max_uncertainty")
    if max_uncertainty is not None and uncertainty_score > float(max_uncertainty):
        return _refuse(step, "UncertaintyEnvelopeExceeded", ["uncertainty exceeds max_uncertainty"])
    stale_index = max(0, len(prices) - 1 - latency_steps)
    latency_prices = [float(value) for value in prices[: stale_index + 1]]
    latency_snapshot = {
        "symbol": snapshot.get("symbol"),
        "prices": latency_prices,
        "count": len(latency_prices),
        "first_price": _round_price(latency_prices[0]),
        "last_price": _round_price(latency_prices[-1]),
        "latency_steps": latency_steps,
        "staleness_steps": staleness_steps,
    }
    out_path = _resolve_output_path(
        ctx,
        step.args,
        key="out_path",
        default_name="latency_snapshot.json",
    )
    payload = _canonical_json(latency_snapshot)
    if out_path:
        out_path.write_text(payload, encoding="utf-8")
        digest = _digest_bytes(out_path.read_bytes())
    else:
        digest = _digest_bytes(payload.encode("utf-8"))
    return _ok(step, {snapshot_path.name: _digest_bytes(snapshot_path.read_bytes()), "latency_snapshot": digest})


def handle_sim_partial_fill_model(step: EffectStep, ctx: RuntimeContext) -> EffectResult:
    fill_path = _resolve_output_path(ctx, step.args, key="trade_fill_path")
    model_path = _resolve_input_path(ctx, step.args.get("model_path"))
    policy_path = _resolve_input_path(ctx, step.args.get("policy_path"))
    if fill_path is None or model_path is None or policy_path is None:
        return _refuse(step, "PartialFillInputsMissing", ["partial fill inputs missing"])
    if not fill_path.exists() or not model_path.exists() or not policy_path.exists():
        return _refuse(step, "PartialFillInputsMissing", ["partial fill inputs missing"])
    fill = json.loads(fill_path.read_text(encoding="utf-8"))
    model = json.loads(model_path.read_text(encoding="utf-8"))
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    fill_ratio = float(model.get("partial_fill_ratio", 1.0))
    min_fill_ratio = float(policy.get("min_fill_ratio", 0.0))
    if fill_ratio < min_fill_ratio:
        return _refuse(step, "PartialFillTooLow", ["partial fill ratio below minimum"], {fill_path.name: _digest_bytes(fill_path.read_bytes())})
    order_size = float(fill.get("order_size", 0.0))
    shadow_fill = dict(fill)
    shadow_fill["fill_fraction"] = _round_price(fill_ratio)
    shadow_fill["filled_size"] = _round_price(order_size * fill_ratio)
    out_path = _resolve_output_path(
        ctx,
        step.args,
        key="out_path",
        default_name="shadow_fill.json",
    )
    payload = _canonical_json(shadow_fill)
    digests = {fill_path.name: _digest_bytes(fill_path.read_bytes())}
    if out_path:
        out_path.write_text(payload, encoding="utf-8")
        digests[out_path.name] = _digest_bytes(out_path.read_bytes())
    else:
        digests["shadow_fill"] = _digest_bytes(payload.encode("utf-8"))
    return _ok(step, digests)


def handle_sim_order_lifecycle(step: EffectStep, ctx: RuntimeContext) -> EffectResult:
    fill_path = _resolve_output_path(ctx, step.args, key="shadow_fill_path")
    model_path = _resolve_input_path(ctx, step.args.get("model_path"))
    if fill_path is None or model_path is None:
        return _refuse(step, "LifecycleInputsMissing", ["shadow fill or model missing"])
    if not fill_path.exists() or not model_path.exists():
        return _refuse(step, "LifecycleInputsMissing", ["shadow fill or model missing"])
    fill = json.loads(fill_path.read_text(encoding="utf-8"))
    model = json.loads(model_path.read_text(encoding="utf-8"))
    latency_steps = int(model.get("latency_steps", 0))
    executed = bool(fill.get("executed"))
    fill_fraction = float(fill.get("fill_fraction", 1.0))
    events = [
        {"event": "submit", "t": 0},
        {"event": "ack", "t": latency_steps},
    ]
    if executed:
        events.append({"event": "partial_fill", "t": latency_steps + 1, "fill_fraction": _round_price(fill_fraction)})
        if fill_fraction < 1.0:
            events.append({"event": "cancel", "t": latency_steps + 2})
        else:
            events.append({"event": "fill", "t": latency_steps + 2})
    else:
        events.append({"event": "no_trade", "t": latency_steps + 1})
    log = {"events": events, "latency_steps": latency_steps}
    out_path = _resolve_output_path(
        ctx,
        step.args,
        key="out_path",
        default_name="shadow_execution_log.json",
    )
    payload = _canonical_json(log)
    if out_path:
        out_path.write_text(payload, encoding="utf-8")
        digest = _digest_bytes(out_path.read_bytes())
    else:
        digest = _digest_bytes(payload.encode("utf-8"))
    return _ok(step, {out_path.name if out_path else "shadow_execution_log": digest})


def handle_sim_emit_trade_ledger(step: EffectStep, ctx: RuntimeContext) -> EffectResult:
    fill_path = _resolve_output_path(ctx, step.args, key="shadow_fill_path")
    risk_path = _resolve_output_path(ctx, step.args, key="risk_envelope_path")
    signal_path = _resolve_output_path(ctx, step.args, key="signal_path")
    if fill_path is None or risk_path is None or signal_path is None:
        return _refuse(step, "LedgerInputsMissing", ["ledger inputs missing"])
    if not fill_path.exists() or not risk_path.exists() or not signal_path.exists():
        return _refuse(step, "LedgerInputsMissing", ["ledger inputs missing"])
    fill = json.loads(fill_path.read_text(encoding="utf-8"))
    risk = json.loads(risk_path.read_text(encoding="utf-8"))
    signal = json.loads(signal_path.read_text(encoding="utf-8"))
    ledger = {
        "action": signal.get("action"),
        "executed": fill.get("executed"),
        "fill_fraction": fill.get("fill_fraction"),
        "filled_size": fill.get("filled_size"),
        "fill_price": fill.get("fill_price"),
        "equity": risk.get("equity"),
        "drawdown": risk.get("drawdown"),
        "pnl": risk.get("pnl"),
    }
    out_path = _resolve_output_path(
        ctx,
        step.args,
        key="out_path",
        default_name="shadow_trade_ledger.json",
    )
    payload = _canonical_json(ledger)
    if out_path:
        out_path.write_text(payload, encoding="utf-8")
        digest = _digest_bytes(out_path.read_bytes())
    else:
        digest = _digest_bytes(payload.encode("utf-8"))
    return _ok(step, {out_path.name if out_path else "shadow_trade_ledger": digest})


def handle_ns_evolve_linear(step: EffectStep, ctx: RuntimeContext) -> EffectResult:
    state_path = _resolve_input_path(ctx, step.args.get("state_path"))
    if state_path is None or not state_path.exists():
        return _refuse(step, "StateMissing", ["state missing"])
    state = _load_pde_state(state_path)
    dt = float(step.args.get("dt", state["dt"]))
    nu = float(step.args.get("nu", state["nu"]))
    decay = _exp_safe(-nu * dt)
    field = [
        {"u": _round_price(cell["u"] * decay), "v": _round_price(cell["v"] * decay)}
        for cell in state["field"]
    ]
    evolved = _with_state(state, field=field, t=state["t"] + dt, dt=dt, nu=nu)
    out_path = _resolve_output_path(ctx, step.args, key="out_path", default_name="ns_state_linear.json")
    return _write_state_result(step, state_path, evolved, out_path)


def handle_ns_apply_duhamel(step: EffectStep, ctx: RuntimeContext) -> EffectResult:
    state_path = _resolve_input_path(ctx, step.args.get("state_path"))
    policy_path = _resolve_input_path(ctx, step.args.get("policy_path"))
    if state_path is None or not state_path.exists():
        return _refuse(step, "StateMissing", ["state missing"])
    state = _load_pde_state(state_path)
    policy = _load_policy(policy_path) if policy_path else {}
    dt = float(step.args.get("dt", state["dt"]))
    coeff = float(policy.get("nonlinear_coeff", 0.1))
    field = []
    for cell in state["field"]:
        u = cell["u"]
        v = cell["v"]
        u_new = u - dt * coeff * u * abs(u)
        v_new = v - dt * coeff * v * abs(v)
        field.append({"u": _round_price(u_new), "v": _round_price(v_new)})
    updated = _with_state(state, field=field, t=state["t"], dt=dt, nu=state["nu"])
    out_path = _resolve_output_path(ctx, step.args, key="out_path", default_name="ns_state_nonlinear.json")
    return _write_state_result(step, state_path, updated, out_path)


def handle_ns_project_leray(step: EffectStep, ctx: RuntimeContext) -> EffectResult:
    state_path = _resolve_input_path(ctx, step.args.get("state_path"))
    if state_path is None or not state_path.exists():
        return _refuse(step, "StateMissing", ["state missing"])
    state = _load_pde_state(state_path)
    grid = state["grid"]
    divergence = _divergence(field=state["field"], nx=grid["nx"], ny=grid["ny"], dx=grid["dx"], dy=grid["dy"])
    residual = _round_price(max(abs(val) for val in divergence))
    projection_gain = float(step.args.get("projection_gain", 0.1))
    field = []
    for idx, cell in enumerate(state["field"]):
        correction = projection_gain * divergence[idx]
        field.append(
            {
                "u": _round_price(cell["u"] - correction),
                "v": _round_price(cell["v"] - correction),
            }
        )
    projected = _with_state(
        state,
        field=field,
        divergence_residual=residual,
        projection_gain=projection_gain,
    )
    out_path = _resolve_output_path(ctx, step.args, key="out_path", default_name="ns_state_projected.json")
    return _write_state_result(step, state_path, projected, out_path)


def handle_ns_pressure_recover(step: EffectStep, ctx: RuntimeContext) -> EffectResult:
    state_path = _resolve_input_path(ctx, step.args.get("state_path"))
    if state_path is None or not state_path.exists():
        return _refuse(step, "StateMissing", ["state missing"])
    state = _load_pde_state(state_path)
    pressure = [_round_price(-0.5 * (cell["u"] ** 2 + cell["v"] ** 2)) for cell in state["field"]]
    out_path = _resolve_output_path(ctx, step.args, key="out_path", default_name="ns_pressure.json")
    payload = _canonical_json({"pressure": pressure})
    digests = {state_path.name: _digest_bytes(state_path.read_bytes())}
    if out_path:
        out_path.write_text(payload, encoding="utf-8")
        digests[out_path.name] = _digest_bytes(out_path.read_bytes())
    else:
        digests["pressure"] = _digest_bytes(payload.encode("utf-8"))
    return _ok(step, digests)


def handle_ns_measure_observables(step: EffectStep, ctx: RuntimeContext) -> EffectResult:
    state_path = _resolve_input_path(ctx, step.args.get("state_path"))
    policy_path = _resolve_input_path(ctx, step.args.get("policy_path"))
    if state_path is None or not state_path.exists():
        return _refuse(step, "StateMissing", ["state missing"])
    state = _load_pde_state(state_path)
    policy = _load_policy(policy_path) if policy_path else {}
    grid = state["grid"]
    energy = _energy(state["field"])
    divergence = _divergence(field=state["field"], nx=grid["nx"], ny=grid["ny"], dx=grid["dx"], dy=grid["dy"])
    residual = max(abs(val) for val in divergence)
    dissipation = _dissipation(state["field"], grid["nx"], grid["ny"], grid["dx"], grid["dy"], state["nu"])
    cfl = _cfl(state["field"], grid["dx"], grid["dy"], state["dt"])
    observables = {
        "energy": _round_price(energy),
        "divergence_residual": _round_price(residual),
        "dissipation": _round_price(dissipation),
        "cfl": _round_price(cfl),
        "dt": _round_price(state["dt"]),
        "policy_id": policy.get("policy_id", "policy"),
    }
    out_path = _resolve_output_path(ctx, step.args, key="out_path", default_name="ns_observables.json")
    payload = _canonical_json(observables)
    digests = {state_path.name: _digest_bytes(state_path.read_bytes())}
    if out_path:
        out_path.write_text(payload, encoding="utf-8")
        digests[out_path.name] = _digest_bytes(out_path.read_bytes())
    else:
        digests["observables"] = _digest_bytes(payload.encode("utf-8"))
    return _ok(step, digests)


def handle_ns_check_barrier(step: EffectStep, ctx: RuntimeContext) -> EffectResult:
    observables_path = _resolve_input_path(ctx, step.args.get("observables_path"))
    policy_path = _resolve_input_path(ctx, step.args.get("policy_path"))
    if observables_path is None or policy_path is None:
        return _refuse(step, "BarrierInputsMissing", ["observables or policy missing"])
    if not observables_path.exists() or not policy_path.exists():
        return _refuse(step, "BarrierInputsMissing", ["observables or policy missing"])
    observables = json.loads(observables_path.read_text(encoding="utf-8"))
    policy = _load_policy(policy_path)
    max_energy = float(policy.get("max_energy", 0.0))
    max_div = float(policy.get("max_divergence", 0.0))
    max_dissipation = float(policy.get("max_dissipation", 0.0))
    max_cfl = float(policy.get("max_cfl", 0.0))
    max_dt = float(policy.get("max_dt", observables.get("dt", 0.0)))
    errors: List[str] = []
    refusal_type = None
    if max_energy and float(observables.get("energy", 0.0)) > max_energy:
        refusal_type = refusal_type or "EnergyBarrierViolated"
        errors.append("energy exceeds max_energy")
    if max_div and float(observables.get("divergence_residual", 0.0)) > max_div:
        refusal_type = refusal_type or "DivergenceResidualExceeded"
        errors.append("divergence residual exceeds max_divergence")
    if max_dissipation and float(observables.get("dissipation", 0.0)) > max_dissipation:
        refusal_type = refusal_type or "DissipationExceeded"
        errors.append("dissipation exceeds max_dissipation")
    if max_cfl and float(observables.get("cfl", 0.0)) > max_cfl:
        refusal_type = refusal_type or "CFLViolation"
        errors.append("cfl exceeds max_cfl")
    if max_dt and float(observables.get("dt", 0.0)) > max_dt:
        refusal_type = refusal_type or "DtExceeded"
        errors.append("dt exceeds max_dt")

    certificate = {
        "ok": not errors,
        "errors": list(errors),
        "observables_digest": _digest_bytes(observables_path.read_bytes()),
        "policy_digest": _digest_bytes(policy_path.read_bytes()),
    }
    out_path = _resolve_output_path(ctx, step.args, key="out_path", default_name="ns_gate_certificate.json")
    if out_path:
        out_path.write_text(_canonical_json(certificate), encoding="utf-8")
    digests = {
        observables_path.name: _digest_bytes(observables_path.read_bytes()),
        policy_path.name: _digest_bytes(policy_path.read_bytes()),
    }
    if out_path:
        digests[out_path.name] = _digest_bytes(out_path.read_bytes())
    if errors:
        return _refuse(step, refusal_type or "BarrierViolation", errors, digests)
    return _ok(step, digests)


def handle_ns_emit_state(step: EffectStep, ctx: RuntimeContext) -> EffectResult:
    state_path = _resolve_input_path(ctx, step.args.get("state_path"))
    if state_path is None or not state_path.exists():
        return _refuse(step, "StateMissing", ["state missing"])
    state = _load_pde_state(state_path)
    out_path = _resolve_output_path(ctx, step.args, key="out_path", default_name="ns_state_final.json")
    return _write_state_result(step, state_path, state, out_path)


def handle_evaluate_agent_proposal(step: EffectStep, ctx: RuntimeContext) -> EffectResult:
    proposal_path = _resolve_output_path(ctx, step.args, key="proposal_path")
    policy_path = _resolve_output_path(ctx, step.args, key="policy_path")
    if proposal_path is None or policy_path is None:
        return _refuse(step, "AgentInputsMissing", ["proposal or policy path missing"])
    if not proposal_path.exists() or not policy_path.exists():
        return _refuse(step, "AgentInputsMissing", ["proposal or policy file missing"])

    try:
        proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return _refuse(step, "AgentProposalInvalid", ["proposal invalid json"])

    try:
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return _refuse(step, "AgentPolicyInvalid", ["policy invalid json"])

    if not isinstance(proposal, dict):
        return _refuse(step, "AgentProposalInvalid", ["proposal must be an object"])
    if not isinstance(policy, dict):
        return _refuse(step, "AgentPolicyInvalid", ["policy must be an object"])

    allowed_actions = policy.get("allowed_actions", [])
    if not isinstance(allowed_actions, list):
        return _refuse(step, "AgentPolicyInvalid", ["allowed_actions must be a list"])
    allowed_actions = [str(item) for item in allowed_actions]

    allowed_capabilities = policy.get("allowed_capabilities", [])
    if not isinstance(allowed_capabilities, list):
        return _refuse(step, "AgentPolicyInvalid", ["allowed_capabilities must be a list"])
    allowed_capabilities = [str(item) for item in allowed_capabilities]

    action = str(proposal.get("action", "")).strip()
    risk_score = proposal.get("risk_score", 0)
    required_caps = proposal.get("required_capabilities", [])
    if not isinstance(required_caps, list):
        return _refuse(step, "AgentProposalInvalid", ["required_capabilities must be a list"])
    required_caps = [str(item) for item in required_caps]

    reasons: List[str] = []
    if not action:
        reasons.append("action missing")
    elif action not in allowed_actions:
        reasons.append("action not allowed")

    try:
        risk_value = float(risk_score)
    except (TypeError, ValueError):
        risk_value = 0.0
        reasons.append("risk_score invalid")

    max_risk = policy.get("max_risk_score", 0)
    try:
        max_risk_value = float(max_risk)
    except (TypeError, ValueError):
        max_risk_value = 0.0
        reasons.append("max_risk_score invalid")

    if risk_value > max_risk_value:
        reasons.append("risk_score exceeds max_risk_score")

    for cap in required_caps:
        if cap not in allowed_capabilities:
            reasons.append(f"capability not allowed: {cap}")

    proposal_digest = _digest_bytes(proposal_path.read_bytes())
    policy_digest = _digest_bytes(policy_path.read_bytes())

    decision = {
        "proposal_id": proposal.get("proposal_id"),
        "policy_id": policy.get("policy_id"),
        "action": action,
        "allowed": not reasons,
        "reasons": list(reasons),
        "proposal_digest": proposal_digest,
        "policy_digest": policy_digest,
    }
    decision_payload = _canonical_json(decision)
    decision_path = _resolve_output_path(
        ctx,
        step.args,
        key="decision_path",
        default_name="agent_decision.json",
    )
    decision_digest = _digest_bytes(decision_payload.encode("utf-8"))
    digests = {
        proposal_path.name: proposal_digest,
        policy_path.name: policy_digest,
    }
    if decision_path:
        decision_path.write_text(decision_payload, encoding="utf-8")
        digests[decision_path.name] = _digest_bytes(decision_path.read_bytes())
    else:
        digests["agent_decision.json"] = decision_digest

    if reasons:
        return _refuse(step, "AgentProposalRefused", reasons, digests)
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


def handle_io_connect(step: EffectStep, ctx: RuntimeContext) -> EffectResult:
    policy_error = _ensure_io_policy(step, ctx, required_scope="BROKER_CONNECT")
    if policy_error:
        return policy_error
    request = _build_io_request(step, ctx, action="connect")
    adapter = _resolve_io_adapter(step, ctx)
    if isinstance(adapter, EffectResult):
        return adapter
    if adapter is not None:
        response = adapter.connect(request.get("endpoint", ""), request.get("params", {}))
    else:
        response = {
            "status": "connected",
            "endpoint": request.get("endpoint"),
            "request_id": request["request_id"],
            "mock": True,
        }
    return _emit_io_artifacts(step, ctx, request, response, event_type="connect")


def handle_io_submit_order(step: EffectStep, ctx: RuntimeContext) -> EffectResult:
    policy_error = _ensure_io_policy(step, ctx, required_scope="ORDER_SUBMIT")
    if policy_error:
        return policy_error
    order = _sanitize_payload(step.args.get("order", {}))
    request = _build_io_request(step, ctx, action="submit_order", extra={"order": order})
    adapter = _resolve_io_adapter(step, ctx)
    if isinstance(adapter, EffectResult):
        return adapter
    if adapter is not None:
        response = adapter.submit_order(request.get("endpoint", ""), order, request.get("params", {}))
    else:
        order_id = _request_id(_canonical_json(request))
        response = {
            "status": "accepted",
            "order_id": order_id,
            "request_id": request["request_id"],
            "mock": True,
        }
    return _emit_io_artifacts(step, ctx, request, response, event_type="submit_order")


def handle_io_cancel_order(step: EffectStep, ctx: RuntimeContext) -> EffectResult:
    policy_error = _ensure_io_policy(step, ctx, required_scope="ORDER_CANCEL")
    if policy_error:
        return policy_error
    order_id = str(step.args.get("order_id", "")).strip()
    if not order_id:
        return _refuse(step, "OrderIdMissing", ["order_id missing"])
    request = _build_io_request(step, ctx, action="cancel_order", extra={"order_id": order_id})
    adapter = _resolve_io_adapter(step, ctx)
    if isinstance(adapter, EffectResult):
        return adapter
    if adapter is not None:
        response = adapter.cancel_order(request.get("endpoint", ""), order_id, request.get("params", {}))
    else:
        response = {
            "status": "cancelled",
            "order_id": order_id,
            "request_id": request["request_id"],
            "mock": True,
        }
    return _emit_io_artifacts(step, ctx, request, response, event_type="cancel_order")


def handle_io_query_fills(step: EffectStep, ctx: RuntimeContext) -> EffectResult:
    policy_error = _ensure_io_policy(step, ctx, required_scope="ORDER_QUERY")
    if policy_error:
        return policy_error
    order_id = str(step.args.get("order_id", "")).strip()
    if not order_id:
        return _refuse(step, "OrderIdMissing", ["order_id missing"])
    request = _build_io_request(step, ctx, action="query_fills", extra={"order_id": order_id})
    fill = {
        "order_id": order_id,
        "fill_qty": _round_price(float(step.args.get("fill_qty", 0.0))),
        "fill_price": _round_price(float(step.args.get("fill_price", 0.0))),
    }
    adapter = _resolve_io_adapter(step, ctx)
    if isinstance(adapter, EffectResult):
        return adapter
    if adapter is not None:
        response = adapter.query_fills(request.get("endpoint", ""), order_id, request.get("params", {}))
    else:
        response = {
            "status": "ok",
            "request_id": request["request_id"],
            "fills": [fill],
            "mock": True,
        }
    return _emit_io_artifacts(step, ctx, request, response, event_type="query_fills")


def handle_io_emit_io_event(step: EffectStep, ctx: RuntimeContext) -> EffectResult:
    policy_error = _ensure_io_policy(step, ctx, required_scope="IO_EVENT")
    if policy_error:
        return policy_error
    request = _build_io_request(step, ctx, action="emit_event")
    event = {
        "event_type": str(step.args.get("event_type", "io_event")),
        "request_id": request["request_id"],
        "endpoint": request.get("endpoint"),
        "mock": True,
    }
    return _emit_io_event(step, ctx, event)


def handle_io_reconcile(step: EffectStep, ctx: RuntimeContext) -> EffectResult:
    policy_error = _ensure_io_policy(step, ctx, required_scope="RECONCILE")
    if policy_error:
        return policy_error
    request_path = _resolve_output_path(ctx, step.args, key="request_path")
    response_path = _resolve_output_path(ctx, step.args, key="response_path")
    if request_path is None or response_path is None:
        return _refuse(step, "IOReconciliationInputsMissing", ["request/response missing"])
    if not request_path.exists() or not response_path.exists():
        return _refuse(step, "IOReconciliationInputsMissing", ["request/response missing"])

    request = json.loads(request_path.read_text(encoding="utf-8"))
    response = json.loads(response_path.read_text(encoding="utf-8"))
    expected_status = step.args.get("expected_status")
    status = response.get("status")
    reasons: List[str] = []
    ok = True
    if expected_status is not None and str(status) != str(expected_status):
        ok = False
        reasons.append("status mismatch")
    if response.get("ambiguous", False):
        ok = False
        reasons.append("ambiguous response")

    action = "commit" if ok else "refuse"
    token = ctx.execution_token
    if not ok and token and token.io_policy and token.io_policy.get("io_requires_reconciliation", True):
        action = "rollback"

    outcome = {
        "ok": ok,
        "action": action,
        "request_digest": _digest_bytes(request_path.read_bytes()),
        "response_digest": _digest_bytes(response_path.read_bytes()),
        "token_id": token.token_id if token else None,
        "reasons": list(reasons),
    }
    outcome_path = _resolve_output_path(
        ctx,
        step.args,
        key="outcome_path",
        default_name="io_outcome.json",
    )
    if outcome_path:
        outcome_path.write_text(_canonical_json(outcome), encoding="utf-8")
    reconciliation = {
        "ok": ok,
        "action": action,
        "request_id": request.get("request_id"),
        "response_status": status,
        "outcome_digest": _digest_bytes(_canonical_json(outcome).encode("utf-8")),
    }
    reconciliation_path = _resolve_output_path(
        ctx,
        step.args,
        key="reconciliation_path",
        default_name="reconciliation_report.json",
    )
    if reconciliation_path:
        reconciliation_path.write_text(_canonical_json(reconciliation), encoding="utf-8")

    digests = {
        request_path.name: _digest_bytes(request_path.read_bytes()),
        response_path.name: _digest_bytes(response_path.read_bytes()),
    }
    if outcome_path:
        digests[outcome_path.name] = _digest_bytes(outcome_path.read_bytes())
    if reconciliation_path:
        digests[reconciliation_path.name] = _digest_bytes(reconciliation_path.read_bytes())

    if not ok:
        return _refuse(step, "IOAmbiguousResult", reasons or ["reconciliation failed"], digests)
    return _ok(step, digests)


def handle_io_rollback(step: EffectStep, ctx: RuntimeContext) -> EffectResult:
    policy_error = _ensure_io_policy(step, ctx, required_scope="ROLLBACK")
    if policy_error:
        return policy_error
    outcome_path = _resolve_output_path(ctx, step.args, key="outcome_path")
    if outcome_path is None or not outcome_path.exists():
        return _refuse(step, "IORollbackMissingOutcome", ["outcome missing"])
    outcome = json.loads(outcome_path.read_text(encoding="utf-8"))
    action = outcome.get("action")
    if action != "rollback":
        return _refuse(step, "IORollbackNotRequired", ["rollback not required"], {outcome_path.name: _digest_bytes(outcome_path.read_bytes())})
    record = {
        "ok": True,
        "outcome_digest": _digest_bytes(outcome_path.read_bytes()),
        "token_id": ctx.execution_token.token_id if ctx.execution_token else None,
        "note": "rollback recorded",
    }
    record_path = _resolve_output_path(
        ctx,
        step.args,
        key="record_path",
        default_name="rollback_record.json",
    )
    digests = {outcome_path.name: _digest_bytes(outcome_path.read_bytes())}
    if record_path:
        record_path.write_text(_canonical_json(record), encoding="utf-8")
        digests[record_path.name] = _digest_bytes(record_path.read_bytes())
    else:
        digests["rollback_record"] = _digest_bytes(_canonical_json(record).encode("utf-8"))
    return _ok(step, digests)


def _ensure_io_policy(step: EffectStep, ctx: RuntimeContext, required_scope: str) -> Optional[EffectResult]:
    token = ctx.execution_token
    if token is None or token.io_policy is None or not token.io_policy.get("io_allowed", False):
        return _refuse(step, "IOPermissionDenied", ["io not permitted"])
    allowed_scopes = {str(item).upper() for item in token.io_policy.get("io_scopes", []) if str(item).strip()}
    if required_scope.upper() not in allowed_scopes:
        return _refuse(step, "IOPermissionDenied", [f"missing scope: {required_scope}"])
    if required_scope.upper() in {"ORDER_SUBMIT", "ORDER_CANCEL"}:
        mode = str(token.io_policy.get("io_mode", "dry_run")).lower()
        if mode != "live":
            return _refuse(step, "IOModeNotAllowed", ["io_mode not live"])
    endpoint = str(step.args.get("endpoint", "")).strip()
    allowed_endpoints = {
        str(item) for item in token.io_policy.get("io_endpoints_allowed", []) if str(item).strip()
    }
    if endpoint and allowed_endpoints and endpoint not in allowed_endpoints:
        return _refuse(step, "EndpointNotAllowed", [f"endpoint not allowed: {endpoint}"])
    timeout_ms = _io_timeout_policy(token.io_policy)
    requested_timeout = _requested_timeout(step.args, timeout_ms)
    if requested_timeout > timeout_ms:
        return _refuse(step, "IOTimeout", [f"timeout_bucket=T{timeout_ms}ms"])
    return None


def _io_timeout_policy(io_policy: Optional[Dict[str, object]]) -> int:
    if not isinstance(io_policy, dict):
        return 2500
    try:
        return int(io_policy.get("io_timeout_ms", 2500))
    except (TypeError, ValueError):
        return 2500


def _requested_timeout(args: Dict[str, object], default_timeout: int) -> int:
    params = args.get("params", {})
    value = None
    if isinstance(params, dict):
        value = params.get("timeout_ms")
    if value is None:
        value = args.get("timeout_ms")
    try:
        return int(value) if value is not None else int(default_timeout)
    except (TypeError, ValueError):
        return int(default_timeout)


def _derive_nonce(policy: str, step_id: str, payload: Dict[str, object]) -> str:
    core = {
        "policy": policy,
        "step_id": step_id,
        "payload_hash": _digest_bytes(_canonical_json(payload).encode("utf-8")),
    }
    return _digest_bytes(_canonical_json(core).encode("utf-8"))


def _build_io_request(
    step: EffectStep,
    ctx: RuntimeContext,
    action: str,
    extra: Optional[Dict[str, object]] = None,
) -> Dict[str, object]:
    endpoint = str(step.args.get("endpoint", "")).strip()
    io_policy = ctx.execution_token.io_policy if ctx.execution_token else None
    io_timeout_ms = _io_timeout_policy(io_policy)
    requested_timeout = _requested_timeout(step.args, io_timeout_ms)
    payload = {
        "action": action,
        "endpoint": endpoint,
        "token_id": ctx.execution_token.token_id if ctx.execution_token else None,
        "params": _sanitize_payload(step.args.get("params", {})),
        "timeout_ms": requested_timeout,
        "io_mode": io_policy.get("io_mode", "dry_run") if isinstance(io_policy, dict) else "dry_run",
        "redaction_policy_id": io_policy.get("io_redaction_policy_id", "R1") if isinstance(io_policy, dict) else "R1",
    }
    if extra:
        payload.update(extra)
    nonce_policy = io_policy.get("io_nonce_policy", "HPL_DETERMINISTIC_NONCE_V1") if isinstance(io_policy, dict) else "HPL_DETERMINISTIC_NONCE_V1"
    payload["nonce_policy"] = nonce_policy
    payload["nonce"] = _derive_nonce(nonce_policy, step.step_id, payload)
    request_id = _request_id(_canonical_json(payload))
    payload["request_id"] = request_id
    return payload


def _emit_io_artifacts(
    step: EffectStep,
    ctx: RuntimeContext,
    request: Dict[str, object],
    response: Dict[str, object],
    event_type: str,
) -> EffectResult:
    request = _sanitize_payload(request)
    response = _sanitize_payload(response)
    request_path = _resolve_output_path(
        ctx,
        step.args,
        key="request_path",
        default_name=f"{step.step_id}_request.json",
    )
    response_path = _resolve_output_path(
        ctx,
        step.args,
        key="response_path",
        default_name=f"{step.step_id}_response.json",
    )
    event = {
        "event_type": event_type,
        "request_id": request["request_id"],
        "response_status": response.get("status"),
        "mock": True,
    }
    digests: Dict[str, str] = {}
    if request_path:
        request_path.write_text(_canonical_json(request), encoding="utf-8")
        digests[request_path.name] = _digest_bytes(request_path.read_bytes())
    else:
        digests["io_request"] = _digest_bytes(_canonical_json(request).encode("utf-8"))
    if response_path:
        response_path.write_text(_canonical_json(response), encoding="utf-8")
        digests[response_path.name] = _digest_bytes(response_path.read_bytes())
    else:
        digests["io_response"] = _digest_bytes(_canonical_json(response).encode("utf-8"))
    event_path = _resolve_output_path(
        ctx,
        step.args,
        key="event_path",
        default_name=f"{step.step_id}_event.json",
    )
    if event_path:
        event_path.write_text(_canonical_json(event), encoding="utf-8")
        digests[event_path.name] = _digest_bytes(event_path.read_bytes())
    else:
        digests["io_event"] = _digest_bytes(_canonical_json(event).encode("utf-8"))
    return _ok(step, digests)


def _emit_io_event(step: EffectStep, ctx: RuntimeContext, event: Dict[str, object]) -> EffectResult:
    event = _sanitize_payload(event)
    event_path = _resolve_output_path(
        ctx,
        step.args,
        key="event_path",
        default_name=f"{step.step_id}_event.json",
    )
    digests: Dict[str, str] = {}
    if event_path:
        event_path.write_text(_canonical_json(event), encoding="utf-8")
        digests[event_path.name] = _digest_bytes(event_path.read_bytes())
    else:
        digests["io_event"] = _digest_bytes(_canonical_json(event).encode("utf-8"))
    return _ok(step, digests)


def _request_id(payload: str) -> str:
    return _digest_bytes(payload.encode("utf-8"))


def _sanitize_payload(value: object) -> object:
    if isinstance(value, dict):
        return {key: _sanitize_payload(item) for key, item in value.items() if not _looks_like_secret_key(key)}
    if isinstance(value, list):
        return [_sanitize_payload(item) for item in value]
    if isinstance(value, str):
        if _looks_like_secret_value(value):
            return "REDACTED"
    return value


def _resolve_io_adapter(step: EffectStep, ctx: RuntimeContext) -> object:
    if not ctx.io_enabled:
        return None
    if os.getenv("HPL_IO_ENABLED") != "1":
        return _refuse(step, "IOGuardNotEnabled", ["HPL_IO_ENABLED not set"])
    try:
        return load_adapter()
    except Exception as exc:
        return _refuse(step, "IOAdapterUnavailable", [str(exc)])


def _looks_like_secret_key(key: str) -> bool:
    lowered = key.lower()
    return any(token in lowered for token in ("secret", "password", "api_key", "apikey", "token"))


def _looks_like_secret_value(value: str) -> bool:
    lowered = value.lower()
    if lowered.startswith("sk_live") or lowered.startswith("sk_test"):
        return True
    if value.startswith("ghp_"):
        return True
    if "bearer " in lowered:
        return True
    return False

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

    redaction_report = scan_artifacts([artifact.source for artifact in artifacts])
    report_path = _resolve_output_path(
        ctx,
        step.args,
        key="redaction_report",
        default_name="redaction_report.json",
    )
    report_payload = _canonical_json(redaction_report)
    redaction_digests: Dict[str, str] = {}
    if report_path:
        report_path.write_text(report_payload, encoding="utf-8")
        redaction_digests[report_path.name] = _digest_bytes(report_path.read_bytes())
        artifacts.append(bundle_module._artifact("redaction_report", report_path))
    else:
        redaction_digests["redaction_report"] = _digest_bytes(report_payload.encode("utf-8"))

    if not redaction_report.get("ok", False):
        return _refuse(
            step,
            "SecretDetectedInArtifact",
            redaction_report.get("errors", ["secrets detected"]),
            redaction_digests,
        )
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
    result_digests = {manifest_path.name: digest}
    result_digests.update(redaction_digests)
    return _ok(step, result_digests)


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


def _resolve_input_path(ctx: RuntimeContext, value: object) -> Optional[Path]:
    if value is None:
        return None
    path = Path(str(value))
    if path.is_absolute():
        return path
    candidate = ROOT / path
    if candidate.exists():
        return candidate
    if ctx.trace_sink is not None:
        trace_candidate = ctx.trace_sink / path
        if trace_candidate.exists():
            return trace_candidate
    return path


def _load_tool(name: str, path: Path):
    import sys

    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_json(data: object) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def _digest_bytes(data: bytes) -> str:
    import hashlib

    digest = hashlib.sha256(data).hexdigest()
    return f"sha256:{digest}"


def _round_price(value: float) -> float:
    return float(f"{value:.8f}")


def _round_delta(value: float) -> float:
    return float(f"{value:.8f}")


def _hash_to_unit(value: bytes) -> float:
    import hashlib

    digest = hashlib.sha256(value).hexdigest()
    as_int = int(digest, 16)
    max_int = (1 << (len(digest) * 4)) - 1
    return as_int / max_int if max_int else 0.0


def _seeded_float(seed: str, label: str) -> float:
    import hashlib

    digest = hashlib.sha256(f"{seed}:{label}".encode("utf-8")).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF


def _load_pde_state(path: Path) -> Dict[str, object]:
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        raise ValueError("state invalid json")
    if not isinstance(state, dict):
        raise ValueError("state must be an object")
    grid = state.get("grid", {})
    nx = int(grid.get("nx", 0))
    ny = int(grid.get("ny", 0))
    if nx <= 0 or ny <= 0:
        raise ValueError("grid dimensions invalid")
    field = state.get("field", [])
    if not isinstance(field, list) or len(field) != nx * ny:
        raise ValueError("field must be a list of length nx*ny")
    normalized_field = []
    for cell in field:
        if not isinstance(cell, dict):
            raise ValueError("field cell must be an object")
        normalized_field.append(
            {
                "u": float(cell.get("u", 0.0)),
                "v": float(cell.get("v", 0.0)),
            }
        )
    return {
        "grid": {
            "nx": nx,
            "ny": ny,
            "dx": float(grid.get("dx", 1.0)),
            "dy": float(grid.get("dy", 1.0)),
        },
        "field": normalized_field,
        "t": float(state.get("t", 0.0)),
        "dt": float(state.get("dt", 0.1)),
        "nu": float(state.get("nu", 0.01)),
        "metadata": dict(state.get("metadata", {}) or {}),
        "projection_gain": float(state.get("projection_gain", 0.1)),
        "divergence_residual": float(state.get("divergence_residual", 0.0)),
    }


def _with_state(state: Dict[str, object], **updates: object) -> Dict[str, object]:
    new_state = dict(state)
    for key, value in updates.items():
        new_state[key] = value
    return new_state


def _write_state_result(step: EffectStep, input_path: Path, state: Dict[str, object], out_path: Optional[Path]) -> EffectResult:
    payload = _canonical_json(state)
    digests = {input_path.name: _digest_bytes(input_path.read_bytes())}
    if out_path:
        out_path.write_text(payload, encoding="utf-8")
        digests[out_path.name] = _digest_bytes(out_path.read_bytes())
    else:
        digests["state"] = _digest_bytes(payload.encode("utf-8"))
    return _ok(step, digests)


def _load_policy(path: Optional[Path]) -> Dict[str, object]:
    if path is None:
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        raise ValueError("policy invalid json")


def _divergence(field: List[Dict[str, float]], nx: int, ny: int, dx: float, dy: float) -> List[float]:
    divergence = []
    for j in range(ny):
        for i in range(nx):
            idx = i + j * nx
            left = ((i - 1) % nx) + j * nx
            right = ((i + 1) % nx) + j * nx
            down = i + ((j - 1) % ny) * nx
            up = i + ((j + 1) % ny) * nx
            du_dx = (field[right]["u"] - field[left]["u"]) / (2.0 * dx)
            dv_dy = (field[up]["v"] - field[down]["v"]) / (2.0 * dy)
            divergence.append(du_dx + dv_dy)
    return divergence


def _energy(field: List[Dict[str, float]]) -> float:
    return sum(0.5 * (cell["u"] ** 2 + cell["v"] ** 2) for cell in field)


def _dissipation(field: List[Dict[str, float]], nx: int, ny: int, dx: float, dy: float, nu: float) -> float:
    grad_sum = 0.0
    for j in range(ny):
        for i in range(nx):
            idx = i + j * nx
            right = ((i + 1) % nx) + j * nx
            up = i + ((j + 1) % ny) * nx
            du_dx = (field[right]["u"] - field[idx]["u"]) / dx
            dv_dy = (field[up]["v"] - field[idx]["v"]) / dy
            grad_sum += du_dx ** 2 + dv_dy ** 2
    return nu * grad_sum


def _cfl(field: List[Dict[str, float]], dx: float, dy: float, dt: float) -> float:
    max_u = max(abs(cell["u"]) for cell in field) if field else 0.0
    max_v = max(abs(cell["v"]) for cell in field) if field else 0.0
    return (max_u * dt / dx) + (max_v * dt / dy)


def _exp_safe(value: float) -> float:
    import math

    return math.exp(value)


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
