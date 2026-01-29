import json
import unittest
from pathlib import Path

from hpl.runtime.effects.measurement_selection import (
    TRACK_PUBLISH,
    TRACK_REGULATOR,
    build_measurement_selection,
)


FIXTURES = Path(__file__).resolve().parents[0] / "fixtures"


class MeasurementSelectionTests(unittest.TestCase):
    def test_selection_id_deterministic(self):
        boundary = {"ci_available": True}
        first = build_measurement_selection(boundary)
        second = build_measurement_selection(boundary)
        self.assertTrue(first.ok)
        self.assertTrue(second.ok)
        self.assertEqual(first.selection["selection_id"], second.selection["selection_id"])
        self.assertEqual(first.selection, second.selection)

    def test_select_publish_track(self):
        boundary = json.loads((FIXTURES / "ecmo_boundary_ci.json").read_text(encoding="utf-8"))
        result = build_measurement_selection(boundary)
        self.assertTrue(result.ok)
        self.assertEqual(result.selection["selected_track"], TRACK_PUBLISH)

    def test_select_regulator_track(self):
        boundary = json.loads((FIXTURES / "ecmo_boundary_regulator.json").read_text(encoding="utf-8"))
        result = build_measurement_selection(boundary)
        self.assertTrue(result.ok)
        self.assertEqual(result.selection["selected_track"], TRACK_REGULATOR)

    def test_ambiguous_refusal(self):
        boundary = json.loads((FIXTURES / "ecmo_boundary_ambiguous.json").read_text(encoding="utf-8"))
        result = build_measurement_selection(boundary)
        self.assertFalse(result.ok)
        self.assertIsNone(result.selection)
        self.assertTrue(result.errors)
