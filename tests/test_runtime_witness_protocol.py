import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = str(ROOT / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from hpl import scheduler
from hpl.runtime.context import RuntimeContext
from hpl.runtime.contracts import ExecutionContract
from hpl.runtime.engine import RuntimeEngine
from hpl.runtime.witness_protocol import (
    RUNTIME_WITNESS_PROTOCOL_ID,
    RUNTIME_WITNESS_PROTOCOL_VERSION,
    RuntimeWitnessStage,
    resolve_runtime_witness_contract,
    runtime_witness_catalog,
    validate_runtime_witness_pair,
    validate_runtime_witness_record,
)


def _sample_program_ir():
    return {
        "program_id": "runtime_witness_protocol_test",
        "hamiltonian": {
            "terms": [
                {"operator_id": "SURF_A", "cls": "C", "coefficient": 1.0},
                {"operator_id": "SURF_B", "cls": "C", "coefficient": 2.0},
            ]
        },
        "operators": {
            "SURF_A": {"type": "unspecified", "commutes_with": [], "backend_map": []},
            "SURF_B": {"type": "unspecified", "commutes_with": [], "backend_map": []},
        },
        "invariants": [],
        "scheduler": {"collapse_policy": "unspecified", "authorized_observers": []},
    }


def _build_plan():
    return scheduler.plan(_sample_program_ir(), scheduler.SchedulerContext())


class RuntimeWitnessProtocolTests(unittest.TestCase):
    def test_protocol_identity_is_frozen(self):
        self.assertEqual(RUNTIME_WITNESS_PROTOCOL_ID, "hpl.runtime-witness")
        self.assertEqual(RUNTIME_WITNESS_PROTOCOL_VERSION, "1.0.0")

    def test_catalog_has_unique_typed_stage_contracts(self):
        catalog = runtime_witness_catalog()
        self.assertEqual(set(catalog), {stage.value for stage in RuntimeWitnessStage})
        for stage, entry in catalog.items():
            contract = resolve_runtime_witness_contract(stage)
            self.assertEqual(entry["attestation"], contract.attestation)

    def test_unknown_stage_is_refused(self):
        with self.assertRaisesRegex(ValueError, "unknown runtime witness stage"):
            resolve_runtime_witness_contract("runtime_finished_maybe")

    def test_attestation_drift_is_refused(self):
        with self.assertRaisesRegex(ValueError, "attestation mismatch"):
            validate_runtime_witness_pair(
                RuntimeWitnessStage.RUNTIME_TERMINAL,
                "execution_completed_witness",
            )

    def test_success_runtime_records_conform_to_protocol(self):
        result = RuntimeEngine().run(
            _build_plan(),
            RuntimeContext(),
            ExecutionContract(allowed_steps={"SURF_A", "SURF_B"}),
        )
        self.assertEqual(result.status, "completed")
        contracts = [validate_runtime_witness_record(record) for record in result.witness_records]
        stages = {contract.stage for contract in contracts}
        self.assertIn(RuntimeWitnessStage.RUNTIME_TERMINAL, stages)
        self.assertIn(RuntimeWitnessStage.RUNTIME_COMPLETE, stages)
        self.assertIn(RuntimeWitnessStage.EXECUTION_COMPLETED, stages)
        self.assertTrue(
            resolve_runtime_witness_contract(RuntimeWitnessStage.RUNTIME_COMPLETE).legacy
        )

    def test_denied_runtime_is_terminal_but_not_completed(self):
        result = RuntimeEngine().run(
            _build_plan(),
            RuntimeContext(),
            ExecutionContract(allowed_steps={"SURF_B"}),
        )
        self.assertEqual(result.status, "denied")
        contracts = [validate_runtime_witness_record(record) for record in result.witness_records]
        stages = {contract.stage for contract in contracts}
        self.assertIn(RuntimeWitnessStage.RUNTIME_TERMINAL, stages)
        self.assertNotIn(RuntimeWitnessStage.RUNTIME_COMPLETE, stages)
        self.assertNotIn(RuntimeWitnessStage.EXECUTION_COMPLETED, stages)
        self.assertTrue(
            resolve_runtime_witness_contract(RuntimeWitnessStage.RUNTIME_TERMINAL).terminal
        )


if __name__ == "__main__":
    unittest.main()
