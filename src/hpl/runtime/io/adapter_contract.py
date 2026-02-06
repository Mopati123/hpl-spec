from __future__ import annotations

from typing import Dict, Protocol, runtime_checkable


@runtime_checkable
class IOAdapterContract(Protocol):
    """
    IO adapter contract. Implementations must be deterministic for the same inputs,
    return sanitized payloads only, and refuse when not configured/readiness-gated.
    """

    def connect(self, endpoint: str, params: Dict[str, object]) -> Dict[str, object]:
        ...

    def submit_order(self, endpoint: str, order: Dict[str, object], params: Dict[str, object]) -> Dict[str, object]:
        ...

    def cancel_order(self, endpoint: str, order_id: str, params: Dict[str, object]) -> Dict[str, object]:
        ...

    def query_fills(self, endpoint: str, order_id: str, params: Dict[str, object]) -> Dict[str, object]:
        ...


def validate_adapter_contract(adapter: object) -> None:
    if not isinstance(adapter, IOAdapterContract):
        raise TypeError("adapter does not implement IOAdapterContract")
