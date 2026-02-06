from __future__ import annotations

from ..adapter import StubBrokerAdapter


class MT5Adapter(StubBrokerAdapter):
    def __init__(self) -> None:
        super().__init__("mt5")
