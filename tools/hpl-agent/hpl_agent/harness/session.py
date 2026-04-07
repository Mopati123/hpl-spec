from __future__ import annotations
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from uuid import uuid4

@dataclass
class PersistentSession:
    session_id: str = field(default_factory=lambda: uuid4().hex)
    messages: list[dict] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    evidence_chain_path: str | None = None

    def add_user_turn(self, content: str | list) -> None:
        if isinstance(content, str):
            content = [{"type": "text", "text": content}]
        self.messages.append({"role": "user", "content": content})

    def add_assistant_turn(self, content: list) -> None:
        self.messages.append({"role": "assistant", "content": content})

    def as_api_messages(self) -> list[dict]:
        return list(self.messages)

    def update_usage(self, usage) -> None:
        self.input_tokens += getattr(usage, "input_tokens", 0)
        self.output_tokens += getattr(usage, "output_tokens", 0)
        self.cache_read_tokens += getattr(usage, "cache_read_input_tokens", 0) or 0
        self.cache_write_tokens += getattr(usage, "cache_creation_input_tokens", 0) or 0

    def save(self, directory: Path) -> Path:
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{self.session_id}.json"
        data = {
            "session_id": self.session_id,
            "messages": self.messages,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_read_tokens": self.cache_read_tokens,
            "cache_write_tokens": self.cache_write_tokens,
            "evidence_chain_path": self.evidence_chain_path,
        }
        path.write_text(json.dumps(data, indent=2))
        return path

    @classmethod
    def load(cls, session_id: str, directory: Path) -> "PersistentSession":
        data = json.loads((directory / f"{session_id}.json").read_text())
        return cls(
            session_id=data["session_id"],
            messages=data["messages"],
            input_tokens=data["input_tokens"],
            output_tokens=data["output_tokens"],
            cache_read_tokens=data.get("cache_read_tokens", 0),
            cache_write_tokens=data.get("cache_write_tokens", 0),
            evidence_chain_path=data.get("evidence_chain_path"),
        )
