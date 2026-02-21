"""
Unit tests for the OSCQuery stack:
  - OSCAddressSpace node tree and JSON serialisation
  - NullOSCServer (hardware-absent fallback)
  - OSCClient noop mode
  - OSCQueryServer HTTP responses
"""

from __future__ import annotations

import json
import time
import urllib.request

import pytest

from vjlive3.osc.address_space import OSCAccess, OSCAddressSpace, OSCNode, OSCType
from vjlive3.osc.client import OSCClient
from vjlive3.osc.server import NullOSCServer


# ---------------------------------------------------------------------------
# OSCAddressSpace tests
# ---------------------------------------------------------------------------


class TestOSCAddressSpace:
    def test_register_creates_node(self) -> None:
        space = OSCAddressSpace()
        node = space.register("/fx/blur", OSCType.FLOAT, 0.5, "Blur amount")
        assert node is not None
        assert node.path == "/fx/blur"
        assert node.osc_type == OSCType.FLOAT
        assert node.value == 0.5

    def test_get_node_by_path(self) -> None:
        space = OSCAddressSpace()
        space.register("/audio/gain", OSCType.FLOAT, 1.0)
        node = space.get_node("/audio/gain")
        assert node is not None
        assert node.path == "/audio/gain"

    def test_get_node_unknown_returns_none(self) -> None:
        space = OSCAddressSpace()
        assert space.get_node("/nonexistent") is None

    def test_set_value_updates_node(self) -> None:
        space = OSCAddressSpace()
        space.register("/fx/blur", OSCType.FLOAT, 0.0)
        success = space.set_value("/fx/blur", 0.8)
        assert success is True
        node = space.get_node("/fx/blur")
        assert node is not None
        assert node.value == 0.8

    def test_set_value_unknown_path_returns_false(self) -> None:
        space = OSCAddressSpace()
        result = space.set_value("/nope", 99)
        assert result is False

    def test_intermediate_nodes_created(self) -> None:
        space = OSCAddressSpace()
        space.register("/a/b/c", OSCType.INT, 42)
        # Intermediate nodes exist
        assert space.get_node("/a") is not None
        assert space.get_node("/a/b") is not None
        assert space.get_node("/a/b/c") is not None

    def test_unregister_removes_node(self) -> None:
        space = OSCAddressSpace()
        space.register("/fx/hue", OSCType.FLOAT, 0.3)
        removed = space.unregister("/fx/hue")
        assert removed is True
        assert space.get_node("/fx/hue") is None

    def test_to_dict_structure(self) -> None:
        space = OSCAddressSpace()
        space.register("/fx/blur", OSCType.FLOAT, 0.5, "Blur", OSCAccess.READ_WRITE)
        d = space.to_dict()
        assert "DESCRIPTION" in d
        assert "CONTENTS" in d
        assert "fx" in d["CONTENTS"]

    def test_osc_node_to_dict_type_and_value(self) -> None:
        node = OSCNode(
            path="/test",
            osc_type=OSCType.INT,
            value=7,
            description="Test node",
            access=OSCAccess.READ_ONLY,
        )
        d = node.to_dict()
        assert d["TYPE"] == "i"
        assert d["VALUE"] == [7]
        assert d["ACCESS"] == OSCAccess.READ_ONLY.value

    def test_iter_nodes_visits_all(self) -> None:
        space = OSCAddressSpace()
        space.register("/a/x", OSCType.FLOAT, 1.0)
        space.register("/a/y", OSCType.FLOAT, 2.0)
        space.register("/b/z", OSCType.FLOAT, 3.0)
        paths = [n.path for n in space.iter_nodes()]
        # Root + /a + /a/x + /a/y + /b + /b/z
        assert "/a/x" in paths
        assert "/b/z" in paths


# ---------------------------------------------------------------------------
# NullOSCServer tests
# ---------------------------------------------------------------------------


class TestNullOSCServer:
    def test_starts_and_stops(self) -> None:
        srv = NullOSCServer()
        result = srv.start("0.0.0.0", 9100)
        assert result is True
        assert srv.is_running is True
        srv.stop()
        assert srv.is_running is False

    def test_handler_dispatch_via_deliver(self) -> None:
        """NullOSCServer.deliver allows injecting test messages."""
        srv = NullOSCServer()
        received: list[tuple] = []

        def handler(address: str, *args: object) -> None:
            received.append((address, args))

        srv.dispatch("/test", handler)
        srv.deliver("/test", 42)
        assert len(received) == 1
        assert received[0][0] == "/test"

    def test_registered_addresses(self) -> None:
        srv = NullOSCServer()
        srv.dispatch("/a", lambda a, *_: None)
        srv.dispatch("/b", lambda a, *_: None)
        addresses = srv.get_registered_addresses()
        assert "/a" in addresses
        assert "/b" in addresses


# ---------------------------------------------------------------------------
# OSCClient tests
# ---------------------------------------------------------------------------


class TestOSCClient:
    def test_noop_mode_when_unavailable(self) -> None:
        """Client should not raise even if UDP socket can't connect."""
        # Port 1 is privileged and will fail — client should degrade gracefully
        client = OSCClient(host="127.0.0.1", port=1)
        # send must not raise
        result = client.send("/test", 1.0)
        # May be True or False depending on whether python-osc is installed
        assert isinstance(result, bool)

    def test_repr_is_informative(self) -> None:
        client = OSCClient("localhost", 9001)
        r = repr(client)
        assert "9001" in r


# ---------------------------------------------------------------------------
# OSCQueryServer HTTP tests
# ---------------------------------------------------------------------------


class TestOSCQueryServer:
    def test_http_server_starts_and_returns_json(self) -> None:
        """Start a real HTTP server on an ephemeral port and fetch the root."""
        from vjlive3.osc.query_server import OSCQueryServer

        space = OSCAddressSpace()
        space.register("/fx/blur", OSCType.FLOAT, 0.25, "Blur")

        server = OSCQueryServer(space)
        port = 18543  # arbitrary high port; unlikely to conflict in CI
        started = server.start(host="127.0.0.1", port=port)

        if not started:
            pytest.skip("OSCQueryServer could not bind (port in use?)")

        try:
            time.sleep(0.05)  # Let the server thread start
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/") as resp:
                data = json.loads(resp.read())
            assert "CONTENTS" in data
        finally:
            server.stop()

    def test_http_server_404_for_unknown_path(self) -> None:
        from vjlive3.osc.query_server import OSCQueryServer

        space = OSCAddressSpace()
        server = OSCQueryServer(space)
        port = 18544
        started = server.start(host="127.0.0.1", port=port)

        if not started:
            pytest.skip("Cannot bind port")

        try:
            time.sleep(0.05)
            with pytest.raises(urllib.error.HTTPError) as exc_info:
                urllib.request.urlopen(f"http://127.0.0.1:{port}/nope")
            assert exc_info.value.code == 404
        finally:
            server.stop()
