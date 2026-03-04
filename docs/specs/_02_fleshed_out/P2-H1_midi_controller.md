# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P2-H1_midi_controller.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P2-H1 — MIDI Controller Integration

**What This Module Does**

Implements bidirectional MIDI signal conversion nodes that bridge external MIDI hardware with VJLive3's modular parameter system. The MIDI Controller module enables seamless integration between VJLive3 and professional MIDI controllers, allowing users to map MIDI controller inputs to VJLive parameters and control external MIDI devices from VJLive's modulation system. This module provides two core converter nodes: MIDI-to-Parameter and Parameter-to-MIDI, facilitating bidirectional communication between VJLive's internal parameter system and external MIDI equipment.

---

## Architecture Decisions

- **Pattern:** Parameter Mapping with Curve-Based Scaling and Bidirectional Conversion
- **Rationale:** Professional MIDI controllers often use 0-127 value ranges, while VJLive's parameter system uses 0-10 ranges. Curve-based scaling allows for nuanced control mapping that matches human perception of control response. Bidirectional conversion enables both control of MIDI devices from VJLive and control of VJLive from MIDI controllers, creating a unified control ecosystem.
- **Constraints:**
  - Must support all standard MIDI messages (Note On/Off, Control Change, Pitch Bend, etc.)
  - Must maintain sub-1ms latency for real-time control
  - Must support configurable min/max ranges for both input and output
  - Must provide curve response shaping (linear, exponential, logarithmic)
  - Must handle MIDI channel assignment per mapping
  - Must maintain state for continuous controller values
  - Must support mapping of multiple MIDI controllers simultaneously
  - Must integrate with existing NodeGraph editor
  - Must provide visual feedback of mapping status
  - Must support MIDI learn functionality for easy mapping
  - Must maintain compatibility with existing modulation system

---

## Public Interface

```python
class MidiToParamNode(BaseMatrixNode):
    """Convert MIDI values (0-127) to parameter range (0-10)"""
    
    def __init__(self, name: str):
        super().__init__(name, "MIDI_TO_PARAM", "UTILITY")
        # Input port
        self.add_input_port("midi_in", SignalType.MIDI)
        # Output port
        self.add_output_port("param_out", SignalType.MODULATION)
        # Parameters
        self.add_parameter("min_out", 0.0, -10.0, 10.0, "Minimum output", "Scaling", SignalType.MODULATION)
        self.add_parameter("max_out", 10.0, -10.0, 10.0, "Maximum output", "Scaling", SignalType.MODULATION)
        self.add_parameter("curve", 1.0, 0.1, 4.0, "Response curve (1.0=linear)", "Scaling", SignalType.MODULATION)
        self.add_parameter("midi_channel", 1, 1, 16, "MIDI channel", "MIDI", SignalType.MODULATION)
        
    def process(self, dt: float = 0.016) -> Dict[str, Any]:
        """Convert MIDI to parameter range"""
        midi_in = self.get_input("midi_in")
        if midi_in is None:
            return {"param_out": 0.0}
        
        # Normalize MIDI (0-127) to 0-1
        normalized = max(0.0, min(127.0, midi_in)) / 127.0
        
        # Apply curve
        curve = self.get_parameter_value("curve")
        curved = normalized ** curve
        
        # Scale to output range
        min_out = self.get_parameter_value("min_out")
        max_out = self.get_parameter_value("max_out")
        output = min_out + (curved * (max_out - min_out))
        
        return {"param_out": output}

class ParamToMidiNode(BaseMatrixNode):
    """Convert parameter range (0-10) to MIDI values (0-127)"""
    
    def __init__(self, name: str):
        super().__init__(name, "PARAM_TO_MIDI", "UTILITY")
        # Input port
        self.add_input_port("param_in", SignalType.MODULATION)
        # Output port
        self.add_output_port("midi_out", SignalType.MIDI)
        # Parameters
        self.add_parameter("min_in", 0.0, -10.0, 10.0, "Minimum input", "Scaling", SignalType.MODULATION)
        self.add_parameter("max_in", 10.0, -10.0, 10.0, "Maximum input", "Scaling", SignalType.MODULATION)
        self.add_parameter("curve", 1.0, 0.1, 4.0, "Response curve (1.0=linear)", "Scaling", SignalType.MODULATION)
        self.add_parameter("midi_channel", 1, 1, 16, "MIDI channel", "MIDI", SignalType.MODULATION)
        
    def process(self, dt: float = 0.016) -> Dict[str, Any]:
        """Convert parameter to MIDI range"""
        param_in = self.get_input("param_in")
        if param_in is None:
            return {"midi_out": 0}
        
        # Normalize parameter to 0-1 based on input range
        min_in = self.get_parameter_value("min_in")
        max_in = self.get_parameter_value("max_in")
        if max_in == min_in:
            normalized = 0.0
        else:
            normalized = (param_in - min_in) / (max_in - min_in)
            normalized = max(0.0, min(1.0, normalized))
        
        # Apply curve
        curve = self.get_parameter_value("curve")
        curved = normalized ** curve
        
        # Scale to MIDI range (0-127)
        midi_value = int(curved * 127)
        midi_value = max(0, min(127, midi_value))
        
        return {"midi_out": midi_value}
```

---

## Core Components

### 1. MidiToParamNode

Converts MIDI controller values to VJLive parameters with configurable scaling and curve response.

```python
class MidiToParamNode(BaseMatrixNode):
    """Convert MIDI values (0-127) to parameter range (0-10)"""
    
    def __init__(self, name: str):
        super().__init__(name, "MIDI_TO_PARAM", "UTILITY")
        # Input port for MIDI signal
        self.add_input_port("midi_in", SignalType.MIDI)
        # Output port for parameter signal
        self.add_output_port("param_out", SignalType.MODULATION)
        # Parameters for scaling and curve
        self.add_parameter("min_out", 0.0, -10.0, 10.0, "Minimum output", "Scaling", SignalType.MODULATION)
        self.add_parameter("max_out", 10.0, -10.0, 10.0, "Maximum output", "Scaling", SignalType.MODULATION)
        self.add_parameter("curve", 1.0, 0.1, 4.0, "Response curve (1.0=linear)", "Scaling", SignalType.MODULATION)
        self.add_parameter("midi_channel", 1, 1, 16, "MIDI channel", "MIDI", SignalType.MODULATION)
        
    def process(self, dt: float = 0.016) -> Dict[str, Any]:
        """Convert MIDI to parameter range"""
        midi_in = self.get_input("midi_in")
        if midi_in is None:
            return {"param_out": 0.0}
        
        # Normalize MIDI value (0-127) to 0-1 range
        normalized = max(0.0, min(127.0, midi_in)) / 127.0
        
        # Apply curve shaping for natural response
        curve = self.get_parameter_value("curve")
        curved = normalized ** curve
        
        # Scale to target output range
        min_out = self.get_parameter_value("min_out")
        max_out = self.get_parameter_value("max_out")
        output = min_out + (curved * (max_out - min_out))
        
        return {"param_out": output}
```

### 2. ParamToMidiNode

Converts VJLive parameters back to MIDI controller values for external device control.

```python
class ParamToMidiNode(BaseMatrixNode):
    """Convert parameter range (0-10) to MIDI values (0-127)"""
    
    def __init__(self, name: str):
        super().__init__(name, "PARAM_TO_MIDI", "UTILITY")
        # Input port for parameter signal
        self.add_input_port("param_in", SignalType.MODULATION)
        # Output port for MIDI signal
        self.add_output_port("midi_out", SignalType.MIDI)
        # Parameters for scaling and curve
        self.add_parameter("min_in", 0.0, -10.0, 10.0, "Minimum input", "Scaling", SignalType.MODULATION)
        self.add_parameter("max_in", 10.0, -10.0, 10.0, "Maximum input", "Scaling", SignalType.MODULATION)
        self.add_parameter("curve", 1.0, 0.1, 4.0, "Response curve (1.0=linear)", "Scaling", SignalType.MODULATION)
        self.add_parameter("midi_channel", 1, 1, 16, "MIDI channel", "MIDI", SignalType.MODULATION)
        
    def process(self, dt: float = 0.016) -> Dict[str, Any]:
        """Convert parameter to MIDI range"""
        param_in = self.get_input("param_in")
        if param_in is None:
            return {"midi_out": 0}
        
        # Normalize parameter value to 0-1 based on configured range
        min_in = self.get_parameter_value("min_in")
        max_in = self.get_parameter_value("max_in")
        if max_in == min_in:
            normalized = 0.0
        else:
            normalized = (param_in - min_in) / (max_in - min_in)
            normalized = max(0.0, min(1.0, normalized))
        
        # Apply curve shaping for natural response
        curve = self.get_parameter_value("curve")
        curved = normalized ** curve
        
        # Scale to MIDI range (0-127) and convert to integer
        midi_value = int(curved * 127)
        midi_value = max(0, min(127, midi_value))
        
        return {"midi_out": midi_value}
```

---

## Integration with NodeGraph

### NodeGraph Implementation

The MIDI converter nodes integrate with VJLive's visual programming environment:

```javascript
// src/components/NodeGraph/nodes/MidiToParamNode.jsx
import React from 'react';
import { Handle, Position } from 'reactflow';
import { Music } from 'lucide-react';

const MidiToParamNode = ({ data, onNodeChange }) => {
    return (
        <div className="bg-gradient-to-br from-yellow-900 to-yellow-700 rounded-lg shadow-lg border-2 border-yellow-400 p-4 min-w-[200px]">
            <div className="flex items-center gap-2 mb-3 border-b border-yellow-400 pb-2">
                <Music className="w-5 h-5 text-yellow-200" />
                <span className="font-bold text-white">{data.label || 'MIDI to Param'}</span>
            </div>
            
            <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                    <span className="text-yellow-200">MIDI Channel:</span>
                    <span className="text-white font-mono text-xs">{data.midiChannel || 1}</span>
                </div>
                <div className="flex justify-between">
                    <span className="text-yellow-200">Curve:</span>
                    <span className="text-white font-mono text-xs">{data.curve || 1.0}</span>
                </div>
                <div className="flex justify-between">
                    <span className="text-yellow-200">Range:</span>
                    <span className="text-white font-mono text-xs">{data.minOut} - {data.maxOut}</span>
                </div>
            </div>
            
            <Handle
                type="source"
                position={Position.Right}
                id="midi_out"
                style={{
                    background: '#eab308',
                    width: 12,
                    height: 12,
                    'border-radius': '50%',
                    border: '2px solid #fff',
                }}
            />
        </div>
    );
};

export default MidiToParamNode;
```

### ParamToMidiNode Implementation

```javascript
// src/components/NodeGraph/nodes/ParamToMidiNode.jsx
import React from 'react';
import { Handle, Position } from 'reactflow';
import { Music } from 'lucide-react';

const ParamToMidiNode = ({ data, onNodeChange }) => {
    return (
        <div className="bg-gradient-to-br from-purple-900 to-purple-700 rounded-lg shadow-lg border-2 border-purple-400 p-4 min-w-[200px]">
            <div className="flex items-center gap-2 mb-3 border-b border-purple-400 pb-2">
                <Music className="w-5 h-5 text-purple-200" />
                <span className="font-bold text-white">{data.label || 'Param to MIDI'}</span>
            </div>
            
            <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                    <span className="text-purple-200">MIDI Channel:</span>
                    <span className="text-white font-mono text-xs">{data.midiChannel || 1}</span>
                </div>
                <div className="flex justify-between">
                    <span className="text-purple-200">Curve:</span>
                    <span className="text-white font-mono text-xs">{data.curve || 1.0}</span>
                </div>
                <div className="flex justify-between">
                    <span className="text-purple-200">Range:</span>
                    <span className="text-white font-mono text-xs">{data.minIn} - {data.maxIn}</span>
                </div>
            </div>
            
            <Handle
                type="sink"
                position={Position.Left}
                id="param_in"
                style={{
                    background: '#8b5cf6',
                    width: 12,
                    height: 12,
                    'border-radius': '50%',
                    border: '2px solid #fff',
                }}
            />
        </div>
    );
};

export default ParamToMidiNode;
```

---

## Performance Requirements

- **Latency:** < 1ms end-to-end conversion latency
- **CPU:** < 1% per node on Orange Pi 5
- **Memory:** < 5MB per node
- **Frame Rate:** No impact on 60 FPS rendering
- **Scalability:** Support 100+ simultaneous mappings
- **Sample Accuracy:** Maintain precise timing for MIDI signals
- **Buffering:** Minimal buffering (max 1 frame delay)

---

## Testing Strategy

### Unit Tests

```python
def test_midi_to_param_linear():
    """Test linear mapping without curve."""
    node = MidiToParamNode("test_node")
    node.set_parameter("min_out", 0.0)
    node.set_parameter("max_out", 10.0)
    node.set_parameter("curve", 1.0)
    
    # Test midpoint
    result = node.process(midi_in=64)  # ~50% of 127
    expected = 5.0  # 50% of 0-10 range
    assert abs(result["param_out"] - expected) < 0.01

def test_midi_to_param_exponential():
    """Test exponential mapping."""
    node = MidiToParamNode("test_node")
    node.set_parameter("min_out", 0.0)
    node.set_parameter("max_out", 10.0)
    node.set_parameter("curve", 0.5)  # Square root curve
    
    # Test midpoint
    result = node.process(midi_in=64)
    # With curve=0.5, sqrt(0.5) ≈ 0.707, so output ≈ 7.07
    assert result["param_out"] > 5.0

def test_param_to_midi_linear():
    """Test linear reverse mapping."""
    node = ParamToMidiNode("test_node")
    node.set_parameter("min_in", 0.0)
    node.set_parameter("max_in", 10.0)
    node.set_parameter("curve", 1.0)
    
    # Test midpoint
    result = node.process(param_in=5.0)
    expected = 64  # ~50% of 0-127
    assert abs(result["midi_out"] - expected) < 1

def test_boundary_conditions():
    """Test boundary values."""
    # MIDI to Param boundaries
    node = MidiToParamNode("test_node")
    node.set_parameter("min_out", 0.0)
    node.set_parameter("max_out", 10.0)
    
    # Test 0 and 127
    result_min = node.process(midi_in=0)
    result_max = node.process(midi_in=127)
    assert result_min["param_out"] == 0.0
    assert result_max["param_out"] == 10.0
    
    # Param to MIDI boundaries
    node2 = ParamToMidiNode("test_node")
    node2.set_parameter("min_in", 0.0)
    node2.set_parameter("max_in", 10.0)
    
    result_min = node2.process(param_in=0.0)
    result_max = node2.process(param_in=10.0)
    assert result_min["midi_out"] == 0
    assert result_max["midi_out"] == 127
```

### Integration Tests

```python
def test_full_midi_to_param_to_midi_cycle():
    """Test complete cycle of conversions."""
    # Create nodes
    midi_node = MidiToParamNode("midi_to_param")
    param_node = ParamToMidiNode("param_to_midi")
    
    # Configure mappings
    midi_node.set_parameter("min_out", 0.0)
    midi_node.set_parameter("max_out", 10.0)
    midi_node.set_parameter("curve", 1.0)
    
    param_node.set_parameter("min_in", 0.0)
    param_node.set_parameter("max_in", 10.0)
    param_node.set_parameter("curve", 1.0)
    
    # Test round-trip conversion
    test_values = [0, 32, 64, 96, 127]
    for midi_val in test_values:
        # MIDI to Param
        param_result = midi_node.process(midi_in=midi_val)
        # Param to MIDI
        midi_result = param_node.process(param_in=param_result["param_out"])
        
        # Allow small tolerance for floating point
        tolerance = 1.0 if midi_val < 127 else 0.0
        assert abs(midi_result["midi_out"] - midi_val) <= tolerance

def test_multiple_mappings():
    """Test multiple simultaneous mappings."""
    # Create multiple nodes
    nodes = []
    for i in range(5):
        node = MidiToParamNode(f"node_{i}")
        node.set_parameter("min_out", i * 2.0)
        node.set_parameter("max_out", (i + 1) * 2.0)
        node.set_parameter("curve", 1.0)
        node.set_parameter("midi_channel", i + 1)
        nodes.append(node)
    
    # Test different MIDI values
    test_midi = 64
    results = [node.process(midi_in=test_midi) for node in nodes]
    
    # All should complete without error
    assert all("param_out" in result for result in results)
```

### Performance Tests

```python
def test_latency_budget():
    """Test that conversion meets latency requirements."""
    import time
    
    # Create node
    node = MidiToParamNode("test_node")
    node.set_parameter("min_out", 0.0)
    node.set_parameter("max_out", 10.0)
    node.set_parameter("curve", 1.0)
    
    # Measure processing time
    test_midi = 64
    iterations = 1000
    
    start = time.perf_counter()
    for _ in range(iterations):
        result = node.process(midi_in=test_midi)
    elapsed = time.perf_counter() - start
    
    avg_latency = (elapsed / iterations) * 1000  # Convert to ms
    assert avg_latency < 1.0, f"Average latency {avg_latency:.3f}ms > 1ms budget"

def test_cpu_usage():
    """Test CPU usage stays within budget."""
    import psutil
    import os
    
    # Create multiple nodes
    nodes = []
    for i in range(10):
        node = MidiToParamNode(f"node_{i}")
        node.set_parameter("min_out", i * 1.0)
        node.set_parameter("max_out", (i + 1) * 1.0)
        nodes.append(node)
    
    # Measure CPU before and after
    process = psutil.Process(os.getpid())
    cpu_before = process.cpu_percent(interval=0.1)
    
    # Process many frames
    test_midi = 64
    for _ in range(10000):
        for node in nodes:
            node.process(midi_in=test_midi)
    
    cpu_after = process.cpu_percent(interval=0.1)
    cpu_delta = cpu_after - cpu_before
    
    assert cpu_delta < 2.0, f"CPU usage increase {cpu_delta:.1f}% > 2% budget"
```

---

## Hardware Considerations

### Real-Time Performance

- Use high-resolution timers for precise timing
- Implement frame pacing to maintain consistent 60 FPS
- Use separate threads for MIDI processing
- Implement jitter compensation for timing drift
- Use lock-free data structures for shared state

### Memory Management

- Use object pooling for node instances
- Implement lazy initialization for parameter mappings
- Use memory-mapped files for configuration storage
- Implement automatic cleanup of unused mappings

---

## Error Handling

### Graceful Degradation

```python
class MidiToParamNode(BaseMatrixNode):
    def __init__(self, name: str):
        # ...
        self.error_state = False
        self.last_error = None
        self.recovery_attempts = 0
        self.max_recovery_attempts = 5
        
    def process(self, dt: float = 0.016) -> Dict[str, Any]:
        try:
            # Normal processing
            result = self._process(midi_in=self.get_input("midi_in"))
            return result
        except ProcessingError as e:
            self.error_state = True
            self.last_error = str(e)
            logger.error(f"Processing error: {e}")
            
            # Attempt recovery
            if self._recover_from_error():
                return self._get_fallback_result()
            else:
                # Return safe fallback
                return self._create_safe_fallback()
        except Exception as e:
            self.error_state = True
            self.last_error = str(e)
            logger.critical(f"Unexpected error: {e}")
            return self._create_safe_fallback()
    
    def _recover_from_error(self) -> bool:
        """Attempt to recover from transient errors."""
        if self.recovery_attempts > 5:
            return False
            
        try:
            # Reset internal state
            self._reset_internal_state()
            self.recovery_attempts += 1
            return True
        except:
            return False
    
    def _create_safe_fallback(self) -> Dict[str, Any]:
        """Create a safe fallback state."""
        # Set all outputs to zero
        return {"param_out": 0.0}
```

### Error Recovery

```python
def recover_from_error(self):
    """Attempt to recover from transient errors."""
    if not self.error_state:
        return True
        
    # Try to reset state
    try:
        # Close and reopen MIDI device
        self._close_midi_device()
        self._open_midi_device()
        self.error_state = False
        self.last_error = None
        self.recovery_attempts = 0
        return True
    except:
        # Escalate to manager-level recovery
        self._notify_manager_of_failure()
        return False
```

---

## Configuration System

### JSON Configuration

```json
{
  "midi_controller": {
    "enabled": true,
    "default_midi_channel": 1,
    "mapping_refresh_rate": 30.0,
    "default_mapping": "linear",
    "smoothing_factor": 0.2,
    "midi_learn_enabled": true,
    "error_recovery": {
      "max_attempts": 5,
      "backoff_ms": 100
    },
    "nodes": [
      {
        "id": "midi_to_param_1",
        "type": "MidiToParamNode",
        "parameters": {
          "min_out": 0.0,
          "max_out": 10.0,
          "curve": 1.0,
          "midi_channel": 1
        },
        "connections": {
          "input": "MIDI_Controller_1/midi_out",
          "output": "Parameter_1/modulation_in"
        }
      },
      {
        "id": "param_to_midi_1",
        "type": "ParamToMidiNode",
        "parameters": {
          "min_in": 0.0,
          "max_in": 10.0,
          "curve": 1.0,
          "midi_channel": 1
        },
        "connections": {
          "input": "Parameter_1/modulation_out",
          "output": "MIDI_Controller_1/midi_in"
        }
      }
    ]
  }
}
```

### Configuration Loading

```python
def load_config(config_path: str) -> dict:
    """Load MIDI controller configuration from JSON."""
    with open(config_path, 'r') as f:
        config = json.load(f)
        
    # Validate required fields
    required_fields = ['enabled']
    for field in required_fields:
        if field not in config['midi_controller']:
            raise ValueError(f"Missing required field: {field}")
            
    return config['midi_controller']
```

---

## Implementation Tips

1. **Start Simple**: Begin with basic linear mapping before adding curve support
2. **Use Data Classes**: For parameter structures to ensure type safety
3. **Implement Proper Cleanup**: Handle resource cleanup on node shutdown
4. **Add Debug Visualization**: Provide WebSocket endpoint to visualize mappings
5. **Test Edge Cases**: Handle zero-volume, silent audio, extreme values
6. **Profile Early**: Measure performance on target hardware from the start
7. **Use Dependency Injection**: Make MIDI device and parameter system injectable
8. **Implement Fallbacks**: Provide dummy mappings when MIDI is unavailable
9. **Add Monitoring**: Track processing latency and error rates
10. **Document Mappings**: Provide clear documentation of mapping configurations

---

## Performance Optimization Checklist

- [ ] Use lock-free data structures for shared state
- [ ] Pre-allocate all audio/MIDI buffers
- [ ] Use SIMD for audio processing operations
- [ ] Pin processing threads to dedicated CPU cores
- [ ] Set real-time scheduling priority for MIDI thread
- [ ] Implement buffer recycling to avoid allocations
- [ ] Monitor CPU and memory usage continuously
- [ ] Profile hot paths identified in profiling
- [ ] Optimize with SIMD where possible

---

## Testing Checklist

- [ ] All unit tests pass with 100% coverage
- [ ] Integration tests verify complete MIDI conversion pipeline
- [ ] Performance tests meet all latency and CPU budgets
- [ ] Stress tests with maximum mappings and MIDI devices
- [ ] Edge case testing (silent MIDI, extreme values, etc.)
- [ ] Hardware validation on Orange Pi 5
- [ ] CI/CD pipeline runs all tests on every commit
- [ ] No memory leaks detected with valgrind
- [ ] No performance regressions compared to baseline
- [ ] MIDI learn functionality works correctly
- [ ] Visual feedback shows mapping status clearly
- [ ] Multiple simultaneous mappings work correctly

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All 20 tests implemented and passing
- [ ] Test coverage >= 90%
- [ ] Performance budget met on Orange Pi 5 hardware
- [ ] MIDI conversion latency < 1ms measured
- [ ] Bidirectional mapping verified
- [ ] MIDI learn functionality tested
- [ ] Collaborative mapping adjustments tested
- [ ] CI/CD pipeline runs tests on every commit
- [ ] No file over 500 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-2] P2-H1: MIDI Controller` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES  

Use these to fill in the spec. These are the REAL implementations:

### DEVELOPER_PROMPTS/08_MIDI_CONVERTER_NODES.md (L1-20) [VJlive (Original)]
```markdown
# DEVELOPER PROMPT 8: MIDI Converter Nodes (Bidirectional Signal Translation)

## Task
Create two converter nodes for translating between MIDI (0-127) and VJLive's parameter range (0-10):
1. **MIDI to Parameter Converter** (0-127 → 0-10)
2. **Parameter to MIDI Converter** (0-10 → 0-127)

These are utility nodes that bridge MIDI hardware with VJLive's modular parameter system.
```

### DEVELOPER_PROMPTS/08_MIDI_CONVERTER_NODES.md (L17-36) [VJlive (Original)]
```markdown
### 1. Create Converter Nodes Backend (`core/matrix/matrix_nodes.py`)

```python
class MidiToParamNode(BaseMatrixNode):
    """Convert MIDI values (0-127) to parameter range (0-10)"""

    def __init__(self, name: str):
        super().__init__(name, "MIDI_TO_PARAM", "UTILITY")

        # Input
        self.add_input_port("midi_in", SignalType.MIDI)

        # Output
        self.add_output_port("param_out", SignalType.MODULATION)

        # Scaling parameters
        self.add_parameter("min_out", 0.0, -10.0, 10.0, "Minimum output", "Scaling", SignalType.MODULATION)
        self.add_parameter("max_out", 10.0, -10.0, 10.0, "Maximum output", "Scaling", SignalType.MODULATION)
        self.add_parameter("curve", 1.0, 0.1, 4.0, "Response curve (1.0=linear)", "Scaling", SignalType.MODULATION)
        self.add_parameter("midi_channel", 1, 1, 16, "MIDI channel", "MIDI", SignalType.MODULATION)
```

### 2. Create Converter Nodes Backend (`core/matrix/matrix_nodes.py`) (continued)

```python
    def process(self, dt: float = 0.016) -> Dict[str, Any]:
        """Convert MIDI to parameter range"""
        midi_in = self.get_input("midi_in")

        if midi_in is None:
            return {"param_out": 0.0}

        # Normalize MIDI (0-127) to 0-1
        normalized = max(0.0, min(127.0, midi_in)) / 127.0

        # Apply curve
        curve = self.get_parameter_value("curve")
        curved = normalized ** curve

        # Scale to output range
        min_out = self.get_parameter_value("min_out")
        max_out = self.get_parameter_value("max_out")
        output = min_out + (curved * (max_out - min_out))

        return {"param_out": output}
```

### 3. Create Converter Nodes Backend (`core/matrix/matrix_nodes.py`) (continued)

```python
class ParamToMidiNode(BaseMatrixNode):
    """Convert parameter range (0-10) to MIDI values (0-127)"""

    def __init__(self, name: str):
        super().__init__(name, "PARAM_TO_MIDI", "UTILITY")

        # Input
        self.add_input_port("param_in", SignalType.MODULATION)

        # Output
        self.add_output_port("midi_out", SignalType.MIDI)

        # Scaling parameters
        self.add_parameter("min_in", 0.0, -10.0, 10.0, "Minimum input", "Scaling", SignalType.MODULATION)
        self.add_parameter("max_in", 10.0, -10.0, 10.0, "Maximum input", "Scaling", SignalType.MODULATION)
        self.add_parameter("curve", 1.0, 0.1, 4.0, "Response curve (1.0=linear)", "Scaling", SignalType.MODULATION)
        self.add_parameter("midi_channel", 1, 1, 16, "MIDI channel", "MIDI", SignalType.MODULATION)
```

### 4. Create Converter Nodes Backend (`core/matrix/matrix_nodes.py`) (continued)

```python
    def process(self, dt: float = 0.016) -> Dict[str, Any]:
        """Convert parameter to MIDI range"""
        param_in = self.get_input("param_in")

        if param_in is None:
            return {"midi_out": 0}

        # Normalize parameter to 0-1 based on input range
        min_in = self.get_parameter_value("min_in")
        max_in = self.get_parameter_value("max_in")

        if max_in == min_in:
            normalized = 0.0
        else:
            normalized = (param_in - min_in) / (max_in - min_in)
            normalized = max(0.0, min(1.0, normalized))

        # Apply curve
        curve = self.get_parameter_value("curve")
        curved = normalized ** curve

        # Scale to MIDI range (0-127)
        midi_value = int(curved * 127)
        midi_value = max(0, min(127, midi_value))

        return {"midi_out": midi_value}
```

## Architecture Notes

- **Scaling**: Both nodes support min/max range adjustment and curve response
- **Curve Parameter**:
  - `curve = 1.0` → Linear response
  - `curve < 1.0` → Exponential (more sensitivity at low end)
  - `curve > 1.0` → Logarithmic (more sensitivity at high end)
- **Integer Conversion**: Param→MIDI converts float to integer (0-127)
- **Clamping**: Both nodes clamp values to prevent overflow
- **Zero Latency**: Direct mathematical conversion, no buffering

## Mathematical Formulas

### MIDI to Parameter
```
normalized = midi_value / 127.0
curved = normalized ^ curve_param
output = min_out + (curved × (max_out - min_out))
```

### Parameter to MIDI
```
normalized = (param_value - min_in) / (max_in - min_in)
curved = normalized ^ curve_param
midi_value = floor(curved × 127)
```

## Performance Considerations

- **Minimal Processing**: Simple arithmetic, no heavy computation
- **No GUI Overhead**: Minimal UI elements for low CPU usage
- **Direct Pass-Through**: No buffering or smoothing (can be added if needed)
- **Sample Accurate**: Processes every frame without latency

## Success Criteria

- Both converter nodes appear in node library under "Utility"
- MIDI→Param correctly scales 0-127 to 0-10
- Param→MIDI correctly scales 0-10 to 0-127
- Nodes display current conversion values in real-time
- Curve parameter affects response shape
- Min/max parameters adjust output range
- Zero latency conversion
- Works with all MIDI and parameter sources
```

---

## Notes for Implementers

1. **Mapping System**: Implement flexible mapping system that allows runtime adjustment of how MIDI controller inputs control DMX channels
2. **Smoothing**: Apply temporal smoothing to prevent flickering in lighting responses
3. **Fallback Behavior**: Provide graceful degradation when MIDI input is unavailable
4. **MIDI Learn**: Support MIDI learn functionality for easy mapping during performance
5. **Protocol Compatibility**: Ensure compatibility with both standard MIDI and USB MIDI devices
6. **Performance**: Optimize for low-latency operation on target hardware
7. **Testing**: Use mock MIDI controller for unit testing without physical hardware
8. **Documentation**: Provide clear examples for common mapping configurations
9. **Error Handling**: Implement robust error recovery for network and MIDI failures
10. **Scalability**: Design for future expansion to more complex mapping scenarios

---

## Implementation Roadmap

1. **Week 1**: Design mapping system architecture and data structures
2. **Week 2**: Implement core MidiToParamNode and ParamToMidiNode with basic linear mapping
3. **Week 3**: Add curve response shaping and range configuration capabilities
4. **Week 4**: Implement MIDI learn functionality and NodeGraph integration
5. **Week 5**: Add visual feedback and real-time parameter display
6. **Week 6**: Performance optimization and comprehensive testing
7. [ ] **Week 7**: Final validation and documentation

---
-

## References

- `core/matrix/matrix_nodes.py` (to be implemented)
- `web_ui/src/components/NodeGraph/nodes/MidiToParamNode.jsx` (to be implemented)
- `web_ui/src/components/NodeGraph/nodes/ParamToMidiNode.jsx` (to be implemented)
- `libartnet` library (for Art-Net implementation)
- `pyfftw` library (for optimized FFT operations)
- `numpy` (for array operations)
- `scipy.signal` (for audio filtering operations)
- BeatRoot algorithm for beat tracking
- Dynamic programming approaches for parameter mapping

---

## Conclusion

The MIDI Controller module is the critical bridge between external MIDI hardware and VJLive3's modular parameter system. By implementing bidirectional MIDI conversion with flexible scaling and curve response, this module enables creators to build deeply integrated control surfaces that respond intelligently to performance gestures. Its robust architecture, real-time performance, and seamless integration with existing systems will empower VJs to create performances where lighting, video, and sound become a unified expression of artistic intent, controlled through professional MIDI equipment with precision and creative flexibility.

---
