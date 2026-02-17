import unittest

from hpl.runtime.invoker import CANONICAL_EQ09, CANONICAL_EQ15, invoke_operator


class OperatorAllowlistInvokerTests(unittest.TestCase):
    def test_canonical_invocation_deterministic(self):
        payload = {"prices": [1.0, 1.1, 1.2], "symbol": "DEMO"}
        result_one = invoke_operator(CANONICAL_EQ09, payload, allowlist=[CANONICAL_EQ09])
        result_two = invoke_operator(CANONICAL_EQ09, payload, allowlist=[CANONICAL_EQ09])
        self.assertEqual(result_one, result_two)
        self.assertEqual(result_one["equation_id"], "EQ09")

    def test_eq15_outputs_admissibility_certificate(self):
        payload = {"entropy_threshold": 0.95, "signal": {"action": "BUY"}}
        result = invoke_operator(CANONICAL_EQ15, payload, allowlist=[CANONICAL_EQ15])
        self.assertEqual(result["equation_id"], "EQ15")
        self.assertIn("admissibility_certificate", result)
        self.assertIn("ok", result["admissibility_certificate"])

    def test_operator_refused_when_not_allowlisted(self):
        payload = {"prices": [1.0, 1.1]}
        with self.assertRaises(PermissionError):
            invoke_operator(CANONICAL_EQ09, payload, allowlist=[CANONICAL_EQ15])


if __name__ == "__main__":
    unittest.main()
