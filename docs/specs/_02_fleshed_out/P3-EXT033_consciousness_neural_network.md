# P3-EXT033_consciousness_neural_network.md

## Task: P3-EXT033 — Consciousness Neural Network

**Phase:** 3 — Effects  
**Assignment:** Implementation Engineer (Worker)  
**Date:** 2026-02-23  
**Status:** Ready for Implementation  

---

## What This Module Does

The Consciousness Neural Network effect creates a living neural network visualization that represents consciousness patterns and quantum thought processes. Points form neural connections that dynamically respond to audio input, consciousness levels, and quantum states. The effect renders a 3D point cloud with connections that simulate neural firing, synaptic strength, and quantum entanglement. It features 28+ parameters organized into four categories: Neural Network dynamics, Consciousness metrics, Quantum Consciousness effects, and Audio Reactivity controls. The effect includes 4 preset configurations for quick creative exploration.

---

## What It Does NOT Do

- Does NOT perform actual neural network inference or machine learning (it's a visual simulation)
- Does NOT replace depth camera input with generated content (it uses depth as a spatial guide)
- Does NOT output audio or MIDI (audio-reactive only as visual modulation)
- Does NOT store persistent state between sessions (state is ephemeral)
- Does NOT include particle physics simulation beyond point rendering
- Does NOT support multi-GPU distributed rendering
- Does NOT provide real-time neural network training capabilities

---

## Public Interface

### Core Classes

```python
from typing import Dict, Any, Optional, Tuple
import numpy as np

class ConsciousnessNeuralNetwork(BaseNode):
    """
    Consciousness Neural Network - Quantum Mind Matrix
    
    Creates a living neural network that represents consciousness patterns
    and quantum thought processes. Points form neural connections that
    respond to audio, consciousness levels, and quantum states.
    """
    
    def __init__(self, name: str = "consciousness_neural_network") -> None:
        """Initialize the effect with default parameters and shader."""
        pass
    
    def process(
        self,
        video_frame: np.ndarray,
        depth_frame: np.ndarray,
        audio_data: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Process video and depth frames through consciousness neural network.
        
        Args:
            video_frame: RGB video frame (HxWx3 uint8)
            depth_frame: Depth frame (HxW float32 or uint16)
            audio_data: Optional audio analysis dict with keys:
                - bass: float [0.0, 1.0]
                - treble: float [0.0, 1.0]
                - mid: float [0.0, 1.0]
                - overall: float [0.0, 1.0]
                - overtone: float [0.0, 1.0]
                - rhythm: float [0.0, 1.0]
                - harmony: float [0.0, 1.0]
                - dissonance: float [0.0, 1.0]
        
        Returns:
            Dictionary containing:
                - 'video': processed video frame (may be modified in-place)
                - 'depth': processed depth frame (may be modified in-place)
                - 'effect_info': dict with effect state and metadata
        """
        pass
    
    def update_preset(self, preset_index: int) -> bool:
        """
        Apply preset configuration.
        
        Args:
            preset_index: 0=Custom, 1=Neural Network, 2=Quantum Mind, 3=Consciousness Flow
        
        Returns:
            True if preset applied successfully, False otherwise
        """
        pass
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get current effect state for serialization.
        
        Returns:
            Dictionary with time, audio_data, parameters, and preset index
        """
        pass
    
    def set_parameter(self, param_name: str, value: float) -> bool:
        """
        Set parameter value with validation.
        
        Args:
            param_name: Parameter name from self.parameters
            value: New parameter value (will be clamped to min/max)
        
        Returns:
            True if parameter set successfully, False if param_name invalid
        """
        pass
```

### Configuration Dataclasses (Optional)

```python
from dataclasses import dataclass

@dataclass
class NeuralNetworkConfig:
    """Neural network simulation parameters."""
    density: float = 0.7
    connection_strength: float = 0.8
    firing_rate: float = 0.6
    synapse_strength: float = 0.7
    growth: float = 0.5
    decay: float = 0.2
    reorganization: float = 0.6
    plasticity: float = 0.8

@dataclass
class ConsciousnessConfig:
    """Consciousness state parameters."""
    level: float = 0.5
    thought_intensity: float = 0.7
    memory_access: float = 0.6
    emotional_state: float = 0.4
    cognitive_load: float = 0.5
    awareness_level: float = 0.6
    perception_intensity: float = 0.3
    intuition_strength: float = 0.4

@dataclass
class QuantumConsciousnessConfig:
    """Quantum consciousness parameters."""
    entanglement: float = 0.5
    superposition: float = 0.6
    tunneling: float = 0.3
    decoherence: float = 0.2
    foam: float = 0.4
    interference: float = 0.5
    coherence: float = 0.6
    entanglement_range: float = 0.5

@dataclass
class AudioReactivityConfig:
    """Audio reactivity parameters."""
    influence: float = 0.5
    bass_response: float = 0.7
    treble_response: float = 0.3
    mid_response: float = 0.4
    overtone_response: float = 0.2
    rhythm_sensitivity: float = 0.6
    harmony_response: float = 0.3
    dissonance_response: float = 0.1

@dataclass
class VisualConfig:
    """Visual rendering parameters."""
    point_size: float = 2.0
    glow_intensity: float = 0.4
    connection_opacity: float = 0.6
    neural_color: float = 0.5
    background_opacity: float = 0.3
    depth_fog: float = 0.2
    motion_blur: float = 0.1
```

---

## Inputs and Outputs

### Parameters

| Parameter Name | Type | Default | Min | Max | Description |
|----------------|------|---------|-----|-----|-------------|
| `neural_density` | float | 0.7 | 0.0 | 1.0 | Density of neural points |
| `connection_strength` | float | 0.8 | 0.0 | 1.0 | Strength of neural connections |
| `neural_firing_rate` | float | 0.6 | 0.0 | 1.0 | Rate of neural firing |
| `synapse_strength` | float | 0.7 | 0.0 | 1.0 | Synaptic connection strength |
| `neural_growth` | float | 0.5 | 0.0 | 1.0 | Neural network growth rate |
| `neural_decay` | float | 0.2 | 0.0 | 1.0 | Neural decay rate |
| `neural_reorganization` | float | 0.6 | 0.0 | 1.0 | Network reorganization frequency |
| `neural_plasticity` | float | 0.8 | 0.0 | 1.0 | Neural plasticity |
| `consciousness_level` | float | 0.5 | 0.0 | 1.0 | Overall consciousness level |
| `thought_intensity` | float | 0.7 | 0.0 | 1.0 | Intensity of thought patterns |
| `memory_access` | float | 0.6 | 0.0 | 1.0 | Memory access depth |
| `emotional_state` | float | 0.4 | 0.0 | 1.0 | Emotional state influence |
| `cognitive_load` | float | 0.5 | 0.0 | 1.0 | Cognitive load factor |
| `awareness_level` | float | 0.6 | 0.0 | 1.0 | Awareness level |
| `perception_intensity` | float | 0.3 | 0.0 | 1.0 | Perception intensity |
| `intuition_strength` | float | 0.4 | 0.0 | 1.0 | Intuition strength |
| `quantum_entanglement` | float | 0.5 | 0.0 | 1.0 | Quantum entanglement strength |
| `quantum_superposition` | float | 0.6 | 0.0 | 1.0 | Superposition effect |
| `quantum_tunneling` | float | 0.3 | 0.0 | 1.0 | Tunneling probability |
| `quantum_decoherence` | float | 0.2 | 0.0 | 1.0 | Decoherence rate |
| `quantum_foam` | float | 0.4 | 0.0 | 1.0 | Quantum foam density |
| `quantum_interference` | float | 0.5 | 0.0 | 1.0 | Interference pattern strength |
| `quantum_coherence` | float | 0.6 | 0.0 | 1.0 | Coherence maintenance |
| `quantum_entanglement_range` | float | 0.5 | 0.0 | 1.0 | Entanglement range |
| `audio_influence` | float | 0.5 | 0.0 | 1.0 | Overall audio influence |
| `bass_response` | float | 0.7 | 0.0 | 1.0 | Bass frequency response |
| `treble_response` | float | 0.3 | 0.0 | 1.0 | Treble frequency response |
| `mid_response` | float | 0.4 | 0.0 | 1.0 | Mid frequency response |
| `overtone_response` | float | 0.2 | 0.0 | 1.0 | Overtone response |
| `rhythm_sensitivity` | float | 0.6 | 0.0 | 1.0 | Rhythm detection sensitivity |
| `harmony_response` | float | 0.3 | 0.0 | 1.0 | Harmony detection response |
| `dissonance_response` | float | 0.1 | 0.0 | 1.0 | Dissonance detection response |
| `point_size` | float | 2.0 | 1.0 | 10.0 | Point size in pixels |
| `glow_intensity` | float | 0.4 | 0.0 | 1.0 | Glow effect intensity |
| `connection_opacity` | float | 0.6 | 0.0 | 1.0 | Connection line opacity |
| `neural_color` | float | 0.5 | 0.0 | 1.0 | Neural color intensity |
| `background_opacity` | float | 0.3 | 0.0 | 1.0 | Background opacity |
| `depth_fog` | float | 0.2 | 0.0 | 1.0 | Depth fog exponent |
| `motion_blur` | float | 0.1 | 0.0 | 1.0 | Motion blur amount |
| `preset` | int (enum) | 0 | 0 | 3 | Preset: 0=Custom, 1=Neural Network, 2=Quantum Mind, 3=Consciousness Flow |

### Inputs

| Input | Type | Description |
|-------|------|-------------|
| `video_frame` | np.ndarray (HxWx3 uint8) | RGB video frame to process |
| `depth_frame` | np.ndarray (HxW float32/uint16) | Depth frame for spatial positioning |
| `audio_data` | Optional[Dict[str, float]] | Audio analysis values (all floats [0.0, 1.0]) |

### Outputs

| Output | Type | Description |
|--------|------|-------------|
| `video` | np.ndarray | Processed video frame (may be modified in-place) |
| `depth` | np.ndarray | Processed depth frame (may be modified in-place) |
| `effect_info` | Dict[str, Any] | Effect state including time, audio_data, parameters |

---

## Edge Cases and Error Handling

### Missing Dependencies

- **OpenGL/GLSL not available**: Fall back to CPU-based point rendering using numpy. Log warning once per session.
- **Shader compilation failure**: Log error, fall back to simple point cloud rendering without connections.
- **numpy not available**: Raise ImportError with clear message about numpy requirement.

### Invalid Parameters

- Parameter values outside [min, max] are automatically clamped during `set_parameter()`.
- Invalid parameter names in `set_parameter()` return False, no exception raised.
- Preset index out of range [0, 3] is ignored, `update_preset()` returns False.

### Resource Limits

- **Memory**: Point cloud size is fixed at approximately 10,000 points. If depth frame is extremely large (>8K), downsample internally to maintain performance.
- **GPU**: If shader compilation fails or OpenGL context lost, fall back to CPU rendering at reduced resolution (max 1920x1080).
- **CPU**: Process frames in separate thread if frame time exceeds 10ms to avoid blocking main pipeline.

### State Corruption

- `get_state()` returns a serializable dict; if audio_data contains non-serializable values, convert to float.
- `set_parameter()` validates parameter existence before assignment.
- Time accumulation uses `time += 0.016` (assuming 60 FPS); if time grows unbounded, wrap at 1,000,000 seconds to prevent float precision issues.

### Collaboration Session

- This effect is stateless regarding collaborative sessions; no special handling needed.

---

## Dependencies

### External Libraries

| Library | Purpose | Import Name | Fallback |
|---------|---------|-------------|----------|
| `numpy` | Array operations, point cloud math | `import numpy as np` | Required — no fallback |
| `OpenGL` (ModernGL/pyopengl) | Shader rendering | `from core.effects.base import BaseNode` | CPU fallback rendering |
| `PyOpenGL` | GLSL shader compilation | `from .shader_base import Effect` | CPU fallback rendering |

### Internal Modules

- `core.effects.base.BaseNode` — Base node class for plugin system
- `plugins.shader_base.Effect` — Shader management wrapper

---

## Test Plan

### Unit Tests

1. **Initialization**
   - Test `__init__` creates default parameters with correct types and ranges
   - Test custom name parameter sets `self.name` correctly
   - Test shader initialization (if OpenGL available)

2. **Parameter Management**
   - Test `set_parameter()` sets valid parameters correctly
   - Test `set_parameter()` returns False for invalid parameter names
   - Test parameter clamping to [min, max] boundaries
   - Test all 38 parameters have correct default values

3. **Preset System**
   - Test `update_preset(0)` applies Custom preset (no change)
   - Test `update_preset(1)` applies Neural Network preset values
   - Test `update_preset(2)` applies Quantum Mind preset values
   - Test `update_preset(3)` applies Consciousness Flow preset values
   - Test `update_preset(5)` returns False (invalid index)

4. **State Serialization**
   - Test `get_state()` returns dict with keys: time, audio_data, parameters, preset
   - Test `get_state()` time is float, audio_data is dict, parameters is dict
   - Test state dict is JSON-serializable

5. **Audio Reactivity**
   - Test `process()` with `audio_data=None` uses default audio_data
   - Test `process()` with custom `audio_data` updates internal state
   - Test audio_data keys are correctly extracted and used

6. **Frame Processing**
   - Test `process()` returns dict with 'video', 'depth', 'effect_info' keys
   - Test `process()` with small frames (320x240) completes without error
   - Test `process()` with large frames (4K) downsamples if needed
   - Test `process()` time increments by ~0.016 per call

7. **Shader Compilation**
   - Test shader source is valid GLSL 330 core
   - Test shader compiles without errors (if OpenGL available)
   - Test shader has all required uniform locations

8. **Error Handling**
   - Test `set_parameter()` with invalid name returns False
   - Test `update_preset()` with invalid index returns False
   - Test CPU fallback when OpenGL unavailable

### Integration Tests

1. **Plugin System Integration**
   - Test ConsciousnessNeuralNetwork can be loaded via plugin registry
   - Test plugin metadata (display_name, category, node_type) is correct
   - Test plugin can be instantiated through factory pattern

2. **Pipeline Integration**
   - Test effect can be inserted into video processing pipeline
   - Test effect receives video, depth, and audio inputs correctly
   - Test effect output can be consumed by downstream nodes

3. **Performance Benchmarks**
   - Test average frame processing time < 10ms on 1080p (60 FPS budget)
   - Test memory usage stays < 50MB for point cloud + shader
   - Test no memory leaks over 10,000 consecutive frames

### Regression Tests

- Test preset values remain stable across code changes
- Test shader output matches reference images (pixel comparison)
- Test parameter changes produce visible output differences

---

## Definition of Done

- [ ] **Specification approved** by user
- [ ] **Task queued** via `mcp--vjlive-switchboard--queue_task`
- [ ] **Implementation complete** in `src/vjlive3/plugins/consciousness_neural_network.py`
- [ ] **All unit tests pass** (≥80% coverage)
- [ ] **Integration tests pass** (pipeline + plugin system)
- [ ] **Performance benchmarks met** (<10ms/frame on 1080p)
- [ ] **Shader compiles** without errors on target hardware
- [ ] **CPU fallback** works when OpenGL unavailable
- [ ] **Documentation updated** (plugin API docs, user guide)
- [ ] **Board updated** with completion status
- [ ] **Code review passed** (if applicable)

---

## Implementation Notes

### Performance Targets

- **Frame Time**: ≤ 10ms per frame on 1080p (60 FPS budget = 16.67ms)
- **Memory**: ≤ 50MB total (point cloud ~10MB, shader ~5MB, overhead ~35MB)
- **Startup**: Shader compilation ≤ 100ms
- **Parameter Updates**: ≤ 1ms per parameter change

### Quality Standards

- Follow VJLive3 plugin architecture: inherit from `BaseNode`
- Use Pydantic validation for parameter definitions
- Implement proper error handling with logging
- Support hot-reload without state loss where possible
- Use type hints throughout (mypy compliance)
- Document all public methods with docstrings

### Legacy References

- **Source file**: `/home/happy/Desktop/claude projects/vjlive/plugins/vdepth/consciousness_neural_network.py`
- **Legacy class**: `ConsciousnessNeuralNetwork(BaseNode)`
- **Shader**: Embedded GLSL 330 core fragment shader with 28+ uniforms
- **Legacy features**: 4 presets (Custom, Neural Network, Quantum Mind, Consciousness Flow)

### Porting Strategy

1. Create plugin file `src/vjlive3/plugins/consciousness_neural_network.py`
2. Copy class structure from legacy, adapt to VJLive3 `BaseNode` API
3. Extract GLSL shader to separate file `shaders/consciousness_neural_network.frag`
4. Implement `process()` method with ModernGL shader pipeline
5. Add parameter definitions using plugin registry schema
6. Implement CPU fallback using numpy point cloud rendering
7. Add audio_data integration with existing audio analysis bus
8. Write unit tests for parameter management and preset system
9. Write integration tests for pipeline compatibility
10. Benchmark and optimize (target <10ms/frame)

### Risks

- **Shader complexity**: 300+ line GLSL shader may be difficult to debug. Mitigation: test incrementally, use simpler fallback first.
- **OpenGL compatibility**: Shader uses GLSL 330 core; may not work on older GPUs. Mitigation: provide CPU fallback.
- **Performance**: Point cloud + connections may be heavy at 4K. Mitigation: implement adaptive point count based on resolution.
- **Audio integration**: Legacy expects specific audio_data dict format. Mitigation: adapt from existing audio bus output format.

---

## References

- Legacy implementation: `vjlive/plugins/vdepth/consciousness_neural_network.py`
- Shader template: `docs/specs/_TEMPLATE.md`
- Plugin architecture: `docs/plugin_api.md`
- Safety rails: `WORKSPACE/SAFETY_RAILS.md`
- Implementation protocols: `WORKSPACE/PRIME_DIRECTIVE.md`
