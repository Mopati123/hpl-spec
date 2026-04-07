from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Any
from .gap_analyzer import StubReport

@dataclass
class GeneratedImpl:
    stub_name: str
    folder_name: str
    python_source: str
    confidence_note: str
    spec_contracts_addressed: list[str]

class ImplGenerator:
    def __init__(self, engine: Any) -> None:  # RealQueryEngine
        self.engine = engine

    def generate_for_stub(self, report: StubReport, stub_name: str) -> GeneratedImpl:
        spec_text = report.folder.readme_text[:3000]
        contracts_text = "\n".join(f"- {c}" for c in report.spec_contracts[:10])
        manifest_text = ""
        for mf in report.manifest_files[:2]:
            try:
                manifest_text += f"\n### {mf.name}\n```json\n{mf.read_text()[:1000]}\n```\n"
            except Exception:
                pass

        prompt = f"""You are implementing a Python module for the HPL (Hamiltonian Programming Language) spec.

## Spec folder: {report.folder.name}
## Target stub: {stub_name}

## Spec README (first 3000 chars):
{spec_text}

## Spec contracts:
{contracts_text}

{manifest_text}

## Already implemented in src/hpl/:
{", ".join(report.implemented_functions[:20]) or "none"}

## Task:
Write a complete Python implementation for `{stub_name}` that satisfies the spec contracts above.
Use standard Python 3.11+. Import from within the hpl package as needed.
Return ONLY a Python code block (```python ... ```) followed by a one-sentence confidence note.
"""
        result = self.engine.submit_message(prompt=prompt, tool_definitions=[])
        source = self._extract_code(result.output)
        confidence = self._extract_confidence(result.output)
        return GeneratedImpl(
            stub_name=stub_name,
            folder_name=report.folder.name,
            python_source=source,
            confidence_note=confidence,
            spec_contracts_addressed=report.spec_contracts[:5],
        )

    def generate_batch(self, reports: list[StubReport]) -> list[GeneratedImpl]:
        results = []
        for report in reports:
            for stub in report.missing[:3]:  # cap at 3 per folder
                results.append(self.generate_for_stub(report, stub))
        return results

    def _extract_code(self, text: str) -> str:
        match = re.search(r"```python\n(.*?)```", text, re.DOTALL)
        return match.group(1).strip() if match else text.strip()

    def _extract_confidence(self, text: str) -> str:
        lines = [l.strip() for l in text.splitlines() if l.strip() and not l.strip().startswith("```")]
        return lines[-1] if lines else "No confidence note."
