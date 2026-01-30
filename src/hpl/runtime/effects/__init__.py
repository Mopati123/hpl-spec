from .effect_types import EffectType
from .effect_step import EffectStep, EffectResult
from .handler_registry import get_handler, register_handler
from .handlers import (
    handle_assert_contract,
    handle_bundle_evidence,
    handle_check_repo_state,
    handle_evaluate_agent_proposal,
    handle_ingest_market_fixture,
    handle_compute_signal,
    handle_simulate_order,
    handle_update_risk_envelope,
    handle_emit_trade_report,
    handle_emit_artifact,
    handle_invert_constraints,
    handle_lower_backend_ir,
    handle_lower_qasm,
    handle_noop,
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
register_handler(EffectType.SIGN_BUNDLE, handle_sign_bundle)
register_handler(EffectType.VERIFY_BUNDLE, handle_verify_bundle)
register_handler(EffectType.LOWER_BACKEND_IR, handle_lower_backend_ir)
register_handler(EffectType.LOWER_QASM, handle_lower_qasm)
register_handler(EffectType.BUNDLE_EVIDENCE, handle_bundle_evidence)
register_handler(EffectType.INVERT_CONSTRAINTS, handle_invert_constraints)
