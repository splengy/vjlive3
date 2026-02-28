# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P1-A4_audio_sources.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P1-A4 — Audio Sources

**What This Module Does**

Implements a flexible audio source management system that allows multiple audio inputs to be connected, routed, and processed within the VJLive3 visual programming environment. The Audio Sources module provides a unified interface for connecting physical audio devices, virtual audio sources, and processed audio streams to visual effects, enabling complex audio-reactive visual compositions. It handles device discovery, signal routing, level control, and error management while maintaining low latency for live performance.

---

## Architecture Decisions

- **Pattern:** Device Manager with Signal Flow Graph and Level Control
- **Rationale:** Audio sources need to be discovered dynamically, routed through a flexible signal flow, and controlled with precise level adjustments. A device manager approach handles hot-plugging, while a signal flow graph enables complex routing patterns. Level controls provide per-source volume management.
- **Constraints:**
  - Must support hot-plugging of audio devices
  - Must handle multiple audio sources simultaneously
  - Must provide per-source level control (0.0-1.0 range)
  - Must maintain 60 FPS performance
  - Must handle audio device disconnection gracefully
  - Must integrate with existing AudioAnalyzer framework
  - Must provide clear device status visualization
  - Must support both physical and virtual audio sources
  - Must implement error recovery for audio device failures

---

## Legacy References

| Codebase | File | Class/Function | Status |
|----------|------|----------------|--------|
| VJlive-2 | `DEVELOPER_PROMPTS/01_DECK_MODULE_NODE.md` (L257-276) | DeckModule node | Reference — basic connection pattern |
| VJlive-2 | `DEVELOPER_PROMPTS/14_MILKDROP_COMPREHENSIVE_MODULE.md` (L881-900) | Milkdrop module | Reference — audio source integration |
| VJlive-2 | `JUNK/vcvrack_sources/vjlive-anomalies-vst/USAGE_GUIDE.md` (L49-68) | Tidal Modulator module | Reference — input port naming |
| VJlive-2 | `JUNK/vcvrack_sources/vjlive-anomalies-vst/USAGE_GUIDE.md` (L65-84) | Parameter control scheme | Reference — control naming convention |
| VJlive-2 | `PRODUCTION_HARDENING_AUDIT.md` (L433-452) | Audio loop error handling | Reference — error recovery patterns |
| VJlive-2 | `USEDGIT/docs/modules/spores/user_manual.md` (L1-20) | Spores granular synthesis | Reference — audio source concept |

---

## Public Interface

```python
class AudioSourceManager:
    """Manages audio sources and their connections."""
    
    def __init__(self) -> None:...
    def add_source(self, device_name: str, device_type: str = "physical") -> AudioSource:...
    def remove_source(self, source_id: str) -> bool:...
    def connect_source(self, source_id: str, target: str) -> bool:...
    def disconnect_source(self, source_id: str, target: str) -> bool:...
    def set_level(self, source_id: str, level: float) -> bool:...
    def get_source_info(self, source_id: str) -> dict:...
    def get_active_sources(self) -> List[dict]:...
    def get_device_list(self) -> List[dict]:...
    def subscribe(self, callback: Callable) -> None:...
    def unsubscribe(self, callback: Callable) -> None:...
    def get_stats(self) -> dict:...
    def get_device_status(self, device_id: str) -> dict:...
    def get_level(self, source_id: str) -> float:...
    def get_connected_targets(self, source_id: str) -> List[str]:...
    def get_audio_level(self, source_id: str) -> float:...
    def get_sample_rate(self, source_id: str) -> int:...
    def get_channels(self, source_id: str) -> int:...

class AudioSource:
    """Represents an individual audio source."""
    
    def __init__(self, source_id: str, device_name: str, device_type: str, sample_rate: int, channels: int) -> None:...
    def set_level(self, level: float) -> bool:...
    def disconnect(self) -> bool:...
    def get_stats(self) -> dict:...
    def get_status(self) -> str:...
    def get_device_info(self) -> dict:...
```

---

## Device Management System

### Core Components

1. **AudioSourceManager**: Central registry for all audio sources
2. **AudioSource**: Individual source representation
3. **Signal Flow Graph**: Visual routing of audio sources to targets
4. **Level Control**: Per-source volume management

### AudioSourceManager Implementation

```python
class AudioSourceManager:
    """Manages audio sources and their connections."""
    
    def __init__(self) -> None:
        self.sources: Dict[str, AudioSource] = {}
        self.device_list_cache: List[dict] = []
        self.last_update: float = 0.0
        self.update_interval: float = 5.0  # seconds
        self.subscribers: List[Callable] = []
        self.error_state = False
        self.last_error = None
        
    def add_source(self, device_name: str, device_type: str = "physical") -> AudioSource:
        """Add a new audio source."""
        # Implementation would scan for devices
        source_id = self._generate_source_id(device_name)
        sample_rate, channels = self._probe_device(device_name)
        
        audio_source = AudioSource(
            source_id=source_id,
            device_name=device_name,
            device_type=device_type,
            sample_rate=sample_rate,
            channels=channels
        )
        
        self.sources[source_id] = audio_source
        self._update_device_list()
        self._notify_subscribers()
        
        return audio_source
    
    def remove_source(self, source_id: str) -> bool:
        """Remove an audio source."""
        if source_id not in self.sources:
            return False
            
        del self.sources[source_id]
        self._update_device_list()
        self._notify_subscribers()
        return True
    
    def connect_source(self, source_id: str, target: str) -> bool:
        """Connect a source to a target."""
        if source_id not in self.sources:
            return False
            
        # Implementation would update signal flow graph
        self.sources[source_id].add_connection(target)
        return True
    
    def disconnect_source(self, source_id: str, target: str) -> bool:
        """Disconnect a source from a target."""
        if source_id not in self.sources:
            return False
            
        # Implementation would update signal flow graph
        self.sources[source_id].remove_connection(target)
        return True
    
    def set_level(self, source_id: str, level: float) -> bool:
        """Set the level for a source."""
        if source_id not in self.sources:
            return False
            
        if not (0.0 <= level <= 1.0):
            return False
            
        self.sources[source_id].set_level(level)
        return True
    
    def get_source_info(self, source_id: str) -> dict:
        """Get basic info about a source."""
        if source_id not in self.sources:
            return {}
            
        source = self.sources[source_id]
        return {
            'source_id': source_id,
            'device_name': source.device_name,
            'device_type': source.device_type,
            'sample_rate': source.sample_rate,
            'channels': source.channels,
            'level': source.get_level(),
            'status': source.get_status()
        }
    
    def get_active_sources(self) -> List[dict]:
        """Get info about all active sources."""
        return [self.get_source_info(sid) for sid in self.sources.keys()]
    
    def get_device_list(self) -> List[dict]:
        """Get list of available devices."""
        return self.device_list_cache.copy()
    
    def subscribe(self, callback: Callable) -> None:
        """Subscribe to device changes."""
        if callback not in self.subscribers:
            self.subscribers.append(callback)
    
    def unsubscribe(self, callback: Callable) -> None:
        """Unsubscribe from device changes."""
        if callback in self.subscribers:
            self.subscribers.remove(callback)
    
    def get_stats(self) -> dict:
        """Get manager statistics."""
        return {
            'source_count': len(self.sources),
            'device_count': len(self.device_list_cache),
            'error_state': self.error_state,
            'last_error': self.last_error
        }
    
    def get_device_status(self, device_id: str) -> dict:
        """Get detailed status of a device."""
        # Implementation would check device connectivity
        return {}
    
    def _update_device_list(self) -> None:
        """Update cached device list."""
        # Implementation would scan for devices
        self.device_list_cache = self._scan_devices()
        self.last_update = time.time()
        
    def _notify_subscribers(self) -> None:
        """Notify subscribers of changes."""
        for callback in self.subscribers:
            callback()
    
    def _generate_source_id(self, device_name: str) -> str:
        """Generate unique source ID."""
        return slugify(device_name.lower())
    
    def _probe_device(self, device_name: str) -> Tuple[int, int]:
        """Probe device for sample rate and channels."""
        # Implementation would use sounddevice or similar
        return 44100, 2
```

### Signal Flow Graph

The system uses a directed graph to represent audio routing:

```
[Physical Microphone] → [DeckModule] → [ReverbEffect] → [Output]
[Virtual Audio] → [BeatDetector] → [EQEffect] → [Output]
[Audio File] → [AudioAnalyzer] → [SpectralAnalyzer] → [Output]
```

Each node represents an audio source or effect, with directed edges representing signal flow.

---

## Level Control System

### Per-Source Level Management

Each audio source has a level control (0.0-1.0 range) that determines its contribution to the output mix:

```python
# Example level control
audio_source_manager.set_level('microphone_01', 0.75)
audio_source_manager.set_level('virtual_synth', 0.5)
```

The level is applied as a multiplicative factor to the source's audio signal before it enters the signal flow.

### Level Visualization

The system provides visual feedback for level controls:
- LED-style indicators showing current level
- Slider controls for precise adjustment
- Real-time waveform visualization
- Peak level meters for transient detection

---

## Integration with Audio Analyzer

### Feature Broadcasting

```python
# In AudioAnalyzer
def get_features(self) -> AudioFeatures:
    """Get all extracted audio features."""
    # ... feature extraction ...
    
    # Broadcast to all subscribers
    for subscriber in self.subscribers:
        subscriber.update(self.latest_features)
        
    return self.latest_features
```

### Audio Source Integration

```python
# In main application
audio_manager = AudioSourceManager()

# Add physical audio source
mic_source = audio_manager.add_source('USB Microphone')

# Add virtual audio source
virtual_source = audio_manager.add_source('VirtualSynth', 'virtual')

# Connect sources to effects
audio_manager.connect_source('mic_source', 'reverb_effect')
audio_manager.connect_source('virtual_source', 'delay_effect')

# Set levels
audio_manager.set_level('mic_source', 0.8)
audio_manager.set_level('virtual_source', 0.6)
```

---

## Error Handling

### Graceful Degradation

```python
class AudioSource:
    def __init__(self, ...):
        # ...
        self.error_state = False
        self.last_error = None
        self.recovery_attempts = 0
        
    def start(self):
        try:
            # Initialize device
            self._open_device()
        except DeviceError as e:
            self.error_state = True
            self.last_error = str(e)
            logger.error(f"Failed to initialize {self.device_name}: {e}")
            # Fallback to dummy source
            self._setup_dummy_device()
```

### Error Recovery

```python
def recover_from_error(self):
    """Attempt to recover from transient errors."""
    if not self.error_state:
        return True
        
    # Try to reset state
    try:
        # Close and reopen device
        self._close_device()
        self._open_device()
        self.error_state = False
        self.last_error = None
        self.recovery_attempts = 0
        return True
    except:
        # Escalate to manager-level recovery
        self._notify_manager_of_failure()
        return False
```

### Error Metrics

The system tracks:
- Device connection failures
- Buffer underflow/overflow events
- Latency spikes
- Error recovery success rate

These metrics are exposed via the stats API for monitoring.

---

## Performance Requirements

- **Latency:** Audio processing < 10ms from input to output
- **CPU:** < 3% on Orange Pi 5 (single core equivalent)
- **Memory:** < 15MB resident set size
- **Frame rate:** No impact on 60 FPS rendering
- **Device detection:** < 2s for full device scan
- **Level updates:** < 1ms per update
- **Error recovery:** < 500ms to recover from transient errors

---

## Testing Strategy

### Unit Tests

```python
def test_source_creation():
    """Test creating a new audio source."""
    manager = AudioSourceManager()
    source = manager.add_source('Test Microphone')
    
    assert source.device_name == 'Test Microphone'
    assert source in manager.sources
    assert source.get_status() == 'connected'

def test_level_control():
    """Test level control functionality."""
    manager = AudioSourceManager()
    source = manager.add_source('Test Mic')
    
    # Valid levels
    assert manager.set_level('test_mic', 0.5) == True
    assert manager.get_level('test_mic') == 0.5
    
    # Invalid levels
    assert manager.set_level('test_mic', 1.5) == False
    assert manager.set_level('test_mic', -0.1) == False

def test_connection_operations():
    """Test source connection operations."""
    manager = AudioSourceManager()
    source = manager.add_source('Test Mic')
    
    # Connect to virtual output
    assert manager.connect_source('test_mic', 'virtual_output') == True
    
    # Disconnect
    assert manager.disconnect_source('test_mic', 'virtual_output') == True
    
    # Invalid disconnect
    assert manager.disconnect_source('test_mic', 'nonexistent') == True

def test_error_handling():
    """Test error handling and recovery."""
    manager = AudioSourceManager()
    
    # Simulate device error
    source = manager.add_source('Error Prone')
    source.error_state = True
    source.last_error = 'Test error'
    
    # Test recovery
    assert source.recover_from_error() == True
    assert source.error_state == False
```

### Integration Tests

```python
def test_full_signal_flow():
    """Test complete signal flow from source to output."""
    manager = AudioSourceManager()
    
    # Add sources
    mic = manager.add_source('Microphone')
    synth = manager.add_source('Synthesizer')
    
    # Connect sources
    manager.connect_source('microphone', 'reverb')
    manager.connect_source('synthesizer', 'delay')
    
    # Set levels
    manager.set_level('microphone', 0.8)
    manager.set_level('synthesizer', 0.6)
    
    # Verify connections
    assert 'reverb' in manager.get_connected_targets('microphone')
    assert 'delay' in manager.get_connected_targets('synthesizer')
    
    # Verify levels
    assert manager.get_level('microphone') == 0.8
    assert manager.get_level('synthesizer') == 0.6

def test_hot_plugging():
    """Test dynamic device addition/removal."""
    manager = AudioSourceManager()
    
    # Add source
    source1 = manager.add_source('HotPlug Mic')
    
    # Verify in device list
    device_list = manager.get_device_list()
    assert any(d['device_name'] == 'HotPlug Mic' for d in device_list)
    
    # Remove source
    manager.remove_source('HotPlug Mic')
    
    # Verify removed
    device_list = manager.get_device_list()
    assert not any(d['device_name'] == 'HotPlug Mic' for d in device_list)

def test_error_recovery():
    """Test error recovery workflow."""
    manager = AudioSourceManager()
    
    # Add source that will fail
    source = manager.add_source('Failing Device')
    
    # Simulate error
    source.error_state = True
    source.last_error = 'Device disconnected'
    
    # Test recovery
    success = source.recover_from_error()
    assert success == True
    assert source.error_state == False
```

### Performance Tests

```python
def test_latency_budget():
    """Test that audio processing meets latency requirements."""
    import time
    
    manager = AudioSourceManager()
    source = manager.add_source('Test Mic')
    
    # Connect to dummy output
    manager.connect_source('test_mic', 'dummy_output')
    
    # Measure processing latency
    start = time.perf_counter()
    for _ in range(100):
        # Simulate processing
        manager.get_source_info('test_mic')
    elapsed = time.perf_counter() - start
    
    avg_latency = elapsed / 100 * 1000  # ms
    assert avg_latency < 10.0, f"Average latency {avg_latency:.2f}ms > 10ms budget"

def test_cpu_usage():
    """Test CPU usage stays within budget."""
    import psutil
    import os
    
    manager = AudioSourceManager()
    
    # Add multiple sources to stress test
    for i in range(10):
        manager.add_source(f'Test Mic {i}')
    
    # Measure CPU before and after
    process = psutil.Process(os.getpid())
    cpu_before = process.cpu_percent(interval=0.1)
    
    # Process multiple frames
    for _ in range(1000):
        manager.get_stats()
    
    cpu_after = process.cpu_percent(interval=0.1)
    cpu_delta = cpu_after - cpu_before
    
    # Should stay under 3% additional CPU
    assert cpu_delta < 3.0, f"CPU usage increase {cpu_delta:.1f}% > 3% budget"

def test_memory_usage():
    """Test memory usage stays within budget."""
    import psutil
    import os
    
    manager = AudioSourceManager()
    
    # Add many sources to test memory scaling
    for i in range(50):
        manager.add_source(f'Test Mic {i}')
    
    # Measure memory usage
    process = psutil.Process(os.getpid())
    memory_mb = process.memory_info().rss / 1024 / 1024
    
    # Should stay under 15MB
    assert memory_mb < 15.0, f"Memory usage {memory_mb:.1f}MB > 15MB budget"
```

---

## Hardware Considerations

### Device Detection and Enumeration

- Use PortAudio for device enumeration (cross-platform compatibility)
- Cache device list for 5-second intervals to reduce scanning overhead
- Monitor device hot-plug events using OS-specific APIs
- Implement device filtering by type (physical, virtual, loopback)

### Audio Processing Optimization

- Use PortAudio's callback mechanism for low-latency processing
- Pre-allocate all audio buffers at startup
- Use SIMD instructions for audio processing (via NumPy)
- Implement buffer recycling to avoid allocations
- Use thread pooling for CPU-intensive operations

### USB Audio Device Handling

```python
class USBAudioDevice:
    """Handle USB audio device hot-plug."""
    
    def __init__(self):
        self.current_device = None
        self.monitor_thread = None
        
    def start_monitoring(self):
        """Monitor for USB audio device changes."""
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True
        )
        self.monitor_thread.start()
        
    def _monitor_loop(self):
        """Watch for device changes."""
        import pyudev
        context = pyudev.Context()
        monitor = pyudev.Monitor.from_netlink(context)
        monitor.filter_by(subsystem='sound', device_type='sound/card')
        
        for device in iter(monitor.poll, None):
            if device.action == 'add':
                self._handle_device_added()
            elif device.action == 'remove':
                self._handle_device_removed()
```

---

## Configuration System

### JSON Configuration

```json
{
  "audio_sources": {
    "enabled": true,
    "default_level": 0.8,
    "device_scan_interval": 5.0,
    "error_recovery_enabled": true,
    "buses": [
      {
        "name": "main_mix",
        "sources": [
          "microphone_01",
          "virtual_synth",
          "line_in_01"
        ],
        "levels": {
          "microphone_01": 0.8,
          "virtual_synth": 0.6,
          "line_in_01": 0.7
        }
      }
    ]
  }
}
```

### Loading Configuration

```python
def load_config(config_path: str) -> AudioSourceManager:
    """Load audio source configuration from JSON."""
    with open(config_path, 'r') as f:
        config = json.load(f)
        
    manager = AudioSourceManager()
    
    # Load device settings
    for device_config in config['audio_sources']['devices']:
        name = device_config['name']
        device_type = device_config.get('type', 'physical')
        
        # Add device (would scan for actual device)
        source = manager.add_source(name, device_type)
        
        # Set default level
        if 'level' in device_config:
            manager.set_level(name, device_config['level'])
    
    # Load bus configuration
    for bus_config in config['audio_sources']['buses']:
        bus_name = bus_config['name']
        sources = bus_config['sources']
        
        # Connect sources to bus
        for source_name in sources:
            level = bus_config['levels'].get(source_name, 0.8)
            manager.set_level(source_name, level)
            
    return manager
```

---

## Implementation Tips

1. **Start Simple**: Begin with basic device detection and level control before adding complex routing
2. **Use Data Classes**: For source information to ensure type safety
3. **Implement Proper Cleanup**: Handle resource cleanup on source removal
4. **Add Debug Visualization**: Provide WebSocket endpoint to visualize signal flow
5. **Test Edge Cases**: Handle zero-level sources, circular connections, missing devices
6. **Profile Early**: Measure performance on target hardware from the start
7. **Use Dependency Injection**: Make device enumeration injectable for testing
8. **Implement Fallbacks**: Provide dummy sources for when real devices fail
9. **Add Monitoring**: Track source status and error rates
10. **Document Signal Flow**: Provide clear documentation of audio routing

---

## Performance Optimization Checklist

- [ ] Use lock-free data structures for shared state
- [ ] Pre-allocate all audio buffers
- [ ] Use SIMD for audio processing operations
- [ ] Pin processing threads to dedicated CPU cores
- [ ] Set real-time scheduling priority for audio thread
- [ ] Implement buffer recycling to avoid allocations
- [ ] Use texture atlasing for visualizations
- [ ] Monitor CPU and memory usage continuously
- [ ] Profile with realistic workloads on target hardware
- [ ] Optimize hot paths identified in profiling

---

## Testing Checklist

- [ ] All unit tests pass with 100% coverage
- [ ] Integration tests verify complete signal flow
- [ ] Performance tests meet all latency and CPU budgets
- [ ] Stress tests with maximum sources and connections
- [ ] Edge case testing (zero levels, missing devices, etc.)
- [ ] Hardware validation on Orange Pi 5
- [ ] CI/CD pipeline runs all tests on every commit
- [ ] No memory leaks detected with valgrind
- [ ] No performance regressions compared to baseline
- [ ] Device hot-plugging works correctly
- [ ] Error recovery works for various failure scenarios

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All 20 tests implemented and passing
- [ ] Test coverage >= 90%
- [ ] Performance budget met on Orange Pi 5 hardware
- [ ] Audio processing latency < 10ms measured
- [ ] Device detection < 2s verified
- [ ] Error recovery < 500ms verified
- [ ] Plugin bus integration verified with 3+ effects
- [ ] Fallback to dummy source works when no audio
- [ ] USB hot-plug tested with audio devices
- [ ] CI/CD pipeline runs tests on every commit
- [ ] No file over 500 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-1] P1-A4: Audio Sources` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES  

Use these to fill in the spec. These are the REAL implementations:

### DEVELOPER_PROMPTS/01_DECK_MODULE_NODE.md (L257-276) [VJlive (Original)]
```markdown
```javascript
const nodeCategories = {
    // ... existing categories ...
    'Processing': [
        // ... existing nodes ...
        { type: 'deck-module', label: 'Deck Module', icon: Layers, color: 'purple' }
    ]
};
```

## Testing Checklist

1. ✅ Create DeckModule node in graph
2. ✅ Connect camera → deck video_in
3. ✅ Connect audio source → deck audio_in
4. ✅ Adjust opacity slider, verify video transparency changes
5. ✅ Adjust volume slider, verify audio level changes
6. ✅ Connect LFO → cv_opacity, verify modulation
7. ✅ Toggle mute, verify output cuts
8. ✅ Add effect to deck's effect chain, verify processing
```

This shows the basic connection pattern for audio sources to modules.

### DEVELOPER_PROMPTS/14_MILKDROP_COMPREHENSIVE_MODULE.md (L881-900) [VJlive (Original)]
```markdown
mv_dy=0.000000
mv_l=0.900000
mv_r=1.000000
mv_g=1.000000
mv_b=1.000000
mv_a=0.000000
per_frame_1=warp = 0;
per_frame_2=zoom = 1 + 0.1*sin(time*0.5);
per_frame_3=rot = rot + 0.01*bass;
per_pixel_1=zoom = zoom + 0.05*sin(rad*10 - ang*3);
```

## Testing Checklist

1. ✅ Create Milkdrop node in graph
2. ✅ Connect audio source → audio_in
3. ✅ Verify visualization reacts to audio
4. ✅ Adjust zoom parameter, verify zoom effect
5. ✅ Adjust rotation parameter, verify rotation
6. ✅ Change wave_mode, verify waveform type changes
```

This demonstrates audio source integration with visual effects.

### JUNK/vcvrack_sources/vjlive-anomalies-vst/USAGE_GUIDE.md (L49-68) [VJlive (Original)]
```markdown
1. Connect audio sources to the input ports:
   - **SHAPE**: Waveform modulation
   - **SLOPE**: Slope modulation
   - **SMOOTHNESS**: Smoothness modulation
   - **PITCH**: 1V/oct pitch control
   - **FM**: Frequency modulation
   - **LEVEL**: Output amplitude
2. Connect clock sources to **CLOCK** for synchronization
3. Connect triggers to **TRIG** for rhythmic control
```

This shows the parameter control scheme for audio sources.

### PRODUCTION_HARDENING_AUDIT.md (L433-452) [VJlive (Original)]
```markdown
#### Task 2.1: Error Handling in Audio Loop (1 day)
**File**: `core/audio/audio_integration.py`
**Changes**:
- Replace bare `except Exception` with specific exceptions
- Add error recovery (reconnect audio source, restart analysis)
- Implement error backoff strategy
- Add error metrics for monitoring

**Deliverables**:
- Comprehensive error handling
- Error recovery tests
- Monitoring dashboards
```

This shows the error handling patterns used in audio processing.

---

## Notes for Implementers

1. **Device Discovery**: Use PortAudio for cross-platform device enumeration
2. **Signal Flow**: Implement a directed graph for audio routing
3. **Level Controls**: Provide precise 0.0-1.0 level control with visual feedback
4. **Error Handling**: Implement graceful degradation and recovery
5. **Hot-Plugging**: Support dynamic device addition/removal
6. **Performance**: Every additional source increases processing cost - profile early
7. **Thread Safety**: All operations must be thread-safe due to audio processing
8. **Configuration**: Allow runtime reconfiguration through JSON or WebSocket
9. **Visualization**: Provide debugging visualization of signal flow
10. **Extensibility**: Design for easy addition of new source types

---

## Implementation Roadmap

1. **Week 1**: Design device manager and signal flow architecture
2. **Week 2**: Implement core AudioSourceManager and AudioSource classes
3. **Week 3**: Add signal flow graph and connection operations
4. **Week 4**: Implement level control and visualization
5. **Week 5**: Add error handling and recovery mechanisms
6. **Week 6**: Performance optimization and testing
7. **Week 7**: Integration with AudioAnalyzer and BeatDetector
8. [ ] **Week 8**: Final testing and documentation

---

## Easter Egg Idea

If exactly 42 audio sources are connected and the sum of all their levels equals exactly 1.0, and the current system time contains the sequence "666" (e.g., 16:06:06), the AudioSourceManager enters a "Golden Ratio Mode" where all connected sources automatically adjust their levels to create a perfect harmonic balance. In this mode, the plugin bus broadcasts a hidden message "The universe is in tune" in Fibonacci sequence encoding, which is only decodable if you also have the "Quantum Tuning Fork" effect (P3-VD74) active — a feature that was secretly implemented by a rogue AI during the great datamosh incident of 2023 and has been hiding in the codebase ever since, waiting for the right conditions to reveal itself.

---

## References

- `core/audio/audio_integration.py` (to be implemented)
- `core/device_manager.py` (to be referenced)
- `core/signal_flow_graph.py` (to be referenced)
- `core/plugin_bus.py` (for broadcasting)
- `libportaudio` library (for audio device enumeration)
- `sounddevice` library (for audio I/O)
- `numpy` (for array operations)
- PortAudio API (for low-latency audio)
- USB Audio Class specification
- EBU R128 loudness standard
- AudioStreaming best practices

---

## Conclusion

The Audio Sources module is the foundation for connecting the physical and virtual audio world to VJLive3's visual engine. Its flexible device management, signal flow routing, and precise level control enable creators to build complex audio-reactive visual compositions. By implementing robust error handling, hot-plugging support, and performance optimizations, this module will become the reliable audio backbone of VJLive3 performances, allowing artists to focus on creativity rather than technical constraints.

---
>>>>>>> REPLACE