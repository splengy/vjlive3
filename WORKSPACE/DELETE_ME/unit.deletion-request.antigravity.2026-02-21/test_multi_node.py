"""Tests for network/node.py (NodeInfo, NodeRegistry) and
network/coordinator.py (NodeCoordinator — stub mode, no ZMQ required).
"""
import time
import threading
import pytest
from unittest.mock import patch

from vjlive3.network.node import (
    NodeCapability, NodeInfo, NodeRegistry, NodeRole,
)
from vjlive3.network.coordinator import NodeCoordinator, MsgType


# ── NodeInfo ──────────────────────────────────────────────────────────────────

class TestNodeInfo:

    def test_defaults(self):
        n = NodeInfo(node_id="abc", host="192.168.1.1", port=5555)
        assert n.role == NodeRole.FOLLOWER
        assert n.capabilities == []
        assert n.timecode_pos == 0.0

    def test_has_capability(self):
        n = NodeInfo("a", "host", 1, capabilities=[NodeCapability.GPU])
        assert n.has_capability(NodeCapability.GPU)
        assert not n.has_capability(NodeCapability.MIDI)

    def test_touch_updates_last_seen(self):
        n = NodeInfo("a", "host", 1)
        old = n.last_seen
        time.sleep(0.01)
        n.touch()
        assert n.last_seen > old

    def test_round_trip_dict(self):
        n = NodeInfo(
            node_id="xyz",
            host="10.0.0.1",
            port=5555,
            role=NodeRole.LEADER,
            capabilities=[NodeCapability.AUDIO],
            timecode_pos=42.0,
        )
        d = n.to_dict()
        n2 = NodeInfo.from_dict(d)
        assert n2.node_id == "xyz"
        assert n2.role == NodeRole.LEADER
        assert NodeCapability.AUDIO in n2.capabilities
        assert n2.timecode_pos == pytest.approx(42.0)


# ── NodeRegistry ──────────────────────────────────────────────────────────────

class TestNodeRegistry:

    def _make_node(self, nid: str, host: str = "h") -> NodeInfo:
        return NodeInfo(node_id=nid, host=host, port=5555)

    def test_register_and_get(self):
        reg = NodeRegistry("self")
        n = self._make_node("peer1")
        reg.register(n)
        assert reg.get("peer1") is n

    def test_get_unknown_returns_none(self):
        reg = NodeRegistry("self")
        assert reg.get("ghost") is None

    def test_remove_existing(self):
        reg = NodeRegistry("self")
        reg.register(self._make_node("p"))
        assert reg.remove("p") is True
        assert reg.get("p") is None

    def test_remove_nonexistent_returns_false(self):
        reg = NodeRegistry("self")
        assert reg.remove("ghost") is False

    def test_list_live_excludes_self(self):
        reg = NodeRegistry("self")
        reg.register(self._make_node("self"))
        reg.register(self._make_node("peer1"))
        live = reg.list_live(timeout=5.0)
        ids = [n.node_id for n in live]
        assert "self" not in ids
        assert "peer1" in ids

    def test_list_live_excludes_stale(self):
        reg = NodeRegistry("self")
        stale = self._make_node("old")
        stale.last_seen -= 100.0   # way in the past
        reg.register(stale)
        live = reg.list_live(timeout=5.0)
        assert not any(n.node_id == "old" for n in live)

    def test_prune_removes_stale(self):
        reg = NodeRegistry("self")
        stale = self._make_node("old")
        stale.last_seen -= 100.0
        reg.register(stale)
        removed = reg.prune(timeout=5.0)
        assert removed == 1
        assert reg.get("old") is None

    def test_prune_does_not_remove_self(self):
        reg = NodeRegistry("self")
        self_node = self._make_node("self")
        self_node.last_seen -= 1000.0
        reg.register(self_node)
        reg.prune(timeout=5.0)
        assert reg.get("self") is not None

    def test_list_by_role(self):
        reg = NodeRegistry("self")
        reg.register(NodeInfo("a", "h", 1, role=NodeRole.LEADER))
        reg.register(NodeInfo("b", "h", 1, role=NodeRole.FOLLOWER))
        leaders = reg.list_by_role(NodeRole.LEADER)
        assert len(leaders) == 1 and leaders[0].node_id == "a"

    def test_thread_safe(self):
        errors = []
        reg = NodeRegistry("self")

        def worker(i):
            try:
                n = NodeInfo(node_id=f"n{i}", host="h", port=1)
                reg.register(n)
                _ = reg.get(f"n{i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert not errors


# ── NodeCoordinator (stub mode — no ZMQ) ─────────────────────────────────────

class TestNodeCoordinatorStub:
    """Test NodeCoordinator when ZMQ is absent (pure stub behaviour)."""

    def test_start_returns_false_without_zmq(self):
        with patch("vjlive3.network.coordinator._HAS_ZMQ", False):
            coord = NodeCoordinator(pub_port=15555, sub_port=15556)
            result = coord.start()
        assert result is False

    def test_is_running_after_start(self):
        with patch("vjlive3.network.coordinator._HAS_ZMQ", False):
            coord = NodeCoordinator(pub_port=15557, sub_port=15558)
            coord.start()
            assert coord.is_running
            coord.stop()

    def test_stop_before_start_is_safe(self):
        with patch("vjlive3.network.coordinator._HAS_ZMQ", False):
            coord = NodeCoordinator(pub_port=15559)
            coord.stop()   # should not raise

    def test_stop_is_idempotent(self):
        with patch("vjlive3.network.coordinator._HAS_ZMQ", False):
            coord = NodeCoordinator(pub_port=15560)
            coord.start()
            coord.stop()
            coord.stop()   # must not raise

    def test_broadcast_timecode_noop(self):
        with patch("vjlive3.network.coordinator._HAS_ZMQ", False):
            coord = NodeCoordinator(pub_port=15561)
            coord.start()
            result = coord.broadcast_timecode(42.0)
        assert result is False   # no ZMQ, noop

    def test_set_role(self):
        with patch("vjlive3.network.coordinator._HAS_ZMQ", False):
            coord = NodeCoordinator(pub_port=15562, role=NodeRole.FOLLOWER)
            coord.start()
            coord.set_role(NodeRole.LEADER)
            assert coord.role == NodeRole.LEADER
            coord.stop()

    def test_node_id_is_string(self):
        coord = NodeCoordinator(pub_port=15563, node_id="test-node")
        assert coord.node_id == "test-node"

    def test_registry_accessible(self):
        coord = NodeCoordinator(node_id="me", pub_port=15564)
        assert coord.registry.self_id == "me"

    def test_on_peer_join_callback_registered(self):
        coord = NodeCoordinator(pub_port=15565)
        called = []
        coord.on_peer_join(lambda n: called.append(n.node_id))
        # Manually invoke internal fire to test callback
        test_node = NodeInfo("peer", "h", 1)
        coord._fire_join(test_node)
        assert "peer" in called

    def test_on_peer_leave_callback_registered(self):
        coord = NodeCoordinator(pub_port=15566)
        left = []
        coord.on_peer_leave(lambda n: left.append(n.node_id))
        test_node = NodeInfo("gone", "h", 1)
        coord._fire_leave(test_node)
        assert "gone" in left
