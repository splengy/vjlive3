"""
OSC UDP Server

Wraps python-osc's ThreadingOSCUDPServer with a clean lifecycle API
and a NullOSCServer fallback for hardware-absent environments.
"""

from __future__ import annotations

import logging
import threading
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# python-osc is a hard dependency declared in pyproject.toml
try:
    from pythonosc import dispatcher as osc_dispatcher
    from pythonosc.server import ThreadingOSCUDPServer

    _PYTHON_OSC_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PYTHON_OSC_AVAILABLE = False
    logger.warning("OSCServer: python-osc not installed — using NullOSCServer")


HandlerFn = Callable[..., None]


class NullOSCServer:
    """Hardware-absent stub — same public API as OSCServer, does nothing.

    METADATA constant — Prime Directive Rule 2.
    """

    METADATA = {
        "name": "NullOSCServer",
        "description": "No-op OSC server for hardware-absent environments",
        "version": "1.0",
    }

    def __init__(self) -> None:
        self._handlers: Dict[str, HandlerFn] = {}
        self._running = False
        logger.info("NullOSCServer: active (python-osc unavailable)")

    # Mirror entire OSCServer API
    @property
    def is_running(self) -> bool:
        return self._running

    def dispatch(self, address: str, handler: HandlerFn) -> None:  # noqa: ARG002
        self._handlers[address] = handler

    def start(self, host: str = "0.0.0.0", port: int = 9000) -> bool:
        logger.info("NullOSCServer.start: noop (%s:%d)", host, port)
        self._running = True
        return True

    def stop(self) -> None:
        self._running = False

    def deliver(self, address: str, *args: Any) -> None:
        """Inject a test message directly into registered handlers."""
        handler = self._handlers.get(address)
        if handler:
            handler(address, *args)

    def get_registered_addresses(self) -> List[str]:
        return list(self._handlers.keys())


class OSCServer:
    """Real OSC UDP server using python-osc's ThreadingOSCUDPServer.

    Usage::

        server = OSCServer()
        server.dispatch("/fx/blur", my_handler)
        server.start("0.0.0.0", 9000)
        # ... later ...
        server.stop()

    METADATA constant — Prime Directive Rule 2.
    """

    METADATA = {
        "name": "OSCServer",
        "description": "UDP OSC receive server — VJLive3 hardware input",
        "version": "1.0",
    }

    def __init__(self) -> None:
        if not _PYTHON_OSC_AVAILABLE:
            raise RuntimeError(
                "python-osc is not installed. Install it or use NullOSCServer."
            )

        self._dispatcher = osc_dispatcher.Dispatcher()
        self._server: Optional[ThreadingOSCUDPServer] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._host = "0.0.0.0"
        self._port = 9000
        logger.info("OSCServer: initialised")

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def address(self) -> Tuple[str, int]:
        return (self._host, self._port)

    # ------------------------------------------------------------------
    # Handler registration
    # ------------------------------------------------------------------

    def dispatch(self, address: str, handler: HandlerFn) -> None:
        """Register *handler* for OSC address pattern *address*."""
        self._dispatcher.map(address, handler)
        logger.debug("OSCServer: mapped %s → %s", address, handler.__name__)

    def dispatch_default(self, handler: HandlerFn) -> None:
        """Register a catch-all handler for unmapped addresses."""
        self._dispatcher.set_default_handler(handler)

    def get_registered_addresses(self) -> List[str]:
        """Return all explicitly mapped address patterns."""
        return list(self._dispatcher._map.keys())  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self, host: str = "0.0.0.0", port: int = 9000) -> bool:
        """Bind and start serving in a background daemon thread.

        Returns True on success, False on bind failure.
        """
        if self._running:
            logger.warning("OSCServer.start: already running on %s:%d", self._host, self._port)
            return True

        self._host = host
        self._port = port

        try:
            self._server = ThreadingOSCUDPServer((host, port), self._dispatcher)
            self._thread = threading.Thread(
                target=self._server.serve_forever,
                daemon=True,
                name=f"OSCServer-{host}:{port}",
            )
            self._thread.start()
            self._running = True
            logger.info("OSCServer: listening on %s:%d", host, port)
            return True
        except OSError as exc:
            logger.error("OSCServer.start: bind failed — %s", exc)
            return False

    def stop(self) -> None:
        """Shutdown the server and release the socket."""
        if not self._running:
            return
        self._running = False
        if self._server:
            self._server.shutdown()
            self._server = None
        logger.info("OSCServer: stopped")

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> "OSCServer":
        return self

    def __exit__(self, *_: Any) -> None:
        self.stop()
