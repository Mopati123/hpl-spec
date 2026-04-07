from __future__ import annotations
import json
from dataclasses import dataclass

# Model context limits
MAX_CTX_TOKENS = 200_000
RESERVED_OUTPUT_TOKENS = 8_000
SAFETY_MARGIN_TOKENS = 5_000
AVAILABLE_INPUT_TOKENS = MAX_CTX_TOKENS - RESERVED_OUTPUT_TOKENS - SAFETY_MARGIN_TOKENS  # 187_000

HOT_MESSAGES = 6       # Always keep last N messages verbatim
WARM_SUMMARY_TARGET = 800   # Target tokens for warm summary
COMPRESS_THRESHOLD = 0.80   # Trigger compression at 80% of available


@dataclass
class TokenBudget:
    system_tokens: int = 0
    history_tokens: int = 0
    query_tokens: int = 0

    @property
    def total(self) -> int:
        return self.system_tokens + self.history_tokens + self.query_tokens

    @property
    def available_remaining(self) -> int:
        return AVAILABLE_INPUT_TOKENS - self.total

    @property
    def utilization(self) -> float:
        return self.total / AVAILABLE_INPUT_TOKENS

    @property
    def needs_compression(self) -> bool:
        return self.utilization > COMPRESS_THRESHOLD

    def __str__(self) -> str:
        return (f"TokenBudget(total={self.total:,} / {AVAILABLE_INPUT_TOKENS:,} "
                f"[{self.utilization:.1%}] remaining={self.available_remaining:,})")


def estimate_tokens(text: str) -> int:
    """Approximate token count: ~4 chars per token for English text."""
    return max(1, len(text) // 4)


def estimate_messages_tokens(messages: list[dict]) -> int:
    """Estimate token count for a list of Anthropic API messages."""
    total = 0
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            total += estimate_tokens(content) + 4  # role overhead
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    text = block.get("text", "") or json.dumps(block)
                    total += estimate_tokens(text) + 2
    return total


def compute_budget(system_prompt: str, messages: list[dict], current_query: str = "") -> TokenBudget:
    return TokenBudget(
        system_tokens=estimate_tokens(system_prompt),
        history_tokens=estimate_messages_tokens(messages),
        query_tokens=estimate_tokens(current_query),
    )
