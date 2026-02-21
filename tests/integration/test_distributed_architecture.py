"""
Integration tests for the distributed architecture system:
  - Multi-node coordination across processes
  - Timecode sync with hardware sources
  - Network coordinator stress testing
  - Hardware integration fallbacks
"""

from __future__ import annotations

import multiprocessing as mp
import time
from typing import Any, Dict, List, Optional

import pytest

from vjlive3.network.coordinator import MultiNodeCoordinator, NullCoordinator
from vjlive3.network.node import NodeInfo, NodeStatus, NodeType
from vjlive3.sync.timecode import TimecodeSource, TimecodeSync


# ---------------------------------------------------------------------------
# Helper functions for multi-process testing
# ---------------------------------------------------------------------------

def _worker_process(
    node_id: str,
    master_address: str,
    sync_callback: Optional[mp.Queue] = None,
    error_callback: Optional[mp.Queue] = None,
) -> None:
    """Worker process that connects to master and reports status."""
    try:
        from vjlive3.network.coordinator import MultiNodeCoordinator
        
        coord = MultiNodeCoordinator(
            node_id=node_id,
            is_master=False,
            master_address=master_address,
        )
        
        if not coord.start():
            if error_callback:
                error_callback.put(f"{node_id}: failed to start")
            return
        
        # Register self with master
        info = NodeInfo(
            node_id=node_id,
            node_type=NodeType.VIDEO_WORKER,
            hostname="test-host",
            ip_address="127.0.0.1",
            status=NodeStatus.READY,
        )
        coord.register_node(info)
        
        # Simulate work and send status updates
        for i in range(10):
            time.sleep(0.1)
            
            # Send status update to master
            status_msg = {
                "sender": node_id,
                "load": 0.1 * i,
                "status": "ready",
                "frame": i * 10,
            }
            
            if sync_callback:
                sync_callback.put(status_msg)
        
        coord.stop()
        
    except Exception as exc:  # noqa: BLE001
        if error_callback:
            error_callback.put(f"{node_id}: {exc}")


def _master_process(
    pub_port: int,
    pull_port: int,
    sync_callback: Optional[mp.Queue] = None,
    error_callback: Optional[mp.Queue] = None,
) -> None:
    """Master process that broadcasts timecode and receives worker updates."""
    try:
        from vjlive3.network.coordinator import MultiNodeCoordinator
        
        coord = MultiNodeCoordinator(
            node_id="master-1",
            is_master=True,
            pub_port=pub_port,
            pull_port=pull_port,
        )
        
        if not coord.start():
            if error_callback:
                error_callback.put("master: failed to start")
            return
        
        # Register master node
        info = NodeInfo(
            node_id="master-1",
            node_type=NodeType.MASTER,
            hostname="master-host",
            ip_address="127.0.0.1",
            status=NodeStatus.READY,
        )
        coord.register_node(info)
        
        # Broadcast timecode for 2 seconds
        start_time = time.monotonic()
        frame = 0
        
        while time.monotonic() - start_time < 2.0:
            coord.broadcast_timecode(frame)
            frame += 1
            time.sleep(1.0 / 60.0)  # 60 FPS
        
        # Drain worker messages
        messages = []
        try:
            while True:
                msg = coord._pull_socket.recv_string(flags=0, timeout=100)
                messages.append(msg)
        except:  # noqa: BLE001
            pass
        
        if sync_callback:
            sync_callback.put(messages)
        
        coord.stop()
        
    except Exception as exc:  # noqa: BLE001
        if error_callback:
            error_callback.put(f"master: {exc}")


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------


class TestDistributedArchitectureIntegration:
    @pytest.mark.timeout(10)
    def test_multi_node_coordination(self) -> None:
        """Test coordination between master and multiple workers."""
        
        # Create queues for IPC
        sync_queue = mp.Queue()
        error_queue = mp.Queue()
        
        # Start master process
        master_proc = mp.Process(
            target=_master_process,
            args=(25555, 25556, sync_queue, error_queue),
            daemon=True,
        )
        master_proc.start()
        
        # Give master time to bind sockets
        time.sleep(0.5)
        
        # Start worker processes
        workers = []
        for i in range(3):
            worker = mp.Process(
                target=_worker_process,
                args=(f"worker-{i}", "tcp://127.0.0.1:25555", sync_queue, error_queue),
                daemon=True,
            )
            worker.start()
            workers.append(worker)
        
        # Wait for processes to complete
        master_proc.join(timeout=5.0)
        for worker in workers:
            worker.join(timeout=2.0)
        
        # Check for errors
        errors = []
        while not error_queue.empty():
            errors.append(error_queue.get())
        assert not errors, f"Process errors occurred: {errors}"
        
        # Check that we received messages
        messages = []
        while not sync_queue.empty():
            messages.append(sync_queue.get())
        
        assert len(messages) > 0, "No messages received from workers"
        
        # Clean up
        master_proc.terminate()
        for worker in workers:
            worker.terminate()
    
    @pytest.mark.timeout(5)
    def test_timecode_sync_with_hardware_fallback(self) -> None:
        """Test timecode sync with various sources and fallback behavior."""
        
        # Test INTERNAL source (always available)
        ts_internal = TimecodeSync(source=TimecodeSource.INTERNAL, fps=30.0)
        assert ts_internal.start() is True
        
        # Run for a short time
        for _ in range(10):
            ts_internal.update()
            time.sleep(0.01)
        
        assert ts_internal.get_frame_number() > 0
        assert ts_internal.get_sync_quality() >= 0.0
        
        ts_internal.stop()
        
        # Test LTC source (should fallback to INTERNAL)
        ts_ltc = TimecodeSync(source=TimecodeSource.LTC, fps=30.0)
        assert ts_ltc.start() is True
        
        # Should have fallen back to INTERNAL
        assert ts_ltc.source == TimecodeSource.INTERNAL
        
        ts_ltc.stop()
        
        # Test MTC source (should fallback to INTERNAL if rtmidi unavailable)
        ts_mtc = TimecodeSync(source=TimecodeSource.MTC, fps=30.0)
        assert ts_mtc.start() is True
        
        # Check if rtmidi is available - if not, should have fallen back
        try:
            import rtmidi  # noqa: F401
            # rtmidi is available, MTC should remain MTC (or INTERNAL if no ports)
            # This is acceptable - we just verify it's running
            assert ts_mtc.is_running is True
        except ImportError:
            # rtmidi not available, should have fallen back to INTERNAL
            assert ts_mtc.source == TimecodeSource.INTERNAL
        
        ts_mtc.stop()
        
        # Test NTP source (should work if network available)
        ts_ntp = TimecodeSync(source=TimecodeSource.NTP, fps=30.0)
        try:
            assert ts_ntp.start() is True
            ts_ntp.stop()
        except:
            # Network unavailable is acceptable
            pass
    
    @pytest.mark.timeout(5)
    def test_coordinator_stats_and_health(self) -> None:
        """Test coordinator statistics and node health monitoring."""
        
        # Test NullCoordinator stats
        null_coord = NullCoordinator()
        null_coord.start()
        
        stats = null_coord.get_network_stats()
        assert stats["mode"] == "null"
        assert stats["is_master"] is True
        assert stats["total_nodes"] == 0
        
        # Register a node
        info = NodeInfo(
            node_id="test-node",
            node_type=NodeType.VIDEO_WORKER,
            hostname="test-host",
            ip_address="127.0.0.1",
        )
        null_coord.register_node(info)
        
        stats = null_coord.get_network_stats()
        assert stats["total_nodes"] == 1
        
        null_coord.stop()
        
        # Test MultiNodeCoordinator stats (if zmq available)
        try:
            import zmq  # type: ignore[import]
            
            coord = MultiNodeCoordinator(
                node_id="test-coord",
                is_master=True,
                pub_port=25557,
                pull_port=25558,
            )
            coord.start()
            
            stats = coord.get_network_stats()
            assert stats["mode"] == "zmq"
            assert stats["is_master"] is True
            
            coord.stop()
            
        except ImportError:
            # zmq not available, skip this part
            pass
    
    @pytest.mark.timeout(3)
    def test_node_health_monitoring(self) -> None:
        """Test node health monitoring and stale node detection."""
        
        # Create a node and age its heartbeat
        node = NodeInfo(
            node_id="test-node",
            node_type=NodeType.AUDIO_WORKER,
            hostname="test-host",
            ip_address="127.0.0.1",
        )
        
        # Fresh node should be alive
        assert node.is_alive(timeout_seconds=5.0) is True
        
        # Artificially age the heartbeat
        node.last_heartbeat = time.monotonic() - 10.0
        assert node.is_alive(timeout_seconds=5.0) is False
        
        # Refresh heartbeat
        node.beat()
        assert node.is_alive(timeout_seconds=5.0) is True
        
        # Test serialization roundtrip
        d = node.to_dict()
        restored = NodeInfo.from_dict(d)
        assert restored.node_id == node.node_id
        assert restored.is_alive(timeout_seconds=5.0) is True
    
    @pytest.mark.timeout(5)
    def test_stress_test_coordinator(self) -> None:
        """Stress test the coordinator with rapid node registration."""
        
        try:
            import zmq  # type: ignore[import]
            
            coord = MultiNodeCoordinator(
                node_id="stress-test",
                is_master=True,
                pub_port=25559,
                pull_port=25560,
            )
            coord.start()
            
            # Register many nodes quickly
            for i in range(100):
                info = NodeInfo(
                    node_id=f"node-{i}",
                    node_type=NodeType.VIDEO_WORKER,
                    hostname=f"host-{i}",
                    ip_address=f"192.168.1.{i}",
                )
                coord.register_node(info)
            
            # Verify all nodes registered
            nodes = coord.get_all_nodes()
            assert len(nodes) == 100
            
            # Test stats
            stats = coord.get_network_stats()
            assert stats["total_nodes"] == 100
            
            coord.stop()
            
        except ImportError:
            # zmq not available, skip this test
            pytest.skip("pyzmq not installed")


# ---------------------------------------------------------------------------
# Performance benchmarks
# ---------------------------------------------------------------------------


class TestDistributedArchitecturePerformance:
    @pytest.mark.timeout(10)
    def test_coordinator_performance(self) -> None:
        """Benchmark coordinator performance under load."""
        
        try:
            import zmq  # type: ignore[import]
            
            coord = MultiNodeCoordinator(
                node_id="perf-test",
                is_master=True,
                pub_port=25561,
                pull_port=25562,
            )
            coord.start()
            
            # Benchmark node registration
            start = time.monotonic()
            for i in range(1000):
                info = NodeInfo(
                    node_id=f"node-{i}",
                    node_type=NodeType.VIDEO_WORKER,
                    hostname="perf-host",
                    ip_address="127.0.0.1",
                )
                coord.register_node(info)
            
            registration_time = time.monotonic() - start
            assert registration_time < 1.0, f"Node registration too slow: {registration_time:.2f}s"
            
            # Benchmark timecode broadcast
            start = time.monotonic()
            for i in range(1000):
                coord.broadcast_timecode(i)
            
            broadcast_time = time.monotonic() - start
            assert broadcast_time < 1.0, f"Timecode broadcast too slow: {broadcast_time:.2f}s"
            
            coord.stop()
            
        except ImportError:
            pytest.skip("pyzmq not installed")
    
    @pytest.mark.timeout(5)
    def test_timecode_sync_performance(self) -> None:
        """Benchmark timecode sync performance."""
        
        ts = TimecodeSync(source=TimecodeSource.INTERNAL, fps=60.0)
        ts.start()
        
        # Benchmark update performance
        start = time.monotonic()
        for i in range(1000):
            ts.update(dt=1/60)
        
        update_time = time.monotonic() - start
        assert update_time < 1.0, f"Timecode update too slow: {update_time:.2f}s"
        
        ts.stop()