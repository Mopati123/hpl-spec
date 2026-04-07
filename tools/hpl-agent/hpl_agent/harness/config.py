from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class HarnessConfig:
    model: str = "claude-opus-4-6"
    max_tokens: int = 16000
    max_turns: int = 8
    enable_thinking: bool = True
    enable_caching: bool = True
    session_dir: Path = Path(".hpl_sessions")
    keys_dir: Path = Path(".hpl_keys")
    api_key: str = ""

    @classmethod
    def from_env(cls) -> "HarnessConfig":
        return cls(
            model=os.environ.get("HPL_MODEL", "claude-opus-4-6"),
            max_tokens=int(os.environ.get("HPL_MAX_TOKENS", "16000")),
            max_turns=int(os.environ.get("HPL_MAX_TURNS", "8")),
            enable_thinking=os.environ.get("HPL_THINKING", "true").lower() == "true",
            enable_caching=os.environ.get("HPL_CACHING", "true").lower() == "true",
            session_dir=Path(os.environ.get("HPL_SESSIONS_DIR", ".hpl_sessions")),
            keys_dir=Path(os.environ.get("HPL_KEYS_DIR", ".hpl_keys")),
            api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
        )
