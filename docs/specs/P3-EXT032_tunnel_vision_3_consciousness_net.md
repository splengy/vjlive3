# P3-EXT032_tunnel_vision_3_consciousness_net.md

**Phase:** Phase 3 / P3-EXT032  
**Assigned To:** Implementation Engineer  
**Spec Written By:** Manager (Gemini-3.1)  
**Date:** 2026-02-23  

---

## Task: P3-EXT032 — Tunnel Vision 3: ConsciousnessNet

**Priority:** P0 (Critical)  
**Status:** ⬜ Todo  
**Source:** `vjlive/plugins/vdepth/tunnel_vision_3.py`  
**Legacy Class:** `QuantumConsciousnessSingularityEffect`

---

## What This Module Does

Tunnel Vision 3.0 (ConsciousnessNet) is a revolutionary depth-mosh visual effect that integrates quantum consciousness processing, multi-dimensional reality warping, and neural singularity to create an unprecedented psychedelic experience. The effect combines a custom PyTorch neural network (ConsciousnessNet) with OpenGL shader rendering to manipulate visual perception through quantum state evolution, dimensional transformation matrices, and audio-synesthetic mapping. It processes depth data, audio frequencies, and frame content to generate immersive, consciousness-inspired visual distortions that simulate reality manipulation and quantum entanglement effects.

---

## What It Does NOT Do

- Does NOT perform actual quantum computation (simulates quantum states classically with numpy)
- Does NOT replace production-grade AI services (uses lightweight 4-layer neural network)
- Does NOT handle 3D rendering beyond 2D matrix with depth simulation
- Does NOT provide standalone neural network training (inference-only, pre-trained weights)
- Does NOT include advanced audio analysis beyond simple frequency band energy extraction
- Does NOT manage WebSocket collaboration or distributed rendering

---

## Public Interface

```python
from typing import Dict, Tuple, Optional, List
import numpy as np
import torch
import torch.nn as nn
from dataclasses import dataclass

@dataclass
class QuantumConsciousnessConfig:
    """Configuration for quantum consciousness processing."""
    frequency: float = 0.1
    amplitude: float = 1.0
    phase: float = 0.0

@dataclass
class RealityManipulationConfig:
    """Configuration for multi-dimensional reality warping."""
    dimension_count: int = 4
    frequency: float = 0.05
    amplitude: float = 1.0
    phase: float = 0.0

@dataclass
class NeuralSingularityConfig:
    """Configuration for neural singularity effects."""
    frequency: float = 0.02
    amplitude: float = 1.0
    intensity: float = 0.0
    phase: float = 0.0

@dataclass
class QuantumEntanglementConfig:
    """Configuration for quantum entanglement effects."""
    strength: float = 0.5
    phase: float = 0.0

@dataclass
class SynestheticMappingConfig:
    """Configuration for audio-to-visual synesthetic mapping."""
    intensity: float = 0.5
    phase: float = 0.0

class ConsciousnessNet(nn.Module):
    """
    Lightweight neural network for quantum consciousness processing.
    4-layer fully connected network with ReLU activations and sigmoid output.
    Input: 8-dimensional quantum state
    Hidden: 16 → 32 → 16
    Output: 8-dimensional processed state
    """
    def __init__(self):
        super().__init__()
        self.layer1 = nn.Linear(8, 16)
        self.layer2 = nn.Linear(16, 32)
        self.layer3 = nn.Linear(32, 16)
        self.layer4 = nn.Linear(16, 8)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = torch.relu(self.layer1(x))
        x = torch.relu(self.layer2(x))
        x = torch.relu(self.layer3(x))
        x = torch.sigmoid(self.layer4(x))
        return x

class QuantumConsciousnessSingularityEffect(Effect):
    """
    Main plugin class for Tunnel Vision 3.0: ConsciousnessNet.
    Inherits from Effect base class.
    """

    METADATA = {
        "name": "Tunnel Vision 3: ConsciousnessNet",
        "version": "1.0.0",
        "description": "Quantum consciousness singularity with neural network processing",
        "author": "VJLive Team",
        "capabilities": [
            "quantum_consciousness",
            "neural_network",
            "multi_dimensional",
            "reality_warping",
            "synesthetic_audio",
            "depth_mosh",
            "shader_rendering",
            "openGL"
        ]
    }

    def __init__(self) -> None:
        """Initialize the quantum consciousness singularity effect."""
        # Quantum Consciousness System
        self.quantum_consciousness: np.ndarray = np.zeros((8, 8))
        self.consciousness_phase: float = 0.0
        self.consciousness_state: np.ndarray = np.random.rand(8)
        self.consciousness_config: QuantumConsciousnessConfig = QuantumConsciousnessConfig()

        # Multi-Dimensional Reality System
        self.reality_matrix: np.ndarray = np.eye(4)
        self.reality_phase: float = 0.0
        self.dimension_count: int = 4
        self.reality_config: RealityManipulationConfig = RealityManipulationConfig()

        # Neural Singularity System
        self.singularity_state: np.ndarray = np.zeros((16, 16))
        self.singularity_phase: float = 0.0
        self.singularity_intensity: float = 0.0
        self.singularity_config: NeuralSingularityConfig = NeuralSingularityConfig()

        # Quantum Entanglement System
        self.entanglement_matrix: np.ndarray = np.eye(8)
        self.entanglement_phase: float = 0.0
        self.entanglement_config: QuantumEntanglementConfig = QuantumEntanglementConfig()

        # Synesthetic Mapping System
        self.synesthetic_map: np.ndarray = np.zeros((3, 3))
        self.synesthetic_phase: float = 0.0
        self.synesthetic_config: SynestheticMappingConfig = SynestheticMappingConfig()

        # Neural Network
        self.consciousness_net: Optional[ConsciousnessNet] = None

        # Shader Programs
        self.quantum_shader: Optional[int] = None
        self.reality_shader: Optional[int] = None
        self.singularity_shader: Optional[int] = None

        # Framebuffers
        self.quantum_fbo: Optional[int] = None
        self.reality_fbo: Optional[int] = None
        self.singularity_fbo: Optional[int] = None

        # External Integrations
        self.rave_effects: Optional[NeuralRaveNexus] = None

    def _initialize_consciousness_net(self) -> ConsciousnessNet:
        """Initialize the neural network for quantum consciousness processing."""
        return ConsciousnessNet()

    def _initialize_quantum_consciousness(self) -> None:
        """Initialize the quantum consciousness state matrix."""
        self.quantum_consciousness = np.random.rand(8, 8)
        self.quantum_consciousness /= np.sum(self.quantum_consciousness)

    def _quantum_consciousness(self, time_val: float) -> np.ndarray:
        """
        Process quantum consciousness state evolution.

        Args:
            time_val: Current time in seconds

        Returns:
            8x8 complex quantum state matrix
        """
        self.consciousness_phase += self.consciousness_config.frequency * time_val

        phase_matrix = np.array([
            [np.cos(self.consciousness_phase), -np.sin(self.consciousness_phase)],
            [np.sin(self.consciousness_phase), np.cos(self.consciousness_phase)]
        ])

        for i in range(8):
            for j in range(8):
                self.quantum_consciousness[i, j] *= np.exp(
                    1j * self.consciousness_phase * (i + j)
                )

        self.quantum_consciousness /= np.sum(np.abs(self.quantum_consciousness))
        return self.quantum_consciousness

    def _reality_manipulation(self, uv: np.ndarray, time_val: float) -> np.ndarray:
        """
        Manipulate reality through multi-dimensional warping.

        Args:
            uv: Nx2 array of UV coordinates
            time_val: Current time in seconds

        Returns:
            Transformed UV coordinates
        """
        self.reality_phase += self.reality_config.frequency * time_val

        reality_transform = np.eye(4)

        for dim in range(self.dimension_count):
            angle = self.reality_phase + dim * np.pi / self.dimension_count
            reality_transform[dim, dim] = np.cos(angle)
            reality_transform[dim, (dim + 1) % 4] = -np.sin(angle)
            reality_transform[(dim + 1) % 4, dim] = np.sin(angle)
            reality_transform[(dim + 1) % 4, (dim + 1) % 4] = np.cos(angle)

        transformed_uv = np.dot(uv, reality_transform[:2, :2])
        return transformed_uv

    def _neural_singularity(self, frame_data: np.ndarray, time_val: float) -> np.ndarray:
        """
        Process neural singularity effects.

        Args:
            frame_data: Optional frame data for processing
            time_val: Current time in seconds

        Returns:
            16x16 singularity field
        """
        self.singularity_phase += self.singularity_config.frequency * time_val

        singularity_field = np.zeros((16, 16))

        for i in range(16):
            for j in range(16):
                distance = np.sqrt((i - 8)**2 + (j - 8)**2)
                singularity_field[i, j] = np.exp(
                    -distance / (1 + self.singularity_intensity)
                ) * np.sin(self.singularity_phase + distance * 0.1)

        return singularity_field

    def _quantum_entanglement(self, time_val: float) -> np.ndarray:
        """
        Process quantum entanglement effects.

        Args:
            time_val: Current time in seconds

        Returns:
            8x8 entanglement matrix
        """
        self.entanglement_phase += time_val * 0.01

        entanglement_matrix = np.eye(8)

        for i in range(8):
            for j in range(8):
                if i != j:
                    entanglement_matrix[i, j] = np.sin(
                        self.entanglement_phase + i * j * 0.1
                    ) * self.entanglement_config.strength

        return entanglement_matrix

    def _synesthetic_mapping(self, audio_data: np.ndarray, time_val: float) -> np.ndarray:
        """
        Map audio data to visual synesthetic effects.

        Args:
            audio_data: Audio frequency data
            time_val: Current time in seconds

        Returns:
            3x3 synesthetic transformation matrix
        """
        synesthetic_map = np.zeros((3, 3))

        # Split audio into frequency bands
        bass_energy = np.mean(audio_data[:int(len(audio_data) * 0.3)])
        mid_energy = np.mean(audio_data[int(len(audio_data) * 0.3):int(len(audio_data) * 0.7)])
        treble_energy = np.mean(audio_data[int(len(audio_data) * 0.7):])

        synesthetic_map[0, 0] = bass_energy * self.synesthetic_config.intensity
        synesthetic_map[1, 1] = mid_energy * self.synesthetic_config.intensity
        synesthetic_map[2, 2] = treble_energy * self.synesthetic_config.intensity

        return synesthetic_map

    def apply_uniforms(self, time_val: float, resolution: Tuple[int, int],
                      audio_reactor: Optional[AudioAnalyzer] = None,
                      semantic_layer: Optional[DepthProcessor] = None,
                      frame_data: Optional[np.ndarray] = None) -> bool:
        """
        Apply uniforms to the shader program and render the effect.

        Args:
            time_val: Current time value
            resolution: Screen resolution (width, height)
            audio_reactor: Optional audio analyzer for audio reactivity
            semantic_layer: Optional depth processor for depth data
            frame_data: Optional frame data for neural processing

        Returns:
            True if rendering succeeded, False otherwise
        """
        try:
            # Get quantum consciousness state
            quantum_state = self._quantum_consciousness(time_val)

            # Get reality manipulation
            uv_coords = np.array([[x / resolution[0], y / resolution[1]]
                                 for x in range(resolution[0])
                                 for y in range(resolution[1])])
            transformed_uv = self._reality_manipulation(uv_coords, time_val)

            # Get neural singularity
            if frame_data is not None:
                singularity_field = self._neural_singularity(frame_data, time_val)
            else:
                singularity_field = np.zeros((16, 16))

            # Get quantum entanglement
            entanglement_matrix = self._quantum_entanglement(time_val)

            # Get synesthetic mapping
            if audio_reactor is not None:
                audio_data = audio_reactor.get_frequency_data()
                synesthetic_map = self._synesthetic_mapping(audio_data, time_val)
            else:
                synesthetic_map = np.zeros((3, 3))

            # Apply uniforms to shader
            glUniform1f(glGetUniformLocation(self.program, "u_consciousness_phase"),
                       self.consciousness_phase)
            glUniform2f(glGetUniformLocation(self.program, "u_consciousness_frequency"),
                       self.consciousness_config.frequency, self.consciousness_config.amplitude)
            glUniformMatrix4fv(glGetUniformLocation(self.program, "u_reality_matrix"),
                              1, GL_TRUE, self.reality_matrix.flatten())
            glUniform1f(glGetUniformLocation(self.program, "u_reality_phase"),
                       self.reality_phase)
            glUniform1f(glGetUniformLocation(self.program, "u_singularity_intensity"),
                       self.singularity_intensity)
            glUniform1f(glGetUniformLocation(self.program, "u_singularity_phase"),
                       self.singularity_phase)
            glUniformMatrix4fv(glGetUniformLocation(self.program, "u_entanglement_matrix"),
                              1, GL_TRUE, self.entanglement_matrix.flatten())
            glUniformMatrix3fv(glGetUniformLocation(self.program, "u_synesthetic_map"),
                              1, GL_TRUE, synesthetic_map.flatten())
            glUniform1f(glGetUniformLocation(self.program, "u_time"), time_val)
            glUniform2f(glGetUniformLocation(self.program, "u_resolution"),
                       resolution[0], resolution[1])

            # Apply rave effects
            if self.rave_effects is not None:
                self.rave_effects.apply_uniforms(time_val, resolution, audio_reactor)

            return True

        except Exception as e:
            # Log error but don't crash
            print(f"Error in ConsciousnessNet apply_uniforms: {e}")
            return False

    def update(self, params: Dict[str, float]) -> None:
        """
        Update plugin parameters.

        Args:
            params: Dictionary of parameter names and values
        """
        for key, value in params.items():
            if key == "consciousness_frequency":
                self.consciousness_config.frequency = value
            elif key == "consciousness_amplitude":
                self.consciousness_config.amplitude = value
            elif key == "reality_dimension_count":
                self.dimension_count = max(2, min(11, int(value)))
            elif key == "reality_frequency":
                self.reality_config.frequency = value
            elif key == "reality_amplitude":
                self.reality_config.amplitude = value
            elif key == "singularity_frequency":
                self.singularity_config.frequency = value
            elif key == "singularity_amplitude":
                self.singularity_config.amplitude = value
            elif key == "singularity_intensity":
                self.singularity_intensity = value
            elif key == "entanglement_strength":
                self.entanglement_config.strength = value
            elif key == "synesthetic_intensity":
                self.synesthetic_config.intensity = value

    def on_param_update(self, param_name: str, value: float) -> None:
        """Handle individual parameter updates."""
        self.update({param_name: value})

    def on_audio_data(self, audio_data: List[float]) -> None:
        """
        Process audio reactivity data.

        Args:
            audio_data: List of audio frequency values
        """
        # Audio is handled in apply_uniforms via audio_reactor
        pass

    def on_midi_data(self, midi_data: Dict) -> None:
        """
        Process MIDI control messages.

        Args:
            midi_data: MIDI message dictionary
        """
        # MIDI handling could map CC values to parameters
        pass

    def render(self, matrix: 'Matrix') -> None:
        """
        Main render method - delegates to apply_uniforms.

        Args:
            matrix: Output matrix to render into
        """
        # This effect uses shader-based rendering via apply_uniforms
        # The actual rendering happens in the shader program
        pass
```

---

## Inputs and Outputs

### Parameters

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `consciousness_frequency` | `float` | Speed of quantum consciousness evolution | 0.01 - 1.0 |
| `consciousness_amplitude` | `float` | Strength of consciousness effects | 0.1 - 2.0 |
| `reality_dimension_count` | `int` | Number of dimensions to warp | 2 - 11 |
| `reality_frequency` | `float` | Speed of reality manipulation | 0.01 - 1.0 |
| `reality_amplitude` | `float` | Strength of reality warping | 0.1 - 2.0 |
| `singularity_frequency` | `float` | Speed of neural singularity pulse | 0.005 - 0.5 |
| `singularity_amplitude` | `float` | Strength of singularity effect | 0.1 - 2.0 |
| `singularity_intensity` | `float` | Focus of singularity field | 0.0 - 1.0 |
| `entanglement_strength` | `float` | Quantum entanglement coupling | 0.0 - 1.0 |
| `synesthetic_intensity` | `float` | Audio-to-visual mapping strength | 0.0 - 1.0 |

### Inputs

- **Matrix**: Output surface to render into (width × height × RGBA)
- **Resolution**: Tuple of (width, height) for coordinate transformations
- **Audio Data**: Optional `AudioAnalyzer` instance providing frequency data
- **Depth Data**: Optional `DepthProcessor` instance for depth-reactive effects
- **Frame Data**: Optional numpy array for neural network processing
- **Time**: Float value representing current time in seconds

### Outputs

- **Rendered Matrix**: Final visual output with quantum consciousness effects applied via shader
- **Shader Uniforms**: Multiple uniform variables sent to GLSL shader program
- **Neural Processing**: 8-dimensional output from ConsciousnessNet
- **Synesthetic Mapping**: 3x3 matrix derived from audio frequency bands

---

## Edge Cases and Error Handling

### Missing Dependencies
- **PyTorch**: Fallback to numpy-based linear algebra (slower, but functional). Disable neural network processing and use identity matrix.
- **OpenGL shaders**: Fallback to CPU rendering with reduced quality. Use simple 2D transformations instead of full shader pipeline.
- **NeuralRaveNexus**: Disable rave effects gracefully; continue without them.

### Invalid Parameters
- Clamp all numeric parameters to their valid ranges
- Log warnings for out-of-range values
- Raise `ValueError` for completely invalid parameter types
- Ensure `dimension_count` stays within 2-11 range

### Resource Limits
- **Neural network inference**: Cap batch size to 1, use half-precision if available
- **Shader compilation**: Retry with simplified shader on failure
- **Memory**: Release framebuffers and shader programs on cleanup
- **CPU fallback**: Use reduced resolution (e.g., 640×480) when falling back to software rendering

### State Corruption
- Validate quantum consciousness matrix sums to 1.0 (probability distribution)
- Re-initialize consciousness net if weights become NaN
- Never crash on malformed input; log errors and continue

### Audio/Depth Missing
- If `audio_reactor` is None, use zero-filled synesthetic map
- If `semantic_layer` is None, skip depth-reactive effects
- If `frame_data` is None, use zero-filled singularity field

---

## Dependencies

### External Libraries
- **torch** (PyTorch) — neural network inference, fallback: numpy (CPU-only, slower)
- **numpy** — matrix operations and quantum state calculations, required
- **PyOpenGL** — shader rendering and framebuffer management, fallback: software renderer
- **OpenGL.GL.shaders** — shader compilation, required for GPU path

### Internal Modules
- `vjlive3.render.effect.Effect` — base class for all effects
- `vjlive3.render.matrix.Matrix` — output surface
- `vjlive3.audio.engine.AudioAnalyzer` — audio reactivity interface
- `vjlive3.depth.processor.DepthProcessor` — depth data interface
- `vjlive3.plugins.neural_rave_nexus.NeuralRaveNexus` — additional rave effects integration

### Shader Resources
- Custom GLSL shader with uniforms: `u_consciousness_phase`, `u_consciousness_frequency`, `u_reality_matrix`, `u_reality_phase`, `u_singularity_intensity`, `u_singularity_phase`, `u_entanglement_matrix`, `u_synesthetic_map`, `u_time`, `u_resolution`

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_defaults` | All configs initialize to valid defaults |
| `test_consciousness_net_creation` | Neural network initializes with correct architecture |
| `test_quantum_consciousness_evolution` | Quantum state evolves correctly over time |
| `test_reality_manipulation` | UV coordinates transform with dimensional warping |
| `test_neural_singularity_field` | Singularity field generates correct pattern |
| `test_quantum_entanglement_matrix` | Entanglement matrix has correct off-diagonal values |
| `test_synesthetic_mapping` | Audio bands map to 3x3 matrix correctly |
| `test_parameter_clamping` | Out-of-range values are clamped to limits |
| `test_dimension_range` | Dimension count clamped to 2-11 range |
| `test_apply_uniforms_success` | Shader uniforms set without errors when all dependencies present |
| `test_apply_uniforms_audio_missing` | Handles missing audio_reactor gracefully |
| `test_apply_uniforms_frame_missing` | Handles missing frame_data gracefully |
| `test_neural_network_inference` | ConsciousnessNet produces 8-dim output from 8-dim input |
| `test_update_method` | Parameter updates modify correct config fields |
| `test_memory_cleanup` | Framebuffers and shaders release properly on cleanup |
| `test_fps_under_load` | Maintains 60 FPS with 1920×1080 resolution |
| `test_torch_fallback` | Numpy fallback works when PyTorch unavailable |
| `test_shader_compilation` | GLSL shader compiles successfully on target GPU |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code (no `pass` statements, no `TODO` comments)
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-EXT032: tunnel_vision_3_consciousness_net` message
- [ ] BOARD.md updated (Status → ✅ Done)
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Implementation Notes

### Performance Targets
- **60 FPS** at 1920×1080 with all effects enabled
- **Neural inference** < 5ms per frame (with PyTorch GPU if available)
- **Shader compilation** < 200ms on first load
- **Parameter updates** < 1ms latency
- **Memory footprint** < 150MB (including PyTorch model ~2MB)

### Quality Standards
- Follow VJlive-2 plugin architecture patterns
- Use type hints throughout
- Document all public methods with docstrings
- Include comprehensive error handling with graceful fallbacks
- Add debug visualization toggle (hold D key to show raw fields)
- Ensure shader code is cross-platform compatible (OpenGL 3.3+)

### Legacy References
- Source: `vjlive/plugins/vdepth/tunnel_vision_3.py` (285 lines)
- Related: `vjlive/plugins/vdepth/neural_rave_nexus.py` for rave effects integration
- Shader: Custom GLSL embedded in Python (needs extraction to `.glsl` file)
- Tests: None in legacy — create comprehensive test suite

### Porting Strategy
1. Create base class inheriting from `Effect`
2. Define dataclasses for configuration (QuantumConsciousnessConfig, etc.)
3. Implement ConsciousnessNet as separate module with proper torch handling
4. Port quantum consciousness evolution to numpy with complex numbers
5. Implement reality manipulation matrix transformations
6. Port neural singularity field generation
7. Implement quantum entanglement matrix
8. Port synesthetic audio mapping
9. Extract GLSL shader code to separate file; implement shader loading
10. Implement `apply_uniforms` with proper OpenGL state management
11. Add parameter update handling via `update()` and `on_param_update()`
12. Integrate with AudioAnalyzer and DepthProcessor interfaces
13. Add fallback paths for missing dependencies
14. Comprehensive testing and performance optimization

### Risks
- **PyTorch dependency**: May be heavy for VJLive3; consider ONNX export or torchscript for lighter weight
- **Shader complexity**: Multi-pass rendering with multiple framebuffers may be complex; simplify if needed
- **Performance**: 8×8 quantum matrix operations and 16×16 singularity field could be expensive on CPU; optimize with numpy vectorization
- **Memory**: Multiple framebuffers (quantum_fbo, reality_fbo, singularity_fbo) increase GPU memory usage; consider single-pass approach
- **Cross-platform**: OpenGL shader compatibility varies; test on multiple drivers

---

## References

- **Legacy Implementation**: `vjlive/plugins/vdepth/tunnel_vision_3.py`
- **Neural Rave Nexus**: `vjlive/plugins/vdepth/neural_rave_nexus.py`
- **Effect Base Class**: `vjlive3.render.effect.Effect`
- **Audio Analyzer**: `vjlive3.audio.engine.AudioAnalyzer`
- **Depth Processor**: `vjlive3.depth.processor.DepthProcessor`
- **Shader Guide**: `docs/architecture/gpu_detector_design.md`
- **Plugin API**: `docs/plugin_api.md`
- **Safety Rails**: `WORKSPACE/SAFETY_RAILS.md`
- **Testing Strategy**: `TESTING_STRATEGY.md`
