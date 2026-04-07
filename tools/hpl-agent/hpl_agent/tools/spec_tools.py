from __future__ import annotations
import json
from pathlib import Path
import os

def list_hpl_stubs_tool() -> tuple[dict, callable]:
    schema = {
        "name": "list_hpl_stubs",
        "description": "List all _H spec-only folders in the HPL repo and whether each has a Python implementation.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    }
    def executor(inp: dict) -> str:
        repo = Path(os.environ.get("HPL_REPO_PATH", "."))
        folders = sorted(repo.glob("*_H"))
        src_hpl = repo / "src" / "hpl"
        results = []
        for f in folders:
            impl_name = f.name.replace("_H", "").lower()
            has_impl = (src_hpl / impl_name).exists()
            readme = (f / "README.md")
            status = "has_impl" if has_impl else "spec_only"
            results.append({"folder": f.name, "status": status, "readme_exists": readme.exists()})
        return json.dumps(results, indent=2)
    return schema, executor

def read_spec_folder_tool() -> tuple[dict, callable]:
    schema = {
        "name": "read_spec_folder",
        "description": "Read the spec manifests and README from an _H folder.",
        "input_schema": {
            "type": "object",
            "properties": {
                "folder_name": {"type": "string", "description": "e.g. 'axioms_H'"},
            },
            "required": ["folder_name"],
        },
    }
    def executor(inp: dict) -> str:
        repo = Path(os.environ.get("HPL_REPO_PATH", "."))
        folder = repo / inp["folder_name"]
        if not folder.exists():
            return json.dumps({"error": f"Folder {inp['folder_name']} not found"})
        out = {"folder": inp["folder_name"], "files": {}}
        for path in sorted(folder.rglob("*")):
            if path.is_file() and path.suffix in (".md", ".json", ".txt", ".toml"):
                try:
                    out["files"][str(path.relative_to(repo))] = path.read_text()[:3000]
                except Exception:
                    pass
        return json.dumps(out, indent=2)
    return schema, executor

def diff_spec_impl_tool() -> tuple[dict, callable]:
    schema = {
        "name": "diff_spec_impl",
        "description": "Compare what a _H spec folder declares vs what exists in src/hpl/. Returns a gap report.",
        "input_schema": {
            "type": "object",
            "properties": {
                "folder_name": {"type": "string", "description": "e.g. 'axioms_H'"},
            },
            "required": ["folder_name"],
        },
    }
    def executor(inp: dict) -> str:
        import ast as ast_mod
        repo = Path(os.environ.get("HPL_REPO_PATH", "."))
        spec_folder = repo / inp["folder_name"]
        impl_name = inp["folder_name"].replace("_H", "").lower()
        impl_folder = repo / "src" / "hpl" / impl_name

        declared = []
        reg = spec_folder / "operators" / "registry.json"
        if reg.exists():
            try:
                entries = json.loads(reg.read_text())
                declared = [e.get("name", "") for e in entries if isinstance(e, dict)]
            except Exception:
                pass

        implemented = []
        if impl_folder.exists():
            for py in impl_folder.rglob("*.py"):
                try:
                    tree = ast_mod.parse(py.read_text())
                    for node in ast_mod.walk(tree):
                        if isinstance(node, (ast_mod.FunctionDef, ast_mod.AsyncFunctionDef, ast_mod.ClassDef)):
                            implemented.append(node.name)
                except Exception:
                    pass

        missing = [d for d in declared if d not in implemented]
        return json.dumps({
            "folder": inp["folder_name"],
            "declared": declared,
            "implemented": implemented,
            "missing": missing,
            "impl_exists": impl_folder.exists(),
        }, indent=2)
    return schema, executor
