# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P8-I8D_telemetry_pipeline.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P8-I8D — Telemetry Pipeline

**What This Module Does**

Implements a high-performance, low-latency telemetry pipeline for VJLive3 that collects, aggregates, and streams system performance metrics, agent state, audio features, and visual analysis data to monitoring endpoints, agent decision systems, and external dashboards. The pipeline supports multiple output formats (UDP, WebSocket, file), configurable sampling rates, and real-time compression to minimize overhead while maintaining 60 FPS sacred performance.

---

## Architecture Decisions

- **Pattern:** Pipeline + Observer + Streaming
- **Rationale:** Telemetry must not impact performance. A pipeline architecture allows data to flow through stages (collect → filter → aggregate → export) with backpressure handling. Observers enable multiple consumers without coupling.
- **Constraints:**
  - Must not impact 60 FPS rendering (max 1% CPU overhead)
  - Must support real-time streaming with < 10ms latency
  - Must handle high-frequency data (audio FFT, depth frames)
  - Must be thread-safe for concurrent producers
  - Must support graceful degradation under load
  - Must enable/disable telemetry at runtime

---

## Legacy References

| Codebase | File | Class/Function | Status |
|----------|------|----------------|--------|
| VJlive-1 | `core/perception_stream_telemetry.py` | `TelemetryStreamer`, `PerceptionStreamTelemetry` | Port — UDP telemetry streaming |
| VJlive-2 | `core/performance_monitor.py` | `PerformanceMonitor` | Port — performance metrics collection |
| VJlive-2 | `web_ui/src/services/performanceService.js` | `PerformanceService` | Port — frontend telemetry |
| VJlive-1 | `core/agent_telemetry.py` | `AgentTelemetry` | Port — agent state telemetry |
| VJlive-2 | `core/coordination/load_balancer.py` | `LoadBalancer` | Port — metrics collection |

---

## Public Interface

```python
class TelemetryPipeline:
    def __init__(self, config: TelemetryConfig) -> None:...
    def add_source(self, name: str, source: TelemetrySource) -> None:...
    def remove_source(self, name: str) -> None:...
    def add_sink(self, name: str, sink: TelemetrySink) -> None:...
    def remove_sink(self, name: str) -> None:...
    def start(self) -> None:...
    def stop(self) -> None:...
    def pause(self) -> None:...
    def resume(self) -> None:...
    def get_stats(self) -> dict:...
    def flush(self) -> None:...
    def configure_sampling(self, rate_hz: float) -> None:...
    def set_throttle(self, max_bytes_per_sec: int) -> None:...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `config` | `TelemetryConfig` | Pipeline configuration | Must include all required parameters |
| `name` | `str` | Source/sink identifier | Must be unique |
| `source` | `TelemetrySource` | Data source object | Must implement source interface |
| `sink` | `TelemetrySink` | Data sink object | Must implement sink interface |
| `rate_hz` | `float` | Sampling rate in Hz | Must be > 0, typically 1-60 |
| `max_bytes_per_sec` | `int` | Throttle limit | Must be > 0 |
| **Output** | `None` | Pipeline runs asynchronously | Stats available via get_stats() |

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `json` — data serialization — fallback: pickle (security risk)
  - `socket` — UDP/WebSocket streaming — fallback: file output only
  - `threading` — concurrent processing — fallback: single-threaded
  - `time` — timing and sampling — fallback: no timing control
  - `logging` — debug logging — fallback: print to stderr
  - `numpy` — array operations — fallback: pure Python (slower)
- Internal modules this depends on:
  - `vjlive3.core.performance_monitor` — performance metrics
  - `vjlive3.core.audio_analyzer` — audio features
  - `vjlive3.core.depth_data_bus` — depth statistics
  - `vjlive3.plugins.manager` — plugin state
  - `vjlive3.core.agent_plugin_bus` — agent state

---

## Error Cases

| Error Condition | Exception / Response | Recovery |
|-----------------|---------------------|----------|
| Source not found | `KeyError("Source not found")` | Check source name |
| Sink connection lost | `ConnectionError` | Reconnect or buffer |
| Serialization failure | `SerializationError` | Use simpler data format |
| Pipeline overflow | `PipelineOverflowError` | Throttle or drop data |
| Invalid configuration | `ValueError` | Validate config before start |
| Thread safety violation | `RuntimeError` | Use proper synchronization |
| Resource exhaustion | `MemoryError` | Reduce buffer sizes |

---

## Configuration Schema

| Field | Type | Default | Range / Constraints | Description |
|-------|------|---------|-------------------|-------------|
| `sampling_rate_hz` | `float` | `30.0` | `0.1 - 120.0` | Global sampling rate |
| `buffer_size` | `int` | `1000` | `10 - 10000` | Pipeline buffer size (messages) |
| `max_batch_size` | `int` | `100` | `1 - 1000` | Max messages per batch |
| `compression_enabled` | `bool` | `True` | — | Enable data compression |
| `compression_level` | `int` | `6` | `0 - 9` | Compression level (if enabled) |
| `udp_enabled` | `bool` | `True` | — | Enable UDP output |
| `udp_host` | `str` | `"127.0.0.1"` | — | UDP destination host |
| `udp_port` | `int` | `5555` | `1 - 65535` | UDP destination port |
| `websocket_enabled` | `bool` | `False` | — | Enable WebSocket output |
| `websocket_url` | `str` | `"ws://localhost:8080"` | — | WebSocket endpoint |
| `file_enabled` | `bool` | `False` | — | Enable file output |
| `file_path` | `str` | `"telemetry.log"` | — | Output file path |
| `throttle_bytes_per_sec` | `int` | `1048576` | `1024 - 10485760` | Rate limit (bytes/sec) |
| `backpressure_strategy` | `str` | `"drop_oldest"` | `drop_oldest`, `block`, `drop_newest` | Backpressure handling |

---

## Data Sources

### Built-in Sources

1. **PerformanceSource** — System performance metrics
   - CPU usage per core
   - Memory usage (RSS, VMS)
   - GPU usage (if available)
   - FPS and frame timing
   - Thread counts and states

2. **AudioSource** — Audio analysis features
   - FFT bins (downsampled to 256 bins)
   - Spectral flux
   - Beat detection
   - RMS energy
   - Frequency band energies

3. **DepthSource** — Depth camera statistics
   - Frame rate
   - Resolution
   - Point cloud size
   - Object detection count
   - Depth range (min/max)

4. **AgentSource** — Multi-agent state
   - Agent identities (julie-roo, maxx-roo, desktop-roo)
   - Agent states (idle, evolving, collaborating)
   - Agent parameters
   - Agent decision history

5. **PluginSource** — Plugin ecosystem metrics
   - Loaded plugins count
   - Plugin parameters (active values)
   - Plugin performance (CPU per plugin)
   - Plugin errors/warnings

### Custom Sources

Plugins and agents can register custom telemetry sources:

```python
pipeline = TelemetryPipeline(config)
pipeline.add_source('my_plugin', MyCustomSource())
```

---

## Data Sinks

### Built-in Sinks

1. **UDPSink** — UDP streaming (high-frequency, low-latency)
   ```python
   sink = UDPSink(host="127.0.0.1", port=5555)
   pipeline.add_sink('udp', sink)
   ```

2. **WebSocketSink** — WebSocket streaming (for UI dashboards)
   ```python
   sink = WebSocketSink(url="ws://localhost:8080/telemetry")
   pipeline.add_sink('websocket', sink)
   ```

3. **FileSink** — File logging (for offline analysis)
   ```python
   sink = FileSink(path="telemetry.log", format="jsonl")
   pipeline.add_sink('file', sink)
   ```

4. **StatsdSink** — Statsd/metrics server (for Grafana, etc.)
   ```python
   sink = StatsdSink(host="localhost", port=8125, prefix="vjlive")
   pipeline.add_sink('statsd', sink)
   ```

### Custom Sinks

Implement `TelemetrySink` interface for custom destinations:

```python
class MySink(TelemetrySink):
    def write(self, data: dict) -> None:
        # Custom logic
        pass
    
    def flush(self) -> None:
        # Flush buffered data
        pass
```

---

## Pipeline Architecture

```
┌─────────────┐
│   Sources   │ (Performance, Audio, Depth, Agent, Plugin)
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│   Collector     │ (Gather data from all sources)
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│   Sampler       │ (Rate limiting, downsampling)
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│   Filter        │ (Remove noise, outliers)
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│   Compressor    │ (Optional: gzip, msgpack)
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│   Throttler     │ (Rate limiting, backpressure)
└──────┬──────────┘
       │
       ▼
┌─────────────┐
│   Sinks     │ (UDP, WebSocket, File, Statsd)
└─────────────┘
```

---

## Threading Model

- **Source threads:** Each source can run in its own thread (optional)
- **Collector thread:** Single thread gathers data from all sources
- **Pipeline thread:** Processes data through filter/compress/throttle
- **Sink threads:** Each sink can have its own thread (for blocking I/O)
- **Lock-free queues:** Use `queue.Queue` or `collections.deque` for inter-thread communication
- **Backpressure:** If pipeline full, apply configured strategy (drop, block, etc.)

---

## Performance Considerations

- **Sampling rate:** Lower rates reduce overhead. 30 Hz typically sufficient.
- **Data reduction:** Downsample FFT, aggregate metrics, send deltas only.
- **Compression:** Use msgpack or gzip for large payloads (FFT bins).
- **Batching:** Send multiple telemetry points in one packet.
- **Async I/O:** Use non-blocking sockets to avoid pipeline stalls.
- **Memory:** Circular buffers to prevent unbounded growth.

---

## Data Formats

### JSON (default)
```json
{
  "timestamp": 1706383200.123,
  "source": "performance",
  "data": {
    "cpu_percent": 45.2,
    "memory_mb": 1024,
    "fps": 60.0
  }
}
```

### MessagePack (binary, more efficient)
```python
# Binary format, ~50% smaller than JSON
```

### Custom (for specific sinks)
- Statsd: `vjlive.performance.cpu:45.2|g`
- InfluxDB line protocol: `performance,host=localhost cpu=45.2,fps=60.0`

---

## Sampling Strategies

1. **Fixed rate:** Sample at exact interval (e.g., 30 Hz)
2. **Adaptive:** Adjust rate based on system load
3. **Event-driven:** Sample only on significant changes
4. **Hybrid:** Fixed rate + event-driven for critical metrics

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | Module starts without crashing if hardware absent |
| `test_add_remove_source` | Sources can be added/removed dynamically |
| `test_add_remove_sink` | Sinks can be added/removed dynamically |
| `test_pipeline_flow` | Data flows correctly through pipeline |
| `test_sampling_rate` | Sampling rate is respected |
| `test_throttling` | Throttle limits data rate correctly |
| `test_backpressure` | Backpressure strategy works as configured |
| `test_compression` | Compression reduces payload size |
| `test_thread_safety` | Concurrent access doesn't corrupt data |
| `test_performance_overhead` | Pipeline overhead < 1% CPU at 60 FPS |
| `test_sink_failure` | Sink failures don't crash pipeline |
| `test_recovery` | Pipeline recovers from errors |
| `test_serialization` | Data serializes correctly for all formats |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-8] P8-I8D: Telemetry Pipeline` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES  

Use these to fill in the spec. These are the REAL implementations:

### core/perception_stream_telemetry.py (L1-20) [VJlive (Original)]
```python
"""
Perception Stream Telemetry System

Provides real-time telemetry data to performing agents, including audio features
and system state for enhanced perception-driven interactions.
"""

import json
import socket
import time
from typing import Dict, List, Callable, Any
import numpy as np

from .audio_analyzer import AudioAnalyzer, AudioFeature


class TelemetryStreamer:
    """
    Handles streaming telemetry data over UDP for high-frequency transmission.
    """
```

This shows the basic telemetry streaming architecture with UDP transport.

### core/perception_stream_telemetry.py (L17-36) [VJlive (Original)]
```python
class TelemetryStreamer:
    """
    Handles streaming telemetry data over UDP for high-frequency transmission.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 5555):
        """
        Initialize UDP streamer.

        Args:
            host: Target host IP address
            port: Target port number
        """
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.address = (host, port)

    def send_data(self, data: Dict[str, Any]) -> None:
        """
        Send telemetry data as JSON over UDP.

        Args:
            data: Dictionary containing telemetry information
        """
        try:
            json_str = json.dumps(data, separators=(',', ':'))  # Compact JSON
            self.sock.sendto(json_str.encode('utf-8'), self.address)
        except Exception as e:
            print(f"Telemetry send error: {e}")

    def close(self) -> None:
        """Close the UDP socket."""
        if self.sock:
            self.sock.close()
```

This demonstrates UDP streaming with compact JSON serialization and error handling.

### core/perception_stream_telemetry.py (L49-68) [VJlive (Original)]
```python
            self.sock.close()


class PerceptionStreamTelemetry:
    """
    Collects and formats telemetry data from VJLive system components.
    """

    def __init__(self,
                 audio_analyzer: AudioAnalyzer,
                 effect_chain: Any,
                 fps_getter: Callable[[], float],
                 interaction_getter: Callable[[], Dict[str, Any]]):
        """
        Initialize telemetry collector.

        Args:
            audio_analyzer: AudioAnalyzer instance for audio features
            effect_chain: EffectChain instance for shader state
            fps_getter: Callable that returns current FPS
```

This shows the telemetry collector pattern with dependency injection.

### core/perception_stream_telemetry.py (L65-84) [VJlive (Original)]
```python
        Args:
            audio_analyzer: AudioAnalyzer instance for audio features
            effect_chain: EffectChain instance for shader state
            fps_getter: Callable that returns current FPS
            interaction_getter: Callable that returns human interaction flags
        """
        self.audio_analyzer = audio_analyzer
        self.effect_chain = effect_chain
        self.get_fps = fps_getter
        self.get_interaction_flags = interaction_getter

        # FFT bin downsampling for efficient transmission
        self.fft_bin_count = 256
```

This demonstrates configuration of telemetry parameters like FFT downsampling.

### core/perception_stream_telemetry.py (L81-100) [VJlive (Original)]
```python
    def get_active_shaders(self) -> List[str]:
        """
        Get list of currently active shader effects.

        Returns:
            List of shader effect names that are enabled
        """
        active_shaders = []
        for effect in self.effect_chain.effects:
            if effect.enabled:
                # Check if it's a shader effect (has fragment source or is ShadertoyEffect)
                if hasattr(effect, 'fragment_source') or hasattr(effect, '__class__') and 'Shadertoy' in str(effect.__class__):
                    active_shaders.append(effect.name)
        return active_shaders
```

This shows how to collect shader/effect state for telemetry.

### core/perception_stream_telemetry.py (L97-116) [VJlive (Original)]
```python
    def collect_audio_data(self) -> Dict[str, Any]:
        """
        Collect current audio features for telemetry.

        Returns:
            Dictionary with audio telemetry data
        """
        # Get spectrum and downsample FFT bins
        full_spectrum = self.audio_analyzer.get_spectrum_data()
        if len(full_spectrum) == 0:
            downsampled_bins = [0.0] * self.fft_bin_count
        else:
            downsampled_bins = np.interp(
                np.linspace(0, len(full_spectrum)-1, self.fft_bin_count),
                np.arange(len(full_spectrum)),
                full_spectrum
            ).tolist()

        return {
            "fft_bins": downsampled_bins,
            "spectral_flux": round(self.audio_analyzer.get_feature_value(AudioFeature.SPECTRAL_FLUX), 4),
            "onset_detection": round(self.audio_analyzer.get_feature_value(AudioFeature.BEAT), 4),
            "rms_energy": round(self.audio_analyzer.get_feature_value(AudioFeature.VOLUME), 4)
        }
```

This demonstrates audio data collection with FFT downsampling for efficient transmission.

### core/perception_stream_telemetry.py (L113-132) [VJlive-2 (Legacy)]
```python
        return {
            "fft_bins": downsampled_bins,
            "spectral_flux": round(self.audio_analyzer.get_feature_value(AudioFeature.SPECTRAL_FLUX), 4),
            "onset_detection": round(self.audio_analyzer.get_feature_value(AudioFeature.BEAT), 4),
            "rms_energy": round(self.audio_analyzer.get_feature_value(AudioFeature.VOLUME), 4)
        }

    def collect_system_state(self) -> Dict[str, Any]:
        """
        Collect current system state for telemetry.

        Returns:
            Dictionary with system telemetry data
        """
        return {
            "active_shaders": self.get_active_shaders(),
            "frame_rate": round(self.get_fps(), 2),
            "human_interaction_flags": self.get_interaction_flags()
        }
```

This shows system state collection including active shaders, FPS, and interaction flags.

### core/perception_stream_telemetry.py (L129-148) [VJlive-2 (Legacy)]
```python
        return {
            "active_shaders": self.get_active_shaders(),
            "frame_rate": round(self.get_fps(), 2),
            "human_interaction_flags": self.get_interaction_flags()
        }

    def generate_telemetry_packet(self) -> Dict[str, Any]:
        """
        Generate complete telemetry packet with timestamp.

        Returns:
            Complete telemetry data dictionary
        """
        return {
            "timestamp": time.time(),
            "audio": self.collect_audio_data(),
            "system": self.collect_system_state()
        }

    def update_and_stream(self, streamer: TelemetryStreamer) -> None:
```

This demonstrates packet generation with timestamp and multiple data sections.

### core/perception_stream_telemetry.py (L145-156) [VJlive-2 (Legacy)]
```python
            "system": self.collect_system_state()
        }

    def update_and_stream(self, streamer: TelemetryStreamer) -> None:
        """
        Collect telemetry data and send via streamer.

        Args:
            streamer: TelemetryStreamer instance to send data through
        """
        packet = self.generate_telemetry_packet()
        streamer.send_data(packet)
```

This shows the complete telemetry collection and streaming loop.

---

## Notes for Implementers

1. **Core Concept**: The telemetry pipeline collects data from multiple sources, processes it through a configurable pipeline (sample → filter → compress), and streams it to multiple sinks without impacting 60 FPS performance.

2. **Performance First**: Design for minimal overhead. Sampling rate, compression, and batching are critical to keep CPU usage low.

3. **Thread Safety**: Sources may run in different threads. Use proper synchronization. Lock-free queues preferred.

4. **Backpressure**: When sinks can't keep up, apply backpressure. Dropping old data is usually better than blocking.

5. **Graceful Degradation**: If telemetry itself causes performance issues, automatically reduce sampling rate or disable non-critical sources.

6. **Configurable at Runtime**: Allow changing sampling rate, enabling/disabling sources and sinks without restarting the pipeline.

7. **Multiple Outputs**: Support UDP (low-latency), WebSocket (UI dashboards), file (logging), and Statsd (monitoring) simultaneously.

8. **Data Efficiency**: Downsample high-frequency data (FFT → 256 bins), send deltas when possible, use binary formats.

9. **Error Isolation**: Sink failures should not affect the pipeline. Buffer and retry or drop failed sinks.

10. **Monitoring**: The telemetry system should monitor its own performance (overhead, buffer sizes, drop rates).

---

## Implementation Tips

1. **Python Implementation**:
   ```python
   import threading
   import time
   import json
   import socket
   from queue import Queue, Empty, Full
   from typing import Dict, List, Callable, Any
   from dataclasses import dataclass
   from abc import ABC, abstractmethod
   
   @dataclass
   class TelemetryConfig:
       sampling_rate_hz: float = 30.0
       buffer_size: int = 1000
       max_batch_size: int = 100
       compression_enabled: bool = True
       udp_enabled: bool = True
       udp_host: str = "127.0.0.1"
       udp_port: int = 5555
       websocket_enabled: bool = False
       websocket_url: str = "ws://localhost:8080/telemetry"
       file_enabled: bool = False
       file_path: str = "telemetry.log"
       throttle_bytes_per_sec: int = 1048576
       backpressure_strategy: str = "drop_oldest"
   
   class TelemetrySource(ABC):
       @abstractmethod
       def collect(self) -> dict:
           """Collect telemetry data."""
           pass
       
       @abstractmethod
       def get_name(self) -> str:
           """Get source name."""
           pass
   
   class TelemetrySink(ABC):
       @abstractmethod
       def write(self, data: dict) -> None:
           """Write telemetry data."""
           pass
       
       @abstractmethod
       def flush(self) -> None:
           """Flush buffered data."""
           pass
       
       @abstractmethod
       def close(self) -> None:
           """Close sink."""
           pass
   
   class TelemetryPipeline:
       def __init__(self, config: TelemetryConfig):
           self.config = config
           self.sources: Dict[str, TelemetrySource] = {}
           self.sinks: Dict[str, TelemetrySink] = {}
           
           # Pipeline queues
           self._queue = Queue(maxsize=config.buffer_size)
           self._running = False
           self._paused = False
           
           # Threading
           self._collector_thread: Optional[threading.Thread] = None
           self._processor_thread: Optional[threading.Thread] = None
           
           # Stats
           self._stats = {
               'collected': 0,
               'processed': 0,
               'dropped': 0,
               'sent': 0,
               'errors': 0,
           }
       
       def add_source(self, name: str, source: TelemetrySource):
           """Add a telemetry source."""
           self.sources[name] = source
       
       def add_sink(self, name: str, sink: TelemetrySink):
           """Add a telemetry sink."""
           self.sinks[name] = sink
       
       def start(self):
           """Start the pipeline."""
           self._running = True
           self._collector_thread = threading.Thread(
               target=self._collector_loop,
               daemon=True
           )
           self._processor_thread = threading.Thread(
               target=self._processor_loop,
               daemon=True
           )
           self._collector_thread.start()
           self._processor_thread.start()
       
       def stop(self):
           """Stop the pipeline."""
           self._running = False
           if self._collector_thread:
               self._collector_thread.join(timeout=5.0)
           if self._processor_thread:
               self._processor_thread.join(timeout=5.0)
           self._flush_all_sinks()
       
       def _collector_loop(self):
           """Collect data from all sources at configured rate."""
           interval = 1.0 / self.config.sampling_rate_hz
           next_collect = time.time()
           
           while self._running:
               if not self._paused:
                   timestamp = time.time()
                   packet = {
                       'timestamp': timestamp,
                       'sources': {}
                   }
                   
                   # Collect from all sources
                   for name, source in self.sources.items():
                       try:
                           data = source.collect()
                           packet['sources'][name] = data
                           self._stats['collected'] += 1
                       except Exception as e:
                           self._stats['errors'] += 1
                           print(f"Source {name} collection error: {e}")
                   
                   # Enqueue for processing
                   try:
                       self._queue.put(packet, block=True, timeout=0.1)
                   except Full:
                       # Apply backpressure strategy
                       self._handle_backpressure()
                       self._stats['dropped'] += 1
               
               # Sleep until next collection time
               next_collect += interval
               sleep_time = next_collect - time.time()
               if sleep_time > 0:
                   time.sleep(sleep_time)
       
       def _processor_loop(self):
           """Process and send telemetry data."""
           while self._running:
               try:
                   packet = self._queue.get(block=True, timeout=0.1)
                   
                   # Process packet (filter, compress, etc.)
                   processed = self._process_packet(packet)
                   
                   # Send to all sinks
                   for sink in self.sinks.values():
                       try:
                           sink.write(processed)
                           self._stats['sent'] += 1
                       except Exception as e:
                           self._stats['errors'] += 1
                           print(f"Sink error: {e}")
                   
                   self._stats['processed'] += 1
               except Empty:
                   continue
       
       def _process_packet(self, packet: dict) -> dict:
           """Apply processing (compression, filtering)."""
           # Add metadata
           processed = {
               'ts': packet['timestamp'],
               'data': packet['sources']
           }
           
           # Compress if enabled
           if self.config.compression_enabled:
               # Could use msgpack, gzip, etc.
               pass
           
           return processed
       
       def _handle_backpressure(self):
           """Handle queue overflow based on strategy."""
           if self.config.backpressure_strategy == "drop_oldest":
               # Drop oldest item in queue
               try:
                   self._queue.get(block=False)
               except Empty:
                   pass
           elif self.config.backpressure_strategy == "drop_newest":
               # Just skip this packet (already dropped by put())
               pass
           # "block" strategy naturally blocks in put()
       
       def _flush_all_sinks(self):
           """Flush all sinks on shutdown."""
           for sink in self.sinks.values():
               try:
                   sink.flush()
               except Exception as e:
                   print(f"Sink flush error: {e}")
   ```

2. **UDP Sink**:
   ```python
   class UDPSink(TelemetrySink):
       def __init__(self, host: str, port: int):
           self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
           self.address = (host, port)
       
       def write(self, data: dict):
           json_str = json.dumps(data, separators=(',', ':'))
           self.sock.sendto(json_str.encode('utf-8'), self.address)
       
       def flush(self):
           pass  # UDP is connectionless
       
       def close(self):
           self.sock.close()
   ```

3. **Sampling Control**: Use a precise timer to maintain exact sampling rate:
   ```python
   def _collector_loop(self):
       interval = 1.0 / self.config.sampling_rate_hz
       next_time = time.perf_counter()
       
       while self._running:
           # ... collect ...
           next_time += interval
           sleep_time = next_time - time.perf_counter()
           if sleep_time > 0:
               time.sleep(sleep_time)
   ```

4. **Performance Monitoring**: Track pipeline overhead:
   ```python
   def get_overhead_stats(self) -> dict:
       return {
           'queue_size': self._queue.qsize(),
           'dropped': self._stats['dropped'],
           'errors': self._stats['errors'],
           'collected_per_sec': self._stats['collected'] / self._runtime,
           'sent_per_sec': self._stats['sent'] / self._runtime,
       }
   ```

5. **Dynamic Reconfiguration**: Allow runtime changes:
   ```python
   def configure_sampling(self, rate_hz: float):
       """Change sampling rate at runtime."""
       self.config.sampling_rate_hz = rate_hz
   
   def set_throttle(self, max_bytes_per_sec: int):
       """Adjust throttle limit."""
       self.config.throttle_bytes_per_sec = max_bytes_per_sec
   ```

---

## Easter Egg Idea

When exactly 666 telemetry packets are sent per second for 666 consecutive seconds, the pipeline enters a "quantum observation" state where all telemetry data becomes simultaneously observed and unobserved, the sampling rate becomes exactly 666 Hz while appearing as 60 Hz to normal observers, the compression algorithm achieves exactly 666:1 ratio by encoding data in quantum superposition, the UDP packets travel exactly 666 times faster than light through quantum tunneling, and the entire telemetry pipeline becomes a "Schrödinger's stream" where the data is both received and not received until observed by the dashboard, at which point it reveals exactly 666 hidden dimensions of performance metrics that exist in parallel universes.

---

## References

- Data pipeline design patterns
- Python threading and queue modules
- UDP and WebSocket networking
- Telemetry and monitoring best practices
- Performance optimization for real-time systems
- VJLive-1 perception stream telemetry
- VJLive-2 performance monitoring

---

## Conclusion

The Telemetry Pipeline is a critical component for monitoring, debugging, and agent decision-making in VJLive3. By implementing a high-performance, thread-safe pipeline with configurable sampling, compression, and multiple output formats, it provides comprehensive system visibility without compromising the sacred 60 FPS performance. Its backpressure handling and graceful degradation ensure stability even under heavy telemetry load, while its extensible architecture allows custom sources and sinks to be added as needed.

---
>>>>>>> REPLACE