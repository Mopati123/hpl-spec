"""Extended tests for IO and NET adapters covering previously missed lines."""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = str(ROOT / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _set_env(**kwargs):
    """Set os.environ keys from kwargs, return previous values for restoration."""
    prev = {}
    for k, v in kwargs.items():
        prev[k] = os.environ.get(k)
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    return prev


def _restore_env(prev):
    for k, v in prev.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


# ===========================================================================
# deriv.py helper functions
# ===========================================================================

class TestDerivHelpers(unittest.TestCase):
    def test_require_env_present(self):
        from hpl.runtime.io.adapters.deriv import _require_env
        prev = _set_env(HPL_TEST_DERIV_VAR="hello")
        try:
            self.assertEqual(_require_env("HPL_TEST_DERIV_VAR"), "hello")
        finally:
            _restore_env(prev)

    def test_require_env_missing_raises(self):
        from hpl.runtime.io.adapters.deriv import _require_env
        prev = _set_env(HPL_TEST_DERIV_MISSING=None)
        try:
            with self.assertRaises(RuntimeError):
                _require_env("HPL_TEST_DERIV_MISSING")
        finally:
            _restore_env(prev)

    def test_safe_err_formats(self):
        from hpl.runtime.io.adapters.deriv import _safe_err
        msg = _safe_err(ValueError("boom"))
        self.assertIn("ValueError", msg)
        self.assertIn("boom", msg)


# ===========================================================================
# DerivAdapter – constructor
# ===========================================================================

class TestDerivAdapterInit(unittest.TestCase):
    def setUp(self):
        self._env = dict(os.environ)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env)

    def _set_ready_env(self):
        os.environ["HPL_IO_ADAPTER_READY"] = "1"
        os.environ["HPL_DERIV_ENDPOINT"] = "wss://ws.binaryws.com/websockets/v3"
        os.environ["HPL_DERIV_TOKEN"] = "tok123"

    def test_init_missing_endpoint_raises(self):
        os.environ["HPL_IO_ADAPTER_READY"] = "1"
        os.environ.pop("HPL_DERIV_ENDPOINT", None)
        os.environ.pop("HPL_DERIV_TOKEN", None)
        from hpl.runtime.io.adapters import deriv as deriv_mod
        with self.assertRaises(RuntimeError):
            deriv_mod.DerivAdapter()

    def test_init_missing_token_raises(self):
        os.environ["HPL_IO_ADAPTER_READY"] = "1"
        os.environ["HPL_DERIV_ENDPOINT"] = "wss://example.com"
        os.environ.pop("HPL_DERIV_TOKEN", None)
        with patch.dict("sys.modules", {"websocket": MagicMock()}):
            from hpl.runtime.io.adapters import deriv as deriv_mod
            import importlib
            importlib.reload(deriv_mod)
            with self.assertRaises(RuntimeError):
                deriv_mod.DerivAdapter()

    def test_init_missing_websocket_raises(self):
        self._set_ready_env()
        with patch.dict("sys.modules", {"websocket": None}):
            from hpl.runtime.io.adapters import deriv as deriv_mod
            import importlib
            importlib.reload(deriv_mod)
            with self.assertRaises(RuntimeError):
                deriv_mod.DerivAdapter()

    def test_init_success(self):
        self._set_ready_env()
        ws_mock = MagicMock()
        with patch.dict("sys.modules", {"websocket": ws_mock}):
            from hpl.runtime.io.adapters import deriv as deriv_mod
            import importlib
            importlib.reload(deriv_mod)
            adapter = deriv_mod.DerivAdapter()
            self.assertIsNotNone(adapter)


# ===========================================================================
# DerivAdapter – connect / submit_order / cancel_order / query_fills
# ===========================================================================

class TestDerivAdapterMethods(unittest.TestCase):
    """Tests for DerivAdapter methods, keeping sys.modules patched during calls."""

    def setUp(self):
        self._env = dict(os.environ)
        os.environ["HPL_IO_ADAPTER_READY"] = "1"
        os.environ["HPL_DERIV_ENDPOINT"] = "wss://ws.binaryws.com/websockets/v3"
        os.environ["HPL_DERIV_TOKEN"] = "tok123"

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env)

    def _make_adapter_and_run(self, ws_mod, method, *args):
        """Build an adapter and call *method* while the websocket mock is active."""
        import importlib
        with patch.dict("sys.modules", {"websocket": ws_mod}):
            from hpl.runtime.io.adapters import deriv as deriv_mod
            importlib.reload(deriv_mod)
            adapter = deriv_mod.DerivAdapter()
            return getattr(adapter, method)(*args)

    def test_connect_success(self):
        import json
        ws_mod = MagicMock()
        ws_conn = MagicMock()
        ws_conn.recv.return_value = json.dumps({
            "authorize": {"loginid": "CR12345", "currency": "USD"}
        })
        ws_mod.create_connection.return_value = ws_conn
        result = self._make_adapter_and_run(ws_mod, "connect", "wss://example.com", {})
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["account"]["loginid"], "CR12345")

    def test_connect_auth_error(self):
        import json
        ws_mod = MagicMock()
        ws_conn = MagicMock()
        ws_conn.recv.return_value = json.dumps({
            "error": {"code": "AuthorizationRequired", "message": "bad token"}
        })
        ws_mod.create_connection.return_value = ws_conn
        result = self._make_adapter_and_run(ws_mod, "connect", "wss://example.com", {})
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"], "deriv_authorize_failed")

    def test_connect_exception(self):
        ws_mod = MagicMock()
        ws_mod.create_connection.side_effect = ConnectionError("refused")
        result = self._make_adapter_and_run(ws_mod, "connect", "wss://example.com", {})
        self.assertEqual(result["status"], "error")
        self.assertIn("ConnectionError", result["error"])

    def test_connect_ws_close_exception_suppressed(self):
        """ws.close() raising should not propagate – covered by finally block."""
        import json
        ws_mod = MagicMock()
        ws_conn = MagicMock()
        ws_conn.recv.return_value = json.dumps({"authorize": {}})
        ws_conn.close.side_effect = OSError("close failed")
        ws_mod.create_connection.return_value = ws_conn
        result = self._make_adapter_and_run(ws_mod, "connect", "wss://example.com", {})
        self.assertEqual(result["status"], "ok")

    def test_submit_order_success(self):
        import json
        ws_mod = MagicMock()
        ws_conn = MagicMock()
        ws_conn.recv.side_effect = [
            json.dumps({"authorize": {"loginid": "CR1"}}),
            json.dumps({"msg_type": "buy", "buy": {"contract_id": 99}}),
        ]
        ws_mod.create_connection.return_value = ws_conn
        result = self._make_adapter_and_run(
            ws_mod, "submit_order", "wss://example.com", {"buy": "R_100", "price": 10}, {}
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["response"]["msg_type"], "buy")

    def test_submit_order_auth_error(self):
        import json
        ws_mod = MagicMock()
        ws_conn = MagicMock()
        ws_conn.recv.return_value = json.dumps({"error": {"code": "BadToken"}})
        ws_mod.create_connection.return_value = ws_conn
        result = self._make_adapter_and_run(
            ws_mod, "submit_order", "wss://example.com", {"buy": "R_100"}, {}
        )
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"], "deriv_authorize_failed")

    def test_submit_order_order_error(self):
        import json
        ws_mod = MagicMock()
        ws_conn = MagicMock()
        ws_conn.recv.side_effect = [
            json.dumps({"authorize": {"loginid": "CR1"}}),
            json.dumps({"error": {"code": "ContractBuyError"}}),
        ]
        ws_mod.create_connection.return_value = ws_conn
        result = self._make_adapter_and_run(
            ws_mod, "submit_order", "wss://example.com", {"buy": "R_100"}, {}
        )
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"], "deriv_order_failed")

    def test_submit_order_exception(self):
        ws_mod = MagicMock()
        ws_mod.create_connection.side_effect = TimeoutError("timed out")
        result = self._make_adapter_and_run(ws_mod, "submit_order", "wss://example.com", {}, {})
        self.assertEqual(result["status"], "error")

    def test_submit_order_close_exception_suppressed(self):
        import json
        ws_mod = MagicMock()
        ws_conn = MagicMock()
        ws_conn.recv.side_effect = [
            json.dumps({"authorize": {}}),
            json.dumps({"msg_type": "buy"}),
        ]
        ws_conn.close.side_effect = OSError("close bad")
        ws_mod.create_connection.return_value = ws_conn
        result = self._make_adapter_and_run(ws_mod, "submit_order", "wss://example.com", {}, {})
        self.assertEqual(result["status"], "ok")

    def test_cancel_order_delegates_to_submit(self):
        import json
        ws_mod = MagicMock()
        ws_conn = MagicMock()
        ws_conn.recv.side_effect = [
            json.dumps({"authorize": {}}),
            json.dumps({"msg_type": "cancel"}),
        ]
        ws_mod.create_connection.return_value = ws_conn
        result = self._make_adapter_and_run(
            ws_mod, "cancel_order", "wss://example.com", "12345", {}
        )
        self.assertEqual(result["status"], "ok")

    def test_query_fills_missing_request_key(self):
        ws_mod = MagicMock()
        result = self._make_adapter_and_run(
            ws_mod, "query_fills", "wss://example.com", "oid", {"no_request": True}
        )
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"], "missing_request")

    def test_query_fills_missing_params(self):
        ws_mod = MagicMock()
        result = self._make_adapter_and_run(
            ws_mod, "query_fills", "wss://example.com", "oid", "not_a_dict"
        )
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"], "missing_request")

    def test_query_fills_non_dict_request(self):
        ws_mod = MagicMock()
        result = self._make_adapter_and_run(
            ws_mod, "query_fills", "wss://example.com", "oid", {"request": "notadict"}
        )
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"], "missing_request")

    def test_query_fills_success(self):
        import json
        ws_mod = MagicMock()
        ws_conn = MagicMock()
        ws_conn.recv.side_effect = [
            json.dumps({"authorize": {}}),
            json.dumps({"msg_type": "profit_table"}),
        ]
        ws_mod.create_connection.return_value = ws_conn
        result = self._make_adapter_and_run(
            ws_mod, "query_fills", "wss://example.com", "oid", {"request": {"profit_table": 1}}
        )
        self.assertEqual(result["status"], "ok")


# ===========================================================================
# mt5.py helper functions
# ===========================================================================

class TestMT5Helpers(unittest.TestCase):
    def test_require_env_present(self):
        from hpl.runtime.io.adapters.mt5 import _require_env
        prev = _set_env(HPL_TEST_MT5_VAR="world")
        try:
            self.assertEqual(_require_env("HPL_TEST_MT5_VAR"), "world")
        finally:
            _restore_env(prev)

    def test_require_env_missing_raises(self):
        from hpl.runtime.io.adapters.mt5 import _require_env
        prev = _set_env(HPL_TEST_MT5_MISSING=None)
        try:
            with self.assertRaises(RuntimeError):
                _require_env("HPL_TEST_MT5_MISSING")
        finally:
            _restore_env(prev)

    def test_safe_err(self):
        from hpl.runtime.io.adapters.mt5 import _safe_err
        msg = _safe_err(TypeError("bad type"))
        self.assertIn("TypeError", msg)


# ===========================================================================
# MT5Adapter – constructor
# ===========================================================================

class TestMT5AdapterInit(unittest.TestCase):
    def setUp(self):
        self._env = dict(os.environ)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env)

    def _set_ready_env(self):
        os.environ["HPL_IO_ADAPTER_READY"] = "1"
        os.environ["HPL_MT5_LOGIN"] = "12345"
        os.environ["HPL_MT5_PASSWORD"] = "pass"
        os.environ["HPL_MT5_SERVER"] = "Demo-Server"

    def test_init_missing_login_raises(self):
        os.environ["HPL_IO_ADAPTER_READY"] = "1"
        os.environ.pop("HPL_MT5_LOGIN", None)
        mt5_mod = MagicMock()
        with patch.dict("sys.modules", {"MetaTrader5": mt5_mod}):
            from hpl.runtime.io.adapters import mt5 as mt5_adapter
            import importlib
            importlib.reload(mt5_adapter)
            with self.assertRaises(RuntimeError):
                mt5_adapter.MT5Adapter()

    def test_init_missing_mt5_package_raises(self):
        self._set_ready_env()
        with patch.dict("sys.modules", {"MetaTrader5": None}):
            from hpl.runtime.io.adapters import mt5 as mt5_adapter
            import importlib
            importlib.reload(mt5_adapter)
            with self.assertRaises(RuntimeError):
                mt5_adapter.MT5Adapter()

    def test_init_success(self):
        self._set_ready_env()
        mt5_mod = MagicMock()
        with patch.dict("sys.modules", {"MetaTrader5": mt5_mod}):
            from hpl.runtime.io.adapters import mt5 as mt5_adapter
            import importlib
            importlib.reload(mt5_adapter)
            adapter = mt5_adapter.MT5Adapter()
            self.assertIsNotNone(adapter)


# ===========================================================================
# MT5Adapter – connect
# ===========================================================================

class TestMT5AdapterConnect(unittest.TestCase):
    def setUp(self):
        self._env = dict(os.environ)
        os.environ["HPL_IO_ADAPTER_READY"] = "1"
        os.environ["HPL_MT5_LOGIN"] = "12345"
        os.environ["HPL_MT5_PASSWORD"] = "pass"
        os.environ["HPL_MT5_SERVER"] = "Demo-Server"

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env)

    def _make_adapter(self, mt5_mod):
        from hpl.runtime.io.adapters import mt5 as mt5_adapter
        import importlib
        with patch.dict("sys.modules", {"MetaTrader5": mt5_mod}):
            importlib.reload(mt5_adapter)
            return mt5_adapter.MT5Adapter(), mt5_adapter

    def test_connect_success_with_account_info(self):
        mt5_mod = MagicMock()
        mt5_mod.initialize.return_value = True
        mt5_mod.login.return_value = True
        info = MagicMock()
        info.login = 12345
        info.currency = "USD"
        info.balance = 1000.0
        info.equity = 1000.0
        mt5_mod.account_info.return_value = info
        adapter, _ = self._make_adapter(mt5_mod)
        with patch.dict("sys.modules", {"MetaTrader5": mt5_mod}):
            result = adapter.connect("demo", {})
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["account"]["login"], 12345)

    def test_connect_success_no_account_info(self):
        mt5_mod = MagicMock()
        mt5_mod.initialize.return_value = True
        mt5_mod.login.return_value = True
        mt5_mod.account_info.return_value = None
        adapter, _ = self._make_adapter(mt5_mod)
        with patch.dict("sys.modules", {"MetaTrader5": mt5_mod}):
            result = adapter.connect("demo", {})
        self.assertEqual(result["status"], "ok")
        self.assertIsNone(result["account"]["login"])

    def test_connect_initialize_failed(self):
        mt5_mod = MagicMock()
        mt5_mod.initialize.return_value = False
        adapter, _ = self._make_adapter(mt5_mod)
        with patch.dict("sys.modules", {"MetaTrader5": mt5_mod}):
            result = adapter.connect("demo", {})
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"], "mt5_initialize_failed")

    def test_connect_login_failed(self):
        mt5_mod = MagicMock()
        mt5_mod.initialize.return_value = True
        mt5_mod.login.return_value = False
        adapter, _ = self._make_adapter(mt5_mod)
        with patch.dict("sys.modules", {"MetaTrader5": mt5_mod}):
            result = adapter.connect("demo", {})
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"], "mt5_login_failed")

    def test_connect_invalid_login_int(self):
        mt5_mod = MagicMock()
        os.environ["HPL_MT5_LOGIN"] = "not_a_number"
        adapter, _ = self._make_adapter(mt5_mod)
        with patch.dict("sys.modules", {"MetaTrader5": mt5_mod}):
            result = adapter.connect("demo", {})
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"], "mt5_login_invalid")

    def test_connect_with_path_env(self):
        mt5_mod = MagicMock()
        mt5_mod.initialize.return_value = True
        mt5_mod.login.return_value = True
        mt5_mod.account_info.return_value = None
        os.environ["HPL_MT5_PATH"] = "/some/path/terminal64.exe"
        adapter, _ = self._make_adapter(mt5_mod)
        with patch.dict("sys.modules", {"MetaTrader5": mt5_mod}):
            result = adapter.connect("demo", {})
        mt5_mod.initialize.assert_called_with(path="/some/path/terminal64.exe")
        self.assertEqual(result["status"], "ok")


# ===========================================================================
# MT5Adapter – submit_order
# ===========================================================================

class TestMT5AdapterSubmitOrder(unittest.TestCase):
    def setUp(self):
        self._env = dict(os.environ)
        os.environ["HPL_IO_ADAPTER_READY"] = "1"
        os.environ["HPL_MT5_LOGIN"] = "12345"
        os.environ["HPL_MT5_PASSWORD"] = "pass"
        os.environ["HPL_MT5_SERVER"] = "Demo-Server"

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env)

    def _make_adapter(self, mt5_mod):
        from hpl.runtime.io.adapters import mt5 as mt5_adapter
        import importlib
        with patch.dict("sys.modules", {"MetaTrader5": mt5_mod}):
            importlib.reload(mt5_adapter)
            return mt5_adapter.MT5Adapter()

    def test_submit_order_success(self):
        mt5_mod = MagicMock()
        mt5_mod.TRADE_RETCODE_DONE = 10009
        mt5_mod.TRADE_RETCODE_PLACED = 10008
        result_obj = MagicMock()
        result_obj.retcode = 10009
        result_obj.order = 777
        result_obj.deal = 888
        mt5_mod.order_send.return_value = result_obj
        adapter = self._make_adapter(mt5_mod)
        with patch.dict("sys.modules", {"MetaTrader5": mt5_mod}):
            result = adapter.submit_order("ep", {"symbol": "EURUSD"}, {})
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["order_id"], 777)
        self.assertEqual(result["deal_id"], 888)

    def test_submit_order_placed_retcode(self):
        mt5_mod = MagicMock()
        mt5_mod.TRADE_RETCODE_DONE = 10009
        mt5_mod.TRADE_RETCODE_PLACED = 10008
        result_obj = MagicMock()
        result_obj.retcode = 10008
        result_obj.order = 111
        result_obj.deal = 0
        mt5_mod.order_send.return_value = result_obj
        adapter = self._make_adapter(mt5_mod)
        with patch.dict("sys.modules", {"MetaTrader5": mt5_mod}):
            result = adapter.submit_order("ep", {}, {})
        self.assertEqual(result["status"], "ok")

    def test_submit_order_none_result(self):
        mt5_mod = MagicMock()
        mt5_mod.order_send.return_value = None
        adapter = self._make_adapter(mt5_mod)
        with patch.dict("sys.modules", {"MetaTrader5": mt5_mod}):
            result = adapter.submit_order("ep", {}, {})
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"], "mt5_order_send_returned_none")

    def test_submit_order_rejected(self):
        mt5_mod = MagicMock()
        mt5_mod.TRADE_RETCODE_DONE = 10009
        mt5_mod.TRADE_RETCODE_PLACED = 10008
        result_obj = MagicMock()
        result_obj.retcode = 10006
        result_obj.comment = "Market closed"
        mt5_mod.order_send.return_value = result_obj
        adapter = self._make_adapter(mt5_mod)
        with patch.dict("sys.modules", {"MetaTrader5": mt5_mod}):
            result = adapter.submit_order("ep", {}, {})
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"], "mt5_order_rejected")
        self.assertEqual(result["retcode"], 10006)

    def test_submit_order_exception(self):
        mt5_mod = MagicMock()
        mt5_mod.order_send.side_effect = RuntimeError("connection lost")
        adapter = self._make_adapter(mt5_mod)
        with patch.dict("sys.modules", {"MetaTrader5": mt5_mod}):
            result = adapter.submit_order("ep", {}, {})
        self.assertEqual(result["status"], "error")
        self.assertIn("RuntimeError", result["error"])


# ===========================================================================
# MT5Adapter – cancel_order
# ===========================================================================

class TestMT5AdapterCancelOrder(unittest.TestCase):
    def setUp(self):
        self._env = dict(os.environ)
        os.environ["HPL_IO_ADAPTER_READY"] = "1"
        os.environ["HPL_MT5_LOGIN"] = "12345"
        os.environ["HPL_MT5_PASSWORD"] = "pass"
        os.environ["HPL_MT5_SERVER"] = "Demo-Server"

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env)

    def _make_adapter(self, mt5_mod):
        from hpl.runtime.io.adapters import mt5 as mt5_adapter
        import importlib
        with patch.dict("sys.modules", {"MetaTrader5": mt5_mod}):
            importlib.reload(mt5_adapter)
            return mt5_adapter.MT5Adapter()

    def test_cancel_order_success(self):
        mt5_mod = MagicMock()
        mt5_mod.TRADE_ACTION_REMOVE = 1
        mt5_mod.TRADE_RETCODE_DONE = 10009
        result_obj = MagicMock()
        result_obj.retcode = 10009
        mt5_mod.order_send.return_value = result_obj
        adapter = self._make_adapter(mt5_mod)
        with patch.dict("sys.modules", {"MetaTrader5": mt5_mod}):
            result = adapter.cancel_order("ep", "99", {})
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["order_id"], "99")

    def test_cancel_order_none_result(self):
        mt5_mod = MagicMock()
        mt5_mod.TRADE_ACTION_REMOVE = 1
        mt5_mod.order_send.return_value = None
        adapter = self._make_adapter(mt5_mod)
        with patch.dict("sys.modules", {"MetaTrader5": mt5_mod}):
            result = adapter.cancel_order("ep", "99", {})
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"], "mt5_cancel_returned_none")

    def test_cancel_order_failed_retcode(self):
        mt5_mod = MagicMock()
        mt5_mod.TRADE_ACTION_REMOVE = 1
        mt5_mod.TRADE_RETCODE_DONE = 10009
        result_obj = MagicMock()
        result_obj.retcode = 10006
        result_obj.comment = "Order not found"
        mt5_mod.order_send.return_value = result_obj
        adapter = self._make_adapter(mt5_mod)
        with patch.dict("sys.modules", {"MetaTrader5": mt5_mod}):
            result = adapter.cancel_order("ep", "99", {})
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"], "mt5_cancel_failed")

    def test_cancel_order_exception(self):
        mt5_mod = MagicMock()
        mt5_mod.TRADE_ACTION_REMOVE = 1
        mt5_mod.order_send.side_effect = OSError("disconnected")
        adapter = self._make_adapter(mt5_mod)
        with patch.dict("sys.modules", {"MetaTrader5": mt5_mod}):
            result = adapter.cancel_order("ep", "99", {})
        self.assertEqual(result["status"], "error")


# ===========================================================================
# MT5Adapter – query_fills
# ===========================================================================

class TestMT5AdapterQueryFills(unittest.TestCase):
    def setUp(self):
        self._env = dict(os.environ)
        os.environ["HPL_IO_ADAPTER_READY"] = "1"
        os.environ["HPL_MT5_LOGIN"] = "12345"
        os.environ["HPL_MT5_PASSWORD"] = "pass"
        os.environ["HPL_MT5_SERVER"] = "Demo-Server"

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env)

    def _make_adapter(self, mt5_mod):
        from hpl.runtime.io.adapters import mt5 as mt5_adapter
        import importlib
        with patch.dict("sys.modules", {"MetaTrader5": mt5_mod}):
            importlib.reload(mt5_adapter)
            return mt5_adapter.MT5Adapter()

    def test_query_fills_missing_time_window(self):
        mt5_mod = MagicMock()
        adapter = self._make_adapter(mt5_mod)
        with patch.dict("sys.modules", {"MetaTrader5": mt5_mod}):
            result = adapter.query_fills("ep", "oid", {"from": "2024-01-01"})
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"], "missing_time_window")

    def test_query_fills_not_dict(self):
        mt5_mod = MagicMock()
        adapter = self._make_adapter(mt5_mod)
        with patch.dict("sys.modules", {"MetaTrader5": mt5_mod}):
            result = adapter.query_fills("ep", "oid", "bad")
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"], "missing_time_window")

    def test_query_fills_success_with_deals(self):
        mt5_mod = MagicMock()
        deal = MagicMock()
        deal.ticket = 1001
        deal.order = 2002
        deal.symbol = "EURUSD"
        deal.volume = 0.1
        deal.price = 1.0850
        deal.time = 1700000000
        deal.type = 0
        mt5_mod.history_deals_get.return_value = [deal]
        adapter = self._make_adapter(mt5_mod)
        with patch.dict("sys.modules", {"MetaTrader5": mt5_mod}):
            result = adapter.query_fills("ep", "oid", {"from": "2024-01-01", "to": "2024-12-31"})
        self.assertEqual(result["status"], "ok")
        self.assertEqual(len(result["fills"]), 1)
        self.assertEqual(result["fills"][0]["deal_id"], 1001)

    def test_query_fills_none_deals(self):
        mt5_mod = MagicMock()
        mt5_mod.history_deals_get.return_value = None
        adapter = self._make_adapter(mt5_mod)
        with patch.dict("sys.modules", {"MetaTrader5": mt5_mod}):
            result = adapter.query_fills("ep", "oid", {"from": "2024-01-01", "to": "2024-12-31"})
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["fills"], [])

    def test_query_fills_exception(self):
        mt5_mod = MagicMock()
        mt5_mod.history_deals_get.side_effect = RuntimeError("mt5 crash")
        adapter = self._make_adapter(mt5_mod)
        with patch.dict("sys.modules", {"MetaTrader5": mt5_mod}):
            result = adapter.query_fills("ep", "oid", {"from": "2024-01-01", "to": "2024-12-31"})
        self.assertEqual(result["status"], "error")


# ===========================================================================
# NET adapter – MockNetworkAdapter and StubNetworkAdapter
# ===========================================================================

class TestMockNetworkAdapter(unittest.TestCase):
    def setUp(self):
        from hpl.runtime.net.adapter import MockNetworkAdapter
        self.adapter = MockNetworkAdapter()

    def test_connect(self):
        r = self.adapter.connect("ws://ep", {})
        self.assertEqual(r["status"], "connected")
        self.assertEqual(r["endpoint"], "ws://ep")
        self.assertTrue(r["mock"])

    def test_handshake(self):
        r = self.adapter.handshake("ws://ep", {})
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["handshake"], "mock")

    def test_key_exchange(self):
        r = self.adapter.key_exchange("ws://ep", {})
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["key_fingerprint"], "mock")

    def test_send(self):
        r = self.adapter.send("ws://ep", {"request_id": "req-42"}, {})
        self.assertEqual(r["status"], "sent")
        self.assertEqual(r["msg_id"], "req-42")

    def test_recv(self):
        r = self.adapter.recv("ws://ep", {})
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["message"]["kind"], "mock")

    def test_close(self):
        r = self.adapter.close("ws://ep", {})
        self.assertEqual(r["status"], "closed")


class TestStubNetworkAdapter(unittest.TestCase):
    def setUp(self):
        self._env = dict(os.environ)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env)

    def test_stub_requires_ready_flag(self):
        os.environ.pop("HPL_NET_ADAPTER_READY", None)
        from hpl.runtime.net.adapter import StubNetworkAdapter
        with self.assertRaises(RuntimeError):
            StubNetworkAdapter("mynet")

    def test_stub_connect(self):
        os.environ["HPL_NET_ADAPTER_READY"] = "1"
        from hpl.runtime.net.adapter import StubNetworkAdapter
        adapter = StubNetworkAdapter("mynet")
        r = adapter.connect("ws://ep", {})
        self.assertEqual(r["status"], "connected")
        self.assertEqual(r["adapter"], "mynet")

    def test_stub_handshake(self):
        os.environ["HPL_NET_ADAPTER_READY"] = "1"
        from hpl.runtime.net.adapter import StubNetworkAdapter
        adapter = StubNetworkAdapter("mynet")
        r = adapter.handshake("ws://ep", {})
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["adapter"], "mynet")

    def test_stub_key_exchange(self):
        os.environ["HPL_NET_ADAPTER_READY"] = "1"
        from hpl.runtime.net.adapter import StubNetworkAdapter
        adapter = StubNetworkAdapter("mynet")
        r = adapter.key_exchange("ws://ep", {})
        self.assertEqual(r["status"], "ok")

    def test_stub_send(self):
        os.environ["HPL_NET_ADAPTER_READY"] = "1"
        from hpl.runtime.net.adapter import StubNetworkAdapter
        adapter = StubNetworkAdapter("mynet")
        r = adapter.send("ws://ep", {"k": "v"}, {})
        self.assertEqual(r["status"], "sent")

    def test_stub_recv(self):
        os.environ["HPL_NET_ADAPTER_READY"] = "1"
        from hpl.runtime.net.adapter import StubNetworkAdapter
        adapter = StubNetworkAdapter("mynet")
        r = adapter.recv("ws://ep", {})
        self.assertEqual(r["status"], "ok")

    def test_stub_close(self):
        os.environ["HPL_NET_ADAPTER_READY"] = "1"
        from hpl.runtime.net.adapter import StubNetworkAdapter
        adapter = StubNetworkAdapter("mynet")
        r = adapter.close("ws://ep", {})
        self.assertEqual(r["status"], "closed")


class TestLoadNetAdapter(unittest.TestCase):
    def setUp(self):
        self._env = dict(os.environ)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env)

    def test_load_mock_default(self):
        os.environ.pop("HPL_NET_ADAPTER", None)
        from hpl.runtime.net import adapter as net_adapter
        import importlib
        importlib.reload(net_adapter)
        a = net_adapter.load_adapter()
        from hpl.runtime.net.adapter import MockNetworkAdapter
        self.assertIsInstance(a, MockNetworkAdapter)

    def test_load_unsupported_raises(self):
        os.environ["HPL_NET_ADAPTER"] = "ftp"
        from hpl.runtime.net import adapter as net_adapter
        import importlib
        importlib.reload(net_adapter)
        with self.assertRaises(RuntimeError):
            net_adapter.load_adapter()


# ===========================================================================
# NET stabilizer
# ===========================================================================

class TestEvaluateStabilizer(unittest.TestCase):
    def _ctx(self, net_enabled=True):
        from hpl.runtime.context import RuntimeContext
        return RuntimeContext(net_enabled=net_enabled)

    def test_net_not_enabled(self):
        from hpl.runtime.net.stabilizer import evaluate_stabilizer
        ctx = self._ctx(net_enabled=False)
        decision = evaluate_stabilizer("send", "ws://ep", ctx, {"net_endpoints_allowlist": []})
        self.assertFalse(decision.ok)
        self.assertEqual(decision.refusal_type, "NetGuardNotEnabled")
        self.assertIn("NET not enabled", decision.reasons)

    def test_net_policy_none(self):
        from hpl.runtime.net.stabilizer import evaluate_stabilizer
        ctx = self._ctx(net_enabled=True)
        decision = evaluate_stabilizer("send", "ws://ep", ctx, None)
        self.assertFalse(decision.ok)
        self.assertEqual(decision.refusal_type, "NetPermissionDenied")
        self.assertIn("net_policy missing", decision.reasons)

    def test_endpoint_not_in_allowlist(self):
        from hpl.runtime.net.stabilizer import evaluate_stabilizer
        ctx = self._ctx(net_enabled=True)
        policy = {"net_endpoints_allowlist": ["ws://allowed.com"]}
        decision = evaluate_stabilizer("send", "ws://blocked.com", ctx, policy)
        self.assertFalse(decision.ok)
        self.assertEqual(decision.refusal_type, "NetEndpointNotAllowed")
        self.assertTrue(any("endpoint not allowed" in r for r in decision.reasons))

    def test_endpoint_in_allowlist_passes(self):
        from hpl.runtime.net.stabilizer import evaluate_stabilizer
        ctx = self._ctx(net_enabled=True)
        policy = {"net_endpoints_allowlist": ["ws://allowed.com"]}
        decision = evaluate_stabilizer("send", "ws://allowed.com", ctx, policy)
        self.assertTrue(decision.ok)
        self.assertIsNone(decision.refusal_type)
        self.assertIn("net_request_log", decision.required_roles)

    def test_empty_allowlist_allows_all(self):
        from hpl.runtime.net.stabilizer import evaluate_stabilizer
        ctx = self._ctx(net_enabled=True)
        policy = {"net_endpoints_allowlist": []}
        decision = evaluate_stabilizer("send", "ws://any.com", ctx, policy)
        self.assertTrue(decision.ok)

    def test_no_allowlist_key_allows_all(self):
        from hpl.runtime.net.stabilizer import evaluate_stabilizer
        ctx = self._ctx(net_enabled=True)
        policy = {}
        decision = evaluate_stabilizer("send", "ws://any.com", ctx, policy)
        self.assertTrue(decision.ok)

    def test_empty_endpoint_skips_allowlist(self):
        from hpl.runtime.net.stabilizer import evaluate_stabilizer
        ctx = self._ctx(net_enabled=True)
        policy = {"net_endpoints_allowlist": ["ws://specific.com"]}
        decision = evaluate_stabilizer("send", "", ctx, policy)
        self.assertTrue(decision.ok)


# ===========================================================================
# IO adapter base – MockBrokerAdapter and StubBrokerAdapter / load_adapter
# ===========================================================================

class TestMockBrokerAdapter(unittest.TestCase):
    def setUp(self):
        from hpl.runtime.io.adapter import MockBrokerAdapter
        self.adapter = MockBrokerAdapter()

    def test_connect(self):
        r = self.adapter.connect("broker://demo", {})
        self.assertEqual(r["status"], "connected")
        self.assertTrue(r["mock"])

    def test_submit_order_with_order_id(self):
        r = self.adapter.submit_order("broker://demo", {"order_id": "oid-1"}, {})
        self.assertEqual(r["status"], "accepted")
        self.assertEqual(r["order_id"], "oid-1")

    def test_submit_order_default_order_id(self):
        r = self.adapter.submit_order("broker://demo", {}, {})
        self.assertEqual(r["order_id"], "mock-order")

    def test_cancel_order(self):
        r = self.adapter.cancel_order("broker://demo", "oid-2", {})
        self.assertEqual(r["status"], "cancelled")
        self.assertEqual(r["order_id"], "oid-2")

    def test_query_fills(self):
        r = self.adapter.query_fills("broker://demo", "oid-3", {})
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["fills"], [])


class TestStubBrokerAdapter(unittest.TestCase):
    def setUp(self):
        self._env = dict(os.environ)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env)

    def test_stub_requires_ready_flag(self):
        os.environ.pop("HPL_IO_ADAPTER_READY", None)
        from hpl.runtime.io.adapter import StubBrokerAdapter
        with self.assertRaises(RuntimeError):
            StubBrokerAdapter("mybroker")

    def test_stub_connect(self):
        os.environ["HPL_IO_ADAPTER_READY"] = "1"
        from hpl.runtime.io.adapter import StubBrokerAdapter
        adapter = StubBrokerAdapter("mybroker")
        r = adapter.connect("broker://demo", {})
        self.assertEqual(r["status"], "accepted")
        self.assertEqual(r["adapter"], "mybroker")

    def test_stub_submit_order_with_id(self):
        os.environ["HPL_IO_ADAPTER_READY"] = "1"
        from hpl.runtime.io.adapter import StubBrokerAdapter
        adapter = StubBrokerAdapter("mybroker")
        r = adapter.submit_order("ep", {"order_id": "x-99"}, {})
        self.assertEqual(r["status"], "accepted")
        self.assertEqual(r["order_id"], "x-99")

    def test_stub_submit_order_default_id(self):
        os.environ["HPL_IO_ADAPTER_READY"] = "1"
        from hpl.runtime.io.adapter import StubBrokerAdapter
        adapter = StubBrokerAdapter("mybroker")
        r = adapter.submit_order("ep", {}, {})
        self.assertEqual(r["order_id"], "stub-order")

    def test_stub_cancel_order(self):
        os.environ["HPL_IO_ADAPTER_READY"] = "1"
        from hpl.runtime.io.adapter import StubBrokerAdapter
        adapter = StubBrokerAdapter("mybroker")
        r = adapter.cancel_order("ep", "oid-5", {})
        self.assertEqual(r["status"], "cancelled")
        self.assertEqual(r["order_id"], "oid-5")

    def test_stub_query_fills(self):
        os.environ["HPL_IO_ADAPTER_READY"] = "1"
        from hpl.runtime.io.adapter import StubBrokerAdapter
        adapter = StubBrokerAdapter("mybroker")
        r = adapter.query_fills("ep", "oid-6", {})
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["fills"], [])


class TestLoadIOAdapter(unittest.TestCase):
    def setUp(self):
        self._env = dict(os.environ)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env)

    def test_load_mock_default(self):
        os.environ.pop("HPL_IO_ADAPTER", None)
        from hpl.runtime.io import adapter as io_adapter
        import importlib
        importlib.reload(io_adapter)
        a = io_adapter.load_adapter()
        from hpl.runtime.io.adapter import MockBrokerAdapter
        self.assertIsInstance(a, MockBrokerAdapter)

    def test_load_mt5(self):
        os.environ["HPL_IO_ADAPTER"] = "mt5"
        os.environ["HPL_IO_ADAPTER_READY"] = "1"
        os.environ["HPL_MT5_LOGIN"] = "1"
        os.environ["HPL_MT5_PASSWORD"] = "p"
        os.environ["HPL_MT5_SERVER"] = "s"
        mt5_mod = MagicMock()
        with patch.dict("sys.modules", {"MetaTrader5": mt5_mod}):
            from hpl.runtime.io import adapter as io_adapter
            from hpl.runtime.io.adapters import mt5 as mt5_adapter
            import importlib
            importlib.reload(mt5_adapter)
            importlib.reload(io_adapter)
            a = io_adapter.load_adapter()
            self.assertIsNotNone(a)

    def test_load_deriv(self):
        os.environ["HPL_IO_ADAPTER"] = "deriv"
        os.environ["HPL_IO_ADAPTER_READY"] = "1"
        os.environ["HPL_DERIV_ENDPOINT"] = "wss://ws.binaryws.com"
        os.environ["HPL_DERIV_TOKEN"] = "tok"
        ws_mod = MagicMock()
        with patch.dict("sys.modules", {"websocket": ws_mod}):
            from hpl.runtime.io import adapter as io_adapter
            from hpl.runtime.io.adapters import deriv as deriv_adapter
            import importlib
            importlib.reload(deriv_adapter)
            importlib.reload(io_adapter)
            a = io_adapter.load_adapter()
            self.assertIsNotNone(a)

    def test_load_unsupported_raises(self):
        os.environ["HPL_IO_ADAPTER"] = "unknownbroker"
        from hpl.runtime.io import adapter as io_adapter
        import importlib
        importlib.reload(io_adapter)
        with self.assertRaises(RuntimeError):
            io_adapter.load_adapter()


if __name__ == "__main__":
    unittest.main()
