from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import Any
from .budget import compute_budget, COMPRESS_THRESHOLD, HOT_MESSAGES, TokenBudget
from .compressor import CompressedState, ContextCompressor, SUMMARY_SYSTEM
from .store import ColdMemoryStore, Checkpoint
from pathlib import Path

CHECKPOINT_EVERY_N_TURNS = 5


@dataclass
class ContextManager:
    """
    Drop-in replacement for the naive ConversationManager.
    Manages all 3 layers: hot, warm, cold.

    Usage:
        ctx = ContextManager.create(session_id, store_dir, claude_client, model)
        messages = ctx.get_messages()           # call before each API turn
        ctx.record_turn(prompt, response_content)  # call after each turn
    """
    session_id: str
    compressor: ContextCompressor
    store: ColdMemoryStore
    messages: list[dict] = field(default_factory=list)
    warm_state: CompressedState = field(default_factory=CompressedState)
    turn_index: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    _last_budget: TokenBudget = field(default_factory=TokenBudget)

    @classmethod
    def create(
        cls,
        session_id: str,
        store_dir: Path = Path(".hpl_memory"),
        claude_client: Any = None,   # anthropic.Anthropic
        model: str = "claude-opus-4-6",
        system_prompt: str = "",
    ) -> "ContextManager":
        store = ColdMemoryStore(store_dir=store_dir)

        # Build summarizer callable if client provided
        summarizer = None
        if claude_client is not None:
            def summarizer(messages: list[dict]) -> str:
                resp = claude_client.messages.create(
                    model=model,
                    max_tokens=1000,
                    system=SUMMARY_SYSTEM,
                    messages=messages,
                )
                return resp.content[0].text

        compressor = ContextCompressor(claude_summarizer=summarizer)

        # Try to restore from cold storage
        checkpoint = store.load_latest_checkpoint(session_id)
        if checkpoint:
            warm_state = CompressedState.from_json(json.dumps(checkpoint.warm_state))
            messages = [warm_state.to_message_block(),
                        {"role": "assistant", "content": "Restored from checkpoint."}] + checkpoint.hot_messages
            return cls(
                session_id=session_id,
                compressor=compressor,
                store=store,
                messages=messages,
                warm_state=warm_state,
                turn_index=checkpoint.turn_index,
                total_input_tokens=checkpoint.input_tokens_at_checkpoint,
                total_output_tokens=checkpoint.output_tokens_at_checkpoint,
            )

        return cls(
            session_id=session_id,
            compressor=compressor,
            store=store,
        )

    def add_user_turn(self, content: str | list) -> None:
        if isinstance(content, str):
            self.messages.append({"role": "user", "content": content})
        else:
            self.messages.append({"role": "user", "content": content})

    def add_assistant_turn(self, content: list) -> None:
        self.messages.append({"role": "assistant", "content": content})
        self.turn_index += 1
        self._maybe_compress_and_checkpoint(system_prompt="")

    def get_messages(self, system_prompt: str = "") -> list[dict]:
        """Get messages, compressing first if over budget."""
        budget = compute_budget(system_prompt, self.messages)
        self._last_budget = budget
        if budget.needs_compression:
            self._compress(system_prompt)
        return list(self.messages)

    def update_usage(self, input_tokens: int, output_tokens: int) -> None:
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens

    def budget_status(self, system_prompt: str = "") -> TokenBudget:
        return compute_budget(system_prompt, self.messages)

    def _maybe_compress_and_checkpoint(self, system_prompt: str) -> None:
        budget = compute_budget(system_prompt, self.messages)
        if budget.needs_compression:
            self._compress(system_prompt)
        if self.turn_index % CHECKPOINT_EVERY_N_TURNS == 0 and self.turn_index > 0:
            self._checkpoint()

    def _compress(self, system_prompt: str) -> None:
        self.messages, self.warm_state = self.compressor.compress(
            self.messages, self.warm_state
        )

    def _checkpoint(self) -> None:
        hot = self.messages[-HOT_MESSAGES:] if len(self.messages) >= HOT_MESSAGES else self.messages
        checkpoint = ColdMemoryStore.make_checkpoint(
            session_id=self.session_id,
            turn_index=self.turn_index,
            warm_state=self.warm_state,
            hot_messages=hot,
            input_tokens=self.total_input_tokens,
            output_tokens=self.total_output_tokens,
        )
        self.store.save_checkpoint(checkpoint)

    def force_checkpoint(self) -> Path:
        """Manually trigger a checkpoint and return its path."""
        self._checkpoint()
        return self.store.store_dir / f"{self.session_id}.jsonl"
