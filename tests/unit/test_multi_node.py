"""
Unit tests for the ZeroMQ multi-node coordination system:
  - NodeInfo heartbeat tracking
  - NodeStatus / NodeType enums
  - NullCoordinator API parity
  - MultiNodeCoordinator (with and without pyzmq)
  - Stats structure
"""

from __future__ import annotations

import time

import pytest

from vjlive3.network.node import NodeInfo, NodeStatus, NodeType
from vjlive3.network.coordinator import NullCoordinator


# ---------------------------------------------------------------------------
# NodeInfo tests
# ---------------------------------------------------------------------------


class TestNodeInfo:
    def _make_node(self, node_id: str = "n1") -> NodeInfo:
        return NodeInfo(
            node_id=node_id,
            node_type=NodeType.VIDEO_WORKER,
            hostname="host1",
            ip_address="192.168.1.10",
        )

    def test_default_status_offline(self) -> None:
        node = self._make_node()
        assert node.status == NodeStatus.OFFLINE

    def test_is_alive_immediately_after_creation(self) -> None:
        node = self._make_node()
        # Fresh node heartbeat = now, should be alive
        assert node.is_alive(timeout_seconds=5.0) is True

    def test_is_alive_after_timeout(self) -> None:
        node = self._make_node()
        # Artificially age the heartbeat
        node.last_heartbeat = time.monotonic() - 10.0
        assert node.is_alive(timeout_seconds=5.0) is False

    def test_beat_refreshes_heartbeat(self) -> None:
        node = self._make_node()
        node.last_heartbeat = time.monotonic() - 10.0
        node.beat()
        assert node.is_alive(timeout_seconds=5.0) is True

    def test_to_dict_keys(self) -> None:
        node = self._make_node()
        d = node.to_dict()
        for key in ("node_id", "node_type", "hostname", "ip_address", "status", "load"):
            assert key in d

    def test_from_dict_roundtrip(self) -> None:
        node = self._make_node("rt-1")
        node.status = NodeStatus.READY
        node.load = 0.42
        d = node.to_dict()
        restored = NodeInfo.from_dict(d)
        assert restored.node_id == "rt-1"
        assert restored.status == NodeStatus.READY
        assert abs(restored.load - 0.42) < 1e-6

    def test_node_type_values(self) -> None:
        assert NodeType.MASTER.value == "master"
        assert NodeType.VIDEO_WORKER.value == "video_worker"
        assert NodeType.DISPLAY_WORKER.value == "display_worker"


# ---------------------------------------------------------------------------
# NullCoordinator tests
# ---------------------------------------------------------------------------


class TestNullCoordinator:
    def test_start_stop(self) -> None:
        coord = NullCoordinator()
        assert coord.is_running is False
        coord.start()
        assert coord.is_running is True
        coord.stop()
        assert coord.is_running is False

    def test_is_master(self) -> None:
        coord = NullCoordinator()
        assert coord.is_master is True

    def test_register_node(self) -> None:
        coord = NullCoordinator()
        info = NodeInfo(
            node_id="w1",
            node_type=NodeType.AUDIO_WORKER,
            hostname="worker1",
            ip_address="10.0.0.2",
        )
        result = coord.register_node(info)
        assert result is True
        nodes = coord.get_all_nodes()
        assert "w1" in nodes

    def test_broadcast_timecode_does_not_raise(self) -> None:
        coord = NullCoordinator()
        coord.start()
        coord.broadcast_timecode(999)  # Must not raise
        coord.stop()

    def test_stats_structure(self) -> None:
        coord = NullCoordinator()
        coord.start()
        stats = coord.get_network_stats()
        assert "mode" in stats
        assert "total_nodes" in stats
        assert "is_master" in stats
        assert stats["mode"] == "null"
        coord.stop()

    def test_set_callbacks_does_not_raise(self) -> None:
        coord = NullCoordinator()
        coord.set_sync_callback(lambda d: None)
        coord.set_error_callback(lambda e: None)


# ---------------------------------------------------------------------------
# MultiNodeCoordinator tests (with zmq if available, ImportError otherwise)
# ---------------------------------------------------------------------------


class TestMultiNodeCoordinator:
    def test_raises_without_zmq(self) -> None:
        """If pyzmq is not installed, MultiNodeCoordinator should raise ImportError."""
        try:
            import zmq  # noqa: F401

            pytest.skip("pyzmq is present — skipping ImportError test")
        except ImportError:
            from vjlive3.network.coordinator import MultiNodeCoordinator

            with pytest.raises(ImportError):
                MultiNodeCoordinator(node_id="test")

    @pytest.mark.skipif(
        not __import__("importlib").util.find_spec("zmq"),
        reason="pyzmq not installed",
    )
    def test_start_stop_master(self) -> None:
        from vjlive3.network.coordinator import MultiNodeCoordinator

        coord = MultiNodeCoordinator(
            node_id="test-master",
            is_master=True,
            pub_port=25555,
            pull_port=25556,
        )
        started = coord.start()
        assert started is True
        assert coord.is_running is True
        coord.stop()
        assert coord.is_running is False

    @pytest.mark.skipif(
        not __import__("importlib").util.find_spec("zmq"),
        reason="pyzmq not installed",
    )
    def test_register_and_retrieve_node(self) -> None:
        from vjlive3.network.coordinator import MultiNodeCoordinator

        coord = MultiNodeCoordinator(
            node_id="test-master",
            is_master=True,
            pub_port=25557,
            pull_port=25558,
        )
        coord.start()
        info = NodeInfo(
            node_id="w1",
            node_type=NodeType.VIDEO_WORKER,
            hostname="worker",
            ip_address="127.0.0.1",
            status=NodeStatus.READY,
        )
        coord.register_node(info)
        nodes = coord.get_all_nodes()
        assert "w1" in nodes
        coord.stop()

    @pytest.mark.skipif(
        not __import__("importlib").util.find_spec("zmq"),
        reason="pyzmq not installed",
    )
    def test_stats_structure_with_zmq(self) -> None:
        from vjlive3.network.coordinator import MultiNodeCoordinator

        coord = MultiNodeCoordinator(
            node_id="stats-master",
            is_master=True,
            pub_port=25559,
            pull_port=25560,
        )
        coord.start()
        stats = coord.get_network_stats()
        assert stats["mode"] == "zmq"
        assert "node_id" in stats
        assert "is_master" in stats
        assert "total_nodes" in stats
        coord.stop()

    @pytest.mark.skipif(
        not __import__("importlib").util.find_spec("zmq"),
        reason="pyzmq not installed",
    )
    def test_broadcast_timecode_no_crash(self) -> None:
        from vjlive3.network.coordinator import MultiNodeCoordinator

        coord = MultiNodeCoordinator(
            node_id="broadcast-master",
            is_master=True,
            pub_port=25561,
            pull_port=25562,
        )
        coord.start()
        # Should not raise even with no connected subscribers
        coord.broadcast_timecode(1800)
        coord.stop()

    @pytest.mark.skipif(
        not __import__("importlib").util.find_spec("zmq"),
        reason="pyzmq not installed",
    )
    def test_stale_node_pruning(self) -> None:
        from vjlive3.network.coordinator import MultiNodeCoordinator

        coord = MultiNodeCoordinator(
            node_id="prune-master",
            is_master=True,
            pub_port=25563,
            pull_port=25564,
        )
        coord.start()
        info = NodeInfo(
            node_id="stale",
            node_type=NodeType.VIDEO_WORKER,
            hostname="stale-host",
            ip_address="127.0.0.1",
            status=NodeStatus.READY,
        )
        info.last_heartbeat = time.monotonic() - 10.0  # Make it stale
        coord.register_node(info)

        # Invoke pruning directly
        coord._prune_stale_nodes()
        assert coord._nodes["stale"].status == NodeStatus.OFFLINE
        coord.stop()
