import unittest

from hpl.execution_token import ExecutionToken
from hpl.runtime.context import RuntimeContext
from hpl.runtime.contracts import ExecutionContract
from hpl.runtime.engine import RuntimeEngine


class NetTokenGateTests(unittest.TestCase):
    def test_net_token_deterministic(self):
        policy = {
            "net_mode": "dry_run",
            "net_caps": ["NET_CONNECT", "NET_SEND", "NET_RECV", "NET_CLOSE"],
            "net_endpoints_allowlist": ["wss://example.test/feed"],
            "net_budget_calls": 2,
            "net_timeout_ms": 2500,
            "net_nonce_policy": "HPL_DETERMINISTIC_NONCE_V1",
            "net_redaction_policy_id": "R1",
            "net_crypto_policy_id": "QKX1",
        }

        token_one = ExecutionToken.build(net_policy=policy)
        token_two = ExecutionToken.build(net_policy=policy)

        self.assertEqual(token_one.token_id, token_two.token_id)

    def test_net_permission_denied(self):
        policy = {
            "net_mode": "dry_run",
            "net_caps": [],
            "net_endpoints_allowlist": ["wss://example.test/feed"],
            "net_budget_calls": 2,
        }

        token = ExecutionToken.build(net_policy=policy)

        plan = {
            "status": "planned",
            "steps": [
                {
                    "step_id": "net_step",
                    "effect_type": "NET_CONNECT",
                    "args": {"endpoint": "wss://example.test/feed"},
                    "requires": {
                        "net_cap": "NET_CONNECT",
                        "net_endpoint": "wss://example.test/feed",
                    },
                }
            ],
            "execution_token": token.to_dict(),
        }

        ctx = RuntimeContext()
        contract = ExecutionContract(allowed_steps={"net_step"})
        result = RuntimeEngine().run(plan, ctx, contract)

        self.assertEqual(result.status, "denied")
        self.assertTrue(
            any("NETPermissionDenied" in reason for reason in result.reasons)
        )

    def test_net_endpoint_not_allowed(self):
        policy = {
            "net_mode": "dry_run",
            "net_caps": ["NET_CONNECT"],
            "net_endpoints_allowlist": ["wss://allowed.test/feed"],
            "net_budget_calls": 2,
        }

        token = ExecutionToken.build(net_policy=policy)

        plan = {
            "status": "planned",
            "steps": [
                {
                    "step_id": "net_step",
                    "effect_type": "NET_CONNECT",
                    "args": {"endpoint": "wss://blocked.test/feed"},
                    "requires": {
                        "net_cap": "NET_CONNECT",
                        "net_endpoint": "wss://blocked.test/feed",
                    },
                }
            ],
            "execution_token": token.to_dict(),
        }

        ctx = RuntimeContext()
        contract = ExecutionContract(allowed_steps={"net_step"})
        result = RuntimeEngine().run(plan, ctx, contract)

        self.assertEqual(result.status, "denied")
        self.assertTrue(
            any("NETEndpointNotAllowed" in reason for reason in result.reasons)
        )

    def test_net_budget_exceeded(self):
        policy = {
            "net_mode": "dry_run",
            "net_caps": ["NET_CONNECT"],
            "net_endpoints_allowlist": ["wss://example.test/feed"],
            "net_budget_calls": 0,
        }

        token = ExecutionToken.build(net_policy=policy)

        plan = {
            "status": "planned",
            "steps": [
                {
                    "step_id": "net_step",
                    "effect_type": "NET_CONNECT",
                    "args": {"endpoint": "wss://example.test/feed"},
                    "requires": {
                        "net_cap": "NET_CONNECT",
                        "net_endpoint": "wss://example.test/feed",
                    },
                }
            ],
            "execution_token": token.to_dict(),
        }

        ctx = RuntimeContext()
        contract = ExecutionContract(allowed_steps={"net_step"})
        result = RuntimeEngine().run(plan, ctx, contract)

        self.assertEqual(result.status, "denied")
        self.assertTrue(any("NETBudgetExceeded" in reason for reason in result.reasons))


if __name__ == "__main__":
    unittest.main()