from __future__ import annotations

from ..adapter import StubBrokerAdapter


class TradingViewAdapter(StubBrokerAdapter):
    def __init__(self) -> None:
        super().__init__("tradingview")
