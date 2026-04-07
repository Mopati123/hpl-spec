from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable
from .token_tree import TokenScope, TokenTree, DerivedToken
from .consumption_witness import ConsumptionWitness

@dataclass
class BudgetState:
    sub_token_id: str
    total_steps: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0

@dataclass
class RevocationRecord:
    sub_token_id: str
    reason: str
    timestamp_iso: str

@dataclass
class ParentScheduler:
    """
    Manages a token tree, receives consumption witnesses from child agents,
    and issues revocations when budgets are exceeded.
    """
    token_tree: TokenTree
    on_revoke: Callable[[RevocationRecord], None] = field(default=lambda r: None)
    _budget_states: dict[str, BudgetState] = field(default_factory=dict, init=False)
    _revocation_log: list[RevocationRecord] = field(default_factory=list, init=False)

    def spawn_child(self, requested_scope: TokenScope) -> DerivedToken:
        """Mint a new child sub-token."""
        child = self.token_tree.mint_child(requested_scope)
        self._budget_states[child.token_id] = BudgetState(sub_token_id=child.token_id)
        return child

    def receive_witness(self, witness: ConsumptionWitness) -> bool:
        """
        Process a consumption witness from a child agent.
        Returns True if child is still active, False if revoked.
        """
        import datetime
        state = self._budget_states.get(witness.sub_token_id)
        if state is None:
            return False
        if not self.token_tree.is_active(witness.sub_token_id):
            return False

        state.total_steps += witness.steps_consumed
        state.total_input_tokens += witness.input_tokens_delta
        state.total_output_tokens += witness.output_tokens_delta

        # Find the child's scope
        child = next((c for c in self.token_tree.children if c.token_id == witness.sub_token_id), None)
        if child and state.total_steps > child.scope.budget_steps:
            record = RevocationRecord(
                sub_token_id=witness.sub_token_id,
                reason=f"Budget exceeded: {state.total_steps} steps > {child.scope.budget_steps} allowed",
                timestamp_iso=datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
            )
            self.token_tree.revoke(witness.sub_token_id)
            self._revocation_log.append(record)
            self.on_revoke(record)
            return False
        return True

    def get_revocation_log(self) -> list[RevocationRecord]:
        return list(self._revocation_log)

    def get_budget_summary(self) -> dict:
        return {
            tid: {"steps": s.total_steps, "input": s.total_input_tokens, "output": s.total_output_tokens}
            for tid, s in self._budget_states.items()
        }
