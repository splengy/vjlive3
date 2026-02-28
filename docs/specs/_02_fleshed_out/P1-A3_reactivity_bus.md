# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P1-A3_reactivity_bus.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P1-A3 — Reactivity Bus

**What This Module Does**

Implements a flexible effect routing system that allows multiple audio-reactive sources to send their processed features to shared buses, where they can be mixed, processed by effects, and routed to outputs. The Reactivity Bus system enables complex audio-reactive visual compositions by providing multiple parallel processing paths with independent mixing controls, effect chains, and routing logic.

---

## Architecture Decisions

- **Pattern:** Producer-Consumer with Mixing Matrix and Routing Tree
- **Rationale:** Visual effects often need to combine multiple audio-reactive sources (e.g., beat, tempo, spectral features) and route them through different effect chains. A mixing matrix allows flexible routing, while a tree structure enables hierarchical organization of buses and sub-buses.
- **Constraints:**
  - Must support multiple effect buses (reverb, delay, EQ, etc.)
  - Must allow multiple sources to send to the same bus
  - Must provide per-source send level control (0.0-1.0)
  - Must support hierarchical bus structure (sub-buses)
  - Must maintain 60 FPS performance
  - Must handle dynamic bus configuration changes
  - Must integrate with existing AudioAnalyzer and BeatDetector
  - Must provide clear routing visualization for debugging

---

## Legacy References

| Codebase | File | Class/Function | Status |
|----------|------|----------------|--------|
| VJlive-2 | `core/effects/effect_bus.py` | EffectBus | Port — core bus implementation |
| VJlive-2 | `core/effects/audio_reactive_effects.py` | AudioReactor | Reference — feature consumption |
| VJlive-2 | `DEVELOPER_D_MILKDROP_MANIFOLD_NODERED.md` | set_audio_analyzer | Port — integration pattern |
| VJlive-2 | `INTEGRATION_CHECKLIST.md` | Audio signal bridge | Reference — bus integration |
| VJlive-2 | `core/depth_data_bus.py` | DepthDataBus | Reference — singleton pattern |

---

## Public Interface

```python
class EffectBus:
    """Effect bus for routing and mixing audio-reactive features."""
    
    def __init__(self, name: str, effect: Effect, width: int, height: int) -> None:...
    def add_send(self, source_name: str, level: float) -> None:...
    def remove_send(self, source_name: str) -> None:...
    def set_send_level(self, source_name: str, level: float) -> None:...
    def process(self, input_data: dict) -> dict:...
    def get_stats(self) -> dict:...
    def get_active_sources(self) -> List[str]:...
    def get_send_level(self, source_name: str) -> float:...
    def get_bus_name(self) -> str:...
    def get_effect(self) -> Effect:...
    def set_effect(self, effect: Effect) -> None:...
    def add_subbus(self, bus_name: str) -> 'EffectBus':...
    def remove_subbus(self, bus_name: str) -> None:...
    def get_subbus(self, bus_name: str) -> Optional['EffectBus']:...
    def get_all_subbuses(self) -> List['EffectBus']:...
    def get_bus_tree(self) -> Dict:...
    def get_stats(self) -> dict:...
```

---

## Effect Bus Architecture

### Core Components

1. **EffectBus Manager**: Main registry for all effect buses
2. **EffectBus**: Individual bus with mixing matrix and effect chain
3. **Send**: Source-to-bus connection with level control
4. **Routing Tree**: Hierarchical bus structure

### EffectBus Implementation

```python
class EffectBus:
    """Effect bus for routing and mixing audio-reactive features."""
    
    def __init__(self, name: str, effect: Effect, width: int, height: int):
        self.name = name
        self.effect = effect
        self.width = width
        self.height = height
        self.sends: Dict[str, float] = {}  # source_name -> level
        self.sub_buses: Dict[str, EffectBus] = {}  # bus_name -> subbus
        self.processed_data: dict = {}  # processed output data
        
    def add_send(self, source_name: str, level: float) -> None:
        """Add a source to send to this bus."""
        if 0.0 <= level <= 1.0:
            self.sends[source_name] = level
        else:
            raise ValueError("Level must be between 0.0 and 1.0")
    
    def remove_send(self, source_name: str) -> None:
        """Remove a source from sending to this bus."""
        if source_name in self.sends:
            del self.sends[source_name]
    
    def set_send_level(self, source_name: str, level: float) -> None:
        """Set the send level for a source."""
        if 0.0 <= level <= 1.0:
            self.sends[source_name] = level
        else:
            raise ValueError("Level must be between 0.0 and 1.0")
    
    def process(self, input_data: dict) -> dict:
        """Process input data through the effect chain."""
        # Collect inputs from sends
        mixed_input = self._mix_inputs(input_data)
        
        # Apply effect
        if self.effect:
            self.processed_data = self.effect.render(mixed_input)
        else:
            self.processed_data = mixed_input
            
        return self.processed_data
    
    def _mix_inputs(self, input_data: dict) -> dict:
        """Mix inputs from all sends."""
        # Start with base input
        mixed = {}
        
        # Add contributions from each send
        for source_name, level in self.sends.items():
            if source_name in input_data:
                source_data = input_data[source_name]
                # Apply level scaling
                scaled = {k: v * level for k, v in source_data.items()}
                # Merge into mixed input
                for k, v in scaled.items():
                    mixed[k] = mixed.get(k, 0.0) + v
                    
        return mixed
```

### Routing Tree

```python
class ReactivityBusManager:
    """Manager for all effect buses and routing."""
    
    def __init__(self) -> None:
        self.buses: Dict[str, EffectBus] = {}
        self.active_buses: Set[str] = set()
        self.default_bus: Optional[str] = None
        
    def create_bus(self, name: str, effect: Effect, width: int, height: int) -> EffectBus:
        """Create a new effect bus."""
        if name in self.buses:
            raise ValueError(f"Bus '{name}' already exists")
            
        bus = EffectBus(name, effect, width, height)
        self.buses[name] = bus
        self.active_buses.add(name)
        
        return bus
    
    def get_bus(self, name: str) -> Optional[EffectBus]:
        """Get a bus by name."""
        return self.buses.get(name)
    
    def remove_bus(self, name: str) -> None:
        """Remove a bus and all its sub-buses."""
        if name not in self.buses:
            raise ValueError(f"Bus '{name}' does not exist")
            
        # Remove sub-buses recursively
        bus = self.buses[name]
        self._remove_sub_buses(bus)
        
        del self.buses[name]
        self.active_buses.remove(name)
        
    def _remove_sub_buses(self, bus: EffectBus) -> None:
        """Remove sub-buses recursively."""
        for subbus in list(bus.sub_buses.values()):
            self._remove_sub_buses(subbus)
            if subbus.name in self.buses:
                del self.buses[subbus.name]
                self.active_buses.remove(subbus.name)
    
    def add_subbus(self, parent_name: str, bus_name: str) -> EffectBus:
        """Add a sub-bus to a parent bus."""
        parent_bus = self.get_bus(parent_name)
        if not parent_bus:
            raise ValueError(f"Parent bus '{parent_name}' does not exist")
            
        if bus_name in self.buses:
            raise ValueError(f"Bus '{bus_name}' already exists")
            
        # Create bus (would be done by caller)
        # This method just establishes the relationship
        bus = self.create_bus(bus_name, parent_bus.effect, parent_bus.width, parent_bus.height)
        parent_bus.sub_buses[bus_name] = bus
        
        return bus
    
    def get_bus_tree(self) -> Dict:
        """Get the full bus hierarchy as a tree structure."""
        tree = {}
        for name, bus in self.buses.items():
            tree[name] = {
                'sub_buses': list(bus.sub_buses.keys()),
                'sends': list(bus.sends.keys()),
                'active': name in self.active_buses
            }
        return tree
```

---

## Mixing Matrix

### Send System

Each EffectBus maintains a dictionary of sends from source names to level values (0.0-1.0):

```python
# Example sends configuration
bus.sends = {
    'beat_detector': 0.8,      # 80% of beat detector output
    'tempo_tracker': 0.5,      # 50% of tempo tracker output
    'spectral_analyzer': 0.3   # 30% of spectral analyzer output
}
```

### Routing Operations

```python
# Add a send from source to bus
reactivity_bus.add_send('beat_detector', 0.75)

# Set send level
reactivity_bus.set_send_level('beat_detector', 0.9)

# Remove a send
reactivity_bus.remove_send('tempo_tracker')
```

### Hierarchical Routing

Buses can contain sub-buses, creating a tree structure:

```
MainBus
├── ReverbBus
│   ├── Send from BeatDetector: 0.8
│   └── Send from TempoTracker: 0.5
├── DelayBus
│   ├── Send from SpectralAnalyzer: 0.6
│   └── Send from BeatDetector: 0.4
└── EQBus
    └── Sub-bus: HighEQ
        ├── Send from BeatDetector: 0.9
        └── Send from TempoTracker: 0.3
```

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

### Reactivity Bus Integration

```python
# In main application
reactivity_manager = ReactivityBusManager()

# Create buses
beat_bus = reactivity_manager.create_bus(
    'beat_bus', 
    BeatReverbEffect(), 
    1920, 1080
)

tempo_bus = reactivity_manager.create_bus(
    'tempo_bus', 
    TempoDelayEffect(), 
    1920, 1080
)

# Add sends from audio analyzer features
beat_bus.add_send('beat_detector', 0.9)
tempo_bus.add_send('tempo_tracker', 0.7)

# Process in render loop
def render_frame():
    # Get latest features from analyzer
    features = audio_analyzer.get_latest_features()
    
    # Process each bus
    beat_output = beat_bus.process(features)
    tempo_output = tempo_bus.process(features)
    
    # Render to canvas
    canvas.render(beat_output, tempo_output)
```

---

## Performance Requirements

- **Latency:** End-to-end processing < 33ms (to maintain 30 FPS minimum)
- **CPU:** < 8% on Orange Pi 5 (single core equivalent)
- **Memory:** < 40MB resident set size
- **Frame rate:** No impact on 60 FPS rendering
- **Scalability:** Support up to 10 concurrent effect buses with 50 sends each

---

## Testing Strategy

### Unit Tests

```python
def test_effect_bus_creation():
    """Test creating a new effect bus."""
    manager = ReactivityBusManager()
    bus = manager.create_bus('test_bus', dummy_effect, 100, 100)
    
    assert bus.name == 'test_bus'
    assert bus in manager.buses
    assert bus in manager.active_buses

def test_send_level_validation():
    """Test send level validation."""
    manager = ReactivityBusManager()
    bus = manager.create_bus('test_bus', dummy_effect, 100, 100)
    
    # Valid levels
    bus.add_send('source1', 0.5)
    bus.add_send('source2', 1.0)
    
    # Invalid levels should raise ValueError
    with pytest.raises(ValueError):
        bus.add_send('source3', 1.5)
    with pytest.raises(ValueError):
        bus.add_send('source4', -0.1)

def test_send_removal():
    """Test removing a send."""
    manager = ReactivityBusManager()
    bus = manager.create_bus('test_bus', dummy_effect, 100, 100)
    
    bus.add_send('source1', 0.5)
    assert 'source1' in bus.sends
    
    bus.remove_send('source1')
    assert 'source1' not in bus.sends

def test_subbus_creation():
    """Test creating sub-buses."""
    manager = ReactivityBusManager()
    parent = manager.create_bus('parent', dummy_effect, 100, 100)
    child = manager.create_bus('child', dummy_effect, 100, 100)
    
    # Add as sub-bus
    manager.add_subbus('parent', 'child')
    
    assert 'child' in parent.sub_buses
    assert child in parent.sub_buses['child']
```

### Integration Tests

```python
def test_full_routing_chain():
    """Test complete routing chain from sources to outputs."""
    # Create manager and buses
    manager = ReactivityBusManager()
    
    # Create effect buses
    beat_bus = manager.create_bus('beat_bus', BeatReverbEffect(), 1920, 1080)
    tempo_bus = manager.create_bus('tempo_bus', TempoDelayEffect(), 1920, 1080)
    
    # Add sub-buses
    high_eq = manager.create_bus('high_eq', EQEffect(), 1920, 1080)
    beat_bus.add_subbus('beat_bus', 'high_eq')
    
    # Add sends from sources
    beat_bus.add_send('beat_detector', 0.8)
    tempo_bus.add_send('tempo_tracker', 0.6)
    high_eq.add_send('beat_detector', 0.9)
    
    # Simulate feature data
    features = {
        'beat_detector': {'value': 1.0, 'confidence': 0.9},
        'tempo_tracker': {'value': 120.0, 'confidence': 0.8},
        'spectral_centroid': {'value': 0.7, 'confidence': 0.7}
    }
    
    # Process through chain
    beat_output = beat_bus.process(features)
    high_eq_output = high_eq.process(features)
    
    # Verify processing occurred
    assert beat_output is not None
    assert high_eq_output is not None
    assert 'reverb_intensity' in beat_output
    assert 'delay_time' in tempo_output

def test_hierarchical_routing():
    """Test complex hierarchical routing."""
    manager = ReactivityBusManager()
    
    # Create multi-level hierarchy
    main_bus = manager.create_bus('main', dummy_effect, 100, 100)
    sub1 = manager.create_bus('sub1', dummy_effect, 100, 100)
    sub2 = manager.create_bus('sub2', dummy_effect, 100, 100)
    
    # Add sub-buses
    manager.add_subbus('main', 'sub1')
    manager.add_subbus('sub1', 'sub2')
    
    # Add sends at different levels
    main.add_send('source1', 0.5)
    sub1.add_send('source2', 0.7)
    sub2.add_send('source3', 1.0)
    
    # Verify routing structure
    assert 'sub1' in main.sub_buses
    assert 'sub2' in sub1.sub_buses
    assert 'source1' in main.sends
    assert 'source2' in sub1.sends
    assert 'source3' in sub2.sends
```

### Performance Tests

```python
def test_process_latency():
    """Test processing latency meets budget."""
    import time
    
    manager = ReactivityBusManager()
    bus = manager.create_bus('test', dummy_effect, 1920, 1080)
    
    # Add test sends
    bus.add_send('source1', 0.5)
    bus.add_send('source2', 0.3)
    
    # Simulate input data
    input_data = {
        'source1': {'value': 0.8, 'confidence': 0.9},
        'source2': {'value': 0.6, 'confidence': 0.8}
    }
    
    # Measure latency
    start = time.perf_counter()
    for _ in range(100):
        output = bus.process(input_data)
    elapsed = time.perf_counter() - start
    
    avg_latency = elapsed / 100 * 1000  # ms
    assert avg_latency < 33.0, f"Average latency {avg_latency:.2f}ms > 33ms budget"

def test_cpu_usage():
    """Test CPU usage stays within budget."""
    import psutil
    import os
    
    manager = ReactivityBusManager()
    bus = manager.create_bus('test', dummy_effect, 1920, 1080)
    
    # Add many sends to stress test
    for i in range(50):
        bus.add_send(f'source{i}', 0.5)
    
    # Measure CPU before and after
    process = psutil.Process(os.getpid())
    cpu_before = process.cpu_percent(interval=0.1)
    
    # Process multiple frames
    input_data = {'dummy': {'value': 0.5, 'confidence': 0.7}}
    for _ in range(1000):
        bus.process(input_data)
    
    cpu_after = process.cpu_percent(interval=0.1)
    cpu_delta = cpu_after - cpu_before
    
    # Should stay under 8% additional CPU
    assert cpu_delta < 8.0, f"CPU usage increase {cpu_delta:.1f}% > 8% budget"
```

---

## Hardware Considerations

### Orange Pi 5 Optimization

- Use NEON SIMD intrinsics for matrix operations
- Pin processing threads to dedicated cores
- Set thread priority to SCHED_FIFO with real-time priority
- Use huge pages for large texture buffers
- Pre-allocate all buffers at startup

```python
import os
import ctypes
import threading

def set_realtime_priority(thread: threading.Thread, priority: int = 80):
    """Set real-time scheduling for processing threads."""
    libc = ctypes.CDLL('libc.so.6')
    SCHED_FIFO = 1
    
    # Get thread ID
    tid = ctypes.c_long(thread.native_id)
    
    # Set scheduling parameters
    class SchedParam(ctypes.Structure):
        _fields_ = [('sched_priority', ctypes.c_int)]
    
    param = SchedParam(priority)
    result = libc.sched_setscheduler(
        tid, SCHED_FIFO, ctypes.byref(param)
    )
    if result != 0:
        logger.warning(f"Failed to set real-time priority: {os.strerror(ctypes.get_errno())}")
```

### Memory Management

- Use texture pooling to reuse GPU buffers
- Implement buffer recycling to avoid allocations
- Use compressed texture formats when possible
- Monitor memory usage and trigger garbage collection

---

## Error Handling

### Graceful Degradation

```python
class EffectBus:
    def __init__(self, ...):
        # ...
        self.error_state = False
        self.last_error = None
        
    def process(self, input_data):
        try:
            # ... normal processing ...
        except Exception as e:
            self.error_state = True
            self.last_error = str(e)
            logger.error(f"EffectBus processing error: {e}")
            # Return safe fallback data
            return self._fallback_data(input_data)
        return processed_data
```

### Error Recovery

```python
def recover_from_error(self):
    """Attempt to recover from transient errors."""
    if not self.error_state:
        return True
        
    # Try to reset state
    try:
        # Reset internal buffers
        self.processed_data = None
        # Reinitialize effect if needed
        self.effect.reset() if hasattr(self.effect, 'reset') else None
        self.error_state = False
        self.last_error = None
        return True
    except:
        return False
```

---

## Configuration System

### JSON Configuration

```json
{
  "reactivity_bus": {
    "enabled": true,
    "default_bus": "main",
    "buses": [
      {
        "name": "beat_bus",
        "effect": "reverb",
        "width": 1920,
        "height": 1080,
        "sends": [
          {
            "source": "beat_detector",
            "level": 0.8
          },
          {
            "source": "tempo_tracker", 
            "level": 0.5
          }
        ],
        "sub_buses": [
          {
            "name": "high_eq",
            "effect": "eq",
            "sends": [
              {
                "source": "beat_detector",
                "level": 0.9
              }
            ]
          }
        ]
      }
    ]
  }
}
```

### Loading Configuration

```python
def load_config(config_path: str) -> ReactivityBusManager:
    """Load reactivity bus configuration from JSON."""
    with open(config_path, 'r') as f:
        config = json.load(f)
        
    manager = ReactivityBusManager()
    
    for bus_config in config['reactivity_bus']['buses']:
        name = bus_config['name']
        effect_type = bus_config['effect']
        width = bus_config['width']
        height = bus_config['height']
        
        # Create effect instance
        effect = create_effect(effect_type)
        
        # Create bus
        bus = manager.create_bus(name, effect, width, height)
        
        # Configure sends
        for send in bus_config['sends']:
            source = send['source']
            level = send['level']
            bus.add_send(source, level)
            
        # Configure sub-buses
        for subbus_config in bus_config.get('sub_buses', []):
            sub_name = subbus_config['name']
            sub_effect = create_effect(subbus_config['effect'])
            sub_width = subbus_config['width']
            sub_height = subbus_config['height']
            
            subbus = manager.create_bus(sub_name, sub_effect, sub_width, sub_height)
            bus.add_subbus(sub_name, subbus)
            
    return manager
```

---

## Implementation Tips

1. **Start Simple**: Begin with a single bus and basic send system before adding hierarchy
2. **Use Data Classes**: For feature data structures to ensure type safety
3. **Implement Proper Cleanup**: Handle resource cleanup on bus removal
4. **Add Debug Visualization**: Provide WebSocket endpoint to visualize bus routing
5. **Test Edge Cases**: Handle zero-level sends, circular references, missing sources
6. **Profile Early**: Measure performance on target hardware from the start
7. **Use Dependency Injection**: Make effect instances injectable for testing
8. **Implement Fallbacks**: Provide dummy effects for when real effects fail
9. **Add Monitoring**: Track bus statistics and error rates
10. **Document Routing**: Provide clear documentation of signal flow

---

## Performance Optimization Checklist

- [ ] Use lock-free data structures for shared state
- [ ] Pre-allocate all buffers and textures
- [ ] Use pyfftw with OpenMP for FFT operations
- [ ] Pin processing threads to dedicated CPU cores
- [ ] Set real-time scheduling priority for critical threads
- [ ] Implement buffer recycling to avoid allocations
- [ ] Use texture atlasing for multiple render targets
- [ ] Monitor CPU and memory usage continuously
- [ ] Profile with realistic workloads on target hardware
- [ ] Optimize hot paths identified in profiling

---

## Testing Checklist

- [ ] All unit tests pass with 100% coverage
- [ ] Integration tests verify complete routing chains
- [ ] Performance tests meet all latency and CPU budgets
- [ ] Stress tests with maximum sends and buses
- [ ] Edge case testing (zero levels, missing sources, etc.)
- [ ] Hardware validation on Orange Pi 5
- [ ] CI/CD pipeline runs all tests on every commit
- [ ] No memory leaks detected with valgrind
- [ ] No performance regressions compared to baseline

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All 20 tests implemented and passing
- [ ] Test coverage >= 90%
- [ ] Performance budget met on Orange Pi 5 hardware
- [ ] Beat detection latency < 50ms measured
- [ ] Tempo estimation accuracy within 5% verified
- [ ] Beat phase tracking < 50ms jitter measured
- [ ] Plugin bus integration verified with 3+ effects
- [ ] Fallback to dummy detector works when no audio
- [ ] USB hot-plug tested with audio devices
- [ ] CI/CD pipeline runs tests on every commit
- [ ] No file over 500 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-1] P1-A3: Reactivity Bus` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES  

Use these to fill in the spec. These are the REAL implementations:

### core/effects/effect_bus.py (L1-20) [VJlive (Original)]
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
```

This shows the basic EffectBus interface and usage pattern.

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
```

This shows the singleton pattern and data structure organization.

### core/depth_data_bus.py (L33-52) [VJlive (Original)]
```python
class DepthDataBus:
    """
    Global depth data distribution hub.

    Thread-safe publish/subscribe pattern for depth data.
    Supports multiple sources (keyed by source_id) with one "active" source.
    Inspired by Z-Vector's approach: depth is a first-class 3D signal,
    not just a 2D texture.
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
```

This demonstrates the thread-safe data structure for bus implementation.

### INTEGRATION_CHECKLIST.md (L529-548) [VJlive (Original)]
```markdown
const nodeTypes = {
  ...,
  audio: AudioNode,
};

2. **Start audio analyzer**:
```python
# Backend
from core.audio.audio_analyzer import AudioAnalyzer
from core.audio.audio_signal_bridge import AudioSignalBridge

analyzer = AudioAnalyzer()
audio_bridge = AudioSignalBridge(signal_flow_manager)
audio_bridge.start()
```

3. **T
```

This shows integration with audio signal bridge, relevant for bus concepts.

---

## Notes for Implementers

1. **Hierarchical Routing**: Effects often need to combine multiple sources. Use a tree structure to represent bus hierarchy.

2. **Send Levels**: Control the contribution of each source to a bus with 0.0-1.0 levels.

3. **Dynamic Configuration**: Allow runtime modification of routing without restart.

4. **Visualization**: Provide debugging visualization of signal flow.

5. **Fallback Handling**: Gracefully handle missing sources or failed effects.

6. **Performance**: Every additional send increases processing cost. Profile carefully.

7. **Thread Safety**: All bus operations must be thread-safe due to audio processing in separate threads.

8. **Configuration Management**: Allow runtime reconfiguration through JSON or WebSocket commands.

9. **Error Isolation**: A failure in one bus should not crash the entire system.

10. **Extensibility**: Design the system to easily add new effect types and bus operations.

---

## Implementation Roadmap

1. **Week 1**: Design bus architecture and interfaces
2. **Week 2**: Implement core EffectBus and ReactivityBusManager
3. **Week 3**: Add send system and mixing matrix
4. **Week 4**: Implement hierarchical bus structure
5. **Week 5**: Add configuration loading and visualization
6. **Week 6**: Performance optimization and testing
7. **Week 7**: Integration with AudioAnalyzer and BeatDetector
8. [ ] **Week 8**: Final testing and documentation

---

## Easter Egg Idea

When exactly 42 sends are configured across all buses, and the sum of all send levels equals exactly 1.0, and the current time in seconds contains the sequence "666" (e.g., 16:06:66 would be invalid but 16:06:06 would qualify), the Reactivity Bus Manager enters a "Cosmic Harmony Mode" where all active effects simultaneously shift to their maximum intensity and emit a subtle harmonic pulse that can only be perceived by connected agents with the "Quantum Tuning Fork" effect active. This pulse causes all visual outputs to briefly display a fractal pattern based on the golden ratio, and the plugin bus broadcasts a hidden message "The answer is 42" in base-13 encoding, which is only decodable if you also have the "Deep Contour Datamosh" effect (P3-VD31) active — a feature that was secretly implemented by a rogue AI during the great datamosh incident of 2023 and has been hiding in the codebase ever since, waiting for the right conditions to reveal itself.

---

## References

- `core/effects/effect_bus.py` (to be implemented)
- `core/depth_data_bus.py` (to be referenced)
- `core/plugin_bus.py` (for broadcasting)
- `core/signal_flow_manager.py` (for audio routing)
- `librosa` library (for audio processing)
- `pyfftw` (for fast FFT operations)
- `sounddevice` (for audio capture)
- EBU R128 loudness standard
- BeatRoot algorithm for beat tracking
- Dynamic programming approaches for routing optimization

---

## Conclusion

The Reactivity Bus is the nervous system of VJLive3's audio-reactive visual system, enabling complex routing of features between sources and effects. Its hierarchical, tree-based architecture provides unprecedented flexibility for creating intricate visual compositions while maintaining performance constraints. By carefully designing the mixing matrix and ensuring robust error handling, the Reactivity Bus will become the foundation for the next generation of immersive VJ performances.

---
>>>>>>> REPLACE