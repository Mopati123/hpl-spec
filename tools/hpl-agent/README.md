# hpl-agent

A production-grade AI execution system built on top of the Hamiltonian Programming Language.

## What this is

Seven interlocked layers built in a single session using Claude Code:

| Layer | Module | Description |
|-------|--------|-------------|
| 1 | `harness/` | Real Anthropic SDK agentic loop — tool use, session persistence, token tracking |
| 2 | `hpl/` | HPL runtime bridge — parse, plan, run `.hpl` programs from Python |
| 3 | `agent/` + `tools/` | Claude-powered HPL assistant with 9 built-in tools |
| 4 | `accelerator/` | Spec implementation generator — fills in spec-only `_H` stubs using Claude |
| 5 | `ci/` | Cryptographic governance — Ed25519 signing, Merkle audit trails, append-only logs |
| 6 | `ctih/` | **Causal Token Inheritance** — novel multi-agent governance via derived sub-tokens |
| 7 | `memory/` | 3-layer infinite context — hot (6 msgs) → warm (Claude summary) → cold (JSONL checkpoint) |

## CTIH — Causal Token Inheritance (novel)

The new idea that emerges from combining HPL + agentic execution:

- Parent scheduler mints a principal `ExecutionToken`
- Derives child sub-tokens: `SHA256(parent_id || child_scope_json)`
- Each child's authority = strict intersection of parent's (fewer tools, smaller budget)
- Children emit signed **ΔS consumption witnesses** back to parent each turn
- Parent auto-revokes any child that exceeds its delegated budget
- HPL becomes a live governance membrane over an entire agent tree

## What runs without API credits

- Full HPL parse → plan → run pipeline
- CTIH multi-agent governance with real-time revocation
- Cryptographic audit logs and Merkle proof chains
- Spec gap analysis across all 11 `_H` folders
- Context compression and cold checkpointing

## What activates with API credits

- Claude answering questions about HPL (`hpl-agent ask "..."`)
- Autonomous tool use during conversation
- Warm memory summarization
- Spec accelerator generating Python for missing `_H` stubs

## Setup

```bash
cd tools/hpl-agent
pip install -e .
cp .env.example .env
# Edit .env: set ANTHROPIC_API_KEY and HPL_REPO_PATH
```

## Usage

```bash
# Parse and run an HPL program (no API key needed)
hpl-agent parse examples/momentum_trade.hpl
hpl-agent run examples/momentum_trade.hpl --backend classical

# CTIH multi-agent governance demo (no API key needed)
hpl-agent ctih-demo --budget 10

# Governed session with audit trail (no API key needed for governance layer)
hpl-agent govern "analyse the momentum strategy" --audit .hpl_audit.jsonl

# Full Claude assistant (requires API credits)
hpl-agent ask "Write a mean-reversion HPL strategy and validate it"

# Generate implementations for spec-only stubs (requires API credits)
hpl-agent generate data_H SomeOperator
```

## Architecture

```
hpl_agent/
├── harness/       — Anthropic SDK: config, client, session, engine (real tool-use loop)
├── hpl/           — HPL bridge: models, bridge (importlib → subprocess fallback)
├── tools/         — Claude tool definitions: hpl_tools, spec_tools, evidence_tools, registry
├── agent/         — HPL assistant: system_prompt, conversation, assistant
├── accelerator/   — Spec generator: scanner, gap_analyzer, generator, validator
├── ci/            — Governance: merkle, signer, evidence_chain, audit_log, governance_agent
├── ctih/          — CTIH: token_tree, consumption_witness, parent_scheduler, child_agent
├── memory/        — Context mgmt: budget, compressor, store, manager
└── cli.py         — Typer CLI: ask/parse/validate/run/generate/govern/ctih-demo
```
