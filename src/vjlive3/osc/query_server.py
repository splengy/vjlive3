"""
OSCQuery HTTP Discovery Server

Exposes the OSCAddressSpace as an HTTP/JSON endpoint conforming to
the OSCQuery specification:
  GET /            → full address space JSON
  GET /some/path   → single-node JSON

Runs in a daemon thread; no external web-framework dependency required
(uses stdlib http.server).
"""

from __future__ import annotations

import http.server
import json
import logging
import threading
import urllib.parse
from typing import Any, Dict, Optional

from vjlive3.osc.address_space import OSCAddressSpace

logger = logging.getLogger(__name__)


class _OSCQueryHandler(http.server.BaseHTTPRequestHandler):
    """Request handler — delegates to the attached address space."""

    # Set by OSCQueryServer before the server starts
    address_space: OSCAddressSpace

    def log_message(self, fmt: str, *args: Any) -> None:
        # Route to our logger instead of stderr
        logger.debug("OSCQuery HTTP: " + fmt, *args)

    def do_GET(self) -> None:
        """Handle every GET — serve address-space JSON."""
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        try:
            if path in ("/", ""):
                body = self.address_space.to_dict()
            else:
                node = self.address_space.get_node(path)
                if node is None:
                    self._send_error(404, f"OSC path not found: {path}")
                    return
                body = node.to_dict()

            self._send_json(200, body)
        except Exception as exc:  # noqa: BLE001
            logger.error("OSCQuery HTTP handler error: %s", exc)
            self._send_error(500, str(exc))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _send_json(self, status: int, payload: Dict[str, Any]) -> None:
        encoded = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(encoded)

    def _send_error(self, status: int, message: str) -> None:
        self._send_json(status, {"error": message})


class OSCQueryServer:
    """HTTP server that exposes an OSCAddressSpace for discovery.

    Usage::

        space = OSCAddressSpace()
        space.register("/fx/blur", OSCType.FLOAT, 0.0, "Blur amount")

        qs = OSCQueryServer(space)
        qs.start(host="0.0.0.0", port=8080)
        # clients can now GET http://host:8080/ for full address space

    METADATA constant — Prime Directive Rule 2.
    """

    METADATA = {
        "name": "OSCQueryServer",
        "description": "HTTP discovery layer for the OSCQuery protocol",
        "version": "1.0",
    }

    def __init__(self, address_space: OSCAddressSpace) -> None:
        self._space = address_space
        self._server: Optional[http.server.HTTPServer] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._host = "0.0.0.0"
        self._port = 8080
        logger.info("OSCQueryServer: initialised")

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def address_space(self) -> OSCAddressSpace:
        return self._space

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self, host: str = "0.0.0.0", port: int = 8080) -> bool:
        """Start the HTTP server in a background daemon thread.

        Returns True on success, False on bind failure.
        """
        if self._running:
            logger.warning("OSCQueryServer.start: already running on %s:%d", self._host, self._port)
            return True

        self._host = host
        self._port = port

        # Inject address space into the handler class at class level
        handler_cls = type(
            "_BoundHandler",
            (_OSCQueryHandler,),
            {"address_space": self._space},
        )

        try:
            self._server = http.server.HTTPServer((host, port), handler_cls)
            self._thread = threading.Thread(
                target=self._server.serve_forever,
                daemon=True,
                name=f"OSCQueryHTTP-{host}:{port}",
            )
            self._thread.start()
            self._running = True
            logger.info("OSCQueryServer: HTTP serving on %s:%d", host, port)
            return True
        except OSError as exc:
            logger.error("OSCQueryServer.start: bind failed — %s", exc)
            return False

    def stop(self) -> None:
        """Shutdown HTTP server and release socket."""
        if not self._running:
            return
        self._running = False
        if self._server:
            self._server.shutdown()
            self._server = None
        logger.info("OSCQueryServer: stopped")

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> "OSCQueryServer":
        return self

    def __exit__(self, *_: Any) -> None:
        self.stop()
