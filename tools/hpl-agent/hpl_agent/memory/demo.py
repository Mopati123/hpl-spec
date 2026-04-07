"""
Demo: context management without API key (uses extractive fallback summarizer).
Run: python -m hpl_agent.memory.demo
"""
from __future__ import annotations
from pathlib import Path
from .budget import compute_budget, estimate_tokens, AVAILABLE_INPUT_TOKENS
from .compressor import ContextCompressor, CompressedState
from .store import ColdMemoryStore
from .manager import ContextManager

def demo():
    print("=== Context Budget Demo ===\n")

    # Simulate a growing conversation
    messages = []
    for i in range(20):
        messages.append({"role": "user", "content": f"User turn {i}: " + "x" * 500})
        messages.append({"role": "assistant", "content": f"Assistant turn {i}: " + "y" * 800})

    system = "You are an HPL assistant. " * 100  # ~2500 chars

    budget = compute_budget(system, messages, "Current query: what is the plan?")
    print(f"Before compression: {budget}")
    print(f"Needs compression: {budget.needs_compression}\n")

    # Compress (no API key — uses extractive fallback)
    compressor = ContextCompressor(claude_summarizer=None)
    compressed_messages, warm_state = compressor.compress(messages)

    budget_after = compute_budget(system, compressed_messages)
    print(f"After compression:  {budget_after}")
    print(f"Messages: {len(messages)} -> {len(compressed_messages)}")
    print(f"Warm state goal: {warm_state.goal}")
    print(f"Warm state completed entries: {len(warm_state.completed)}\n")

    # Test cold storage
    print("=== Cold Storage Demo ===\n")
    store = ColdMemoryStore(store_dir=Path(".hpl_memory_demo"))
    cp = ColdMemoryStore.make_checkpoint(
        session_id="demo-session",
        turn_index=20,
        warm_state=warm_state,
        hot_messages=messages[-6:],
        input_tokens=15000,
        output_tokens=8000,
    )
    path = store.save_checkpoint(cp)
    print(f"Checkpoint saved: {path}")

    loaded = store.load_latest_checkpoint("demo-session")
    print(f"Checkpoint loaded: turn={loaded.turn_index}, in={loaded.input_tokens_at_checkpoint}, out={loaded.output_tokens_at_checkpoint}")
    print(f"Sessions in store: {store.list_sessions()}")

if __name__ == "__main__":
    demo()
