from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, Optional

from ..context import RuntimeContext
from .effect_step import EffectResult, EffectStep


RECONCILIATION_OPERATORS = (
    "reconcile_trade_effect",
    "reconcile_portfolio_state",
)


def handle_sim_reconcile_trade(step: EffectStep, ctx: RuntimeContext) -> EffectResult:
    paths = {
        "signal": _resolve_path(ctx, step.args.get("signal_path")),
        "shadow_fill": _resolve_path(ctx, step.args.get("shadow_fill_path")),
        "risk_envelope": _resolve_path(ctx, step.args.get("risk_envelope_path")),
        "shadow_trade_ledger": _resolve_path(ctx, step.args.get("ledger_path")),
        "trade_report": _resolve_path(ctx, step.args.get("report_path")),
    }
    missing = [name for name, path in paths.items() if path is None or not path.exists()]
    if missing:
        return _refuse(
            step,
            "ShadowReconciliationInputsMissing",
            [f"missing reconciliation input: {name}" for name in missing],
            {},
        )

    payloads: Dict[str, Dict[str, object]] = {}
    digests: Dict[str, str] = {}
    reasons: list[str] = []

    for name, path in paths.items():
        assert path is not None
        raw = path.read_bytes()
        digests[path.name] = _digest_bytes(raw)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            reasons.append(f"{name} is not valid utf-8 json")
            continue
        if not isinstance(payload, dict):
            reasons.append(f"{name} must be a json object")
            continue
        payloads[name] = payload
        canonical = _canonical_json(payload).encode("utf-8")
        if raw != canonical:
            reasons.append(f"{name} bytes are not canonical json")

    if reasons:
        witness = _build_witness(payloads, paths, digests, reasons)
        witness_digest = _write_witness(ctx, step, witness)
        if witness_digest is not None:
            digests[witness_digest[0]] = witness_digest[1]
        return _refuse(step, "ShadowReconciliationArtifactInvalid", reasons, digests)

    signal = payloads["signal"]
    fill = payloads["shadow_fill"]
    risk = payloads["risk_envelope"]
    ledger = payloads["shadow_trade_ledger"]
    report = payloads["trade_report"]

    expected_ledger = {
        "action": signal.get("action"),
        "executed": fill.get("executed"),
        "fill_fraction": fill.get("fill_fraction"),
        "filled_size": fill.get("filled_size"),
        "fill_price": fill.get("fill_price"),
        "equity": risk.get("equity"),
        "drawdown": risk.get("drawdown"),
        "pnl": risk.get("pnl"),
    }
    expected_report = {
        "symbol": report.get("symbol"),
        "action": signal.get("action"),
        "executed": fill.get("executed"),
        "fill_price": fill.get("fill_price"),
        "fill_fraction": fill.get("fill_fraction"),
        "equity": risk.get("equity"),
        "drawdown": risk.get("drawdown"),
        "max_drawdown": risk.get("max_drawdown"),
        "pnl": risk.get("pnl"),
    }

    comparisons = {
        "ledger_matches_derived_state": ledger == expected_ledger,
        "report_matches_derived_state": report == expected_report,
        "ledger_report_action": ledger.get("action") == report.get("action"),
        "ledger_report_executed": ledger.get("executed") == report.get("executed"),
        "ledger_report_fill_fraction": ledger.get("fill_fraction") == report.get("fill_fraction"),
        "ledger_report_fill_price": ledger.get("fill_price") == report.get("fill_price"),
        "ledger_report_equity": ledger.get("equity") == report.get("equity"),
        "ledger_report_drawdown": ledger.get("drawdown") == report.get("drawdown"),
        "ledger_report_pnl": ledger.get("pnl") == report.get("pnl"),
    }
    reasons = [name for name, ok in comparisons.items() if not ok]

    witness = {
        "schema_version": "hpl.shadow_reconciliation.v1",
        "ok": not reasons,
        "operators": list(RECONCILIATION_OPERATORS),
        "comparisons": comparisons,
        "source_digests": {
            name: digests[path.name]
            for name, path in paths.items()
            if path is not None
        },
        "reasons": reasons,
    }
    witness_digest = _write_witness(ctx, step, witness)
    if witness_digest is not None:
        digests[witness_digest[0]] = witness_digest[1]

    if reasons:
        return _refuse(step, "ShadowReconciliationMismatch", reasons, digests)
    return _ok(step, digests)


def _build_witness(
    payloads: Dict[str, Dict[str, object]],
    paths: Dict[str, Optional[Path]],
    digests: Dict[str, str],
    reasons: list[str],
) -> Dict[str, object]:
    return {
        "schema_version": "hpl.shadow_reconciliation.v1",
        "ok": False,
        "operators": list(RECONCILIATION_OPERATORS),
        "comparisons": {},
        "source_digests": {
            name: digests[path.name]
            for name, path in paths.items()
            if path is not None and path.name in digests
        },
        "parsed_inputs": sorted(payloads),
        "reasons": list(reasons),
    }


def _write_witness(
    ctx: RuntimeContext,
    step: EffectStep,
    witness: Dict[str, object],
) -> Optional[tuple[str, str]]:
    out_path = _resolve_path(
        ctx,
        step.args.get("out_path", "shadow_reconciliation.json"),
        for_output=True,
    )
    if out_path is None:
        return None
    out_path.write_text(_canonical_json(witness), encoding="utf-8")
    return out_path.name, _digest_bytes(out_path.read_bytes())


def _resolve_path(
    ctx: RuntimeContext,
    value: object,
    *,
    for_output: bool = False,
) -> Optional[Path]:
    if value is None:
        return None
    path = Path(str(value))
    if path.is_absolute():
        return path
    if ctx.trace_sink is not None:
        trace_path = ctx.trace_sink / path
        if for_output or trace_path.exists():
            return trace_path
    return path


def _canonical_json(data: object) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def _digest_bytes(data: bytes) -> str:
    return f"sha256:{hashlib.sha256(data).hexdigest()}"


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
    reasons: list[str],
    digests: Dict[str, str],
) -> EffectResult:
    return EffectResult(
        step_id=step.step_id,
        effect_type=step.effect_type,
        ok=False,
        refusal_type=refusal_type,
        refusal_reasons=list(reasons),
        artifact_digests=digests,
    )
