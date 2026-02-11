from __future__ import annotations

from typing import Dict

from ..adapter import StubNetworkAdapter


class LocalLoopbackAdapter(StubNetworkAdapter):
    def __init__(self) -> None:
        super().__init__("local_loopback")

    def recv(self, endpoint: str, params: Dict[str, object]) -> Dict[str, object]:
        return {
            "status": "ok",
            "endpoint": endpoint,
            "adapter": "local_loopback",
            "message": {"kind": "loopback"},
            "mock": True,
        }
