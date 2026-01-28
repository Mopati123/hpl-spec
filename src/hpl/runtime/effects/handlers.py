from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from .effect_step import EffectResult, EffectStep
from .effect_types import EffectType


def handle_noop(step: EffectStep) -> EffectResult:
    return EffectResult(
        step_id=step.step_id,
        effect_type=step.effect_type,
        ok=True,
        refusal_type=None,
        refusal_reasons=[],
        artifact_digests={},
    )


def handle_emit_artifact(step: EffectStep) -> EffectResult:
    args = step.args
    target = args.get("path")
    if not target:
        return EffectResult(
            step_id=step.step_id,
            effect_type=step.effect_type,
            ok=False,
            refusal_type="MissingArtifactPath",
            refusal_reasons=["missing artifact path"],
            artifact_digests={},
        )
    path = Path(str(target))
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
    return EffectResult(
        step_id=step.step_id,
        effect_type=step.effect_type,
        ok=True,
        refusal_type=None,
        refusal_reasons=[],
        artifact_digests={path.name: digest},
    )


def _digest_bytes(data: bytes) -> str:
    import hashlib

    digest = hashlib.sha256(data).hexdigest()
    return f"sha256:{digest}"
