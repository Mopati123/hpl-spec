from __future__ import annotations
import ast as ast_mod, json
from dataclasses import dataclass
from pathlib import Path
from .scanner import SpecFolder

@dataclass
class StubReport:
    folder: SpecFolder
    declared_operators: list[str]
    implemented_functions: list[str]
    missing: list[str]
    extra: list[str]
    spec_contracts: list[str]

class GapAnalyzer:
    def analyze(self, spec_folder: SpecFolder, src_hpl_root: Path) -> StubReport:
        declared = self._load_declared(spec_folder)
        implemented = self._load_implemented(spec_folder, src_hpl_root)
        contracts = self._extract_contracts(spec_folder.readme_text)
        missing = [d for d in declared if d not in implemented]
        extra = [i for i in implemented if i not in declared and not i.startswith("_")]
        return StubReport(
            folder=spec_folder,
            declared_operators=declared,
            implemented_functions=implemented,
            missing=missing,
            extra=extra,
            spec_contracts=contracts,
        )

    def analyze_all(self, folders: list[SpecFolder], src_hpl_root: Path) -> list[StubReport]:
        return [self.analyze(f, src_hpl_root) for f in folders]

    def _load_declared(self, folder: SpecFolder) -> list[str]:
        reg = folder.path / "operators" / "registry.json"
        if not reg.exists():
            return []
        try:
            data = json.loads(reg.read_text())
            return [e.get("name", "") for e in data if isinstance(e, dict) and e.get("name")]
        except Exception:
            return []

    def _load_implemented(self, folder: SpecFolder, src_hpl_root: Path) -> list[str]:
        impl_name = folder.name.replace("_H", "").lower()
        impl_folder = src_hpl_root / impl_name
        if not impl_folder.exists():
            return []
        names = []
        for py in impl_folder.rglob("*.py"):
            try:
                tree = ast_mod.parse(py.read_text())
                for node in ast_mod.walk(tree):
                    if isinstance(node, (ast_mod.FunctionDef, ast_mod.AsyncFunctionDef, ast_mod.ClassDef)):
                        names.append(node.name)
            except Exception:
                pass
        return names

    def _extract_contracts(self, readme: str) -> list[str]:
        contracts = []
        for line in readme.splitlines():
            stripped = line.strip()
            if stripped.startswith("- ") or stripped.startswith("* "):
                contracts.append(stripped[2:].strip())
        return contracts[:20]
