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
        if self.allowed_steps and step_id not in self.allowed_steps:
            errors.append(f"step not allowed: {step_id}")
        required_backend = None
        if isinstance(step.get("requires"), dict):
            required_backend = step.get("requires", {}).get("backend")
        if required_backend is None:
            required_backend = step.get("required_backend") or self.required_backend
        if required_backend:
            token = ctx.execution_token
            if token is None:
                errors.append("execution token missing for backend requirement")
            elif str(required_backend).upper() not in token.allowed_backends:
                errors.append(f"backend not permitted: {str(required_backend).upper()}")
        return not errors, errors

    def postconditions(self, step: Dict[str, object], ctx: RuntimeContext) -> Tuple[bool, List[str]]:
        return True, []
