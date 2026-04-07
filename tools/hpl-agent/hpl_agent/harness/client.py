from __future__ import annotations
import os
import anthropic

class AnthropicClientFactory:
    @staticmethod
    def create(api_key: str | None = None) -> anthropic.Anthropic:
        key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        if not key:
            raise ValueError("ANTHROPIC_API_KEY not set. Export it or pass api_key explicitly.")
        return anthropic.Anthropic(api_key=key)
