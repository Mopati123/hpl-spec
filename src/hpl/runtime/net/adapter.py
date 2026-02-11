from __future__ import annotations

import os
from typing import Dict

from .adapter_contract import NetworkAdapterContract


class MockNetworkAdapter(NetworkAdapterContract):
    def connect(self, endpoint: str, params: Dict[str, object]) -> Dict[str, object]:
        return {"status": "connected", "endpoint": endpoint, "mock": True}

    def handshake(self, endpoint: str, params: Dict[str, object]) -> Dict[str, object]:
        return {"status": "ok", "endpoint": endpoint, "handshake": "mock", "mock": True}

    def key_exchange(self, endpoint: str, params: Dict[str, object]) -> Dict[str, object]:
        return {"status": "ok", "endpoint": endpoint, "key_fingerprint": "mock", "mock": True}

    def send(self, endpoint: str, payload: Dict[str, object], params: Dict[str, object]) -> Dict[str, object]:
        return {"status": "sent", "endpoint": endpoint, "msg_id": payload.get("request_id"), "mock": True}

    def recv(self, endpoint: str, params: Dict[str, object]) -> Dict[str, object]:
        return {"status": "ok", "endpoint": endpoint, "message": {"kind": "mock"}, "mock": True}

    def close(self, endpoint: str, params: Dict[str, object]) -> Dict[str, object]:
        return {"status": "closed", "endpoint": endpoint, "mock": True}


class StubNetworkAdapter(NetworkAdapterContract):
    def __init__(self, name: str) -> None:
        self._name = name
        if os.getenv("HPL_NET_ADAPTER_READY") != "1":
            raise RuntimeError(f"{name} adapter not configured")

    def connect(self, endpoint: str, params: Dict[str, object]) -> Dict[str, object]:
        return {"status": "connected", "endpoint": endpoint, "adapter": self._name, "mock": True}

    def handshake(self, endpoint: str, params: Dict[str, object]) -> Dict[str, object]:
        return {"status": "ok", "endpoint": endpoint, "adapter": self._name, "mock": True}

    def key_exchange(self, endpoint: str, params: Dict[str, object]) -> Dict[str, object]:
        return {"status": "ok", "endpoint": endpoint, "adapter": self._name, "mock": True}

    def send(self, endpoint: str, payload: Dict[str, object], params: Dict[str, object]) -> Dict[str, object]:
        return {"status": "sent", "endpoint": endpoint, "adapter": self._name, "mock": True}

    def recv(self, endpoint: str, params: Dict[str, object]) -> Dict[str, object]:
        return {"status": "ok", "endpoint": endpoint, "adapter": self._name, "mock": True}

    def close(self, endpoint: str, params: Dict[str, object]) -> Dict[str, object]:
        return {"status": "closed", "endpoint": endpoint, "adapter": self._name, "mock": True}


def load_adapter() -> NetworkAdapterContract:
    adapter_name = os.getenv("HPL_NET_ADAPTER", "mock").lower()
    if adapter_name == "mock":
        return MockNetworkAdapter()
    if adapter_name == "ws":
        from .adapters.ws import WebSocketAdapter

        return WebSocketAdapter()
    if adapter_name == "local":
        from .adapters.local_loopback import LocalLoopbackAdapter

        return LocalLoopbackAdapter()
    raise RuntimeError(f"unsupported net adapter: {adapter_name}")
