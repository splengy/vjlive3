"""P2-H2 extension — dedicated OSC Client module.

Separates client concerns from server (osc/server.py).
Supports:
- Fire-and-forget UDP send (SimpleUDPClient wrapper)
- Batch send (multiple messages per call)
- Message builder with type inference
- Graceful no-op when python-osc is absent

Dependencies: python-osc >= 1.8 (optional)
"""
from __future__ import annotations

import logging
from typing import Any, List, Optional, Sequence, Tuple

_log = logging.getLogger(__name__)

try:
    from pythonosc.udp_client import SimpleUDPClient as _UDPClient
    from pythonosc.osc_message_builder import OscMessageBuilder as _MsgBuilder
    _HAS_PYTHONOSC = True
except ImportError:
    _HAS_PYTHONOSC = False
    _log.warning("python-osc not installed — OscClient is no-op")


# ── OscBundle (simple grouping) ───────────────────────────────────────────────

class OscBundle:
    """A list of (address, args) messages to send atomically."""

    def __init__(self) -> None:
        self._messages: List[Tuple[str, tuple]] = []

    def add(self, address: str, *args: Any) -> "OscBundle":
        """Append a message to the bundle. Returns self for chaining."""
        if not address.startswith("/"):
            raise ValueError(f"OSC address must start with '/': {address!r}")
        self._messages.append((address, args))
        return self

    def __iter__(self):
        return iter(self._messages)

    def __len__(self) -> int:
        return len(self._messages)


# ── OscClient ─────────────────────────────────────────────────────────────────

class OscClient:
    """
    UDP OSC client — send messages and bundles to a remote OSC host.

    Usage::

        client = OscClient("192.168.1.100", port=8000)
        client.send("/vjlive/intensity", 0.75)
        client.send("/vjlive/bpm", 120.0)

        bundle = OscBundle()
        bundle.add("/a", 1.0).add("/b", 2.0)
        client.send_bundle(bundle)

    Falls back silently to no-op when python-osc is unavailable.
    Thread-safe: ``send`` / ``send_bundle`` can be called from any thread.
    """

    def __init__(self, host: str, port: int) -> None:
        self._host = host
        self._port = port
        self._client: Optional[Any] = None

        if _HAS_PYTHONOSC:
            try:
                self._client = _UDPClient(host, port)
                _log.debug("OscClient ready → %s:%d", host, port)
            except Exception as exc:
                _log.warning("OscClient init failed (%s:%d): %s", host, port, exc)

    # ── Send ──────────────────────────────────────────────────────────────────

    def send(self, address: str, *args: Any) -> bool:
        """Send a single OSC message.

        Args:
            address: OSC address (must start with '/').
            *args:   Message arguments (int, float, str, bool, bytes supported).

        Returns:
            True on success, False if unavailable or send failed.
        """
        if self._client is None:
            return False
        if not address.startswith("/"):
            raise ValueError(f"OSC address must start with '/': {address!r}")
        try:
            builder = _MsgBuilder(address=address)
            for arg in args:
                builder.add_arg(self._coerce(arg))
            self._client.send(builder.build())
            return True
        except Exception as exc:
            _log.warning("OscClient.send(%s) failed: %s", address, exc)
            return False

    def send_bundle(self, bundle: OscBundle) -> int:
        """Send all messages in a bundle. Returns number successfully sent."""
        sent = 0
        for address, args in bundle:
            if self.send(address, *args):
                sent += 1
        return sent

    # ── Type coercion ─────────────────────────────────────────────────────────

    @staticmethod
    def _coerce(val: Any) -> Any:
        """Ensure value is an OSC-legal type (int, float, str, bytes, bool)."""
        if isinstance(val, bool):
            return val
        if isinstance(val, int):
            return val
        if isinstance(val, float):
            return val
        if isinstance(val, (str, bytes)):
            return val
        # Try numeric coercion
        try:
            return float(val)
        except (TypeError, ValueError):
            return str(val)

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int:
        return self._port

    @property
    def available(self) -> bool:
        """True when python-osc is installed and client is initialised."""
        return self._client is not None


__all__ = ["OscBundle", "OscClient"]
