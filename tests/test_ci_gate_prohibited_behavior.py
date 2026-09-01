from pathlib import Path

from tools.ci_gate_prohibited_behavior import validate_authority_boundaries


ENGINE_SOURCE = '''
reasons.append("execution token missing")
reasons.append("plan not approved")
def _execute_effect(step):
    raise RuntimeError("effect execution requires context")
'''


def _write(path: Path, content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _lawful_tree(root: Path) -> None:
    _write(root / "src/hpl/scheduler.py", "def plan(): pass\n")
    _write(root / "src/hpl/execution_token.py", "class ExecutionToken: pass\n")
    _write(root / "src/hpl/runtime/engine.py", ENGINE_SOURCE)
    _write(root / "src/hpl/runtime/effects/handler_registry.py", "def get_handler(): pass\n")
    _write(root / "src/hpl/backends/classical_lowering.py", "def lower(): pass\n")
    _write(root / "src/hpl/observers/papas.py", "def observe(): pass\n")


def test_gate_c_allows_governed_runtime_implementation(tmp_path):
    _lawful_tree(tmp_path)
    assert validate_authority_boundaries(tmp_path) == []


def test_gate_c_refuses_effect_dispatch_outside_runtime(tmp_path):
    _lawful_tree(tmp_path)
    _write(
        tmp_path / "src/hpl/backends/rogue.py",
        "def execute():\n    return get_handler('LIVE')\n",
    )

    violations = validate_authority_boundaries(tmp_path)

    assert any("effect dispatch outside governed runtime" in item for item in violations)


def test_gate_c_refuses_missing_execution_token_guard(tmp_path):
    _lawful_tree(tmp_path)
    engine = tmp_path / "src/hpl/runtime/engine.py"
    engine.write_text(
        ENGINE_SOURCE.replace('reasons.append("execution token missing")\n', ""),
        encoding="utf-8",
    )

    violations = validate_authority_boundaries(tmp_path)

    assert any("ExecutionToken" in item for item in violations)


def test_gate_c_refuses_missing_scheduler_approval_guard(tmp_path):
    _lawful_tree(tmp_path)
    engine = tmp_path / "src/hpl/runtime/engine.py"
    engine.write_text(
        ENGINE_SOURCE.replace('reasons.append("plan not approved")\n', ""),
        encoding="utf-8",
    )

    violations = validate_authority_boundaries(tmp_path)

    assert any("non-approved plan" in item for item in violations)


def test_gate_c_refuses_raw_effect_execution_without_context_guard(tmp_path):
    _lawful_tree(tmp_path)
    engine = tmp_path / "src/hpl/runtime/engine.py"
    engine.write_text(
        ENGINE_SOURCE.replace(
            'raise RuntimeError("effect execution requires context")',
            "return None",
        ),
        encoding="utf-8",
    )

    violations = validate_authority_boundaries(tmp_path)

    assert any("governed runtime context" in item for item in violations)
