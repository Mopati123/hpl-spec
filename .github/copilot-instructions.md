# Copilot / AI Agent Instructions for this repo

This repository currently contains minimal top-level documentation. Use the steps below to discover project specifics, and confirm any assumptions before making changes.

## Quick context (what I discovered)
- There are no `README.md` or language-specific entry points in the repo root.
- The repository includes a kluster rules file at `.github/instructions/kluster-code-verify.instructions.md` which defines mandatory verification steps and dependency checks. Follow those rules strictly.

---

## What to do first (discovery checklist)
1. Repo scan
   - Search for language or build files: `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `pom.xml`, `*.csproj`, `Dockerfile`, `Makefile`.
   - If none are present, stop and ask the maintainers which language and build/test commands are authoritative.
2. Look for tests and CI
   - Search for `tests/`, `__tests__/`, `*.spec.*`, `.github/workflows/` to learn test and CI patterns.
3. Inspect `.github/instructions/kluster-code-verify.instructions.md`
   - This file is authoritative for dependency checks and code verification. If you add/modify dependency files, run the required kluster dependency check before any installs.

---

## Authoring guidance (how to make changes)
- Always prefer small, incremental PRs that include a focused description, rationale, and verification steps.
- If you add or change dependency files (e.g., `package.json`, `requirements.txt`, `pyproject.toml`), run the kluster dependency check (see `.github/instructions/kluster-code-verify.instructions.md`) before performing any package installation commands.
- If the project lacks a README or CI, create succinct docs that explain:
  - The primary language(s) and version(s)
  - How to build, run, and test locally (exact commands)
  - Where tests live and how to run them

---

## Project-specific rules and examples
- Kluster verification: this repo contains `.github/instructions/kluster-code-verify.instructions.md`. Respect its rules:
  - "Running kluster code review..." is required before/after code changes (project CI may depend on it)
  - Run `kluster_dependency_check` before any dependency installation
- Example reference (do not change without approval): `.github/instructions/kluster-code-verify.instructions.md`

---

## When something is missing or ambiguous (ask, don't guess)
- If you cannot find build/test commands or primary language, open a short issue or ask the maintainer in the PR description. Example prompt: "What command(s) should I use to run the test suite locally?" Include OS specifics if relevant.
- If adding a new language or toolchain, include the exact installation and invocation commands in the PR description and update the README.

---

## Suggested PR checklist for contributors
- [ ] Does this change include a short rationale and test instructions in the PR body?
- [ ] If dependencies were added/changed, did you run the kluster dependency check? (see `.github/instructions/kluster-code-verify.instructions.md`)
- [ ] If changing runtime code, are there tests or a plan to add them in a follow-up PR?
- [ ] If adding a build or run command to docs, verify it works on a fresh VM/container or document prerequisites explicitly.

---

## If you are an automated agent (strict):
- Do not make assumptions about language, build, or test commands — confirm before committing.
- Preserve or reference existing instruction files (especially `.github/instructions/kluster-code-verify.instructions.md`). If you propose changes to those files, include a human-review request and rationale.
- Keep changes small, reversible, and well-documented.

---

If any part of the repo or operational commands are missing or unclear, ask me which files or commands to reference and I will update this file accordingly.