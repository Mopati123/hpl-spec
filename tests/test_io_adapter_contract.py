import unittest

from hpl.runtime.io.adapter import MockBrokerAdapter, StubBrokerAdapter
from hpl.runtime.io.adapter_contract import IOAdapterContract, validate_adapter_contract
from hpl.runtime.io.adapters.deriv import DerivAdapter
from hpl.runtime.io.adapters.mt5 import MT5Adapter
from hpl.runtime.io.adapters.tradingview import TradingViewAdapter


class IOAdapterContractTests(unittest.TestCase):
    def test_mock_adapter_conforms(self):
        adapter = MockBrokerAdapter()
        self.assertIsInstance(adapter, IOAdapterContract)
        validate_adapter_contract(adapter)

    def test_stub_adapter_conforms(self):
        # Instantiate without readiness to avoid side effects; just check type via class.
        self.assertTrue(issubclass(StubBrokerAdapter, IOAdapterContract))

    def test_named_adapters_conform(self):
        self.assertTrue(issubclass(MT5Adapter, IOAdapterContract))
        self.assertTrue(issubclass(DerivAdapter, IOAdapterContract))
        self.assertTrue(issubclass(TradingViewAdapter, IOAdapterContract))


if __name__ == "__main__":
    unittest.main()
