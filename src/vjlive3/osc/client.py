"""
OSC Send Client

Thin wrapper around python-osc's SimpleUDPClient that adds typed
value dispatch and OSC bundle support.
"""

from __future__ import annotations

import logging
from typing import Any, List, Tuple

logger = logging.getLogger(__name__)

try:
    from pythonosc import udp_client as osc_udp

    _PYTHON_OSC_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PYTHON_OSC_AVAILABLE = False


class OSCClient:
    """Send OSC messages to a remote host.

    Falls back gracefully to a no-op mode when python-osc is absent.

    METADATA constant — Prime Directive Rule 2.
    """

    METADATA = {
        "name": "OSCClient",
        "description": "OSC UDP send client — typed dispatch + bundle support",
        "version": "1.0",
    }

    def __init__(self, host: str = "127.0.0.1", port: int = 9001) -> None:
        self._host = host
        self._port = port
        self._client: Any = None
        self._available = _PYTHON_OSC_AVAILABLE

        if self._available:
            try:
                self._client = osc_udp.SimpleUDPClient(host, port)
                logger.info("OSCClient: connected to %s:%d", host, port)
            except Exception as exc:  # noqa: BLE001
                logger.warning("OSCClient: could not create UDP client — %s", exc)
                self._available = False
        else:
            logger.warning("OSCClient: python-osc unavailable — noop mode")

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int:
        return self._port

    @property
    def is_available(self) -> bool:
        return self._available and self._client is not None

    # ------------------------------------------------------------------
    # Send API
    # ------------------------------------------------------------------

    def send(self, address: str, *args: Any) -> bool:
        """Send an OSC message to *address* with zero or more typed args.

        Returns True if message was dispatched, False otherwise.
        """
        if not self.is_available:
            logger.debug("OSCClient.send: noop — %s %s", address, args)
            return False
        try:
            self._client.send_message(address, list(args))
            logger.debug("OSCClient.send: %s %s → %s:%d", address, args, self._host, self._port)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error("OSCClient.send: error — %s", exc)
            return False

    def batch_send(self, messages: List[Tuple[str, Any]]) -> int:
        """Send multiple OSC messages; returns the count successfully sent."""
        count = 0
        for address, value in messages:
            if isinstance(value, (list, tuple)):
                sent = self.send(address, *value)
            else:
                sent = self.send(address, value)
            if sent:
                count += 1

        logger.debug("OSCClient.batch_send: %d/%d dispatched", count, len(messages))
        return count

    def __repr__(self) -> str:
        status = "live" if self.is_available else "noop"
        return f"OSCClient({self._host}:{self._port} [{status}])"
