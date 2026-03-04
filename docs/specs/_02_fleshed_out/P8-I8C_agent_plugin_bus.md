# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P8-I8C_agent_plugin_bus.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P8-I8C — Agent Plugin Bus

**What This Module Does**

Implements a high-performance, thread-safe message bus for inter-agent and agent-to-plugin communication in VJLive3. This bus provides publish/subscribe semantics, priority-based message routing, guaranteed delivery for critical messages, and dead-letter queues for failed deliveries. It serves as the central nervous system for all autonomous agent interactions, enabling coordination between multiple AI agents (julie-roo, maxx-roo, desktop-roo) and the plugin ecosystem.

---

## Architecture Decisions

- **Pattern:** Event Bus + Priority Queue + Dead Letter Queue
- **Rationale:** Multiple autonomous agents need to communicate reliably without blocking each other. Priority ensures critical messages (emergency stop, state sync) get through first. Dead letter queues prevent message loss and enable debugging.
- **Constraints:**
  - Must support 60 FPS real-time operation (no blocking in hot path)
  - Must handle multiple concurrent publishers and subscribers
  - Must guarantee delivery for system-critical messages
  - Must support message filtering and routing rules
  - Must provide message tracing for debugging agent interactions
  - Must not become a bottleneck as agent count scales

---

## Legacy References

| Codebase | File | Class/Function | Status |
|----------|------|----------------|--------|
| VJlive-1 | `core/depth_data_bus.py` | `DepthDataBus` | Port — singleton bus pattern |
| VJlive-1 | `core/effects/effect_bus.py` | `EffectBus` | Port — auxiliary bus routing |
| VJlive-2 | `core/plugin_api.py` | `PluginBase` | Port — plugin communication |
| VJlive-2 | `web_ui/src/contexts/MixerContext.jsx` | `MixerProvider` | Port — context-based messaging |
| VJlive-2 | `core/coordination/load_balancer.py` | `LoadBalancer` | Port — task distribution |

---

## Public Interface

```python
class AgentPluginBus:
    def __init__(self, config: BusConfig) -> None:...
    def publish(self, channel: str, message: dict, priority: int = 0) -> None:...
    def subscribe(self, channel: str, callback: Callable, filter: Optional[dict] = None) -> str:...
    def unsubscribe(self, subscription_id: str) -> None:...
    def broadcast(self, message: dict, priority: int = 0) -> None:...
    def request(self, channel: str, message: dict, timeout: float = 5.0) -> dict:...
    def get_subscribers(self, channel: str) -> List[str]:...
    def get_message_stats(self) -> dict:...
    def get_dead_letters(self) -> List[dict]:...
    def retry_dead_letters(self) -> int:...
    def clear_dead_letters(self) -> None:...
    def shutdown(self) -> None:...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `config` | `BusConfig` | Bus configuration | Must include all required parameters |
| `channel` | `str` | Message channel name | Must be unique, no wildcards |
| `message` | `dict` | Message payload | Must be JSON-serializable |
| `priority` | `int` | Message priority (0-9) | 0=lowest, 9=highest |
| `callback` | `Callable` | Subscription callback | Must accept message dict |
| `filter` | `dict` | Message filter criteria | Optional, matches message fields |
| `subscription_id` | `str` | Unique subscription ID | Returned by subscribe() |
| `timeout` | `float` | Request timeout (seconds) | Must be > 0 |
| **Output** | `dict` or `None` | Response message or None | None if no response or timeout |

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `json` — message serialization — fallback: use pickle (security risk)
  - `threading` — thread safety — fallback: single-threaded mode
  - `queue` — priority queue — fallback: use list (no priority)
  - `time` — timeouts and delays — fallback: no timeout
  - `logging` — debug tracing — fallback: print to stderr
- Internal modules this depends on:
  - `vjlive3.core.context` — context for agent identity
  - `vjlive3.core.scheduler` — scheduled message delivery
  - `vjlive3.core.monitoring` — performance metrics
  - `vjlive3.plugins.manager` — plugin discovery

---

## Error Cases

| Error Condition | Exception / Response | Recovery |
|-----------------|---------------------|----------|
| Invalid channel | `ValueError("Invalid channel")` | Use valid channel name |
| Message too large | `MessageTooLargeError` | Split message or increase limit |
| Queue full | `QueueFullError` | Retry with backoff or drop low-priority |
| Subscription not found | `KeyError("Subscription not found")` | Check subscription ID |
| Dead letter overflow | `DeadLetterOverflowError` | Clear dead letters or increase limit |
| Serialization error | `SerializationError` | Use JSON-serializable data |
| Timeout on request | `TimeoutError` | Increase timeout or check subscriber |

---

## Configuration Schema

| Field | Type | Default | Range / Constraints | Description |
|-------|------|---------|-------------------|-------------|
| `max_queue_size` | `int` | `10000` | `100 - 1000000` | Maximum messages in queue |
| `max_message_size` | `int` | `1048576` | `1024 - 10485760` | Max message size (bytes) |
| `default_timeout` | `float` | `5.0` | `0.1 - 300.0` | Default request timeout (s) |
| `dead_letter_limit` | `int` | `1000` | `10 - 10000` | Max dead letters stored |
| `priority_levels` | `int` | `10` | `1 - 10` | Number of priority levels |
| `trace_enabled` | `bool` | `False` | — | Enable message tracing |
| `trace_buffer_size` | `int` | `1000` | `10 - 10000` | Trace buffer size |
| `stats_interval` | `int` | `60` | `1 - 3600` | Stats collection interval (s) |

---

## State Management

- **Per-message state:** (ephemeral, cleared after delivery)
  - Message ID
  - Priority
  - Timestamp
  - Retry count
- **Persistent state:** (survives across restarts)
  - Dead letter queue
  - Message statistics
  - Subscription registry (recovered on restart)
- **Initialization state:** (set once at startup)
  - Priority queues (one per priority level)
  - Dead letter queue
  - Statistics collector
  - Trace buffer
- **Cleanup required:** Yes — stop all processing, flush queues, clear resources

---

## Message Priority Levels

| Priority | Use Case | Delivery Guarantee |
|----------|----------|-------------------|
| 9 | Emergency stop, system halt | Immediate, preemptive |
| 8 | Agent state sync, heartbeat | High priority queue |
| 7 | Plugin load/unload | High priority queue |
| 6 | Parameter changes, snapshots | Normal priority queue |
| 5 | Effect enable/disable | Normal priority queue |
| 4 | UI updates, status messages | Normal priority queue |
| 3 | Performance metrics | Low priority queue |
| 2 | Debug messages, telemetry | Low priority queue |
| 1 | Log messages, verbose debug | Lowest priority queue |
| 0 | Background tasks, cleanup | Lowest priority queue |

---

## Communication Patterns

### 1. Publish-Subscribe (Fire-and-Forget)
```python
bus = AgentPluginBus(config)

# Publisher
bus.publish('agent.state.update', {
    'agent': 'julie-roo',
    'state': 'evolving',
    'params': {'chaos': 5.2}
}, priority=6)

# Subscriber
def on_state_update(msg):
    print(f"Agent state: {msg['agent']} -> {msg['state']}")

sub_id = bus.subscribe('agent.state.update', on_state_update)
```

### 2. Request-Response (Synchronous)
```python
# Requester
response = bus.request('plugin.get_params', {
    'plugin_id': 'depth_cloud_effect'
}, timeout=2.0)

if response:
    print(f"Plugin params: {response['params']}")
else:
    print("No response or timeout")

# Responder (in plugin)
def on_get_params(msg):
    plugin = plugin_manager.get(msg['plugin_id'])
    return {
        'params': plugin.get_parameters(),
        'timestamp': time.time()
    }

bus.subscribe('plugin.get_params', on_get_params)
```

### 3. Broadcast (To All Agents)
```python
# Send to all agents
bus.broadcast({
    'type': 'system.shutdown',
    'reason': 'user_requested',
    'delay': 5.0
}, priority=9)
```

### 4. Filtered Subscription
```python
# Only receive messages from specific agent
sub_id = bus.subscribe('agent.state.update', on_state_update, 
                       filter={'agent': 'maxx-roo'})
```

---

## Thread Safety Model

- **Lock-free reads:** Message delivery uses atomic operations where possible
- **Per-queue locks:** Each priority queue has its own lock to minimize contention
- **Publisher blocks only if queue full:** Publishers block briefly if queue at capacity
- **Subscriber callbacks execute in separate thread pool:** Prevent long-running callbacks from blocking bus
- **Dead letter processing runs asynchronously:** No impact on message delivery

---

## Performance Considerations

- **Hot path (publish):** < 100μs for lock acquisition + enqueue
- **Delivery latency:** < 1ms for high-priority messages, < 10ms for normal
- **Throughput:** Target 10,000+ messages/sec sustained
- **Memory overhead:** ~1KB per 1000 queued messages
- **Scalability:** Linear scaling with CPU cores (per-queue locking)

---

## Dead Letter Queue

Messages that fail delivery (no subscribers, serialization error, timeout) are moved to dead letter queue for analysis:

```python
dead_letters = bus.get_dead_letters()
for dl in dead_letters:
    print(f"Failed: {dl['channel']} - {dl['error']}")
    # Retry or debug
```

Automatic retry: Call `bus.retry_dead_letters()` to attempt redelivery after fixing issues.

---

## Message Tracing

Enable tracing for debugging agent interactions:

```python
config = BusConfig(trace_enabled=True, trace_buffer_size=5000)
bus = AgentPluginBus(config)

# Get recent message trace
trace = bus.get_trace()  # Returns last N messages
for msg in trace:
    print(f"{msg['timestamp']}: {msg['channel']} from {msg['sender']}")
```

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | Module starts without crashing if hardware absent |
| `test_publish_subscribe` | Basic pub/sub works correctly |
| `test_priority_ordering` | High-priority messages delivered first |
| `test_multiple_subscribers` | All subscribers receive copies |
| `test_filtered_subscription` | Filters work correctly |
| `test_request_response` | Request-response pattern works |
| `test_broadcast` | Broadcast reaches all subscribers |
| `test_dead_letters` | Failed messages go to dead letter queue |
| `test_thread_safety` | Concurrent access doesn't corrupt state |
| `test_performance` | Throughput and latency meet requirements |
| `test_trace` | Message tracing captures correct data |
| `test_queue_overflow` | Queue overflow handled gracefully |
| `test_shutdown` | Clean shutdown releases resources |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-8] P8-I8C: Agent Plugin Bus` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES  

Use these to fill in the spec. These are the REAL implementations:

### core/depth_data_bus.py (L1-20) [VJlive (Original)]
```python
"""
DepthDataBus — Global Depth Data Distribution Hub

Central singleton for sharing depth camera data across the VJLive app.
Any depth source (Astra, RealSense, ML estimator) publishes here.
Any consumer (effects, nodes, WebSocket handlers) reads from here.

Inspired by Z-Vector's approach: depth is a first-class 3D signal,
not just a 2D texture.
"""

import threading
import time
import logging
import numpy as np
from typing import Optional, Dict, List, Callable, Tuple, Any

logger = logging.getLogger(__name__)

# Astra S approximate intrinsics (640x480 depth mode)
```

This shows the singleton bus pattern with thread-safe publish/subscribe.

### core/depth_data_bus.py (L40-68) [VJlive (Original)]
```python
class DepthDataBus:
    """
    Global depth data distribution hub.

    Thread-safe publish/subscribe pattern for depth data.
    Supports multiple sources (keyed by source_id) with one "active" source.
    """

    def __init__(self):
        self._lock = threading.RLock()

        # Latest data from all sources
        self._sources: Dict[str, Dict[str, Any]] = {}
        self._active_source_id: Optional[str] = None

        # Camera intrinsics for depth→3D conversion
        self._fx = DEFAULT_FX
        self._fy = DEFAULT_FY
        self._cx = DEFAULT_CX
        self._cy = DEFAULT_CY

        # Cached point cloud (recomputed on new depth frame)
        self._point_cloud: Optional[np.ndarray] = None
        self._point_cloud_colors: Optional[np.ndarray] = None
        self._point_cloud_stamp: float = 0.0

        # Depth slice cache
        self._slice_cache: Dict[Tuple[float, float], np.ndarray] = {}
        self._slice_stamp: float = 0.0

        # Subscribers for push-based updates
        self._subscribers: List[Callable] = []

        # Stats
        self._publish_count: int = 0
        self._last_publish_time: float = 0.0

        logger.info("DepthDataBus initialized")
```

This demonstrates the core bus structure: lock, data storage, subscribers, and statistics.

### core/depth_data_bus.py (L105-145) [VJlive (Original)]
```python
    def publish(
        self,
        source_id: str,
        depth_raw: Optional[np.ndarray] = None,
        depth_filtered: Optional[np.ndarray] = None,
        color: Optional[np.ndarray] = None,
        depth_colorized: Optional[np.ndarray] = None,
        objects: Optional[List] = None,
    ):
        """
        Publish depth data from a source.

        Args:
            source_id: Unique identifier for the source (e.g., 'astra_0')
            depth_raw: Raw 16-bit depth in millimeters (uint16, HxW)
            depth_filtered: Filtered/smoothed depth in meters (float32, HxW)
            color: RGB camera frame (uint8, HxWx3)
            depth_colorized: Colorized depth for preview (uint8, HxWx3)
            objects: List of DetectedObject instances
        """
        now = time.time()

        with self._lock:
            source_data = self._sources.get(source_id, {})
            source_data['last_update'] = now

            if depth_raw is not None:
                source_data['depth_raw'] = depth_raw
            if depth_filtered is not None:
                source_data['depth_filtered'] = depth_filtered
            if color is not None:
                source_data['color'] = color
            if depth_colorized is not None:
                source_data['depth_colorized'] = depth_colorized
            if objects is not None:
                source_data['objects'] = objects

            self._sources[source_id] = source_data
            self._active_source_id = source_id
            self._publish_count += 1
            self._last_publish_time = now

        # Notify subscribers outside lock to avoid deadlocks
        for callback in self._subscribers:
            try:
                callback(source_id)
            except Exception as e:
                logger.warning(f"Subscriber callback failed: {e}")
```

This shows the publish pattern with lock management and subscriber notification.

### core/effects/effect_bus.py (L1-30) [VJlive (Original)]
```python
"""
Effect Bus - Send/Return Routing for VJLive.

Provides auxiliary effect busses similar to audio mixing consoles.
Multiple sources can send to a shared bus, which processes through
an effect and returns the result for mixing.

Usage:
    # Create a reverb bus
    reverb_bus = EffectBus('reverb_bus', reverb_effect, chain.width, chain.height)
    
    # Add sends from multiple decks
    reverb_bus.add_send('deck_a', 0.5)  # 50% send
    reverb_bus.add_send('deck_b', 0.3)  # 30% send
    
    # Process in render loop
    bus_output = reverb_bus.process(input_textures)
"""

from typing import Dict, Optional

class EffectBus:
    """Auxiliary send/return bus for effects processing."""
    
    def __init__(self, name: str, effect, width: int, height: int):
        self.name = name
        self.effect = effect
        self.width = width
        self.height = height
        self.sends: Dict[str, float] = {}  # source_id -> send level
        self.return_level: float = 1.0
        self.muted: bool = False
```

This demonstrates a specialized bus for effect routing with send/return semantics.

### core/plugin_api.py (L97-116) [VJlive-2 (Legacy)]
```python
    def schedule(self, delay_seconds: float, callback: Callable):
        """Schedule callback after delay."""
        try:
            if hasattr(self._matrix, 'scheduler'):
                if hasattr(self._matrix.scheduler, 'schedule'):
                    self._matrix.scheduler.schedule(delay_seconds, callback)
                elif hasattr(self._matrix.scheduler, 'add_timer'):
                    self._matrix.scheduler.add_timer(delay_seconds, callback)
            elif hasattr(self._matrix, 'schedule'):
                self._matrix.schedule(delay_seconds, callback)
            else:
                logger.debug(f"Matrix does not support scheduling — {delay_seconds}s")
        except Exception as e:
            logger.warning(f"Failed to schedule callback for {delay_seconds}s: {e}")
```

This shows defensive programming with fallback mechanisms for bus operations.

---

## Notes for Implementers

1. **Core Concept**: The Agent Plugin Bus is the central communication hub for all agent and plugin interactions, providing reliable, priority-based message delivery with dead letter handling.

2. **Singleton Pattern**: The bus should be a singleton accessible via `get_agent_plugin_bus()` to ensure a single point of coordination.

3. **Thread Safety**: All public methods must be thread-safe. Use per-queue locks to minimize contention.

4. **Priority Queuing**: Implement separate queues per priority level. Always drain higher-priority queues first.

5. **Dead Letter Handling**: Messages that fail delivery (no subscribers, errors, timeouts) must be moved to dead letter queue with error details for debugging.

6. **Message Tracing**: Optional tracing captures message flow for debugging agent interactions. Keep trace buffer circular to avoid memory growth.

7. **Performance**: Minimize lock contention. Use lock-free data structures where possible. Keep critical path (publish) as short as possible.

8. **Backpressure**: When queues fill, apply backpressure by blocking publishers or dropping low-priority messages based on config.

9. **Subscription Management**: Subscriptions must be uniquely identifiable to allow proper cleanup. Use UUIDs for subscription IDs.

10. **Request-Response**: Implement request-response pattern with correlation IDs to match responses to requests. Use timeout to avoid blocking forever.

---

## Implementation Tips

1. **Python Implementation**:
   ```python
   import threading
   import time
   import uuid
   import json
   from queue import Queue, Empty, Full
   from typing import Dict, List, Callable, Optional, Any
   from dataclasses import dataclass, field
   from enum import Enum
   
   class MessagePriority(Enum):
       LOWEST = 0
       LOW = 2
       NORMAL = 5
       HIGH = 7
       HIGHEST = 9
   
   @dataclass
   class BusMessage:
       id: str
       channel: str
       payload: dict
       priority: int
       timestamp: float
       sender: Optional[str] = None
       correlation_id: Optional[str] = None
   
   @dataclass
   class Subscription:
       id: str
       channel: str
       callback: Callable
       filter: Optional[dict]
       subscriber_id: str
   
   class AgentPluginBus:
       def __init__(self, config: BusConfig):
           self.config = config
           self._lock = threading.RLock()
           
           # Priority queues (0-9)
           self._queues: List[Queue] = [
               Queue(maxsize=config.max_queue_size) 
               for _ in range(config.priority_levels)
           ]
           
           # Subscriptions by channel
           self._subscriptions: Dict[str, List[Subscription]] = {}
           self._subscription_by_id: Dict[str, Subscription] = {}
           
           # Dead letter queue
           self._dead_letters: List[dict] = []
           
           # Statistics
           self._stats = {
               'published': 0,
               'delivered': 0,
               'failed': 0,
               'dead_letters': 0,
           }
           
           # Worker threads for delivery
           self._workers: List[threading.Thread] = []
           self._running = True
           
           # Start worker threads
           self._start_workers()
       
       def publish(self, channel: str, message: dict, priority: int = 0):
           """Publish message to channel."""
           if priority < 0 or priority >= self.config.priority_levels:
               raise ValueError(f"Priority must be 0-{self.config.priority_levels-1}")
           
           msg = BusMessage(
               id=str(uuid.uuid4()),
               channel=channel,
               payload=message,
               priority=priority,
               timestamp=time.time(),
               sender=self._get_agent_id()
           )
           
           # Enqueue in priority queue
           try:
               self._queues[priority].put(msg, block=True, timeout=1.0)
               self._stats['published'] += 1
           except Full:
               # Queue full — move to dead letters or drop
               self._dead_letters.append({
                   'message': msg,
                   'error': 'Queue full',
                   'timestamp': time.time()
               })
               self._stats['failed'] += 1
       
       def subscribe(self, channel: str, callback: Callable, 
                     filter: Optional[dict] = None) -> str:
           """Subscribe to channel with optional filter."""
           sub_id = str(uuid.uuid4())
           subscription = Subscription(
               id=sub_id,
               channel=channel,
               callback=callback,
               filter=filter,
               subscriber_id=self._get_agent_id()
           )
           
           with self._lock:
               self._subscriptions.setdefault(channel, []).append(subscription)
               self._subscription_by_id[sub_id] = subscription
           
           return sub_id
       
       def _deliver_message(self, msg: BusMessage):
           """Deliver message to all matching subscribers."""
           with self._lock:
               subscriptions = self._subscriptions.get(msg.channel, [])
           
           for sub in subscriptions:
               # Apply filter if present
               if sub.filter and not self._matches_filter(msg.payload, sub.filter):
                   continue
               
               try:
                   # If callback expects response (request pattern)
                   result = sub.callback(msg.payload)
                   if result and msg.correlation_id:
                       # Send response
                       self.publish(
                           f"response.{msg.correlation_id}",
                           {'result': result, 'message_id': msg.id}
                       )
               except Exception as e:
                   # Move to dead letters
                   self._dead_letters.append({
                       'message': msg,
                       'subscription': sub.id,
                       'error': str(e),
                       'timestamp': time.time()
                   })
                   self._stats['failed'] += 1
           
           self._stats['delivered'] += 1
       
       def _matches_filter(self, payload: dict, filter: dict) -> bool:
           """Check if payload matches filter criteria."""
           for key, value in filter.items():
               if key not in payload or payload[key] != value:
                   return False
           return True
       
       def _worker_loop(self):
           """Worker thread main loop."""
           while self._running:
               # Drain highest priority queues first
               msg = None
               for priority in range(self.config.priority_levels - 1, -1, -1):
                   try:
                       msg = self._queues[priority].get(block=True, timeout=0.01)
                       break
                   except Empty:
                       continue
               
               if msg:
                   self._deliver_message(msg)
       
       def _start_workers(self):
           """Start worker threads."""
           num_workers = min(4, self.config.priority_levels)
           for i in range(num_workers):
               worker = threading.Thread(
                   target=self._worker_loop,
                   name=f"AgentBusWorker-{i}",
                   daemon=True
               )
               worker.start()
               self._workers.append(worker)
       
       def shutdown(self):
           """Clean shutdown."""
           self._running = False
           for worker in self._workers:
               worker.join(timeout=5.0)
   ```

2. **Priority Queue**: Use separate `Queue` instances per priority level. Workers check highest priority first.

3. **Request-Response**: Implement with correlation IDs:
   ```python
   def request(self, channel: str, message: dict, timeout: float = 5.0):
       correlation_id = str(uuid.uuid4())
       response_queue = Queue()
       
       # Subscribe to response channel
       def on_response(msg):
           if msg.get('correlation_id') == correlation_id:
               response_queue.put(msg)
       
       response_sub = self.subscribe(f"response.{correlation_id}", on_response)
       
       # Send request with correlation ID
       self.publish(channel, {
           **message,
           'correlation_id': correlation_id,
           'timestamp': time.time()
       })
       
       # Wait for response
       try:
           response = response_queue.get(block=True, timeout=timeout)
           return response.get('result')
       except Empty:
           return None
       finally:
           self.unsubscribe(response_sub)
   ```

4. **Dead Letter Processing**: Periodically retry dead letters or provide manual inspection:
   ```python
   def retry_dead_letters(self) -> int:
       """Retry all dead letters. Returns count retried."""
       retried = 0
       while self._dead_letters:
           dl = self._dead_letters.pop(0)
           msg = dl['message']
           # Re-publish with original priority
           try:
               self._queues[msg.priority].put(msg, block=False)
               retried += 1
           except Full:
               # Put back in dead letters
               self._dead_letters.insert(0, dl)
               break
       return retried
   ```

5. **Statistics**: Track key metrics:
   ```python
   def get_message_stats(self) -> dict:
       with self._lock:
           return {
               **self._stats,
               'queue_sizes': [q.qsize() for q in self._queues],
               'subscriber_count': len(self._subscription_by_id),
               'dead_letter_count': len(self._dead_letters),
           }
   ```

---
-

## References

- Enterprise Integration Patterns (Gregor Hohpe, Bobby Woolf)
- Python threading and queue modules
- Publish-subscribe pattern
- Dead letter queue pattern
- Priority queue design
- VJLive-2 plugin API and bus implementations

---

## Conclusion

The Agent Plugin Bus is the communication backbone of VJLive3's multi-agent architecture, enabling reliable, high-performance coordination between autonomous AI agents and the plugin ecosystem. By implementing priority-based queuing, dead letter handling, and request-response patterns, it ensures that critical messages get through even under heavy load, while providing debugging capabilities through tracing and dead letter analysis. Its thread-safe design and performance optimizations make it suitable for real-time 60 FPS operation, which is sacred in VJLive.

---
