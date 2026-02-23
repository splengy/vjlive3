"""Tests for vjlive3.ui.web_remote — WebRemoteServer and WebSocketBroadcaster."""
import pytest
import json
import threading
from io import BytesIO
from http.client import HTTPConnection
from unittest.mock import MagicMock
from vjlive3.ui.web_remote import (
    WebRemoteServer, WebSocketBroadcaster, VJLiveAPIHandler
)
from vjlive3.ui.cli import ParamStore


# ── VJLiveAPIHandler unit tests (no real server) ──────────────────────────────

def _make_handler(method, path, body=b"", store=None, registry=None):
    """Return a handler instance with mocked socket infrastructure."""
    handler = VJLiveAPIHandler.__new__(VJLiveAPIHandler)
    handler._param_store = store or ParamStore()
    handler._plugin_registry = registry or {}
    handler._agent_state = {}
    handler.path = path
    handler.command = method
    handler.headers = {"Content-Length": str(len(body))}
    handler.rfile = BytesIO(body)
    out = BytesIO()
    handler.wfile = out
    handler.requestline = f"{method} {path} HTTP/1.1"
    handler.client_address = ("127.0.0.1", 0)
    handler.server = MagicMock()
    handler._response = out
    return handler, out


def _capture_response(handler, method):
    responses = []
    def send_response(code, msg=None): responses.append(code)
    def send_header(k, v): pass
    def end_headers(): pass
    def send_error(code, msg=None): responses.append(code)
    handler.send_response = send_response
    handler.send_header = send_header
    handler.end_headers = end_headers
    handler.send_error = send_error
    handler.wfile = BytesIO()
    getattr(handler, f"do_{method}")()
    return responses, handler.wfile.getvalue()


def test_get_plugins():
    s = ParamStore()
    handler, _ = _make_handler("GET", "/api/plugins", store=s,
                                registry={"bloom": [], "hue": []})
    codes, body = _capture_response(handler, "GET")
    assert codes[0] == 200
    data = json.loads(body)
    assert set(data) == {"bloom", "hue"}


def test_get_params_empty():
    s = ParamStore()
    handler, _ = _make_handler("GET", "/api/params/bloom", store=s)
    codes, body = _capture_response(handler, "GET")
    assert codes[0] == 200
    assert json.loads(body) == {}


def test_get_params_with_value():
    s = ParamStore()
    s.set("bloom", "intensity", 7.0)
    handler, _ = _make_handler("GET", "/api/params/bloom", store=s)
    codes, body = _capture_response(handler, "GET")
    data = json.loads(body)
    assert data["intensity"] == pytest.approx(7.0)


def test_post_params():
    s = ParamStore()
    body = json.dumps({"intensity": 9.0}).encode()
    handler, _ = _make_handler("POST", "/api/params/bloom", body=body, store=s)
    codes, resp = _capture_response(handler, "POST")
    assert codes[0] == 200
    assert s.get("bloom", "intensity") == pytest.approx(9.0)


def test_post_invalid_json():
    s = ParamStore()
    handler, _ = _make_handler("POST", "/api/params/bloom", body=b"bad json", store=s)
    codes, _ = _capture_response(handler, "POST")
    assert codes[0] == 400


def test_get_agents():
    s = ParamStore()
    handler, _ = _make_handler("GET", "/api/agents", store=s)
    handler._agent_state = {"agent_count": 3, "time": 1.0}
    codes, body = _capture_response(handler, "GET")
    assert codes[0] == 200


def test_get_not_found():
    s = ParamStore()
    handler, _ = _make_handler("GET", "/no/such/path", store=s)
    codes, _ = _capture_response(handler, "GET")
    assert codes[0] == 404


def test_post_not_found():
    s = ParamStore()
    handler, _ = _make_handler("POST", "/no/such/path", body=b"{}", store=s)
    codes, _ = _capture_response(handler, "POST")
    assert codes[0] == 404


# ── WebRemoteServer unit tests ────────────────────────────────────────────────

def test_web_remote_url():
    srv = WebRemoteServer(host="localhost", port=9999)
    assert srv.url == "http://localhost:9999"


def test_web_remote_update_agent_state():
    srv = WebRemoteServer()
    srv.update_agent_state({"agent_count": 2})
    assert srv._agent_state["agent_count"] == 2


# ── WebSocketBroadcaster ──────────────────────────────────────────────────────

def test_ws_broadcaster_publish_and_flush():
    wb = WebSocketBroadcaster()
    wb.publish({"event": "param_change", "plugin": "bloom"})
    msgs = wb.flush()
    assert len(msgs) == 1
    assert msgs[0]["event"] == "param_change"
    assert wb.flush() == []   # Cleared after flush


def test_ws_broadcaster_add_remove_client():
    wb = WebSocketBroadcaster()
    c = MagicMock()
    wb.add_client(c)
    assert wb.client_count == 1
    wb.remove_client(c)
    assert wb.client_count == 0


def test_ws_broadcaster_multiple_messages():
    wb = WebSocketBroadcaster()
    for i in range(5):
        wb.publish({"i": i})
    msgs = wb.flush()
    assert len(msgs) == 5
