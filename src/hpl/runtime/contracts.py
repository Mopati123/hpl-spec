"""Execution contracts for runtime gating."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple

from .context import RuntimeContext


@dataclass(frozen=True)
class ExecutionContract:
    allowed_steps: Set[str] = field(default_factory=set)
    require_epoch_verification: bool = False
    require_signature_verification: bool = False

    def preconditions(self, step: Dict[str, object], ctx: RuntimeContext) -> Tuple[bool, List[str]]:
        errors: List[str] = []
        step_id = str(step.get("operator_id", ""))
        if self.allowed_steps and step_id not in self.allowed_steps:
            errors.append(f"step not allowed: {step_id}")
        return not errors, errors

    def postconditions(self, step: Dict[str, object], ctx: RuntimeContext) -> Tuple[bool, List[str]]:
        return True, []
