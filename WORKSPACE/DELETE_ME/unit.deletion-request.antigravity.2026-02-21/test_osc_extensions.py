"""Tests for osc/address_space.py and osc/client.py"""
import threading
import pytest
from vjlive3.osc.address_space import OscAddressSpace, OscType, AddressNode
from vjlive3.osc.client import OscBundle, OscClient


# ── OscAddressSpace ───────────────────────────────────────────────────────────

class TestOscAddressSpace:

    def test_register_and_has(self):
        space = OscAddressSpace()
        space.register("/vjlive/intensity", OscType.FLOAT)
        assert space.has("/vjlive/intensity")

    def test_missing_returns_false(self):
        space = OscAddressSpace()
        assert not space.has("/nothing/here")

    def test_invalid_address_raises(self):
        space = OscAddressSpace()
        with pytest.raises(ValueError):
            space.register("no_slash")

    def test_get_returns_node(self):
        space = OscAddressSpace()
        space.register("/x/y/z", OscType.INT, description="test node")
        node = space.get("/x/y/z")
        assert node is not None
        assert node.description == "test node"
        assert node.type_tag == OscType.INT

    def test_get_unknown_returns_none(self):
        space = OscAddressSpace()
        assert space.get("/nonexistent") is None

    def test_intermediate_containers_created(self):
        space = OscAddressSpace()
        space.register("/a/b/c", OscType.FLOAT)
        assert space.has("/a/b/c")
        # Intermediate nodes exist but have no type_tag
        node_b = space.get("/a/b")
        assert node_b is not None
        assert node_b.type_tag is None

    def test_register_range(self):
        space = OscAddressSpace()
        space.register("/val", OscType.FLOAT, min_val=0.0, max_val=1.0)
        node = space.get("/val")
        assert node.min_val == 0.0
        assert node.max_val == 1.0

    def test_register_updates_existing(self):
        space = OscAddressSpace()
        space.register("/x", OscType.FLOAT, description="old")
        space.register("/x", OscType.INT, description="new")
        node = space.get("/x")
        assert node.type_tag == OscType.INT
        assert node.description == "new"

    def test_unregister_removes_leaf(self):
        space = OscAddressSpace()
        space.register("/a/b", OscType.FLOAT)
        assert space.unregister("/a/b") is True
        assert not space.has("/a/b")

    def test_unregister_nonexistent_returns_false(self):
        space = OscAddressSpace()
        assert space.unregister("/ghost") is False

    def test_list_addresses(self):
        space = OscAddressSpace()
        space.register("/vjlive/intensity", OscType.FLOAT)
        space.register("/vjlive/bpm", OscType.FLOAT)
        space.register("/other/val", OscType.INT)
        addr = space.list_addresses("/vjlive")
        assert "/vjlive/intensity" in addr
        assert "/vjlive/bpm" in addr
        assert "/other/val" not in addr

    def test_address_count(self):
        space = OscAddressSpace()
        space.register("/a", OscType.FLOAT)
        space.register("/b", OscType.INT)
        space.register("/c/d", OscType.STRING)
        assert space.address_count == 3

    def test_to_dict_structure(self):
        space = OscAddressSpace("TestHost", 7700)
        space.register("/val", OscType.FLOAT, description="A value")
        d = space.to_dict()
        assert "HOST_INFO" in d
        assert d["HOST_INFO"]["NAME"] == "TestHost"
        assert "CONTENTS" in d

    def test_to_dict_node_has_type(self):
        space = OscAddressSpace()
        space.register("/x", OscType.FLOAT)
        d = space.to_dict()
        assert d["CONTENTS"]["x"]["TYPE"] == OscType.FLOAT

    def test_thread_safety(self):
        errors = []
        space = OscAddressSpace()

        def worker(i):
            try:
                space.register(f"/ch/{i}", OscType.FLOAT)
                space.has(f"/ch/{i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert not errors


# ── OscBundle ─────────────────────────────────────────────────────────────────

class TestOscBundle:

    def test_add_and_iterate(self):
        b = OscBundle()
        b.add("/a", 1.0).add("/b", "hello")
        msgs = list(b)
        assert len(msgs) == 2
        assert msgs[0] == ("/a", (1.0,))
        assert msgs[1] == ("/b", ("hello",))

    def test_invalid_address_raises(self):
        with pytest.raises(ValueError):
            OscBundle().add("no_slash")

    def test_len(self):
        b = OscBundle()
        b.add("/a", 1)
        b.add("/b", 2)
        assert len(b) == 2


# ── OscClient (stub mode) ─────────────────────────────────────────────────────

class TestOscClientStub:
    """Test OscClient in stub mode (no python-osc)."""

    def test_properties(self):
        from unittest.mock import patch
        with patch("vjlive3.osc.client._HAS_PYTHONOSC", False):
            c = OscClient("127.0.0.1", 9000)
            assert c.host == "127.0.0.1"
            assert c.port == 9000

    def test_send_returns_false_when_unavailable(self):
        from unittest.mock import patch
        with patch("vjlive3.osc.client._HAS_PYTHONOSC", False):
            c = OscClient("127.0.0.1", 9000)
            assert c.send("/test", 1.0) is False

    def test_available_false_when_no_pythonosc(self):
        from unittest.mock import patch
        with patch("vjlive3.osc.client._HAS_PYTHONOSC", False):
            c = OscClient("127.0.0.1", 9000)
            assert c.available is False

    def test_invalid_address_raises(self):
        from unittest.mock import patch
        with patch("vjlive3.osc.client._HAS_PYTHONOSC", False):
            c = OscClient("127.0.0.1", 9000)
            with pytest.raises(ValueError):
                c.send("no_slash", 1.0)

    def test_send_bundle_returns_zero_when_unavailable(self):
        from unittest.mock import patch
        with patch("vjlive3.osc.client._HAS_PYTHONOSC", False):
            c = OscClient("127.0.0.1", 9000)
            b = OscBundle().add("/a", 1.0).add("/b", 2.0)
            assert c.send_bundle(b) == 0
