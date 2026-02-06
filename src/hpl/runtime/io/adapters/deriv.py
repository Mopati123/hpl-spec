from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

from ..adapter import StubBrokerAdapter


def _require_env(name: str) -> str:
    value = os.getenv(name, "")
    if not value:
        raise RuntimeError(f"Missing env var: {name}")
    return value


def _safe_err(exc: Exception) -> str:
    return f"{type(exc).__name__}: {str(exc)[:200]}"


class DerivAdapter(StubBrokerAdapter):
    def __init__(self) -> None:
        super().__init__("deriv")
        _require_env("HPL_DERIV_ENDPOINT")
        _require_env("HPL_DERIV_TOKEN")
        try:
            import websocket  # noqa: F401
        except Exception as exc:
            raise RuntimeError("websocket-client not available") from exc

    def _endpoint(self) -> str:
        return _require_env("HPL_DERIV_ENDPOINT")

    def connect(self, endpoint: str, params: Dict[str, object]) -> Dict[str, Any]:
        token = _require_env("HPL_DERIV_TOKEN")
        url = self._endpoint()
        try:
            import websocket  # type: ignore
        except Exception as exc:
            return {"status": "error", "error": _safe_err(exc)}
        ws = None
        try:
            ws = websocket.create_connection(url, timeout=10)
            ws.send(json.dumps({"authorize": token}))
            resp = json.loads(ws.recv())
            if "error" in resp:
                return {"status": "error", "error": "deriv_authorize_failed", "code": resp["error"].get("code")}
            auth = resp.get("authorize", {})
            return {
                "status": "ok",
                "account": {
                    "loginid": auth.get("loginid"),
                    "currency": auth.get("currency"),
                },
            }
        except Exception as exc:
            return {"status": "error", "error": _safe_err(exc)}
        finally:
            if ws is not None:
                try:
                    ws.close()
                except Exception:
                    pass

    def submit_order(self, endpoint: str, order: Dict[str, object], params: Dict[str, object]) -> Dict[str, Any]:
        token = _require_env("HPL_DERIV_TOKEN")
        url = self._endpoint()
        try:
            import websocket  # type: ignore
        except Exception as exc:
            return {"status": "error", "error": _safe_err(exc)}
        ws = None
        try:
            ws = websocket.create_connection(url, timeout=10)
            ws.send(json.dumps({"authorize": token}))
            auth_resp = json.loads(ws.recv())
            if "error" in auth_resp:
                return {"status": "error", "error": "deriv_authorize_failed", "code": auth_resp["error"].get("code")}
            ws.send(json.dumps(dict(order)))
            resp = json.loads(ws.recv())
            if "error" in resp:
                return {"status": "error", "error": "deriv_order_failed", "code": resp["error"].get("code")}
            return {"status": "ok", "response": {"msg_type": resp.get("msg_type")}}
        except Exception as exc:
            return {"status": "error", "error": _safe_err(exc)}
        finally:
            if ws is not None:
                try:
                    ws.close()
                except Exception:
                    pass

    def cancel_order(self, endpoint: str, order_id: str, params: Dict[str, object]) -> Dict[str, Any]:
        request = {"cancel": int(order_id)}
        return self.submit_order(endpoint, request, params)

    def query_fills(self, endpoint: str, order_id: str, params: Dict[str, object]) -> Dict[str, Any]:
        if not isinstance(params, dict) or "request" not in params:
            return {"status": "error", "error": "missing_request"}
        request = params["request"]
        if not isinstance(request, dict):
            return {"status": "error", "error": "missing_request"}
        return self.submit_order(endpoint, request, {})
