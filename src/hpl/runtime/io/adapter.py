from __future__ import annotations

import os
from typing import Dict, Protocol


class BrokerAdapter(Protocol):
    def connect(self, endpoint: str, params: Dict[str, object]) -> Dict[str, object]:
        ...

    def submit_order(self, endpoint: str, order: Dict[str, object], params: Dict[str, object]) -> Dict[str, object]:
        ...

    def cancel_order(self, endpoint: str, order_id: str, params: Dict[str, object]) -> Dict[str, object]:
        ...

    def query_fills(self, endpoint: str, order_id: str, params: Dict[str, object]) -> Dict[str, object]:
        ...


class MockBrokerAdapter:
    def connect(self, endpoint: str, params: Dict[str, object]) -> Dict[str, object]:
        return {"status": "connected", "endpoint": endpoint, "mock": True}

    def submit_order(self, endpoint: str, order: Dict[str, object], params: Dict[str, object]) -> Dict[str, object]:
        order_id = order.get("order_id") or "mock-order"
        return {
            "status": "accepted",
            "endpoint": endpoint,
            "order_id": order_id,
            "mock": True,
        }

    def cancel_order(self, endpoint: str, order_id: str, params: Dict[str, object]) -> Dict[str, object]:
        return {
            "status": "cancelled",
            "endpoint": endpoint,
            "order_id": order_id,
            "mock": True,
        }

    def query_fills(self, endpoint: str, order_id: str, params: Dict[str, object]) -> Dict[str, object]:
        return {
            "status": "ok",
            "endpoint": endpoint,
            "order_id": order_id,
            "fills": [],
            "mock": True,
        }


class StubBrokerAdapter:
    def __init__(self, name: str) -> None:
        self._name = name
        if os.getenv("HPL_IO_ADAPTER_READY") != "1":
            raise RuntimeError(f"{name} adapter not configured")

    def connect(self, endpoint: str, params: Dict[str, object]) -> Dict[str, object]:
        return {
            "status": "accepted",
            "endpoint": endpoint,
            "adapter": self._name,
            "mock": True,
        }

    def submit_order(self, endpoint: str, order: Dict[str, object], params: Dict[str, object]) -> Dict[str, object]:
        return {
            "status": "accepted",
            "endpoint": endpoint,
            "adapter": self._name,
            "order_id": order.get("order_id") or "stub-order",
            "mock": True,
        }

    def cancel_order(self, endpoint: str, order_id: str, params: Dict[str, object]) -> Dict[str, object]:
        return {
            "status": "cancelled",
            "endpoint": endpoint,
            "adapter": self._name,
            "order_id": order_id,
            "mock": True,
        }

    def query_fills(self, endpoint: str, order_id: str, params: Dict[str, object]) -> Dict[str, object]:
        return {
            "status": "ok",
            "endpoint": endpoint,
            "adapter": self._name,
            "order_id": order_id,
            "fills": [],
            "mock": True,
        }


def load_adapter() -> BrokerAdapter:
    adapter_name = os.getenv("HPL_IO_ADAPTER", "mock").lower()
    if adapter_name == "mock":
        return MockBrokerAdapter()
    if adapter_name in {"mt5", "deriv", "tradingview"}:
        return StubBrokerAdapter(adapter_name)
    raise RuntimeError(f"unsupported io adapter: {adapter_name}")
