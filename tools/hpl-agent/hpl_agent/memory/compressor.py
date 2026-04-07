from __future__ import annotations
import json
from dataclasses import dataclass
from typing import Any
from .budget import HOT_MESSAGES, WARM_SUMMARY_TARGET, estimate_tokens

SUMMARY_SYSTEM = """You are a context compressor for an HPL (Hamiltonian Programming Language) agent session.
Compress the conversation history below into a structured summary.
Return ONLY valid JSON (no markdown, no explanation) matching this schema:
{
  "goal": "one sentence describing the user's main objective",
  "completed": ["list of things accomplished"],
  "decisions": ["key decisions made"],
  "in_progress": ["what is currently being worked on"],
  "constraints": ["hard constraints or requirements stated by user"],
  "open_questions": ["unresolved questions"],
  "hpl_artifacts": ["HPL programs written, tokens minted, plans created, runs executed"],
  "token_estimate": <integer: estimated tokens in this summary>
}
Be terse. Each list item should be one short sentence. Total response must be under 600 tokens."""


@dataclass
class CompressedState:
    goal: str = ""
    completed: list[str] = None
    decisions: list[str] = None
    in_progress: list[str] = None
    constraints: list[str] = None
    open_questions: list[str] = None
    hpl_artifacts: list[str] = None
    token_estimate: int = 0
    raw_summary: str = ""

    def __post_init__(self):
        for field in ("completed", "decisions", "in_progress", "constraints", "open_questions", "hpl_artifacts"):
            if getattr(self, field) is None:
                setattr(self, field, [])

    def to_message_block(self) -> dict:
        """Convert to a system-style message block for injection into prompt."""
        lines = [
            "=== WARM MEMORY (compressed prior context) ===",
            f"Goal: {self.goal}",
        ]
        if self.completed:
            lines += ["Completed:"] + [f"  - {x}" for x in self.completed]
        if self.decisions:
            lines += ["Decisions:"] + [f"  - {x}" for x in self.decisions]
        if self.in_progress:
            lines += ["In Progress:"] + [f"  - {x}" for x in self.in_progress]
        if self.constraints:
            lines += ["Constraints:"] + [f"  - {x}" for x in self.constraints]
        if self.hpl_artifacts:
            lines += ["HPL Artifacts:"] + [f"  - {x}" for x in self.hpl_artifacts]
        if self.open_questions:
            lines += ["Open Questions:"] + [f"  - {x}" for x in self.open_questions]
        lines.append("=== END WARM MEMORY ===")
        return {"role": "user", "content": "\n".join(lines)}

    @classmethod
    def from_json(cls, data: dict) -> "CompressedState":
        return cls(
            goal=data.get("goal", ""),
            completed=data.get("completed", []),
            decisions=data.get("decisions", []),
            in_progress=data.get("in_progress", []),
            constraints=data.get("constraints", []),
            open_questions=data.get("open_questions", []),
            hpl_artifacts=data.get("hpl_artifacts", []),
            token_estimate=data.get("token_estimate", 0),
        )


class ContextCompressor:
    """
    Implements the 3 compression levels:
    1. Truncation: drop oldest messages
    2. Summarization: call Claude to compress old messages into CompressedState
    3. State encoding: replace everything with structured JSON state
    """

    def __init__(self, claude_summarizer: Any | None = None):
        """
        claude_summarizer: optional callable(messages: list[dict]) -> str
        If None, falls back to extractive truncation only.
        """
        self._summarizer = claude_summarizer

    def compress(self, messages: list[dict], warm_state: CompressedState | None = None) -> tuple[list[dict], CompressedState]:
        """
        Returns (compressed_messages, new_warm_state).
        Keeps HOT_MESSAGES verbatim, summarizes the rest.
        """
        if len(messages) <= HOT_MESSAGES:
            return messages, warm_state or CompressedState()

        cold_messages = messages[:-HOT_MESSAGES]
        hot_messages = messages[-HOT_MESSAGES:]

        new_state = self._summarize(cold_messages, warm_state)

        # Rebuild: warm memory block + hot messages
        result = [new_state.to_message_block()]
        # Add a synthetic assistant ack so the message alternation is valid
        result.append({"role": "assistant", "content": "Understood. Continuing from compressed context."})
        result.extend(hot_messages)
        return result, new_state

    def _summarize(self, messages: list[dict], existing: CompressedState | None) -> CompressedState:
        if self._summarizer is None:
            # Extractive fallback: build minimal state from message text
            texts = []
            for m in messages:
                c = m.get("content", "")
                if isinstance(c, str):
                    texts.append(c[:200])
            return CompressedState(
                goal="(summarizer unavailable — extractive fallback)",
                completed=texts[:3],
                in_progress=[texts[-1]] if texts else [],
            )

        # Build the summarization prompt
        history_text = self._render_messages(messages)
        existing_context = ""
        if existing and existing.goal:
            existing_context = f"\nExisting warm state to merge into:\n{json.dumps(existing.__dict__, indent=2)}\n"

        prompt = f"{existing_context}\nConversation to compress:\n{history_text}"

        try:
            raw = self._summarizer([
                {"role": "user", "content": prompt}
            ])
            data = json.loads(raw)
            state = CompressedState.from_json(data)
            state.raw_summary = raw
            return state
        except Exception as exc:
            return CompressedState(
                goal="(compression failed)",
                constraints=[str(exc)],
                in_progress=["restore from cold storage if available"],
            )

    def _render_messages(self, messages: list[dict]) -> str:
        parts = []
        for m in messages:
            role = m.get("role", "?")
            content = m.get("content", "")
            if isinstance(content, list):
                text = " ".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
            else:
                text = str(content)
            parts.append(f"[{role.upper()}]: {text[:800]}")
        return "\n\n".join(parts)
