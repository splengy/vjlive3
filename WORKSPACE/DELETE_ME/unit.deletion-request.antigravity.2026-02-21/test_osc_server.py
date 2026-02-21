"""Tests for P2-H2 OscServer / OscClient.

Covers:
- OscMessage: address validation, args storage
- OscServer: no-op when python-osc absent, handler registration,
  remove_handler, clear_handlers, simulate_message dispatch, default handler,
  start/stop lifecycle, is_running, count
- OscClient: degrades when python-osc absent
- Thread safety: concurrent handler registration + simulate_message
"""
import threading
from unittest.mock import MagicMock, patch

import pytest

from vjlive3.osc.server import OscClient, OscMessage, OscServer


# ── OscMessage ────────────────────────────────────────────────────────────────

class TestOscMessage:

    def test_valid_address(self):
        msg = OscMessage("/test", 1, "hello")
        assert msg.address == "/test"
        assert msg.args == (1, "hello")

    def test_invalid_address_raises(self):
        with pytest.raises(ValueError):
            OscMessage("no_slash")

    def test_repr(self):
        msg = OscMessage("/x", 42)
        assert "/x" in repr(msg)


# ── OscServer ─────────────────────────────────────────────────────────────────

class TestOscServer:

    def test_add_handler_invalid_address_raises(self):
        srv = OscServer(port=19900)
        with pytest.raises(ValueError):
            srv.add_handler("bad_address", lambda a, v: None)

    def test_simulate_message_dispatches(self):
        received = []
        srv = OscServer(port=19901)
        srv.add_handler("/test/val", lambda addr, *args: received.append((addr, args)))
        srv.simulate_message("/test/val", 0.75)
        assert len(received) == 1
        assert received[0][0] == "/test/val"
        assert received[0][1] == (0.75,)

    def test_multiple_handlers_same_address(self):
        calls = []
        srv = OscServer(port=19902)
        srv.add_handler("/x", lambda a, *v: calls.append("h1"))
        srv.add_handler("/x", lambda a, *v: calls.append("h2"))
        srv.simulate_message("/x", 1)
        assert calls == ["h1", "h2"]

    def test_remove_handler(self):
        received = []
        srv = OscServer(port=19903)

        def handler(addr, *args):
            received.append(args)

        srv.add_handler("/val", handler)
        srv.remove_handler("/val", handler)
        srv.simulate_message("/val", 99)
        assert received == []

    def test_remove_nonexistent_returns_false(self):
        srv = OscServer(port=19904)
        result = srv.remove_handler("/ghost", lambda a: None)
        assert result is False

    def test_clear_handlers(self):
        received = []
        srv = OscServer(port=19905)
        srv.add_handler("/a", lambda a, *v: received.append(v))
        srv.add_handler("/b", lambda a, *v: received.append(v))
        srv.clear_handlers()
        srv.simulate_message("/a", 1)
        srv.simulate_message("/b", 2)
        assert received == []

    def test_default_handler_called_for_unknown(self):
        caught = []
        srv = OscServer(port=19906)
        srv.set_default_handler(lambda addr, *args: caught.append(addr))
        srv.simulate_message("/unknown/addr", 1.0)
        assert "/unknown/addr" in caught

    def test_handler_error_does_not_crash_server(self):
        """A handler that raises must not propagate to caller."""
        def bad_handler(addr, *args):
            raise RuntimeError("boom")

        srv = OscServer(port=19907)
        srv.add_handler("/x", bad_handler)
        srv.simulate_message("/x", 1)  # must not raise

    def test_handler_count(self):
        srv = OscServer(port=19908)
        assert srv.handler_count == 0
        srv.add_handler("/a", lambda a: None)
        srv.add_handler("/a", lambda a: None)
        srv.add_handler("/b", lambda a: None)
        assert srv.handler_count == 3

    def test_is_not_running_initially(self):
        srv = OscServer(port=19909)
        assert not srv.is_running

    def test_stop_before_start_is_safe(self):
        srv = OscServer(port=19910)
        srv.stop()   # must not raise

    def test_noop_when_python_osc_missing(self):
        """When python-osc is unavailable, server returns False from start() but doesn't crash."""
        with patch("vjlive3.osc.server._HAS_PYTHONOSC", False):
            srv = OscServer(port=19911)
            srv.add_handler("/x", lambda a: None)  # no-ops silently
            result = srv.start()
        assert result is False

    def test_simulate_message_no_handlers_default(self):
        """simulate_message with no registered handler falls to default."""
        caught = []
        srv = OscServer(port=19912)
        srv.set_default_handler(lambda addr, *args: caught.append(addr))
        srv.simulate_message("/nothing", 1.0)
        assert len(caught) == 1

    def test_simulate_message_no_handlers_no_default(self):
        """simulate_message with nothing registered just logs — no crash."""
        srv = OscServer(port=19913)
        srv.simulate_message("/silent", 1.0)   # must not raise


# ── OscClient ─────────────────────────────────────────────────────────────────

class TestOscClient:

    def test_properties(self):
        client = OscClient("127.0.0.1", 8080)
        assert client.host == "127.0.0.1"
        assert client.port == 8080

    def test_send_returns_false_when_no_pythonosc(self):
        with patch("vjlive3.osc.server._HAS_PYTHONOSC", False):
            client = OscClient("127.0.0.1", 8080)
            result = client.send("/test", 1.0)
        assert result is False


# ── Thread safety ─────────────────────────────────────────────────────────────

class TestThreadSafety:

    def test_concurrent_handler_registration_and_dispatch(self):
        errors = []
        srv = OscServer(port=19920)
        counts = [0]

        def handler(addr, *args):
            counts[0] += 1

        def register_and_fire(i: int):
            try:
                srv.add_handler(f"/channel/{i}", handler)
                srv.simulate_message(f"/channel/{i}", float(i))
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=register_and_fire, args=(i,))
                   for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Thread errors: {errors}"
        assert counts[0] == 20
