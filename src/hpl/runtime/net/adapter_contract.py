from __future__ import annotations

from typing import Dict, Protocol


class NetworkAdapterContract(Protocol):
    def connect(self, endpoint: str, params: Dict[str, object]) -> Dict[str, object]:
        ...

    def handshake(self, endpoint: str, params: Dict[str, object]) -> Dict[str, object]:
        ...

    def key_exchange(self, endpoint: str, params: Dict[str, object]) -> Dict[str, object]:
        ...

    def send(self, endpoint: str, payload: Dict[str, object], params: Dict[str, object]) -> Dict[str, object]:
        ...

    def recv(self, endpoint: str, params: Dict[str, object]) -> Dict[str, object]:
        ...

    def close(self, endpoint: str, params: Dict[str, object]) -> Dict[str, object]:
        ...
