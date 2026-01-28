from __future__ import annotations

from typing import Callable, Dict

from .effect_step import EffectResult, EffectStep


Handler = Callable[[EffectStep], EffectResult]


_REGISTRY: Dict[str, Handler] = {}


def register_handler(effect_type: str, handler: Handler) -> None:
    _REGISTRY[effect_type] = handler


def get_handler(effect_type: str) -> Handler:
    if effect_type in _REGISTRY:
        return _REGISTRY[effect_type]
    return _REGISTRY["NOOP"]
