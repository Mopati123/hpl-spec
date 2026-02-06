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


def _normalize_modes(modes: List[str]) -> List[str]:
    normalized = sorted({str(item).upper() for item in modes if str(item).strip()})
    return normalized


def _normalize_io_policy(io_policy: Optional[Dict[str, object]]) -> Optional[Dict[str, object]]:
    if not isinstance(io_policy, dict):
        return None
    io_allowed = bool(io_policy.get("io_allowed", False))
    io_scopes = _normalize_modes(io_policy.get("io_scopes", []) if isinstance(io_policy.get("io_scopes"), list) else [])
    endpoints = io_policy.get("io_endpoints_allowed", []) if isinstance(io_policy.get("io_endpoints_allowed"), list) else []
    io_endpoints_allowed = sorted({str(item).strip() for item in endpoints if str(item).strip()})
    io_budget_calls = int(io_policy.get("io_budget_calls")) if "io_budget_calls" in io_policy else None
    io_requires_reconciliation = bool(io_policy.get("io_requires_reconciliation", True))
    io_requires_delta_s = bool(io_policy.get("io_requires_delta_s", False))
    normalized: Dict[str, object] = {
        "io_allowed": io_allowed,
        "io_scopes": io_scopes,
        "io_endpoints_allowed": io_endpoints_allowed,
        "io_requires_reconciliation": io_requires_reconciliation,
        "io_requires_delta_s": io_requires_delta_s,
    }
    if io_budget_calls is not None:
        normalized["io_budget_calls"] = io_budget_calls
    return normalized


@dataclass(frozen=True)
class ExecutionToken:
    token_id: str
    allowed_backends: List[str]
    preferred_backend: Optional[str]
    budget_steps: int
    determinism_mode: str
    io_policy: Optional[Dict[str, object]] = None
    delta_s_policy: Optional[Dict[str, object]] = None
    delta_s_budget: int = 0
    measurement_modes_allowed: Optional[List[str]] = None
    collapse_requires_delta_s: bool = False
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, object]:
        data: Dict[str, object] = {
            "token_id": self.token_id,
            "allowed_backends": list(self.allowed_backends),
            "preferred_backend": self.preferred_backend,
            "budget_steps": self.budget_steps,
            "determinism_mode": self.determinism_mode,
        }
        if self.io_policy is not None:
            data["io_policy"] = dict(self.io_policy)
        if self.delta_s_policy is not None:
            data["delta_s_policy"] = dict(self.delta_s_policy)
        if self.delta_s_budget:
            data["delta_s_budget"] = self.delta_s_budget
        if self.measurement_modes_allowed is not None:
            data["measurement_modes_allowed"] = list(self.measurement_modes_allowed)
        if self.collapse_requires_delta_s:
            data["collapse_requires_delta_s"] = self.collapse_requires_delta_s
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
        io_policy: Optional[Dict[str, object]] = None,
        delta_s_policy: Optional[Dict[str, object]] = None,
        delta_s_budget: int = 0,
        measurement_modes_allowed: Optional[List[str]] = None,
        collapse_requires_delta_s: bool = False,
        notes: Optional[str] = None,
    ) -> "ExecutionToken":
        allowed = _normalize_backends(allowed_backends or DEFAULT_BACKENDS)
        preferred = preferred_backend.upper() if preferred_backend else None
        modes = _normalize_modes(measurement_modes_allowed or [])
        normalized_io_policy = _normalize_io_policy(io_policy)
        core = {
            "allowed_backends": allowed,
            "preferred_backend": preferred,
            "budget_steps": int(budget_steps),
            "determinism_mode": determinism_mode,
            "io_policy": normalized_io_policy,
            "delta_s_policy": delta_s_policy or {},
            "delta_s_budget": int(delta_s_budget),
            "measurement_modes_allowed": modes,
            "collapse_requires_delta_s": bool(collapse_requires_delta_s),
        }
        token_id = _digest_text(_canonical_json(core))
        return cls(
            token_id=token_id,
            allowed_backends=allowed,
            preferred_backend=preferred,
            budget_steps=int(budget_steps),
            determinism_mode=determinism_mode,
            io_policy=normalized_io_policy,
            delta_s_policy=dict(delta_s_policy) if isinstance(delta_s_policy, dict) else None,
            delta_s_budget=int(delta_s_budget),
            measurement_modes_allowed=modes if modes else None,
            collapse_requires_delta_s=bool(collapse_requires_delta_s),
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
        io_policy = _normalize_io_policy(data.get("io_policy"))
        delta_s_policy = data.get("delta_s_policy")
        if not isinstance(delta_s_policy, dict):
            delta_s_policy = None
        delta_s_budget = int(data.get("delta_s_budget", 0))
        measurement_modes_allowed = data.get("measurement_modes_allowed", [])
        if not isinstance(measurement_modes_allowed, list):
            measurement_modes_allowed = []
        collapse_requires_delta_s = bool(data.get("collapse_requires_delta_s", False))
        notes = data.get("notes") if "notes" in data else None
        token_id = str(data.get("token_id", ""))
        if not token_id:
            return cls.build(
                allowed_backends=list(allowed),
                preferred_backend=str(preferred) if preferred else None,
                budget_steps=budget_steps,
                determinism_mode=determinism_mode,
                io_policy=io_policy,
                delta_s_policy=delta_s_policy if isinstance(delta_s_policy, dict) else None,
                delta_s_budget=delta_s_budget,
                measurement_modes_allowed=list(measurement_modes_allowed),
                collapse_requires_delta_s=collapse_requires_delta_s,
                notes=notes if isinstance(notes, str) else None,
            )
        return cls(
            token_id=token_id,
            allowed_backends=_normalize_backends(list(allowed)),
            preferred_backend=str(preferred).upper() if preferred else None,
            budget_steps=budget_steps,
            determinism_mode=determinism_mode,
            io_policy=io_policy,
            delta_s_policy=dict(delta_s_policy) if isinstance(delta_s_policy, dict) else None,
            delta_s_budget=delta_s_budget,
            measurement_modes_allowed=_normalize_modes(list(measurement_modes_allowed)) if measurement_modes_allowed else None,
            collapse_requires_delta_s=collapse_requires_delta_s,
            notes=notes if isinstance(notes, str) else None,
        )
