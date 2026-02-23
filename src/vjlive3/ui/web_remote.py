"""
P7-U2: VJLive3 Web-based remote control.

Provides a lightweight HTTP + WebSocket server so that browsers, tablets,
and phones can control VJLive3 parameters without installing software.

Architecture
------------
* ``WebRemoteServer`` — wraps ``http.server`` for static files and a
  simple REST API (/api/params GET/POST, /api/plugins GET, /api/agents GET).
* ``WebSocketBroadcaster`` — collects state diffs each frame and fans out
  JSON messages to all connected WS clients.
* No third-party dependencies required (pure stdlib). For production use,
  replace with FastAPI/aiohttp; this implementation is spec-complete for
  headless CI testing.
"""
from __future__ import annotations
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from io import BytesIO
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlparse, parse_qs


# ── REST API handler ──────────────────────────────────────────────────────────

class VJLiveAPIHandler(BaseHTTPRequestHandler):
    """
    Minimal REST handler for VJLive3 remote control.

    Routes:
        GET  /api/plugins       → list all plugin names
        GET  /api/params/<plug> → all params for a plugin
        POST /api/params/<plug> → set params (JSON body)
        GET  /api/agents        → agent system state snapshot
    """

    # Injected by WebRemoteServer
    _param_store: Any = None
    _plugin_registry: Dict[str, List[Dict]] = {}
    _agent_state: Dict = {}

    def log_message(self, fmt, *args):  # Silence default httpd logging in tests
        pass

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/plugins":
            body = json.dumps(list(self._plugin_registry.keys())).encode()
            self._json_response(body)

        elif path.startswith("/api/params/"):
            plugin = path[len("/api/params/"):]
            params = (self._param_store.get_all(plugin)
                      if self._param_store else {})
            self._json_response(json.dumps(params).encode())

        elif path == "/api/agents":
            snap = {k: v for k, v in self._agent_state.items()
                    if k != "agents"}  # agents not JSON-serialisable
            self._json_response(json.dumps(snap).encode())

        else:
            self.send_error(404, "Not found")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/params/"):
            plugin = path[len("/api/params/"):]
            # SEC: strip path traversal characters from plugin name
            plugin = plugin.replace("..", "").replace("/", "").replace("\\", "")
            # SEC: cap body size to 64 KB to prevent memory exhaustion
            _MAX_BODY = 65536
            length = min(int(self.headers.get("Content-Length", 0)), _MAX_BODY)
            body = self.rfile.read(length)
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                self.send_error(400, "Invalid JSON")
                return
            if self._param_store:
                for param, value in data.items():
                    # SEC: reject inf/nan from network input
                    try:
                        fval = float(value)
                    except (ValueError, TypeError):
                        self.send_error(400, f"Invalid value for param '{param}'")
                        return
                    import math
                    if not math.isfinite(fval):
                        self.send_error(400, f"Non-finite value rejected for '{param}'")
                        return
                    self._param_store.set(plugin, param, fval)
            self._json_response(b'{"ok": true}')
        else:
            self.send_error(404, "Not found")

    def _json_response(self, body: bytes) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)


class WebRemoteServer:
    """
    VJLive3 web remote control server.

    Runs an HTTP server in a daemon thread so the render loop is unblocked.
    """

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8765,
        param_store=None,
        plugin_registry: Optional[Dict[str, List[Dict]]] = None,
    ) -> None:
        self.host = host
        self.port = port
        self._param_store = param_store
        self._plugin_registry = plugin_registry or {}
        self._agent_state: Dict = {}
        self._server: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start the HTTP server in a background daemon thread."""
        handler = self._make_handler()
        self._server = HTTPServer((self.host, self.port), handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._server:
            self._server.shutdown()
            self._server = None

    def update_agent_state(self, state: Dict) -> None:
        """Called each frame to update the agent snapshot for /api/agents."""
        self._agent_state.update(state)
        if hasattr(self._server, "_handler_class"):
            self._server._handler_class._agent_state = dict(self._agent_state)

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def _make_handler(self):
        """Create a handler class with injected references."""
        param_store = self._param_store
        plugin_registry = self._plugin_registry
        agent_state = self._agent_state

        class Handler(VJLiveAPIHandler):
            _param_store = param_store
            _plugin_registry = plugin_registry
            _agent_state = agent_state

        return Handler


# ── WebSocket broadcaster (stub — requires ws library for full impl) ──────────

class WebSocketBroadcaster:
    """
    Collects parameter diffs and fans them out to WebSocket clients.

    In the stdlib-only version this is a simple in-memory diff accumulator.
    A future version would use ``websockets`` or ``aiohttp`` to push live.
    """

    def __init__(self) -> None:
        self._clients: List[Any] = []   # WebSocket connection objects
        self._pending: List[Dict] = []  # Accumulated messages

    def publish(self, message: Dict) -> None:
        """Queue a message for broadcast to all connected clients."""
        self._pending.append(message)

    def flush(self) -> List[Dict]:
        """Return and clear the pending message queue."""
        msgs = list(self._pending)
        self._pending.clear()
        return msgs

    def add_client(self, client: Any) -> None:
        self._clients.append(client)

    def remove_client(self, client: Any) -> None:
        self._clients = [c for c in self._clients if c is not client]

    @property
    def client_count(self) -> int:
        return len(self._clients)
