from .effect_types import EffectType
from .effect_step import EffectStep, EffectResult
from .handler_registry import get_handler, register_handler
from .handlers import (
    handle_assert_contract,
    handle_bundle_evidence,
    handle_check_repo_state,
    handle_compute_delta_s,
    handle_evaluate_agent_proposal,
    handle_ingest_market_fixture,
    handle_compute_signal,
    handle_simulate_order,
    handle_update_risk_envelope,
    handle_emit_trade_report,
    handle_sim_market_model_load,
    handle_sim_regime_shift_step,
    handle_sim_latency_apply,
    handle_sim_partial_fill_model,
    handle_sim_order_lifecycle,
    handle_sim_emit_trade_ledger,
    handle_ns_evolve_linear,
    handle_ns_apply_duhamel,
    handle_ns_project_leray,
    handle_ns_pressure_recover,
    handle_ns_measure_observables,
    handle_ns_check_barrier,
    handle_ns_emit_state,
    handle_emit_artifact,
    handle_invert_constraints,
    handle_lower_backend_ir,
    handle_lower_qasm,
    handle_noop,
    handle_measure_condition,
    handle_delta_s_gate,
    handle_select_measurement_track,
    handle_sign_bundle,
    handle_validate_coupling_topology,
    handle_validate_quantum_semantics,
    handle_validate_registries,
    handle_verify_bundle,
    handle_verify_epoch,
    handle_verify_signature,
)


register_handler(EffectType.NOOP, handle_noop)
register_handler(EffectType.EMIT_ARTIFACT, handle_emit_artifact)
register_handler(EffectType.ASSERT_CONTRACT, handle_assert_contract)
register_handler(EffectType.VERIFY_EPOCH, handle_verify_epoch)
register_handler(EffectType.VERIFY_SIGNATURE, handle_verify_signature)
register_handler(EffectType.SELECT_MEASUREMENT_TRACK, handle_select_measurement_track)
register_handler(EffectType.MEASURE_CONDITION, handle_measure_condition)
register_handler(EffectType.COMPUTE_DELTA_S, handle_compute_delta_s)
register_handler(EffectType.DELTA_S_GATE, handle_delta_s_gate)
register_handler(EffectType.CHECK_REPO_STATE, handle_check_repo_state)
register_handler(EffectType.VALIDATE_REGISTRIES, handle_validate_registries)
register_handler(EffectType.VALIDATE_COUPLING_TOPOLOGY, handle_validate_coupling_topology)
register_handler(EffectType.VALIDATE_QUANTUM_SEMANTICS, handle_validate_quantum_semantics)
register_handler(EffectType.EVALUATE_AGENT_PROPOSAL, handle_evaluate_agent_proposal)
register_handler(EffectType.INGEST_MARKET_FIXTURE, handle_ingest_market_fixture)
register_handler(EffectType.COMPUTE_SIGNAL, handle_compute_signal)
register_handler(EffectType.SIMULATE_ORDER, handle_simulate_order)
register_handler(EffectType.UPDATE_RISK_ENVELOPE, handle_update_risk_envelope)
register_handler(EffectType.EMIT_TRADE_REPORT, handle_emit_trade_report)
register_handler(EffectType.SIM_MARKET_MODEL_LOAD, handle_sim_market_model_load)
register_handler(EffectType.SIM_REGIME_SHIFT_STEP, handle_sim_regime_shift_step)
register_handler(EffectType.SIM_LATENCY_APPLY, handle_sim_latency_apply)
register_handler(EffectType.SIM_PARTIAL_FILL_MODEL, handle_sim_partial_fill_model)
register_handler(EffectType.SIM_ORDER_LIFECYCLE, handle_sim_order_lifecycle)
register_handler(EffectType.SIM_EMIT_TRADE_LEDGER, handle_sim_emit_trade_ledger)
register_handler(EffectType.NS_EVOLVE_LINEAR, handle_ns_evolve_linear)
register_handler(EffectType.NS_APPLY_DUHAMEL, handle_ns_apply_duhamel)
register_handler(EffectType.NS_PROJECT_LERAY, handle_ns_project_leray)
register_handler(EffectType.NS_PRESSURE_RECOVER, handle_ns_pressure_recover)
register_handler(EffectType.NS_MEASURE_OBSERVABLES, handle_ns_measure_observables)
register_handler(EffectType.NS_CHECK_BARRIER, handle_ns_check_barrier)
register_handler(EffectType.NS_EMIT_STATE, handle_ns_emit_state)
register_handler(EffectType.SIGN_BUNDLE, handle_sign_bundle)
register_handler(EffectType.VERIFY_BUNDLE, handle_verify_bundle)
register_handler(EffectType.LOWER_BACKEND_IR, handle_lower_backend_ir)
register_handler(EffectType.LOWER_QASM, handle_lower_qasm)
register_handler(EffectType.BUNDLE_EVIDENCE, handle_bundle_evidence)
register_handler(EffectType.INVERT_CONSTRAINTS, handle_invert_constraints)
