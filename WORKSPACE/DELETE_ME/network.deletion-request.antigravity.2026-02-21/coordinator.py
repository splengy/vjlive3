"""P2-X1 — Multi-Node Coordinator (ZeroMQ backbone).

Manages peer discovery, heartbeat, and state broadcast between
VJLive3 instances on a LAN using ZeroMQ PUB/SUB + REQ/REP sockets.

Architecture:
  - LEADER publishes heartbeat + timecode on PUB socket
  - FOLLOWERs subscribe to leader PUB
  - REP socket answers peer queries (node list, capabilities)
  - NodeRegistry tracks all known peers

Falls back to a no-op stub when ZeroMQ is not installed so the
engine always imports cleanly in headless CI environments.

Dependencies: pyzmq >= 25 (optional)
"""
from __future__ import annotations

import json
import logging
import threading
import time
import uuid
from typing import Callable, Dict, List, Optional

from vjlive3.network.node import NodeCapability, NodeInfo, NodeRegistry, NodeRole

_log = logging.getLogger(__name__)

# ── Optional ZeroMQ ───────────────────────────────────────────────────────────
try:
    import zmq as _zmq
    _HAS_ZMQ = True
except ImportError:
    _zmq = None          # type: ignore[assignment]
    _HAS_ZMQ = False
    _log.warning("pyzmq not installed — NodeCoordinator will be a no-op")


# ── Message types ─────────────────────────────────────────────────────────────

class MsgType:
    HEARTBEAT  = "hb"
    HELLO      = "hello"
    BYE        = "bye"
    QUERY      = "query"
    QUERY_RESP = "query_resp"
    TC_SYNC    = "tc_sync"


# ── NodeCoordinator ───────────────────────────────────────────────────────────

PeerCallback = Callable[[NodeInfo], None]


class NodeCoordinator:
    """
    Coordinates discovery and state sync between VJLive3 nodes.

    Usage::

        coord = NodeCoordinator(
            host="0.0.0.0",
            pub_port=5555,
            sub_port=5556,
            capabilities=[NodeCapability.GPU, NodeCapability.AUDIO],
        )
        coord.on_peer_join(lambda node: print("joined:", node.node_id))
        coord.on_peer_leave(lambda node: print("left:", node.node_id))
        coord.start()
        # …
        coord.broadcast_timecode(position=12.5)
        coord.stop()

    When pyzmq is unavailable, start() returns False and all other methods
    are safe no-ops — no exceptions.
    """

    _HEARTBEAT_INTERVAL  = 1.0    # seconds between HB broadcasts
    _PRUNE_INTERVAL      = 3.0    # seconds between registry prune
    _NODE_TIMEOUT        = 5.0    # seconds before a peer is considered dead

    def __init__(
        self,
        host: str = "0.0.0.0",
        pub_port: int = 5555,    # We PUBlish on this port
        sub_port: int = 5556,    # We SUBscribe to peers on this port
        node_id: Optional[str] = None,
        role: NodeRole = NodeRole.FOLLOWER,
        capabilities: Optional[List[NodeCapability]] = None,
    ) -> None:
        self._host = host
        self._pub_port = pub_port
        self._sub_port = sub_port
        self._node_id = node_id or str(uuid.uuid4())[:8]
        self._role = role
        self._capabilities = capabilities or []

        self._registry = NodeRegistry(self_id=self._node_id)
        self._lock = threading.RLock()
        self._running = False
        self._threads: List[threading.Thread] = []

        # Callbacks
        self._on_join:  List[PeerCallback] = []
        self._on_leave: List[PeerCallback] = []

        # ZMQ context + sockets (None until start)
        self._ctx = None
        self._pub_sock = None
        self._sub_sock = None

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self, peer_addresses: Optional[List[str]] = None) -> bool:
        """Start coordinator.

        Args:
            peer_addresses: List of "tcp://host:port" strings to subscribe to.
                            If omitted, only listens (useful if peers will connect in).

        Returns:
            True if ZMQ started, False if ZMQ unavailable.
        """
        if self._running:
            return True
        if not _HAS_ZMQ:
            _log.warning("NodeCoordinator: pyzmq not available — running as stub")
            with self._lock:
                self._running = True
            return False

        try:
            ctx = _zmq.Context()
            self._ctx = ctx

            # PUB socket
            pub = ctx.socket(_zmq.PUB)
            pub.bind(f"tcp://{self._host}:{self._pub_port}")
            self._pub_sock = pub

            # SUB socket
            sub = ctx.socket(_zmq.SUB)
            sub.setsockopt(_zmq.SUBSCRIBE, b"")
            for addr in (peer_addresses or []):
                sub.connect(addr)
            self._sub_sock = sub

        except Exception as exc:
            _log.error("NodeCoordinator.start() failed: %s", exc)
            return False

        with self._lock:
            self._running = True

        # Register self
        self._registry.register(self._self_info())

        # Start background threads
        hb_thread = threading.Thread(
            target=self._heartbeat_loop, name="NC:heartbeat", daemon=True
        )
        sub_thread = threading.Thread(
            target=self._subscribe_loop, name="NC:subscribe", daemon=True
        )
        prune_thread = threading.Thread(
            target=self._prune_loop, name="NC:prune", daemon=True
        )
        self._threads = [hb_thread, sub_thread, prune_thread]
        for t in self._threads:
            t.start()

        # Announce presence
        self._send(MsgType.HELLO, self._self_info().to_dict())
        _log.info("NodeCoordinator started — id=%s role=%s", self._node_id, self._role)
        return True

    def stop(self) -> None:
        """Stop coordinator. Idempotent."""
        with self._lock:
            if not self._running:
                return
            self._running = False

        if _HAS_ZMQ and self._pub_sock:
            try:
                self._send(MsgType.BYE, {"node_id": self._node_id})
            except Exception:
                pass

        for sock in (self._pub_sock, self._sub_sock):
            if sock:
                try:
                    sock.close(linger=0)
                except Exception:
                    pass
        if self._ctx:
            try:
                self._ctx.term()
            except Exception:
                pass
        self._pub_sock = None
        self._sub_sock = None
        self._ctx = None

        for t in self._threads:
            t.join(timeout=2.0)
        self._threads.clear()
        _log.info("NodeCoordinator stopped")

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def on_peer_join(self, cb: PeerCallback) -> None:
        with self._lock:
            self._on_join.append(cb)

    def on_peer_leave(self, cb: PeerCallback) -> None:
        with self._lock:
            self._on_leave.append(cb)

    # ── Broadcast ─────────────────────────────────────────────────────────────

    def broadcast_timecode(self, position: float) -> bool:
        """Broadcast current timecode position to all peers."""
        return self._send(MsgType.TC_SYNC, {
            "node_id": self._node_id,
            "position": position,
            "ts": time.monotonic(),
        })

    def set_role(self, role: NodeRole) -> None:
        """Change this node's role and broadcast update."""
        with self._lock:
            self._role = role
        self._send(MsgType.HELLO, self._self_info().to_dict())

    # ── Registry access ───────────────────────────────────────────────────────

    @property
    def registry(self) -> NodeRegistry:
        return self._registry

    @property
    def node_id(self) -> str:
        return self._node_id

    @property
    def role(self) -> NodeRole:
        with self._lock:
            return self._role

    @property
    def is_running(self) -> bool:
        with self._lock:
            return self._running

    # ── Internal ──────────────────────────────────────────────────────────────

    def _self_info(self) -> NodeInfo:
        with self._lock:
            return NodeInfo(
                node_id=self._node_id,
                host=self._host,
                port=self._pub_port,
                role=self._role,
                capabilities=list(self._capabilities),
            )

    def _send(self, msg_type: str, payload: dict) -> bool:
        if not _HAS_ZMQ or self._pub_sock is None:
            return False
        try:
            envelope = {"type": msg_type, **payload}
            self._pub_sock.send_string(json.dumps(envelope), _zmq.NOBLOCK)
            return True
        except Exception as exc:
            _log.debug("NodeCoordinator._send error: %s", exc)
            return False

    def _heartbeat_loop(self) -> None:
        while True:
            with self._lock:
                if not self._running:
                    break
            self._send(MsgType.HEARTBEAT, {
                "node_id": self._node_id,
                "role": self._role.value,
                "ts": time.monotonic(),
            })
            time.sleep(self._HEARTBEAT_INTERVAL)

    def _subscribe_loop(self) -> None:
        """Receive and process incoming messages from peers."""
        if self._sub_sock is None:
            return
        while True:
            with self._lock:
                if not self._running:
                    break
            try:
                if self._sub_sock.poll(timeout=500):   # ms
                    raw = self._sub_sock.recv_string(flags=_zmq.NOBLOCK)
                    self._handle(raw)
            except Exception:
                time.sleep(0.05)

    def _handle(self, raw: str) -> None:
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            return

        msg_type = msg.get("type", "")
        node_id  = msg.get("node_id", "")
        if node_id == self._node_id:
            return   # own message

        if msg_type in (MsgType.HEARTBEAT, MsgType.HELLO, MsgType.TC_SYNC):
            existing = self._registry.get(node_id)
            if msg_type == MsgType.HELLO:
                info = NodeInfo.from_dict(msg)
            elif msg_type == MsgType.TC_SYNC:
                # Update timecode on existing node
                info = self._registry.get(node_id)
                if info:
                    info.timecode_pos = float(msg.get("position", 0.0))
                    info.touch()
                return
            else:
                # Heartbeat — touch or create minimal entry
                info = self._registry.get(node_id)
                if info:
                    info.touch()
                    return
                info = NodeInfo(
                    node_id=node_id,
                    host=msg.get("host", "?"),
                    port=int(msg.get("port", 0)),
                    role=NodeRole(msg.get("role", "follower")),
                )

            is_new = existing is None
            self._registry.register(info)
            if is_new:
                self._fire_join(info)

        elif msg_type == MsgType.BYE:
            node = self._registry.get(node_id)
            if node:
                self._registry.remove(node_id)
                self._fire_leave(node)

    def _prune_loop(self) -> None:
        while True:
            with self._lock:
                if not self._running:
                    break
            time.sleep(self._PRUNE_INTERVAL)
            stale: List[NodeInfo] = [
                n for n in self._registry.list_all()
                if n.node_id != self._node_id
                and (time.monotonic() - n.last_seen) >= self._NODE_TIMEOUT
            ]
            for n in stale:
                self._registry.remove(n.node_id)
                self._fire_leave(n)

    def _fire_join(self, node: NodeInfo) -> None:
        with self._lock:
            cbs = list(self._on_join)
        for cb in cbs:
            try:
                cb(node)
            except Exception as exc:
                _log.warning("on_peer_join callback error: %s", exc)

    def _fire_leave(self, node: NodeInfo) -> None:
        with self._lock:
            cbs = list(self._on_leave)
        for cb in cbs:
            try:
                cb(node)
            except Exception as exc:
                _log.warning("on_peer_leave callback error: %s", exc)


__all__ = ["NodeCoordinator", "MsgType"]
