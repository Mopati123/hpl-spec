from __future__ import annotations
import anthropic
from dataclasses import dataclass, field
from typing import Callable, Generator
from .config import HarnessConfig
from .session import PersistentSession

@dataclass
class TurnResult:
    prompt: str
    output: str
    tool_calls_made: list[dict]
    input_tokens: int
    output_tokens: int
    stop_reason: str
    session_id: str

@dataclass
class RealQueryEngine:
    config: HarnessConfig
    client: anthropic.Anthropic
    session: PersistentSession
    system_prompt: str
    tool_executor: Callable[[str, dict], str] = field(default=lambda name, inp: f"[no executor: {name}]")

    def submit_message(
        self,
        prompt: str,
        tool_definitions: list[dict],
        denied_tool_names: set[str] = frozenset(),
    ) -> TurnResult:
        ctx = getattr(self, "_context_manager", None)

        self.session.add_user_turn(prompt)
        if ctx is not None:
            ctx.add_user_turn(prompt)

        allowed_tools = [t for t in tool_definitions if t.get("name") not in denied_tool_names]

        tool_calls_made: list[dict] = []
        final_output = ""
        turns = 0

        while turns < self.config.max_turns:
            turns += 1
            system_blocks = self._build_system(self.system_prompt)

            if ctx is not None:
                api_messages = ctx.get_messages(self.system_prompt)
            else:
                api_messages = self.session.as_api_messages()

            kwargs: dict = dict(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                system=system_blocks,
                tools=allowed_tools if allowed_tools else [],
                messages=api_messages,
            )
            if self.config.enable_thinking:
                kwargs["thinking"] = {"type": "enabled", "budget_tokens": 5000}

            response = self.client.messages.create(**kwargs)
            self.session.update_usage(response.usage)
            assistant_content = [b.model_dump() for b in response.content]
            self.session.add_assistant_turn(assistant_content)
            if ctx is not None:
                ctx.add_assistant_turn(assistant_content)
                ctx.update_usage(
                    getattr(response.usage, "input_tokens", 0),
                    getattr(response.usage, "output_tokens", 0),
                )

            if response.stop_reason == "end_turn":
                final_output = self._extract_text(response.content)
                break

            if response.stop_reason == "tool_use":
                tool_result_blocks = []
                for block in response.content:
                    if block.type == "tool_use":
                        tool_calls_made.append({"name": block.name, "input": block.input})
                        try:
                            result = self.tool_executor(block.name, block.input)
                        except Exception as exc:
                            result = f"Tool error: {exc}"
                        tool_result_blocks.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        })
                self.session.add_user_turn(tool_result_blocks)
                if ctx is not None:
                    ctx.add_user_turn(tool_result_blocks)
                continue

            # max_tokens or other stop
            final_output = self._extract_text(response.content)
            break

        return TurnResult(
            prompt=prompt,
            output=final_output,
            tool_calls_made=tool_calls_made,
            input_tokens=self.session.input_tokens,
            output_tokens=self.session.output_tokens,
            stop_reason=response.stop_reason if turns > 0 else "no_turns",
            session_id=self.session.session_id,
        )

    def _build_system(self, text: str) -> list[dict]:
        block: dict = {"type": "text", "text": text}
        if self.config.enable_caching:
            block["cache_control"] = {"type": "ephemeral"}
        return [block]

    @staticmethod
    def _extract_text(content) -> str:
        parts = []
        for block in content:
            if hasattr(block, "type") and block.type == "text":
                parts.append(block.text)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "\n".join(parts)

    @classmethod
    def create_with_context_manager(
        cls,
        config: "HarnessConfig",
        client: "anthropic.Anthropic",
        system_prompt: str,
        tool_executor,
        store_dir=None,
    ) -> tuple["RealQueryEngine", "ContextManager"]:
        """
        Factory that creates an engine + a ContextManager wired together.
        The engine's session is a thin wrapper; ContextManager owns message history.
        """
        from pathlib import Path
        from ..memory.manager import ContextManager
        from .session import PersistentSession
        from uuid import uuid4

        session = PersistentSession(session_id=uuid4().hex)
        sd = store_dir or Path(".hpl_memory")
        ctx = ContextManager.create(
            session_id=session.session_id,
            store_dir=sd,
            claude_client=client,
            model=config.model,
            system_prompt=system_prompt,
        )
        engine = cls(
            config=config,
            client=client,
            session=session,
            system_prompt=system_prompt,
            tool_executor=tool_executor,
        )
        engine._context_manager = ctx
        return engine, ctx
