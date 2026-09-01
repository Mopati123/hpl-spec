import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
DOCS_SCHEMA_PATH = ROOT / "docs" / "spec" / "04_ir_schema.json"
PACKAGED_SCHEMA_PATH = ROOT / "src" / "hpl" / "spec_data" / "04_ir_schema.json"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_packaged_program_ir_schema_matches_canonical_docs_schema():
    """Installed HPL must validate ProgramIR with the same schema published by the spec."""
    assert _load(PACKAGED_SCHEMA_PATH) == _load(DOCS_SCHEMA_PATH)
