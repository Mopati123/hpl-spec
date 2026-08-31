import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = str(ROOT / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from hpl.architecture import compile_architecture_spec, lower_architecture_ir_to_program_ir
from hpl.errors import ValidationError


def _spec(domain="trading"):
    return {
        "architecture_id": f"{domain}.reference.v1",
        "domain": domain,
        "states": [{"id": "domain_state"}],
        "observables": [{"id": "observe_state", "type": "measurement"}],
        "dynamics": [{"id": "evolve_state", "type": "evolution"}],
        "proposals": [{"id": "propose_transition", "type": "proposal"}],
        "constraints": [{"id": "project_admissibility", "type": "projector"}],
        "invariants": [{"id": "preserve_domain_invariant", "expression": "admissible == true"}],
        "authorities": [{"id": "scheduler_authority", "kind": "execution", "owner": "hpl.scheduler"}],
        "effects": [{"id": "commit_effect", "type": "effect"}],
        "evidence": [{"id": "emit_evidence", "type": "evidence"}],
        "reconciliation": [{"id": "reconcile_effect", "type": "reconciliation"}],
    }


class ArchitectureUniversalJoinTests(unittest.TestCase):
    def test_multiple_domains_lower_to_same_program_ir_contract(self):
        for domain in ("trading", "agriculture", "banking", "agent"):
            architecture_ir = compile_architecture_spec(_spec(domain))
            program_ir = lower_architecture_ir_to_program_ir(architecture_ir)
            self.assertEqual(program_ir["program_id"], f"{domain}.reference.v1")
            self.assertEqual(
                program_ir["scheduler"]["collapse_policy"],
                "architecture_ir_scheduler_sovereignty",
            )
            self.assertIn("project_admissibility", program_ir["operators"])
            self.assertIn("emit_evidence", program_ir["operators"])
            self.assertIn("reconcile_effect", program_ir["operators"])

    def test_domain_cannot_mint_execution_authority(self):
        spec = _spec()
        spec["authorities"][0]["owner"] = "domain.self"
        with self.assertRaises(ValidationError):
            compile_architecture_spec(spec)

    def test_evidence_and_reconciliation_are_mandatory(self):
        spec = _spec()
        spec["evidence"] = []
        with self.assertRaises(ValidationError):
            compile_architecture_spec(spec)
        spec = _spec()
        spec["reconciliation"] = []
        with self.assertRaises(ValidationError):
            compile_architecture_spec(spec)

    def test_lowering_is_deterministic(self):
        first = compile_architecture_spec(_spec())
        second = compile_architecture_spec(_spec())
        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertEqual(
            lower_architecture_ir_to_program_ir(first),
            lower_architecture_ir_to_program_ir(second),
        )


if __name__ == "__main__":
    unittest.main()
