"""
P2-X1 ZMQ Coordinator for VJLive3
Provides low-latency inter-process and inter-node communication.
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

import zmq

_logger = logging.getLogger("vjlive3.sync.zmq_coordinator")


class ZmqRole:
    PUBLISHER = "pub"
    SUBSCRIBER = "sub"
    REQ = "req"
    REP = "rep"


@dataclass
class ZmqMessage:
    topic: str
    payload: Dict[str, Any]
    timestamp: float


class ZmqCoordinator:
    def __init__(self, node_id: str) -> None:
        self.node_id = node_id
        self.context = zmq.Context.instance()
        self.pub_socket: Optional[zmq.Socket] = None
        self.sub_sockets: list[zmq.Socket] = []
        self.poller = zmq.Poller()
        
        # topic -> list of callbacks
        self.subscriptions: dict[str, list[Callable[[ZmqMessage], None]]] = {}

    def bind_publisher(self, port: int) -> None:
        """Bind a publisher to the given port."""
        if self.pub_socket is not None:
            _logger.warning("Publisher already bound for this coordinator.")
            return

        self.pub_socket = self.context.socket(zmq.PUB)
        # Use a high water mark to prevent dropping messages if possible,
        # but don't stall the memory if subscriber is slow.
        self.pub_socket.set(zmq.SNDHWM, 1000)
        
        self.pub_socket.bind(f"tcp://*:{port}")
        _logger.info("Node %s publishing on port %d", self.node_id, port)

    def connect_subscriber(self, address: str, topics: list[str]) -> None:
        """Connect to a publisher address and subscribe to given topics."""
        sub_socket = self.context.socket(zmq.SUB)
        sub_socket.set(zmq.RCVHWM, 1000)
        
        sub_socket.connect(address)
        for topic in topics:
            sub_socket.setsockopt_string(zmq.SUBSCRIBE, topic)
            if topic not in self.subscriptions:
                self.subscriptions[topic] = []

        self.sub_sockets.append(sub_socket)
        self.poller.register(sub_socket, zmq.POLLIN)
        _logger.info("Node %s subscribed to %s for topics: %s", self.node_id, address, topics)

    def publish(self, topic: str, payload: dict) -> None:
        """Publish a message to the given topic."""
        if not self.pub_socket:
            _logger.warning("Attempted to publish without bound publisher socket.")
            return

        try:
            # Check JSON serialization eagerly to raise ValueError on non-serializable per spec
            serialized_payload = json.dumps(payload)
        except (TypeError, ValueError) as err:
            _logger.error("Failed to serialize payload to JSON for topic %s: %s", topic, err)
            raise ValueError(f"Payload not JSON serializable: {err}") from err

        timestamp = time.time()
        
        # Framing: TOPIC <space> JSON_DATA
        envelope = f"{topic} {json.dumps({'payload': payload, 'timestamp': timestamp})}"
        self.pub_socket.send_string(envelope)

    def subscribe(self, topic: str, callback: Callable[[ZmqMessage], None]) -> None:
        """Register a callback to handle incoming messages for a topic."""
        if topic not in self.subscriptions:
            self.subscriptions[topic] = []
        self.subscriptions[topic].append(callback)

    def poll_events(self, timeout_ms: int = 0) -> None:
        """Poll incoming messages on all subscriber sockets and dispatch them."""
        start_time = time.time()
        
        try:
            socks = dict(self.poller.poll(timeout_ms))
        except zmq.ZMQError as err:
            _logger.warning("Poller error: %s", err)
            return

        for sock in self.sub_sockets:
            if socks.get(sock) == zmq.POLLIN:
                self._read_and_dispatch(sock)

        elapsed_ms = (time.time() - start_time) * 1000.0
        if elapsed_ms > 10.0:  # Warn if polling blocks for >10ms
            _logger.warning("ZmqCoordinator.poll_events took %.2fms", elapsed_ms)

    def _read_and_dispatch(self, sock: zmq.Socket) -> None:
        while True:
            try:
                envelope = sock.recv_string(zmq.NOBLOCK)
            except zmq.Again:
                # No more messages on this socket
                break
            except Exception as e:
                _logger.error("Error reading from ZMQ sub socket: %s", e)
                break

            parts = envelope.split(" ", 1)
            if len(parts) == 2:
                topic_str, data_str = parts
                try:
                    data = json.loads(data_str)
                    payload = data.get("payload", {})
                    timestamp = data.get("timestamp", time.time())
                except json.JSONDecodeError:
                    _logger.warning("Received invalid JSON on topic %s", topic_str)
                    continue

                msg = ZmqMessage(topic=topic_str, payload=payload, timestamp=timestamp)

                # Route to callbacks based on prefix match
                for sub_topic, callbacks in self.subscriptions.items():
                    if topic_str.startswith(sub_topic):
                        for cb in callbacks:
                            try:
                                cb(msg)
                            except Exception as e:
                                _logger.error("Error in callback for topic %s: %s", sub_topic, e)

    def shutdown(self) -> None:
        """Cleanly terminate all sockets."""
        if self.pub_socket:
            self.pub_socket.close()
            self.pub_socket = None

        for sock in self.sub_sockets:
            self.poller.unregister(sock)
            sock.close()
        self.sub_sockets.clear()

        _logger.info("Node %s ZmqCoordinator shutdown.", self.node_id)
