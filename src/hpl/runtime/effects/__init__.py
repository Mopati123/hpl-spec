from .effect_types import EffectType
from .effect_step import EffectStep, EffectResult
from .handler_registry import get_handler, register_handler
from .handlers import handle_emit_artifact, handle_noop


register_handler(EffectType.NOOP, handle_noop)
register_handler(EffectType.EMIT_ARTIFACT, handle_emit_artifact)
