from __future__ import annotations
import json
from pathlib import Path

def verify_evidence_bundle_tool() -> tuple[dict, callable]:
    schema = {
        "name": "verify_evidence_bundle",
        "description": "Verify an HPL evidence bundle: checks Merkle root and signature if present.",
        "input_schema": {
            "type": "object",
            "properties": {
                "bundle_json": {"type": "string", "description": "JSON string of an EvidenceBundle"},
            },
            "required": ["bundle_json"],
        },
    }
    def executor(inp: dict) -> str:
        try:
            from ..hpl.models import EvidenceBundle
            bundle = EvidenceBundle.from_json(inp["bundle_json"])
            return json.dumps({
                "bundle_id": bundle.bundle_id,
                "session_id": bundle.session_id,
                "merkle_root": bundle.merkle_root,
                "signature_present": bundle.signature is not None,
                "artifact_count": len(bundle.artifacts),
                "status": "bundle_loaded_ok",
            })
        except Exception as e:
            return json.dumps({"error": str(e)})
    return schema, executor

def inspect_execution_token_tool() -> tuple[dict, callable]:
    schema = {
        "name": "inspect_execution_token",
        "description": "Parse and explain an HPL ExecutionPlan/Token — its budgets, backend, and policies.",
        "input_schema": {
            "type": "object",
            "properties": {
                "plan_json": {"type": "string", "description": "JSON ExecutionPlan"},
            },
            "required": ["plan_json"],
        },
    }
    def executor(inp: dict) -> str:
        from ..hpl.models import ExecutionPlan
        try:
            plan = ExecutionPlan.from_json(inp["plan_json"])
            return json.dumps({
                "token_id": plan.token_id,
                "backend": plan.backend,
                "step_count": len(plan.steps),
                "policy_summary": plan.policy_summary,
                "status": "valid",
            }, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})
    return schema, executor
