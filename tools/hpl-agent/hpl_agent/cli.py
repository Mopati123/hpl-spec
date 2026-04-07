from __future__ import annotations
import json, os
from pathlib import Path
from typing import Optional
import typer

app = typer.Typer(name="hpl-agent", help="HPL-powered Claude agent with governed execution.")

def _get_config():
    from hpl_agent.harness.config import HarnessConfig
    return HarnessConfig.from_env()

def _get_assistant():
    from hpl_agent.agent.assistant import HplAssistant
    return HplAssistant.create()

@app.command("ask")
def cmd_ask(
    prompt: str = typer.Argument(..., help="Prompt to send to the HPL assistant"),
    save: bool = typer.Option(False, "--save", help="Save session after response"),
):
    """Ask the HPL assistant a question."""
    assistant = _get_assistant()
    response = assistant.ask(prompt)
    typer.echo(response)
    if save:
        path = assistant.save_session()
        typer.echo(f"\nSession saved: {path}", err=True)

@app.command("parse")
def cmd_parse(
    file: Path = typer.Argument(..., help="HPL source file to parse"),
):
    """Parse an HPL source file."""
    from hpl_agent.hpl.bridge import HplBridge
    source = file.read_text()
    result = HplBridge.get().parse(source)
    typer.echo(result.to_json())

@app.command("validate")
def cmd_validate(
    ir_file: Path = typer.Argument(..., help="JSON IR file to validate"),
):
    """Validate an HPL IR against axioms."""
    from hpl_agent.hpl.bridge import HplBridge
    ir = json.loads(ir_file.read_text())
    result = HplBridge.get().validate(ir)
    typer.echo(result.to_json())

@app.command("run")
def cmd_run(
    file: Path = typer.Argument(..., help="HPL source file to parse, plan, and run"),
    backend: str = typer.Option("classical", "--backend", help="Execution backend"),
    budget: int = typer.Option(100, "--budget", help="Step budget"),
):
    """Parse, plan, and run an HPL program end-to-end."""
    from hpl_agent.hpl.bridge import HplBridge
    bridge = HplBridge.get()
    source = file.read_text()
    parse_result = bridge.parse(source)
    if not parse_result.success:
        typer.echo(f"Parse failed: {parse_result.errors}", err=True)
        raise typer.Exit(1)
    plan = bridge.plan(parse_result.ast_json or {}, backend=backend, budget_steps=budget)
    result = bridge.run(plan)
    typer.echo(result.to_json())

@app.command("generate")
def cmd_generate(
    folder: str = typer.Argument(..., help="_H folder name to generate impl for, e.g. axioms_H"),
    stub: str = typer.Argument(..., help="Stub function/class name to implement"),
):
    """Generate Python implementation for an HPL spec stub."""
    from hpl_agent.accelerator.scanner import HFolderScanner
    from hpl_agent.accelerator.gap_analyzer import GapAnalyzer
    from hpl_agent.accelerator.generator import ImplGenerator
    from hpl_agent.harness.config import HarnessConfig
    from hpl_agent.harness.client import AnthropicClientFactory
    from hpl_agent.harness.engine import RealQueryEngine
    from hpl_agent.harness.session import PersistentSession
    from hpl_agent.agent.system_prompt import build_system_prompt

    cfg = _get_config()
    repo = Path(os.environ.get("HPL_REPO_PATH", "."))
    scanner = HFolderScanner()
    folders = scanner.scan(repo)
    target = next((f for f in folders if f.name == folder), None)
    if target is None:
        typer.echo(f"Folder {folder} not found in {repo}", err=True)
        raise typer.Exit(1)

    client = AnthropicClientFactory.create()
    session = PersistentSession()
    engine = RealQueryEngine(
        config=cfg, client=client, session=session,
        system_prompt=build_system_prompt(repo),
        tool_executor=lambda n, i: f"[{n}]",
    )
    analyzer = GapAnalyzer()
    report = analyzer.analyze(target, repo / "src" / "hpl")
    generator = ImplGenerator(engine)
    impl = generator.generate_for_stub(report, stub)
    typer.echo(f"# Generated: {impl.stub_name} in {impl.folder_name}")
    typer.echo(f"# Confidence: {impl.confidence_note}")
    typer.echo(impl.python_source)

@app.command("govern")
def cmd_govern(
    prompt: str = typer.Argument(..., help="Prompt to run under governance"),
    audit_file: Path = typer.Option(Path(".hpl_audit.jsonl"), "--audit", help="Audit log path"),
    turns: int = typer.Option(1, "--turns", help="Number of governed turns"),
):
    """Run a governed agent turn with cryptographic audit trail."""
    from hpl_agent.harness.config import HarnessConfig
    from hpl_agent.harness.client import AnthropicClientFactory
    from hpl_agent.harness.engine import RealQueryEngine
    from hpl_agent.harness.session import PersistentSession
    from hpl_agent.agent.system_prompt import build_system_prompt
    from hpl_agent.ci.signer import Ed25519Signer
    from hpl_agent.ci.audit_log import AuditLog
    from hpl_agent.ci.governance_agent import GovernanceAgent
    from hpl_agent.tools.registry import ALL_TOOL_SCHEMAS, ALL_TOOL_EXECUTORS

    cfg = _get_config()
    client = AnthropicClientFactory.create()
    session = PersistentSession()
    engine = RealQueryEngine(
        config=cfg, client=client, session=session,
        system_prompt=build_system_prompt(),
        tool_executor=lambda name, inp: ALL_TOOL_EXECUTORS.get(name, lambda i: "not found")(inp),
    )
    signer = Ed25519Signer()
    audit_log = AuditLog(path=audit_file)
    agent = GovernanceAgent(
        engine=engine, signer=signer, audit_log=audit_log,
        tool_definitions=ALL_TOOL_SCHEMAS,
        tool_executor=lambda name, inp: ALL_TOOL_EXECUTORS.get(name, lambda i: "not found")(inp),
    )
    for i in range(turns):
        turn_prompt = prompt if i == 0 else f"{prompt} [turn {i+1}]"
        result = agent.run_governed_turn(turn_prompt)
        typer.echo(f"\n=== Turn {result.turn_index} ===")
        typer.echo(result.response)
    chain = agent.finalize_session()
    typer.echo(f"\nSession finalized. Merkle root: {chain.merkle_root[:16]}...", err=True)
    typer.echo(f"Audit log: {audit_file}", err=True)

@app.command("ctih-demo")
def cmd_ctih_demo(
    child_budget: int = typer.Option(10, "--budget", help="Child agent step budget"),
):
    """Demo Causal Token Inheritance: parent mints child sub-token, monitors consumption."""
    from hpl_agent.ctih.token_tree import TokenScope, TokenTree
    from hpl_agent.ctih.parent_scheduler import ParentScheduler
    from hpl_agent.ctih.consumption_witness import ConsumptionWitness
    from hpl_agent.ci.signer import Ed25519Signer
    import hashlib

    root_token_id = hashlib.sha256(b"demo-root").hexdigest()[:16]
    root_scope = TokenScope(
        allowed_backends=("classical", "python"),
        budget_steps=1000,
        enable_io=False,
        enable_net=False,
        allow_tool_names=("parse_hpl", "validate_hpl", "plan_hpl"),
    )
    tree = TokenTree(root_token_id=root_token_id, root_scope=root_scope)

    revocations = []
    scheduler = ParentScheduler(
        token_tree=tree,
        on_revoke=lambda r: revocations.append(r),
    )

    child_scope = TokenScope(
        allowed_backends=("classical",),
        budget_steps=child_budget,
        enable_io=False,
        enable_net=False,
        allow_tool_names=("parse_hpl",),
    )
    child_token = scheduler.spawn_child(child_scope)
    typer.echo(f"Child token minted: {child_token.token_id[:16]}...")
    typer.echo(f"Child scope: {child_token.scope.to_dict()}")

    signer = Ed25519Signer()
    for step in range(1, child_budget + 5):
        witness = ConsumptionWitness.create(
            session_id="demo-session",
            sub_token_id=child_token.token_id,
            steps=step,
            input_tokens=step * 100,
            output_tokens=step * 50,
        ).sign(signer)
        still_active = scheduler.receive_witness(witness)
        typer.echo(f"Step {step}: active={still_active}")
        if not still_active:
            typer.echo(f"Child revoked at step {step}")
            break

    typer.echo(f"\nRevocations: {len(revocations)}")
    typer.echo(f"Budget summary: {scheduler.get_budget_summary()}")

if __name__ == "__main__":
    app()
