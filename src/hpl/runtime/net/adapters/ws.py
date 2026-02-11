from __future__ import annotations

from typing import Dict

from ..adapter import StubNetworkAdapter


class WebSocketAdapter(StubNetworkAdapter):
    def __init__(self) -> None:
        super().__init__("websocket")

    def handshake(self, endpoint: str, params: Dict[str, object]) -> Dict[str, object]:
        return {
            "status": "ok",
            "endpoint": endpoint,
            "adapter": "websocket",
            "mock": True,
        }
