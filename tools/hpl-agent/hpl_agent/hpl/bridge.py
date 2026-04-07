from __future__ import annotations
import json, os, subprocess, sys, tempfile
from pathlib import Path
from typing import ClassVar
from .models import ParseResult, ValidationResult, ExecutionPlan, RuntimeResult

class HplBridge:
    _instance: ClassVar["HplBridge | None"] = None
    _use_import: bool = False
    _hpl_repo: Path | None = None

    def __init__(self) -> None:
        repo_env = os.environ.get("HPL_REPO_PATH", "")
        if repo_env:
            self._hpl_repo = Path(repo_env)
            src = self._hpl_repo / "src"
            if src.exists() and str(src) not in sys.path:
                sys.path.insert(0, str(src))
        self._use_import = self._try_import()

    @classmethod
    def get(cls) -> "HplBridge":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def parse(self, source: str) -> ParseResult:
        import tempfile as _tf
        with _tf.NamedTemporaryFile(suffix=".hpl", mode="w", delete=False) as f:
            f.write(source)
            tmp = f.name
        with _tf.NamedTemporaryFile(suffix=".json", delete=False) as fo:
            out_path = fo.name
        try:
            rc, out, err = self._run_cli(["ir", tmp, "--out", out_path])
            if rc == 0:
                try:
                    ast = json.loads(Path(out_path).read_text())
                    return ParseResult(success=True, ast_json=ast, errors=[], source=source)
                except (json.JSONDecodeError, FileNotFoundError):
                    return ParseResult(success=True, ast_json={"raw": out}, errors=[], source=source)
            return ParseResult(success=False, ast_json=None, errors=[err or out], source=source)
        except FileNotFoundError:
            return ParseResult(success=False, ast_json=None, errors=["HPL runtime not found. Set HPL_REPO_PATH."], source=source)
        finally:
            Path(tmp).unlink(missing_ok=True)
            Path(out_path).unlink(missing_ok=True)

    def validate(self, ir: dict) -> ValidationResult:
        """Validate by running plan with budget=0 as a dry-run check."""
        try:
            plan = self.plan(ir, budget_steps=1)
            return ValidationResult(valid=True, violated_axioms=[], witnesses=[f"token_id={plan.token_id}"])
        except Exception as exc:
            return ValidationResult(valid=False, violated_axioms=[str(exc)], witnesses=[])

    def plan(self, ir: dict, backend: str = "classical", budget_steps: int = 100, enable_io: bool = False) -> ExecutionPlan:
        import tempfile as _tf, hashlib
        with _tf.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            json.dump(ir, f)
            ir_path = f.name
        with _tf.NamedTemporaryFile(suffix=".json", delete=False) as fo:
            out_path = fo.name
        try:
            args = ["plan", ir_path, "--out", out_path,
                    "--allowed-backends", backend,
                    "--budget-steps", str(budget_steps)]
            rc, out, err = self._run_cli(args)
            if rc == 0:
                try:
                    data = json.loads(Path(out_path).read_text())
                    token_id = data.get("execution_token", {}).get("token_id",
                        hashlib.sha256(json.dumps(ir, sort_keys=True).encode()).hexdigest()[:16])
                    steps = data.get("steps", [])
                    return ExecutionPlan(
                        token_id=token_id,
                        backend=backend,
                        steps=steps,
                        policy_summary={"backend": backend, "budget_steps": budget_steps, "enable_io": enable_io, "plan_file": out_path},
                    )
                except Exception:
                    token_id = hashlib.sha256(json.dumps(ir, sort_keys=True).encode()).hexdigest()[:16]
                    return ExecutionPlan(token_id=token_id, backend=backend, steps=[], policy_summary={"backend": backend, "budget_steps": budget_steps})
            raise RuntimeError(err or out)
        finally:
            Path(ir_path).unlink(missing_ok=True)

    def run(self, plan: ExecutionPlan) -> RuntimeResult:
        import tempfile as _tf
        # plan_file may have been written during plan(); if not, write it now
        plan_file = plan.policy_summary.get("plan_file", "")
        cleanup_plan = False
        if not plan_file or not Path(plan_file).exists():
            with _tf.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
                json.dump({"execution_token": {"token_id": plan.token_id}, "steps": plan.steps}, f)
                plan_file = f.name
            cleanup_plan = True
        with _tf.NamedTemporaryFile(suffix=".json", delete=False) as fo:
            out_path = fo.name
        try:
            args = ["run", plan_file, "--out", out_path, "--backend", plan.backend]
            rc, out, err = self._run_cli(args)
            success = rc == 0
            output_data = {}
            try:
                output_data = json.loads(Path(out_path).read_text())
            except Exception:
                pass
            return RuntimeResult(
                success=success,
                output=json.dumps(output_data) if output_data else out,
                witness_records=output_data.get("witness_records", []),
                transcript=output_data.get("transcript", [{"step": "run", "rc": rc}]),
                refusal_reasons=output_data.get("refusal_reasons", [err] if not success and err else []),
            )
        finally:
            if cleanup_plan:
                Path(plan_file).unlink(missing_ok=True)
            Path(out_path).unlink(missing_ok=True)

    def _try_import(self) -> bool:
        try:
            import hpl  # noqa: F401
            return True
        except ImportError:
            return False

    def _run_cli(self, args: list[str], stdin: str | None = None) -> tuple[int, str, str]:
        cmd = [sys.executable, "-m", "hpl.cli"] + args
        if self._hpl_repo:
            env = {**os.environ, "PYTHONPATH": str(self._hpl_repo / "src")}
        else:
            env = os.environ.copy()
        result = subprocess.run(
            cmd, input=stdin, capture_output=True, text=True, env=env, timeout=30
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
