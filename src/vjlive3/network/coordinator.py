"""
ZeroMQ Multi-Node Coordinator

Synchronises multiple VJLive3 nodes over a LAN using ZeroMQ PUB/SUB
for frame-sync broadcasts and PUSH/PULL for task dispatch.

Falls back gracefully to NullCoordinator when pyzmq is not installed.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from typing import Any, Callable, Dict, List, Optional

from vjlive3.network.node import NodeInfo, NodeStatus, NodeType

logger = logging.getLogger(__name__)

try:
    import zmq  # type: ignore[import]

    _ZMQ_AVAILABLE = True
except ImportError:
    _ZMQ_AVAILABLE = False
    logger.warning("network.coordinator: pyzmq not installed — NullCoordinator active")

# Heartbeat every second; nodes expire after 5 s of silence
_HEARTBEAT_INTERVAL = 1.0
_NODE_TIMEOUT = 5.0
_BROADCAST_FPS = 60.0


class NullCoordinator:
    """No-op coordinator for environments without pyzmq.

    METADATA constant — Prime Directive Rule 2.
    """

    METADATA = {
        "name": "NullCoordinator",
        "description": "No-op multi-node coordinator (pyzmq unavailable)",
        "version": "1.0",
    }

    def __init__(self, **_: Any) -> None:
        self._nodes: Dict[str, NodeInfo] = {}
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def is_master(self) -> bool:
        return True

    def start(self) -> bool:
        self._running = True
        return True

    def stop(self) -> None:
        self._running = False

    def register_node(self, node_info: NodeInfo) -> bool:
        self._nodes[node_info.node_id] = node_info
        return True

    def broadcast_timecode(self, frame: int) -> None:  # noqa: ARG002
        pass

    def get_network_stats(self) -> Dict[str, Any]:
        return {
            "mode": "null",
            "total_nodes": len(self._nodes),
            "active_nodes": 0,
            "is_master": True,
        }

    def get_all_nodes(self) -> Dict[str, NodeInfo]:
        return dict(self._nodes)

    def set_sync_callback(self, _: Callable[[Dict[str, Any]], None]) -> None:
        pass

    def set_error_callback(self, _: Callable[[str], None]) -> None:
        pass


class MultiNodeCoordinator:
    """Real ZeroMQ multi-node coordinator.

    Architecture
    ============
    Master node
    -----------
    - PUB socket on *pub_port* → broadcasts timecode + heartbeat JSON
    - PULL socket on *pull_port* ← receives status updates from workers

    Worker node
    -----------
    - SUB socket → subscribes to master's PUB
    - PUSH socket → sends status to master's PULL

    Usage::

        # Master
        coord = MultiNodeCoordinator(node_id="master-1", is_master=True)
        coord.start()
        # every frame:
        coord.broadcast_timecode(frame_number)

        # Worker (separate machine)
        coord = MultiNodeCoordinator(
            node_id="worker-1",
            is_master=False,
            master_address="tcp://192.168.1.10:5555",
        )
        coord.start()

    METADATA constant — Prime Directive Rule 2.
    """

    METADATA = {
        "name": "MultiNodeCoordinator",
        "description": "ZeroMQ PUB/SUB frame-sync coordinator for distributed VJLive3",
        "version": "1.0",
    }

    def __init__(
        self,
        node_id: str = "node-0",
        is_master: bool = True,
        master_address: str = "tcp://localhost:5555",
        pub_port: int = 5555,
        pull_port: int = 5556,
        fps: float = 60.0,
    ) -> None:
        if not _ZMQ_AVAILABLE:
            raise ImportError(
                "pyzmq is required for MultiNodeCoordinator. "
                "Install it or use NullCoordinator."
            )

        self._node_id = node_id
        self._is_master = is_master
        self._master_address = master_address
        self._pub_port = pub_port
        self._pull_port = pull_port
        self._fps = fps

        self._nodes: Dict[str, NodeInfo] = {}
        self._running = False
        self._last_broadcast = 0.0
        self._broadcast_interval = 1.0 / fps

        self._ctx: Optional[Any] = None  # zmq.Context
        self._pub_socket: Optional[Any] = None
        self._sub_socket: Optional[Any] = None
        self._pull_socket: Optional[Any] = None
        self._push_socket: Optional[Any] = None

        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        self._sync_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        self._error_callback: Optional[Callable[[str], None]] = None

        logger.info(
            "MultiNodeCoordinator: %s node_id=%s master=%s",
            "MASTER" if is_master else "WORKER",
            node_id,
            master_address,
        )

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def is_master(self) -> bool:
        return self._is_master

    @property
    def node_id(self) -> str:
        return self._node_id

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> bool:
        """Open ZeroMQ sockets and begin coordination loop."""
        if self._running:
            return True

        try:
            self._ctx = zmq.Context()

            if self._is_master:
                self._pub_socket = self._ctx.socket(zmq.PUB)
                self._pub_socket.bind(f"tcp://*:{self._pub_port}")

                self._pull_socket = self._ctx.socket(zmq.PULL)
                self._pull_socket.bind(f"tcp://*:{self._pull_port}")
                self._pull_socket.setsockopt(zmq.RCVTIMEO, 50)  # ms
            else:
                self._sub_socket = self._ctx.socket(zmq.SUB)
                self._sub_socket.connect(self._master_address)
                self._sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")
                self._sub_socket.setsockopt(zmq.RCVTIMEO, 50)  # ms

                push_addr = self._master_address.replace(
                    f":{5555}", f":{self._pull_port}"
                )
                # Derive pull port address from master pub address
                host = self._master_address.rsplit(":", 1)[0]
                self._push_socket = self._ctx.socket(zmq.PUSH)
                self._push_socket.connect(f"{host}:{self._pull_port}")

            self._running = True
            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._coordination_loop,
                daemon=True,
                name=f"Coordinator-{'master' if self._is_master else 'worker'}",
            )
            self._thread.start()

            logger.info(
                "MultiNodeCoordinator.start: %s running",
                "MASTER" if self._is_master else "WORKER",
            )
            return True

        except Exception as exc:  # noqa: BLE001
            logger.error("MultiNodeCoordinator.start: %s", exc)
            self._teardown_sockets()
            if self._error_callback:
                self._error_callback(str(exc))
            return False

    def stop(self) -> None:
        """Shutdown sockets and background thread."""
        if not self._running:
            return

        self._running = False
        self._stop_event.set()

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

        self._teardown_sockets()
        logger.info("MultiNodeCoordinator: stopped")

    # ------------------------------------------------------------------
    # Node registry
    # ------------------------------------------------------------------

    def register_node(self, node_info: NodeInfo) -> bool:
        """Register or update a node in the node table."""
        self._nodes[node_info.node_id] = node_info
        logger.info("MultiNodeCoordinator: registered node %s (%s)", node_info.node_id, node_info.node_type.value)
        return True

    def get_all_nodes(self) -> Dict[str, NodeInfo]:
        return dict(self._nodes)

    def is_node_active(self, node_id: str) -> bool:
        node = self._nodes.get(node_id)
        return node is not None and node.is_alive(_NODE_TIMEOUT)

    # ------------------------------------------------------------------
    # Timecode broadcast
    # ------------------------------------------------------------------

    def broadcast_timecode(self, frame: int) -> None:
        """Master: publish a timecode sync message to all subscribers."""
        if not (self._is_master and self._pub_socket and self._running):
            return

        now = time.monotonic()
        if now - self._last_broadcast < self._broadcast_interval:
            return  # rate-limit to configured FPS

        msg = json.dumps(
            {"type": "timecode", "frame": frame, "ts": time.time(), "sender": self._node_id}
        )
        try:
            self._pub_socket.send_string(msg, zmq.NOBLOCK)
            self._last_broadcast = now
        except Exception as exc:  # noqa: BLE001
            logger.debug("MultiNodeCoordinator.broadcast_timecode: %s", exc)

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_network_stats(self) -> Dict[str, Any]:
        """Return a stats dict snapshot."""
        active = sum(1 for n in self._nodes.values() if n.is_alive(_NODE_TIMEOUT))
        return {
            "mode": "zmq",
            "node_id": self._node_id,
            "is_master": self._is_master,
            "total_nodes": len(self._nodes),
            "active_nodes": active,
            "broadcast_fps": self._fps,
            "running": self._running,
        }

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def set_sync_callback(self, fn: Callable[[Dict[str, Any]], None]) -> None:
        self._sync_callback = fn

    def set_error_callback(self, fn: Callable[[str], None]) -> None:
        self._error_callback = fn

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _coordination_loop(self) -> None:
        """60 Hz loop: master sends heartbeats + prunes stale nodes;
        workers receive and forward to callback."""
        heartbeat_timer = 0.0
        interval = 1.0 / 60.0

        while self._running and not self._stop_event.is_set():
            now = time.monotonic()

            if self._is_master:
                # Periodic heartbeat
                if now - heartbeat_timer >= _HEARTBEAT_INTERVAL:
                    self._send_heartbeat()
                    self._prune_stale_nodes()
                    heartbeat_timer = now

                # Drain worker status messages
                self._drain_pull()
            else:
                # Receive master messages
                self._receive_from_master()

            self._stop_event.wait(timeout=interval)

    def _send_heartbeat(self) -> None:
        if not self._pub_socket:
            return
        msg = json.dumps(
            {"type": "heartbeat", "sender": self._node_id, "ts": time.time()}
        )
        try:
            self._pub_socket.send_string(msg, zmq.NOBLOCK)
        except Exception:  # noqa: BLE001
            pass

    def _drain_pull(self) -> None:
        if not self._pull_socket:
            return
        try:
            while True:
                raw = self._pull_socket.recv_string()
                data = json.loads(raw)
                self._handle_worker_message(data)
        except zmq.Again:
            pass  # no more messages
        except Exception as exc:  # noqa: BLE001
            logger.debug("MultiNodeCoordinator._drain_pull: %s", exc)

    def _receive_from_master(self) -> None:
        if not self._sub_socket:
            return
        try:
            raw = self._sub_socket.recv_string()
            data = json.loads(raw)
            if self._sync_callback:
                self._sync_callback(data)
        except zmq.Again:
            pass  # no message this tick
        except Exception as exc:  # noqa: BLE001
            logger.debug("MultiNodeCoordinator._receive_from_master: %s", exc)

    def _handle_worker_message(self, data: Dict[str, Any]) -> None:
        """Process a status/heartbeat message received from a worker."""
        sender = data.get("sender")
        if sender and sender in self._nodes:
            self._nodes[sender].beat()
            load = data.get("load")
            if load is not None:
                self._nodes[sender].load = float(load)
            status = data.get("status")
            if status:
                try:
                    self._nodes[sender].status = NodeStatus(status)
                except ValueError:
                    pass

    def _prune_stale_nodes(self) -> None:
        """Mark nodes that have stopped heartbeating as OFFLINE."""
        for node in self._nodes.values():
            if not node.is_alive(_NODE_TIMEOUT):
                if node.status != NodeStatus.OFFLINE:
                    logger.info(
                        "MultiNodeCoordinator: node %s went offline", node.node_id
                    )
                    node.status = NodeStatus.OFFLINE

    def _teardown_sockets(self) -> None:
        """Close all ZeroMQ sockets and destroy context."""
        for sock_attr in ("_pub_socket", "_sub_socket", "_pull_socket", "_push_socket"):
            sock = getattr(self, sock_attr, None)
            if sock is not None:
                try:
                    sock.close(linger=0)
                except Exception:  # noqa: BLE001
                    pass
                setattr(self, sock_attr, None)

        if self._ctx is not None:
            try:
                self._ctx.term()
            except Exception:  # noqa: BLE001
                pass
            self._ctx = None
