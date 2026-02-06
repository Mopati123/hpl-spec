from __future__ import annotations

from ..adapter import StubBrokerAdapter


class DerivAdapter(StubBrokerAdapter):
    def __init__(self) -> None:
        super().__init__("deriv")
