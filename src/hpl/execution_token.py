from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Dict, List, Optional


DEFAULT_BACKENDS = ["PYTHON", "CLASSICAL", "QASM"]


def _canonical_json(data: object) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def _digest_text(value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _normalize_backends(backends: List[str]) -> List[str]:
    normalized = sorted({str(item).upper() for item in backends if str(item).strip()})
    return normalized


@dataclass(frozen=True)
class ExecutionToken:
    token_id: str
    allowed_backends: List[str]
    preferred_backend: Optional[str]
    budget_steps: int
    determinism_mode: str
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, object]:
        data: Dict[str, object] = {
            "token_id": self.token_id,
            "allowed_backends": list(self.allowed_backends),
            "preferred_backend": self.preferred_backend,
            "budget_steps": self.budget_steps,
            "determinism_mode": self.determinism_mode,
        }
        if self.notes is not None:
            data["notes"] = self.notes
        return data

    @classmethod
    def build(
        cls,
        allowed_backends: Optional[List[str]] = None,
        preferred_backend: Optional[str] = None,
        budget_steps: int = 100,
        determinism_mode: str = "deterministic",
        notes: Optional[str] = None,
    ) -> "ExecutionToken":
        allowed = _normalize_backends(allowed_backends or DEFAULT_BACKENDS)
        preferred = preferred_backend.upper() if preferred_backend else None
        core = {
            "allowed_backends": allowed,
            "preferred_backend": preferred,
            "budget_steps": int(budget_steps),
            "determinism_mode": determinism_mode,
        }
        token_id = _digest_text(_canonical_json(core))
        return cls(
            token_id=token_id,
            allowed_backends=allowed,
            preferred_backend=preferred,
            budget_steps=int(budget_steps),
            determinism_mode=determinism_mode,
            notes=notes,
        )

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "ExecutionToken":
        allowed = data.get("allowed_backends", [])
        if not isinstance(allowed, list):
            allowed = []
        preferred = data.get("preferred_backend")
        budget_steps = int(data.get("budget_steps", 100))
        determinism_mode = str(data.get("determinism_mode", "deterministic"))
        notes = data.get("notes") if "notes" in data else None
        token_id = str(data.get("token_id", ""))
        if not token_id:
            return cls.build(
                allowed_backends=list(allowed),
                preferred_backend=str(preferred) if preferred else None,
                budget_steps=budget_steps,
                determinism_mode=determinism_mode,
                notes=notes if isinstance(notes, str) else None,
            )
        return cls(
            token_id=token_id,
            allowed_backends=_normalize_backends(list(allowed)),
            preferred_backend=str(preferred).upper() if preferred else None,
            budget_steps=budget_steps,
            determinism_mode=determinism_mode,
            notes=notes if isinstance(notes, str) else None,
        )
