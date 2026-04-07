from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Generator
from ..harness.config import HarnessConfig
from ..harness.client import AnthropicClientFactory
from ..harness.engine import RealQueryEngine, TurnResult
from ..harness.session import PersistentSession
from ..tools.registry import ALL_TOOL_SCHEMAS, ALL_TOOL_EXECUTORS
from .system_prompt import build_system_prompt
from .conversation import ConversationManager

@dataclass
class HplAssistant:
    config: HarnessConfig
    engine: RealQueryEngine
    conversation: ConversationManager

    @classmethod
    def create(cls, config: HarnessConfig | None = None) -> "HplAssistant":
        cfg = config or HarnessConfig.from_env()
        client = AnthropicClientFactory.create(cfg.api_key or None)
        session = PersistentSession()
        system = build_system_prompt()

        def tool_executor(name: str, inp: dict) -> str:
            fn = ALL_TOOL_EXECUTORS.get(name)
            if fn is None:
                return f"Unknown tool: {name}"
            return fn(inp)

        engine = RealQueryEngine(
            config=cfg,
            client=client,
            session=session,
            system_prompt=system,
            tool_executor=tool_executor,
        )
        conversation = ConversationManager(session=session)
        return cls(config=cfg, engine=engine, conversation=conversation)

    def ask(self, prompt: str) -> str:
        result = self.engine.submit_message(
            prompt=prompt,
            tool_definitions=ALL_TOOL_SCHEMAS,
        )
        return result.output

    def save_session(self) -> Path:
        return self.engine.session.save(self.config.session_dir)
