from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable
from .token_tree import DerivedToken
from .consumption_witness import ConsumptionWitness

@dataclass
class ChildAgentSession:
    """
    A child agent session governed by a DerivedToken.
    Emits ConsumptionWitnesses back to the ParentScheduler after each turn.
    """
    sub_token: DerivedToken
    engine: Any  # RealQueryEngine
    report_witness: Callable[[ConsumptionWitness], bool]  # parent's receive_witness
    signer: Any  # Ed25519Signer
    _steps_this_session: int = field(default=0, init=False)
    _active: bool = field(default=True, init=False)

    def run_turn(self, prompt: str, tool_definitions: list[dict]) -> str | None:
        """
        Run one turn. Returns response text, or None if token was revoked.
        Emits a signed ConsumptionWitness to parent after each turn.
        """
        if not self._active:
            return None

        # Filter tools to only those allowed by sub-token scope
        allowed = set(self.sub_token.scope.allow_tool_names)
        if allowed:
            tool_definitions = [t for t in tool_definitions if t.get("name") in allowed]

        result = self.engine.submit_message(
            prompt=prompt,
            tool_definitions=tool_definitions,
        )
        self._steps_this_session += len(result.tool_calls_made) + 1

        witness = ConsumptionWitness.create(
            session_id=self.engine.session.session_id,
            sub_token_id=self.sub_token.token_id,
            steps=self._steps_this_session,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
        ).sign(self.signer)

        still_active = self.report_witness(witness)
        if not still_active:
            self._active = False
            return f"[REVOKED by parent scheduler after turn] {result.output}"

        return result.output

    @property
    def is_active(self) -> bool:
        return self._active
