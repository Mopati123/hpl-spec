from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional


DEFAULT_REFERENCE_MANIFEST = Path(
    "references/phase1/navier_stokes/machine_a_f06023a/anchor_manifest.json"
)
DEFAULT_REFERENCE_LEAVES = Path(
    "references/phase1/navier_stokes/machine_a_f06023a/anchor_leaves.json"
)
DEFAULT_OUT_DIR = Path("artifacts/phase1/navier_stokes/run_002")
DEFAULT_SIGNING_KEY = Path("tests/fixtures/keys/ci_ed25519_test.sk")
DEFAULT_PUBLIC_KEY = Path("tests/fixtures/keys/ci_ed25519_test.pub")
DEFAULT_REPO_SLUG = "Mopati123/hpl-spec"


@dataclass(frozen=True)
class TrackAConfig:
    repo_root: Path
    worktree_dir: Path
    reference_manifest: Path
    reference_leaves: Path
    out_dir: Path
    demo_name: str
    signing_key: Path
    public_key: Path
    repo_slug: str
    skip_tests: bool
    recreate_venv: bool


def _run(
    cmd: Iterable[str],
    *,
    cwd: Path,
    capture: bool = False,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        list(cmd),
        cwd=cwd,
        text=True,
        capture_output=capture,
    )
    if check and result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(cmd)}\n{detail}")
    return result


def _extract_json_line(output: str) -> Dict[str, object]:
    for line in output.splitlines():
        text = line.strip()
        if text.startswith("{") and text.endswith("}"):
            return json.loads(text)
    raise ValueError("No JSON object found in command output")


def _load_reference_contract(reference_manifest: Path) -> Dict[str, object]:
    payload = json.loads(reference_manifest.read_text(encoding="utf-8"))
    git_commit = str(payload.get("git_commit") or "").strip()
    if not git_commit:
        raise ValueError(f"Reference manifest is missing git_commit: {reference_manifest}")
    _validate_reference_folder_name(reference_manifest.parent.name, git_commit)
    return payload


def _validate_reference_folder_name(folder_name: str, git_commit: str) -> None:
    match = re.fullmatch(r"machine_a_([0-9a-f]{7,40})", folder_name)
    if not match:
        return
    expected_prefix = match.group(1)
    if not git_commit.startswith(expected_prefix):
        raise ValueError(
            f"Reference folder '{folder_name}' does not match git_commit '{git_commit}'. "
            "Use a folder name that matches the manifest commit prefix."
        )


def _ensure_paths_exist(paths: Iterable[Path]) -> None:
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        joined = ", ".join(missing)
        raise FileNotFoundError(f"Missing required files: {joined}")


def _ensure_worktree(repo_root: Path, worktree_dir: Path, git_commit: str) -> None:
    _run(["git", "fetch", "origin"], cwd=repo_root, check=True)
    cat_result = _run(["git", "cat-file", "-e", f"{git_commit}^{{commit}}"], cwd=repo_root, check=False)
    if cat_result.returncode != 0:
        raise RuntimeError(f"Reference git_commit not found in repository: {git_commit}")

    if worktree_dir.exists():
        _run(
            ["git", "worktree", "remove", "--force", str(worktree_dir)],
            cwd=repo_root,
            check=False,
        )
        if worktree_dir.exists():
            shutil.rmtree(worktree_dir)

    _run(
        [
            "git",
            "-c",
            "core.autocrlf=false",
            "-c",
            "core.eol=lf",
            "worktree",
            "add",
            "--detach",
            str(worktree_dir),
            git_commit,
        ],
        cwd=repo_root,
        check=True,
    )


def _venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _prepare_venv(worktree_dir: Path, recreate: bool, skip_tests: bool) -> Path:
    venv_dir = worktree_dir / ".venv_tracka"
    if recreate and venv_dir.exists():
        shutil.rmtree(venv_dir)
    python_path = _venv_python(venv_dir)
    if not python_path.exists():
        _run([sys.executable, "-m", "venv", str(venv_dir)], cwd=worktree_dir, check=True)

    _run([str(python_path), "-m", "pip", "install", "-U", "pip"], cwd=worktree_dir, check=True)
    _run([str(python_path), "-m", "pip", "install", "-e", "."], cwd=worktree_dir, check=True)
    _run(
        [str(python_path), "-m", "pip", "install", "pytest", "pynacl", "cryptography"],
        cwd=worktree_dir,
        check=True,
    )
    if not skip_tests:
        _run([str(python_path), "-m", "pytest", "-q"], cwd=worktree_dir, check=True)
    return python_path


def _run_demo_and_anchor(
    *,
    python_path: Path,
    worktree_dir: Path,
    config: TrackAConfig,
    reference_commit: str,
) -> Dict[str, Path]:
    demo_result = _run(
        [
            str(python_path),
            "-m",
            "hpl.cli",
            "demo",
            config.demo_name,
            "--out-dir",
            str(config.out_dir),
            "--signing-key",
            str(config.signing_key),
            "--pub",
            str(config.public_key),
        ],
        cwd=worktree_dir,
        capture=True,
        check=True,
    )
    demo_payload = _extract_json_line(demo_result.stdout)
    if not demo_payload.get("ok"):
        raise RuntimeError(f"Demo execution failed: {demo_result.stdout}")

    bundle_dir_value = str(demo_payload.get("bundle_path") or "").strip()
    if not bundle_dir_value:
        raise RuntimeError("Demo output missing bundle_path")
    bundle_dir = (worktree_dir / bundle_dir_value).resolve()
    anchor_dir = (worktree_dir / config.out_dir / "anchor").resolve()

    _run(
        [
            str(python_path),
            "tools/anchor_generator.py",
            str(bundle_dir),
            "--out-dir",
            str(anchor_dir),
            "--repo",
            config.repo_slug,
            "--git-commit",
            reference_commit,
            "--signing-key",
            str(config.signing_key),
            "--public-key",
            str(config.public_key),
        ],
        cwd=worktree_dir,
        check=True,
    )
    _run(
        [
            str(python_path),
            "tools/verify_anchor.py",
            str(bundle_dir),
            str(anchor_dir / "anchor_manifest.json"),
            "--public-key",
            str(config.public_key),
        ],
        cwd=worktree_dir,
        check=True,
    )
    return {
        "bundle_dir": bundle_dir,
        "anchor_manifest": anchor_dir / "anchor_manifest.json",
        "anchor_leaves": anchor_dir / "anchor_leaves.json",
    }


def _compare_contracts(
    *,
    python_path: Path,
    repo_root: Path,
    reference_manifest: Path,
    reference_leaves: Path,
    candidate_manifest: Path,
    candidate_leaves: Path,
) -> Dict[str, object]:
    compare_tool = repo_root / "tools" / "compare_anchor_contract.py"
    compare_result = _run(
        [
            str(python_path),
            str(compare_tool),
            "--machine-a-manifest",
            str(reference_manifest),
            "--machine-a-leaves",
            str(reference_leaves),
            "--machine-b-manifest",
            str(candidate_manifest),
            "--machine-b-leaves",
            str(candidate_leaves),
        ],
        cwd=repo_root,
        capture=True,
        check=False,
    )
    payload = _extract_json_line(compare_result.stdout)
    payload["compare_exit_code"] = compare_result.returncode
    return payload


def run_track_a(config: TrackAConfig) -> int:
    _ensure_paths_exist([config.reference_manifest, config.reference_leaves, config.signing_key, config.public_key])
    reference_contract = _load_reference_contract(config.reference_manifest)
    reference_commit = str(reference_contract["git_commit"])

    _ensure_worktree(config.repo_root, config.worktree_dir, reference_commit)
    python_path = _prepare_venv(config.worktree_dir, config.recreate_venv, config.skip_tests)

    generated = _run_demo_and_anchor(
        python_path=python_path,
        worktree_dir=config.worktree_dir,
        config=config,
        reference_commit=reference_commit,
    )
    compare_payload = _compare_contracts(
        python_path=python_path,
        repo_root=config.repo_root,
        reference_manifest=config.reference_manifest,
        reference_leaves=config.reference_leaves,
        candidate_manifest=generated["anchor_manifest"],
        candidate_leaves=generated["anchor_leaves"],
    )

    report = {
        "reference_commit": reference_commit,
        "reference_manifest": str(config.reference_manifest),
        "reference_leaves": str(config.reference_leaves),
        "candidate_manifest": str(generated["anchor_manifest"]),
        "candidate_leaves": str(generated["anchor_leaves"]),
        "bundle_dir": str(generated["bundle_dir"]),
        "CONTRACT_MATCH": bool(compare_payload.get("CONTRACT_MATCH")),
        "MERKLE_MATCH": bool(compare_payload.get("MERKLE_MATCH")),
        "ROOT_CAUSE": str(compare_payload.get("ROOT_CAUSE")),
        "NEXT_ACTION": str(compare_payload.get("NEXT_ACTION")),
        "compare_exit_code": int(compare_payload.get("compare_exit_code", 1)),
    }

    report_path = (config.worktree_dir / config.out_dir / "track_a_report.json").resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, sort_keys=True, separators=(",", ":")), encoding="utf-8")
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    print(f"CONTRACT_MATCH={'true' if report['CONTRACT_MATCH'] else 'false'}")
    print(f"MERKLE_MATCH={'true' if report['MERKLE_MATCH'] else 'false'}")
    print(f"REPORT_PATH={report_path}")
    if report["CONTRACT_MATCH"] and report["MERKLE_MATCH"]:
        return 0
    return 1


def _parse_args(argv: Optional[list[str]] = None) -> TrackAConfig:
    parser = argparse.ArgumentParser(
        description="Run deterministic Track A reproducibility against canonical Machine A reference artifacts."
    )
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--worktree-dir", type=Path, default=Path.cwd().parent / "hpl-spec-tracka-ref")
    parser.add_argument("--reference-manifest", type=Path, default=DEFAULT_REFERENCE_MANIFEST)
    parser.add_argument("--reference-leaves", type=Path, default=DEFAULT_REFERENCE_LEAVES)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--demo-name", default="navier-stokes")
    parser.add_argument("--signing-key", type=Path, default=DEFAULT_SIGNING_KEY)
    parser.add_argument("--public-key", type=Path, default=DEFAULT_PUBLIC_KEY)
    parser.add_argument("--repo", default=DEFAULT_REPO_SLUG)
    parser.add_argument("--skip-tests", action="store_true")
    parser.add_argument("--recreate-venv", action="store_true")
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    return TrackAConfig(
        repo_root=repo_root,
        worktree_dir=args.worktree_dir.resolve(),
        reference_manifest=(repo_root / args.reference_manifest).resolve()
        if not args.reference_manifest.is_absolute()
        else args.reference_manifest.resolve(),
        reference_leaves=(repo_root / args.reference_leaves).resolve()
        if not args.reference_leaves.is_absolute()
        else args.reference_leaves.resolve(),
        out_dir=args.out_dir,
        demo_name=args.demo_name,
        signing_key=(repo_root / args.signing_key).resolve()
        if not args.signing_key.is_absolute()
        else args.signing_key.resolve(),
        public_key=(repo_root / args.public_key).resolve()
        if not args.public_key.is_absolute()
        else args.public_key.resolve(),
        repo_slug=args.repo,
        skip_tests=bool(args.skip_tests),
        recreate_venv=bool(args.recreate_venv),
    )


def main(argv: Optional[list[str]] = None) -> int:
    config = _parse_args(argv)
    try:
        return run_track_a(config)
    except Exception as exc:  # pragma: no cover - surfaced to CLI callers
        error = {
            "CONTRACT_MATCH": False,
            "MERKLE_MATCH": False,
            "ROOT_CAUSE": "track_a_runner_failed",
            "NEXT_ACTION": str(exc),
        }
        print(json.dumps(error, sort_keys=True, separators=(",", ":")))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
