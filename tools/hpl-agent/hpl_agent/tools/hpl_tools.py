from __future__ import annotations
import json
from ..hpl.bridge import HplBridge

# Each function returns (tool_schema_dict, executor_callable)
# tool_schema_dict matches Anthropic's tool format:
# {"name": ..., "description": ..., "input_schema": {"type": "object", "properties": {...}, "required": [...]}}

def parse_hpl_tool() -> tuple[dict, callable]:
    schema = {
        "name": "parse_hpl",
        "description": "Parse an HPL source program. Returns JSON ParseResult with AST and any errors.",
        "input_schema": {
            "type": "object",
            "properties": {
                "source_code": {"type": "string", "description": "The HPL source code to parse"},
                "source_path": {"type": "string", "description": "Optional path label for error messages", "default": "<stdin>"},
            },
            "required": ["source_code"],
        },
    }
    def executor(inp: dict) -> str:
        result = HplBridge.get().parse(inp["source_code"])
        return result.to_json()
    return schema, executor

def validate_hpl_tool() -> tuple[dict, callable]:
    schema = {
        "name": "validate_hpl",
        "description": "Validate an HPL ProgramIR against HPL axioms. Returns ValidationResult.",
        "input_schema": {
            "type": "object",
            "properties": {
                "program_ir_json": {"type": "string", "description": "JSON string of the ProgramIR (output of parse_hpl)"},
            },
            "required": ["program_ir_json"],
        },
    }
    def executor(inp: dict) -> str:
        ir = json.loads(inp["program_ir_json"])
        result = HplBridge.get().validate(ir)
        return result.to_json()
    return schema, executor

def plan_hpl_tool() -> tuple[dict, callable]:
    schema = {
        "name": "plan_hpl",
        "description": "Schedule an HPL ProgramIR. Mints an ExecutionToken and returns the ExecutionPlan.",
        "input_schema": {
            "type": "object",
            "properties": {
                "program_ir_json": {"type": "string", "description": "JSON ProgramIR"},
                "backend": {"type": "string", "enum": ["classical", "python", "qasm"], "default": "classical"},
                "budget_steps": {"type": "integer", "default": 100},
                "enable_io": {"type": "boolean", "default": False},
            },
            "required": ["program_ir_json"],
        },
    }
    def executor(inp: dict) -> str:
        ir = json.loads(inp["program_ir_json"])
        result = HplBridge.get().plan(
            ir,
            backend=inp.get("backend", "classical"),
            budget_steps=inp.get("budget_steps", 100),
            enable_io=inp.get("enable_io", False),
        )
        return result.to_json()
    return schema, executor

def run_hpl_tool() -> tuple[dict, callable]:
    schema = {
        "name": "run_hpl",
        "description": "Execute a planned HPL program. Returns RuntimeResult with witness records and transcript.",
        "input_schema": {
            "type": "object",
            "properties": {
                "execution_plan_json": {"type": "string", "description": "JSON ExecutionPlan from plan_hpl"},
            },
            "required": ["execution_plan_json"],
        },
    }
    def executor(inp: dict) -> str:
        from ..hpl.models import ExecutionPlan
        plan = ExecutionPlan.from_json(inp["execution_plan_json"])
        result = HplBridge.get().run(plan)
        return result.to_json()
    return schema, executor
