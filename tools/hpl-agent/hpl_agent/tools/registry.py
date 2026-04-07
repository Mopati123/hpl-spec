from __future__ import annotations
from .hpl_tools import parse_hpl_tool, validate_hpl_tool, plan_hpl_tool, run_hpl_tool
from .spec_tools import list_hpl_stubs_tool, read_spec_folder_tool, diff_spec_impl_tool
from .evidence_tools import verify_evidence_bundle_tool, inspect_execution_token_tool

def build_tool_registry() -> tuple[list[dict], dict[str, callable]]:
    """Returns (tool_definitions_for_api, {tool_name: executor_fn})."""
    schemas = []
    executors = {}
    for factory in [
        parse_hpl_tool, validate_hpl_tool, plan_hpl_tool, run_hpl_tool,
        list_hpl_stubs_tool, read_spec_folder_tool, diff_spec_impl_tool,
        verify_evidence_bundle_tool, inspect_execution_token_tool,
    ]:
        schema, executor = factory()
        schemas.append(schema)
        executors[schema["name"]] = executor
    return schemas, executors

ALL_TOOL_SCHEMAS, ALL_TOOL_EXECUTORS = build_tool_registry()
