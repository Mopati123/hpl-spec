from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass(frozen=True)
class EffectStep:
    step_id: str
    effect_type: str
    args: Dict[str, object] = field(default_factory=dict)
    requires: Dict[str, object] = field(default_factory=dict)
    cost_model: Dict[str, object] = field(default_factory=dict)
    expected_artifacts: Dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, object]:
        return {
            "step_id": self.step_id,
            "effect_type": self.effect_type,
            "args": dict(self.args),
            "requires": dict(self.requires),
            "cost_model": dict(self.cost_model),
            "expected_artifacts": dict(self.expected_artifacts),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "EffectStep":
        return cls(
            step_id=str(data.get("step_id", "")),
            effect_type=str(data.get("effect_type", "")),
            args=dict(data.get("args", {}) or {}),
            requires=dict(data.get("requires", {}) or {}),
            cost_model=dict(data.get("cost_model", {}) or {}),
            expected_artifacts=dict(data.get("expected_artifacts", {}) or {}),
        )


@dataclass(frozen=True)
class EffectResult:
    step_id: str
    effect_type: str
    ok: bool
    refusal_type: Optional[str]
    refusal_reasons: list[str]
    artifact_digests: Dict[str, str]

    def to_dict(self) -> Dict[str, object]:
        return {
            "step_id": self.step_id,
            "effect_type": self.effect_type,
            "ok": self.ok,
            "refusal_type": self.refusal_type,
            "refusal_reasons": list(self.refusal_reasons),
            "artifact_digests": dict(self.artifact_digests),
        }
