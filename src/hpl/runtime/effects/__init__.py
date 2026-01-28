from .effect_types import EffectType
from .effect_step import EffectStep, EffectResult
from .handler_registry import get_handler, register_handler
from .handlers import (
    handle_assert_contract,
    handle_bundle_evidence,
    handle_emit_artifact,
    handle_invert_constraints,
    handle_lower_backend_ir,
    handle_lower_qasm,
    handle_noop,
    handle_verify_epoch,
    handle_verify_signature,
)


register_handler(EffectType.NOOP, handle_noop)
register_handler(EffectType.EMIT_ARTIFACT, handle_emit_artifact)
register_handler(EffectType.ASSERT_CONTRACT, handle_assert_contract)
register_handler(EffectType.VERIFY_EPOCH, handle_verify_epoch)
register_handler(EffectType.VERIFY_SIGNATURE, handle_verify_signature)
register_handler(EffectType.LOWER_BACKEND_IR, handle_lower_backend_ir)
register_handler(EffectType.LOWER_QASM, handle_lower_qasm)
register_handler(EffectType.BUNDLE_EVIDENCE, handle_bundle_evidence)
register_handler(EffectType.INVERT_CONSTRAINTS, handle_invert_constraints)
