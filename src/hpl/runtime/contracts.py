"""Execution contracts for runtime gating."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from .context import RuntimeContext


@dataclass(frozen=True)
class ExecutionContract:
    allowed_steps: Set[str] = field(default_factory=set)
    require_epoch_verification: bool = False
    require_signature_verification: bool = False
    required_backend: Optional[str] = None

    def preconditions(self, step: Dict[str, object], ctx: RuntimeContext) -> Tuple[bool, List[str]]:
        errors: List[str] = []
        step_id = str(step.get("step_id") or step.get("operator_id") or "")
        effect_type = str(step.get("effect_type") or "")
        if self.allowed_steps and step_id not in self.allowed_steps:
            errors.append(f"step not allowed: {step_id}")
        required_backend = None
        if isinstance(step.get("requires"), dict):
            required_backend = step.get("requires", {}).get("backend")
        if required_backend is None:
            required_backend = step.get("required_backend") or self.required_backend
        token = ctx.execution_token
        requires = step.get("requires") if isinstance(step.get("requires"), dict) else {}
        if required_backend:
            if token is None:
                errors.append("execution token missing for backend requirement")
            elif str(required_backend).upper() not in token.allowed_backends:
                errors.append(f"backend not permitted: {str(required_backend).upper()}")
        required_operator_ids: List[str] = []
        if isinstance(requires, dict):
            operator_id = requires.get("operator_id")
            operator_ids = requires.get("operator_ids")
            if isinstance(operator_id, str) and operator_id.strip():
                required_operator_ids.append(operator_id.strip().upper())
            if isinstance(operator_ids, list):
                required_operator_ids.extend(
                    str(item).strip().upper()
                    for item in operator_ids
                    if str(item).strip()
                )
        if required_operator_ids:
            if token is None or token.operator_policy is None:
                errors.append("OperatorPermissionDenied")
            else:
                allowlist = {
                    str(item).upper()
                    for item in token.operator_policy.get("operator_allowlist", [])
                    if str(item).strip()
                }
                for operator_name in sorted(set(required_operator_ids)):
                    if operator_name not in allowlist:
                        errors.append(f"OperatorPermissionDenied:{operator_name}")
        if token and token.measurement_modes_allowed:
            allowed_modes = {mode.upper() for mode in token.measurement_modes_allowed}
            if effect_type and effect_type.upper().startswith("MEASURE"):
                if effect_type.upper() not in allowed_modes:
                    errors.append(f"measurement mode not permitted: {effect_type}")
            if effect_type.upper() in {"COMPUTE_DELTA_S", "DELTA_S_GATE"}:
                if effect_type.upper() not in allowed_modes:
                    errors.append(f"measurement mode not permitted: {effect_type}")
        io_scope = requires.get("io_scope") if isinstance(requires, dict) else None
        io_scopes = requires.get("io_scopes") if isinstance(requires, dict) else None
        io_endpoint = requires.get("io_endpoint") if isinstance(requires, dict) else None
        net_cap = requires.get("net_cap") if isinstance(requires, dict) else None
        net_caps = requires.get("net_caps") if isinstance(requires, dict) else None
        net_endpoint = requires.get("net_endpoint") if isinstance(requires, dict) else None
        required_scopes: List[str] = []
        if isinstance(io_scope, str):
            required_scopes.append(io_scope)
        if isinstance(io_scopes, list):
            required_scopes.extend([str(item) for item in io_scopes])
        if required_scopes or io_endpoint:
            if token is None or token.io_policy is None or not token.io_policy.get("io_allowed", False):
                errors.append("IOPermissionDenied")
            else:
                allowed_scopes = {
                    str(item).upper()
                    for item in token.io_policy.get("io_scopes", [])
                    if str(item).strip()
                }
                for scope in required_scopes:
                    if scope.upper() not in allowed_scopes:
                        errors.append(f"IOPermissionDenied:{scope}")
                allowed_endpoints = {
                    str(item)
                    for item in token.io_policy.get("io_endpoints_allowed", [])
                    if str(item).strip()
                }
                if io_endpoint and allowed_endpoints and str(io_endpoint) not in allowed_endpoints:
                    errors.append("EndpointNotAllowed")
        required_net_caps: List[str] = []
        if isinstance(net_cap, str):
            required_net_caps.append(net_cap)
        if isinstance(net_caps, list):
            required_net_caps.extend([str(item) for item in net_caps])
        if required_net_caps or net_endpoint:
            if token is None or token.net_policy is None:
                errors.append("NetPermissionDenied")
            else:
                allowed_caps = {
                    str(item).upper()
                    for item in token.net_policy.get("net_caps", [])
                    if str(item).strip()
                }
                for cap in required_net_caps:
                    if cap.upper() not in allowed_caps:
                        errors.append(f"NetPermissionDenied:{cap}")
                allowed_endpoints = {
                    str(item)
                    for item in token.net_policy.get("net_endpoints_allowlist", [])
                    if str(item).strip()
                }
                if net_endpoint and allowed_endpoints and str(net_endpoint) not in allowed_endpoints:
                    errors.append("NetEndpointNotAllowed")
        return not errors, errors

    def postconditions(self, step: Dict[str, object], ctx: RuntimeContext) -> Tuple[bool, List[str]]:
        return True, []
