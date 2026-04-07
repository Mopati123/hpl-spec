from __future__ import annotations
from dataclasses import dataclass, field
from ..harness.session import PersistentSession

@dataclass
class ConversationManager:
    session: PersistentSession
    max_history: int = 40

    def add_user_turn(self, content: str | list) -> None:
        self.session.add_user_turn(content)
        self._compact_if_needed()

    def add_assistant_turn(self, content: list) -> None:
        self.session.add_assistant_turn(content)

    def as_api_messages(self) -> list[dict]:
        return self.session.as_api_messages()

    def _compact_if_needed(self) -> None:
        if len(self.session.messages) > self.max_history:
            # Keep system context + last N messages
            self.session.messages = self.session.messages[-self.max_history:]
