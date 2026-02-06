from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from ..adapter import StubBrokerAdapter


def _require_env(name: str) -> str:
    value = os.getenv(name, "")
    if not value:
        raise RuntimeError(f"Missing env var: {name}")
    return value


def _safe_err(exc: Exception) -> str:
    return f"{type(exc).__name__}: {str(exc)[:200]}"


class MT5Adapter(StubBrokerAdapter):
    def __init__(self) -> None:
        super().__init__("mt5")
        _require_env("HPL_MT5_LOGIN")
        _require_env("HPL_MT5_PASSWORD")
        _require_env("HPL_MT5_SERVER")
        try:
            import MetaTrader5  # noqa: F401
        except Exception as exc:
            raise RuntimeError("MetaTrader5 package not available") from exc

    def connect(self, endpoint: str, params: Dict[str, object]) -> Dict[str, object]:
        try:
            import MetaTrader5 as mt5  # type: ignore
        except Exception as exc:
            return {"status": "error", "error": _safe_err(exc)}
        login_raw = _require_env("HPL_MT5_LOGIN")
        try:
            login = int(login_raw)
        except ValueError:
            return {"status": "error", "error": "mt5_login_invalid"}
        password = _require_env("HPL_MT5_PASSWORD")
        server = _require_env("HPL_MT5_SERVER")
        path = os.getenv("HPL_MT5_PATH")
        ok = mt5.initialize(path=path) if path else mt5.initialize()
        if not ok:
            return {"status": "error", "error": "mt5_initialize_failed"}
        authorized = mt5.login(login=login, password=password, server=server)
        if not authorized:
            return {"status": "error", "error": "mt5_login_failed"}
        info = mt5.account_info()
        return {
            "status": "ok",
            "account": {
                "login": info.login if info else None,
                "server": server,
                "currency": info.currency if info else None,
                "balance": float(info.balance) if info else None,
                "equity": float(info.equity) if info else None,
            },
        }

    def submit_order(self, endpoint: str, order: Dict[str, object], params: Dict[str, object]) -> Dict[str, object]:
        try:
            import MetaTrader5 as mt5  # type: ignore
        except Exception as exc:
            return {"status": "error", "error": _safe_err(exc)}
        try:
            result = mt5.order_send(dict(order))
            if result is None:
                return {"status": "error", "error": "mt5_order_send_returned_none"}
            if result.retcode not in (mt5.TRADE_RETCODE_DONE, mt5.TRADE_RETCODE_PLACED):
                return {
                    "status": "error",
                    "error": "mt5_order_rejected",
                    "retcode": int(result.retcode),
                    "comment": (result.comment or "")[:200],
                }
            return {
                "status": "ok",
                "order_id": int(getattr(result, "order", 0) or 0),
                "deal_id": int(getattr(result, "deal", 0) or 0),
                "retcode": int(result.retcode),
            }
        except Exception as exc:
            return {"status": "error", "error": _safe_err(exc)}

    def cancel_order(self, endpoint: str, order_id: str, params: Dict[str, object]) -> Dict[str, object]:
        try:
            import MetaTrader5 as mt5  # type: ignore
        except Exception as exc:
            return {"status": "error", "error": _safe_err(exc)}
        request = {"action": mt5.TRADE_ACTION_REMOVE, "order": int(order_id)}
        try:
            result = mt5.order_send(request)
            if result is None:
                return {"status": "error", "error": "mt5_cancel_returned_none"}
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return {
                    "status": "error",
                    "error": "mt5_cancel_failed",
                    "retcode": int(result.retcode),
                    "comment": (result.comment or "")[:200],
                }
            return {"status": "ok", "order_id": str(order_id)}
        except Exception as exc:
            return {"status": "error", "error": _safe_err(exc)}

    def query_fills(self, endpoint: str, order_id: str, params: Dict[str, object]) -> Dict[str, object]:
        try:
            import MetaTrader5 as mt5  # type: ignore
        except Exception as exc:
            return {"status": "error", "error": _safe_err(exc)}
        if not isinstance(params, dict) or "from" not in params or "to" not in params:
            return {"status": "error", "error": "missing_time_window"}
        from_dt = params["from"]
        to_dt = params["to"]
        try:
            deals = mt5.history_deals_get(from_dt, to_dt) or []
            fills: List[Dict[str, object]] = []
            for deal in deals:
                fills.append(
                    {
                        "deal_id": int(deal.ticket),
                        "order_id": int(deal.order),
                        "symbol": deal.symbol,
                        "volume": float(deal.volume),
                        "price": float(deal.price),
                        "time": int(deal.time),
                        "type": int(deal.type),
                    }
                )
            return {"status": "ok", "fills": fills}
        except Exception as exc:
            return {"status": "error", "error": _safe_err(exc)}
