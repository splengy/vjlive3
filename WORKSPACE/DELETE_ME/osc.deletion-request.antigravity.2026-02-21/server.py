"""P2-H2 — OSC Server (python-osc backend)

Lightweight OSC server for VJLive3 parameter control.
Listens on a configurable UDP port, dispatches messages to registered
handler callbacks, and provides a typed parameter-binding shorthand.

Designed to run headless (no GUI dependency).
Gracefully degrades when python-osc is not installed — OscServer still
instantiates but all methods become no-ops (so import-time failures don't
crash the engine on systems without the dependency).

Board: P2-H2 — OSCQuery (advanced OSC discovery)
Dependencies: python-osc >= 1.8 (optional), stdlib threading/socket
"""
from __future__ import annotations

import logging
import socket
import threading
from typing import Any, Callable, Dict, List, Optional, Tuple

_log = logging.getLogger(__name__)

# ── Optional: python-osc ──────────────────────────────────────────────────────
try:
    from pythonosc import dispatcher as _dispatcher_mod
    from pythonosc import osc_server as _server_mod
    from pythonosc.udp_client import SimpleUDPClient as _UDPClient
    _HAS_PYTHONOSC = True
except ImportError:
    _HAS_PYTHONOSC = False
    _log.warning("python-osc not installed — OscServer will be a no-op")


# ── Types ─────────────────────────────────────────────────────────────────────

OscHandler = Callable[[str, Any], None]
"""Signature: (address: str, *args) — handler receives address and unpacked args."""


# ── OscMessage (thin wrapper for testing without hardware) ──────────────────

class OscMessage:
    """Represents an outgoing or received OSC message (address + args)."""

    def __init__(self, address: str, *args: Any) -> None:
        if not address.startswith("/"):
            raise ValueError(f"OSC address must start with '/': {address!r}")
        self.address = address
        self.args: Tuple[Any, ...] = args

    def __repr__(self) -> str:
        return f"OscMessage({self.address!r}, {self.args!r})"


# ── OscServer ────────────────────────────────────────────────────────────────

class OscServer:
    """
    UDP OSC server with handler dispatch and typed address registration.

    Usage::

        srv = OscServer(host="0.0.0.0", port=7700)
        srv.add_handler("/vjlive/intensity", lambda addr, val: print(val))
        srv.add_handler("/vjlive/bpm", lambda addr, bpm: print(bpm))
        srv.start()
        # …
        srv.stop()

    Thread-safe: start/stop/add_handler can be called from any thread.
    When python-osc is absent, all methods succeed silently (no-op).
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 7700) -> None:
        self._host = host
        self._port = port
        self._lock = threading.RLock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._server = None  # python-osc BlockingOSCUDPServer or None
        self._dispatcher = None

        # Handler registry (used for both real and stub modes)
        self._handlers: Dict[str, List[OscHandler]] = {}
        # Default (catch-all) handler
        self._default_handler: Optional[OscHandler] = None

        if _HAS_PYTHONOSC:
            self._dispatcher = _dispatcher_mod.Dispatcher()
            self._dispatcher.set_default_handler(self._dispatch_default)

    # ── Handler registration ──────────────────────────────────────────────────

    def add_handler(self, address: str, handler: OscHandler) -> None:
        """Register a handler for an OSC address pattern.

        Multiple handlers per address are supported — all are called in
        registration order.

        Args:
            address: OSC address pattern (must start with '/').
                     Wildcards '*' and '?' are passed through to python-osc.
            handler: Callable(address: str, *args) invoked on match.

        Raises:
            ValueError: If address does not start with '/'.
        """
        if not address.startswith("/"):
            raise ValueError(f"OSC address must start with '/': {address!r}")
        with self._lock:
            self._handlers.setdefault(address, []).append(handler)
            if _HAS_PYTHONOSC and self._dispatcher is not None:
                self._dispatcher.map(address, self._make_bridge(address))

    def remove_handler(self, address: str, handler: OscHandler) -> bool:
        """Remove a specific handler for an address. Returns True if found."""
        with self._lock:
            lst = self._handlers.get(address, [])
            try:
                lst.remove(handler)
                if not lst:
                    del self._handlers[address]
                return True
            except ValueError:
                return False

    def set_default_handler(self, handler: Optional[OscHandler]) -> None:
        """Set a catch-all handler for unregistered addresses."""
        with self._lock:
            self._default_handler = handler

    def clear_handlers(self) -> None:
        """Remove all registered handlers."""
        with self._lock:
            self._handlers.clear()
            self._default_handler = None

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self) -> bool:
        """Start the OSC server in a background thread.

        Returns:
            True if started successfully (or already running).
            False if python-osc unavailable or bind failed.
        """
        with self._lock:
            if self._running:
                return True
            if not _HAS_PYTHONOSC:
                _log.warning("OscServer: python-osc not available — server is no-op")
                self._running = True
                return False

        try:
            server = _server_mod.BlockingOSCUDPServer(
                (self._host, self._port), self._dispatcher
            )
        except OSError as exc:
            _log.error("OscServer: failed to bind %s:%d — %s", self._host, self._port, exc)
            return False

        with self._lock:
            self._server = server
            self._running = True

        self._thread = threading.Thread(
            target=server.serve_forever,
            name=f"OscServer:{self._port}",
            daemon=True,
        )
        self._thread.start()
        _log.info("OscServer listening on %s:%d", self._host, self._port)
        return True

    def stop(self) -> None:
        """Stop the OSC server. Idempotent."""
        with self._lock:
            if not self._running:
                return
            self._running = False
            if self._server:
                try:
                    self._server.shutdown()
                except Exception:
                    pass
                self._server = None

        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        _log.info("OscServer stopped")

    # ── Dispatch (internal) ───────────────────────────────────────────────────

    def _make_bridge(self, address: str) -> Callable:
        """Return a python-osc-compatible handler that calls our handler list."""
        def bridge(addr: str, *args: Any) -> None:
            self._dispatch(addr, *args)
        return bridge

    def _dispatch(self, address: str, *args: Any) -> None:
        with self._lock:
            handlers = list(self._handlers.get(address, []))
        for h in handlers:
            try:
                h(address, *args)
            except Exception as exc:
                _log.warning("OscServer handler error (%s): %s", address, exc)

    def _dispatch_default(self, address: str, *args: Any) -> None:
        with self._lock:
            default = self._default_handler
        if default is not None:
            try:
                default(address, *args)
            except Exception as exc:
                _log.warning("OscServer default handler error (%s): %s", address, exc)
        else:
            _log.debug("OscServer: unhandled address %s %s", address, args)

    # Expose for testing — simulate receiving a message even without network
    def simulate_message(self, address: str, *args: Any) -> None:
        """Inject a synthetic OSC message for unit testing (bypasses UDP)."""
        if self._handlers.get(address):
            self._dispatch(address, *args)
        else:
            self._dispatch_default(address, *args)

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int:
        return self._port

    @property
    def is_running(self) -> bool:
        with self._lock:
            return self._running

    @property
    def handler_count(self) -> int:
        with self._lock:
            return sum(len(v) for v in self._handlers.values())


# ── OscClient (send from VJLive3 to other OSC hosts) ─────────────────────────

class OscClient:
    """
    Simple UDP OSC client for sending messages to a remote host.

    Degrades gracefully when python-osc is unavailable.
    """

    def __init__(self, host: str, port: int) -> None:
        self._host = host
        self._port = port
        self._client = None
        if _HAS_PYTHONOSC:
            try:
                self._client = _UDPClient(host, port)
            except Exception as exc:
                _log.warning("OscClient init failed (%s:%d): %s", host, port, exc)

    def send(self, address: str, *args: Any) -> bool:
        """Send an OSC message. Returns True on success."""
        if self._client is None:
            return False
        try:
            from pythonosc.osc_message_builder import OscMessageBuilder
            builder = OscMessageBuilder(address=address)
            for arg in args:
                builder.add_arg(arg)
            msg = builder.build()
            self._client.send(msg)
            return True
        except Exception as exc:
            _log.warning("OscClient.send(%s) failed: %s", address, exc)
            return False

    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int:
        return self._port


__all__ = ["OscMessage", "OscServer", "OscClient"]
