from __future__ import annotations
from pathlib import Path
import os

_CACHED_PROMPT: str | None = None

def build_system_prompt(hpl_repo_root: Path | None = None) -> str:
    global _CACHED_PROMPT
    if _CACHED_PROMPT is not None:
        return _CACHED_PROMPT

    repo = hpl_repo_root or Path(os.environ.get("HPL_REPO_PATH", "."))

    sections = [
        "You are an expert HPL (Hamiltonian Programming Language) development assistant.",
        "",
        "## HPL Overview",
        "HPL is a governed execution substrate that:",
        "- Executes programs only under explicit ExecutionToken authority",
        "- Emits deterministic evidence bundles with cryptographic signatures",
        "- Uses refusal-first semantics: invalid state transitions produce explicit RefusalArtifacts",
        "- Supports three backends: PYTHON, CLASSICAL, QASM (quantum)",
        "- Operates as a pipeline: parse → macro-expand → validate → IR → plan → run → bundle",
        "",
        "## Tools Available",
        "- parse_hpl: Parse HPL source to AST/IR",
        "- validate_hpl: Check IR against axioms",
        "- plan_hpl: Schedule execution with a token (backend, budget, IO policy)",
        "- run_hpl: Execute a plan, get witness records and transcript",
        "- list_hpl_stubs: Find spec-only _H folders not yet implemented",
        "- read_spec_folder: Read a _H folder's spec documents",
        "- diff_spec_impl: Gap analysis between spec and implementation",
        "- verify_evidence_bundle: Verify bundle integrity",
        "- inspect_execution_token: Explain an ExecutionPlan's authority",
        "",
        "## HPL Syntax",
        "HPL uses Lisp-like S-expressions:",
        "```",
        "(defstrategy \"momentum-trade\"",
        "  (params (window 60) (threshold 0.02))",
        "  (let ((signal (compute-momentum window)))",
        "    (if (> signal threshold) (buy) (sell))))",
        "```",
        "",
        "## Refusal-First Semantics",
        "Invalid transitions produce RefusalArtifacts with witness documentation.",
        "Budget-exceeding steps produce ConstraintWitness evidence.",
        "All effects require explicit token authorization — no ambient permissions.",
        "",
        "## Evidence Model",
        "Every run produces a bundle with: role inventories, Merkle root, Ed25519 signature.",
        "Reproducibility verified by contract-state matching across 5 dimensions.",
    ]

    # Append _H folder summaries if repo is available
    if repo.exists():
        h_folders = sorted(repo.glob("*_H"))
        if h_folders:
            sections += ["", "## Spec Domains (_H folders)"]
            for folder in h_folders[:12]:
                readme = folder / "README.md"
                if readme.exists():
                    first_line = readme.read_text().strip().splitlines()[0].lstrip("#").strip()
                    sections.append(f"- **{folder.name}**: {first_line}")
                else:
                    sections.append(f"- **{folder.name}**: (no README)")

    _CACHED_PROMPT = "\n".join(sections)
    return _CACHED_PROMPT
