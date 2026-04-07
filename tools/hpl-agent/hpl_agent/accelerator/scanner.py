from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class SpecFolder:
    name: str
    path: Path
    readme_text: str
    manifest_files: list[Path]
    has_python_impl: bool
    impl_path: Path | None

class HFolderScanner:
    def scan(self, hpl_repo_root: Path) -> list[SpecFolder]:
        src_hpl = hpl_repo_root / "src" / "hpl"
        folders = sorted(hpl_repo_root.glob("*_H"))
        results = []
        for folder in folders:
            if not folder.is_dir():
                continue
            readme = folder / "README.md"
            readme_text = readme.read_text() if readme.exists() else ""
            manifests = list(folder.rglob("*.json")) + list(folder.rglob("*.toml"))
            impl_name = folder.name.replace("_H", "").lower()
            impl_path = src_hpl / impl_name if (src_hpl / impl_name).exists() else None
            results.append(SpecFolder(
                name=folder.name,
                path=folder,
                readme_text=readme_text,
                manifest_files=manifests,
                has_python_impl=impl_path is not None,
                impl_path=impl_path,
            ))
        return results
