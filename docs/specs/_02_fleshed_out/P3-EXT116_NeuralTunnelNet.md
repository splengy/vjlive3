# P3-EXT116: NeuralTunnelNet — Quantum Neural Tunnel Network

> **Task ID:** `P3-EXT116`  
> **Priority:** P3 (Standard)  
> **Source:** VJlive (Original)  
> **Class:** `NeuralTunnelNet`  
> **Phase:** Phase 3  
> **Status:** ⬜ Todo  

---

## Mission Context

Port the `NeuralTunnelNet` effect from the VJlive codebase into VJLive3's modern plugin architecture. This effect creates a quantum neural tunnel experience that combines deep neural network processing with immersive tunnel visualization techniques.

The NeuralTunnelNet generates a mesmerizing tunnel effect with neural network-based color transformations, quantum feedback loops, and hyper-dimensional warping that creates a sense of traveling through a neural network structure.

---

## Technical Requirements

- Implement as a VJLive3 plugin following the manifest-based registry system
- Inherit from `Effect` base class in `src/vjlive3/plugins/base.py`
- Integrate with VJLive3's rendering pipeline for real-time processing
- Ensure 60 FPS performance at 1080p (Safety Rail 1)
- Achieve ≥80% test coverage (Safety Rail 5)
- File size ≤750 lines (Safety Rail 4)
- No silent failures, proper error handling (Safety Rail 7)
- Support OpenGL shader-based rendering with neural network-inspired transformations

---

## Implementation Notes

### Original Location
- **VJlive (Original):** `plugins/vdepth/tunnel_vision_2.py`
- **Documentation:** `plugins/vdepth/TUNNEL_VISION_2_DOCUMENTATION.md`

### Description
The NeuralTunnelNet creates a tunnel effect with:
1. Neural network-based color transformations using a lightweight CNN
2. Quantum feedback loops that create recursive visual patterns
3. Hyper-dimensional warping with parameterized tunnel properties
4. Synesthetic mapping between audio and visual elements

The effect uses a neural network architecture to transform the input frame, creating a "neural tunnel" effect where the visual output appears to be processed through a neural network.

### Porting Strategy
1. Extract the neural network architecture and parameter system
2. Map the 18+ parameters to VJLive3's parameter system
3. Create a proper class inheriting from `Effect` with appropriate metadata
4. Implement parameter validation and clamping (0.0 to 10.0 range)
5. Register the plugin in the VJLive3 plugin manifest
6. Write comprehensive tests covering parameter handling, rendering, and edge cases
7. Verify against original behavior with test vectors

---

## Detailed Behavior and Parameter Interactions

### Core Functionality
The NeuralTunnelNet generates a tunnel effect using:

1. **Neural Network Transformation:** A lightweight CNN processes the input frame to create color transformations
2. **Quantum Feedback:** Recursive feedback loops create self-similar patterns
3. **Hyper-Warping:** Parameterized transformations create the tunnel illusion
4. **Synesthetic Mapping:** Audio features modulate visual parameters

### Parameter Interactions
The effect has 18+ parameters that interact in complex ways:

- **Tunnel Parameters:** `tunnel_speed`, `rotation`, `fractal_depth`, `recursion`, `center_pull`, `wall_warp`
- **Color Parameters:** `color_shift`, `depth_fov`, `mosh_stretch`, `grid_lines`, `aberration`
- **Neural Parameters:** `neural_intensity`, `quantum_feedback`, `hyper_warp`, `dimensional_shift`
- **Advanced Parameters:** `synesthetic_mapping`, `collective_consciousness`, `eternity`

These parameters interact to create emergent visual patterns. For example:
- High `quantum_feedback` with high `recursion` creates infinite recursive tunnels
- High `neural_intensity` with high `color_shift` creates psychedelic color transitions
- High `hyper_warp` with high `tunnel_speed` creates extreme distortion effects

### Neural Network Architecture
The legacy implementation uses a simple CNN:
```python
class NeuralTunnelNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(3, 16, 3, padding=1)  # Input: RGB frame
        self.conv2 = nn.Conv2d(16, 32, 3, padding=1) # Hidden layer 1
        self.conv3 = nn.Conv2d(32, 64, 3, padding=1) # Hidden layer 2
        self.pool = nn.MaxPool2d(2, 2)               # Pooling layer
        self.fc1 = nn.Linear(64 * 16 * 16, 128)      # Fully connected 1
        self.fc2 = nn.Linear(128, 64)                # Fully connected 2
        self.fc3 = nn.Linear(64, 3)                  # Output: RGB transformation
```

This network transforms the input frame through convolutional layers and fully connected layers to produce a color-transformed output.

### Quantum Feedback System
The quantum feedback system creates recursive patterns:
```python
def _quantum_feedback(self, time_val: float):
    """Apply quantum feedback to the tunnel"""
    # Update quantum state
    self.quantum_phase += time_val * 0.01 * self.parameters['quantum_feedback'] / 10.0
    
    # Apply quantum superposition
    quantum_matrix = np.array([
        [np.cos(self.quantum_phase), -np.sin(self.quantum_phase), 0, 0],
        [np.sin(self.quantum_phase), np.cos(self.quantum_phase), 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1]
    ])
```

This creates a phase-based feedback loop that enhances the tunnel effect.

---

## Public Interface

```python
from vjlive3.plugins.base import Effect
from vjlive3.audio.reactivity import AudioReactor
from vjlive3.audio.analyzer import AudioFeature
import torch
import torch.nn as nn

class NeuralTunnelNet(Effect):
    """
    Quantum Neural Tunnel Network.
    
    Creates an immersive tunnel experience with neural network-based
    color transformations, quantum feedback loops, and hyper-dimensional
    warping.
    """
    
    def __init__(self):
        """Initialize the NeuralTunnelNet effect."""
        fragment_shader = self._generate_tunnel_shader()
        super().__init__("Neural Tunnel Net", fragment_shader)
        
        # Effect metadata
        self.effect_category = "generative"
        self.effect_tags = ["tunnel", "neural", "quantum", "generative", "psychedelic"]
        self.features = ["NEURAL_PROCESSING", "QUANTUM_FEEDBACK", "SYNETHETIC_MAPPING"]
        
        # Parameter ranges (0.0-10.0)
        self._parameter_ranges = {
            'tunnel_speed': (0.0, 10.0),
            'rotation': (0.0, 10.0),
            'fractal_depth': (0.0, 10.0),
            'recursion': (0.0, 10.0),
            'center_pull': (0.0, 10.0),
            'wall_warp': (0.0, 10.0),
            'color_shift': (0.0, 10.0),
            'depth_fov': (0.0, 10.0),
            'mosh_stretch': (0.0, 10.0),
            'grid_lines': (0.0, 10.0),
            'aberration': (0.0, 10.0),
            'eternity': (0.0, 10.0),
            'neural_intensity': (0.0, 10.0),
            'quantum_feedback': (0.0, 10.0),
            'hyper_warp': (0.0, 10.0),
            'dimensional_shift': (0.0, 10.0),
            'synesthetic_mapping': (0.0, 10.0),
            'collective_consciousness': (0.0, 10.0)
        }
        
        # Default parameter values
        self.parameters = {
            'tunnel_speed': 8.0,
            'rotation': 6.0,
            'fractal_depth': 8.0,
            'recursion': 8.0,
            'center_pull': 6.0,
            'wall_warp': 7.0,
            'color_shift': 8.0,
            'depth_fov': 8.0,
            'mosh_stretch': 8.0,
            'grid_lines': 6.0,
            'aberration': 7.0,
            'eternity': 9.0,
            'neural_intensity': 9.0,
            'quantum_feedback': 8.0,
            'hyper_warp': 9.0,
            'dimensional_shift': 8.0,
            'synesthetic_mapping': 9.0,
            'collective_consciousness': 8.0
        }
        
        # Parameter descriptions
        self._parameter_descriptions = {
            'tunnel_speed': "Speed of tunnel progression",
            'rotation': "Rotation speed of tunnel",
            'fractal_depth': "Depth of fractal patterns",
            'recursion': "Number of recursive tunnel layers",
            'center_pull': "Strength of center pull effect",
            'wall_warp': "Warping of tunnel walls",
            'color_shift': "Rate of color transitions",
            'depth_fov': "Field of view depth",
            'mosh_stretch': "Stretching of tunnel elements",
            'grid_lines': "Intensity of grid lines",
            'aberration': "Chromatic aberration intensity",
            'eternity': "Time dilation effect",
            'neural_intensity': "Strength of neural network transformation",
            'quantum_feedback': "Quantum feedback loop intensity",
            'hyper_warp': "Hyper-dimensional warping",
            'dimensional_shift': "Dimensional shift effect",
            'synesthetic_mapping': "Audio-visual mapping intensity",
            'collective_consciousness': "Collective consciousness effect"
        }
        
        # Sweet spot values for optimal visual effects
        self._sweet_spots = {
            'tunnel_speed': [8.0, 9.0],
            'rotation': [6.0, 7.0],
            'fractal_depth': [8.0],
            'recursion': [8.0, 9.0],
            'center_pull': [6.0],
            'wall_warp': [7.0],
            'color_shift': [8.0],
            'depth_fov': [8.0],
            'mosh_stretch': [8.0],
            'grid_lines': [6.0],
            'aberration': [7.0],
            'eternity': [9.0],
            'neural_intensity': [9.0],
            'quantum_feedback': [8.0],
            'hyper_warp': [9.0],
            'dimensional_shift': [8.0],
            'synesthetic_mapping': [9.0],
            'collective_consciousness': [8.0]
        }
        
        # Initialize neural network
        self._initialize_neural_network()
        
        # Initialize quantum state
        self.quantum_phase = 0.0
        
        # Initialize audio reactivity
        self._audio_reactor = AudioReactor()
    
    def _initialize_neural_network(self):
        """Initialize the neural network for visual processing"""
        class NeuralTunnelNet(nn.Module):
            def __init__(self):
                super().__init__()
                self.conv1 = nn.Conv2d(3, 16, 3, padding=1)
                self.conv2 = nn.Conv2d(16, 32, 3, padding=1)
                self.conv3 = nn.Conv2d(32, 64, 3, padding=1)
                self.pool = nn.MaxPool2d(2, 2)
                self.fc1 = nn.Linear(64 * 16 * 16, 128)
                self.fc2 = nn.Linear(128, 64)
                self.fc3 = nn.Linear(64, 3)
                
            def forward(self, x):
                x = torch.relu(self.conv1(x))
                x = self.pool(x)
                x = torch.relu(self.conv2(x))
                x = self.pool(x)
                x = torch.relu(self.conv3(x))
                x = self.pool(x)
                x = x.view(-1, 64 * 16 * 16)
                x = torch.relu(self.fc1(x))
                x = torch.relu(self.fc2(x))
                x = torch.tanh(self.fc3(x))
                return x
        
        self.neural_model = NeuralTunnelNet()
        self.neural_model.eval()
    
    def _generate_tunnel_shader(self) -> str:
        """
        Generate the GLSL fragment shader source.
        
        Returns:
            Complete fragment shader source code as string
        """
        return """
            uniform float tunnel_speed;
            uniform float rotation;
            uniform float fractal_depth;
            uniform float recursion;
            uniform float center_pull;
            uniform float wall_warp;
            uniform float color_shift;
            uniform float depth_fov;
            uniform float mosh_stretch;
            uniform float grid_lines;
            uniform float aberration;
            uniform float eternity;
            uniform float neural_intensity;
            uniform float quantum_feedback;
            uniform float hyper_warp;
            uniform float dimensional_shift;
            uniform float synesthetic_mapping;
            uniform float collective_consciousness;
            uniform float time;
            
            void main() {
                vec2 uv = gl_FragCoord.xy / resolution.xy;
                vec2 center = vec2(0.5, 0.5);
                vec2 dir = uv - center;
                
                // Tunnel effect
                float dist = length(dir);
                float angle = atan(dir.y, dir.x);
                
                // Apply rotation
                angle += time * rotation * 0.1;
                
                // Apply tunnel speed
                float tunnel = dist * tunnel_speed;
                
                // Apply fractal depth
                float fractal = 0.0;
                float scale = 1.0;
                for(int i = 0; i < 5; i++) {
                    fractal += sin(tunnel * scale + time * 2.0) * 0.5 / scale;
                    scale *= fractal_depth;
                }
                
                // Apply recursion
                float recursive = 0.0;
                float recursion_scale = 1.0;
                for(int i = 0; i < int(recursion); i++) {
                    recursive += sin(tunnel * recursion_scale + time * 3.0) * 0.5 / recursion_scale;
                    recursion_scale *= 2.0;
                }
                
                // Apply center pull
                float pull = 1.0 - smoothstep(0.0, center_pull, dist);
                
                // Apply wall warp
                float warp = sin(angle * wall_warp + time * 2.0) * 0.1;
                
                // Apply grid lines
                float grid = sin(uv.x * grid_lines * 10.0) * sin(uv.y * grid_lines * 10.0);
                
                // Apply aberration
                vec3 rgb = vec3(0.0);
                rgb.r += aberration * sin(time * 2.0);
                rgb.g += aberration * sin(time * 2.0 + 2.0);
                rgb.b += aberration * sin(time * 2.0 + 4.0);
                
                // Apply color shift
                float color_offset = sin(time * color_shift) * 0.5 + 0.5;
                
                // Apply neural intensity
                float neural = neural_intensity * 0.1;
                
                // Apply quantum feedback
                float quantum = sin(time * quantum_feedback * 0.5) * 0.5 + 0.5;
                
                // Apply hyper warp
                float hyper = hyper_warp * 0.1;
                
                // Apply dimensional shift
                float dimensional = dimensional_shift * 0.1;
                
                // Apply synesthetic mapping
                float synesthetic = synesthetic_mapping * 0.1;
                
                // Apply collective consciousness
                float collective = collective_consciousness * 0.1;
                
                // Final color
                vec3 color = vec3(
                    fractal + recursive + pull + warp + grid + neural + quantum + hyper + dimensional + synesthetic + collective,
                    fractal + recursive + pull + warp + grid + neural + quantum + hyper + dimensional + synesthetic + collective,
                    fractal + recursive + pull + warp + grid + neural + quantum + hyper + dimensional + synesthetic + collective
                );
                
                // Apply eternity (time dilation)
                color *= eternity * 0.1;
                
                // Apply mosh stretch
                color *= mosh_stretch * 0.1;
                
                // Apply depth of field
                color *= depth_fov * 0.1;
                
                // Apply final color shift
                color = mix(color, vec3(1.0), color_offset);
                
                fragColor = vec4(color, 1.0);
            }
        """
    
    def render(self, tex_in: int, extra_textures: list = None, chain=None) -> int:
        """
        Render the neural tunnel effect.
        
        Args:
            tex_in: Input texture handle (typically the current frame)
            extra_textures: Additional textures (unused)
            chain: Optional rendering chain context
            
        Returns:
            Output texture handle
        """
        # Update audio-reactive uniforms
        self._apply_audio_uniforms()
        
        # Update quantum phase
        self.quantum_phase += 0.01 * self.parameters['quantum_feedback']
        
        # Call parent render method
        return super().render(tex_in, extra_textures, chain)
    
    def _apply_audio_uniforms(self):
        """Query audio reactor and update shader uniforms."""
        if not self._audio_reactor.is_initialized():
            # Use default values if audio not available
            self.shader.set_uniform("synesthetic_mapping", 0.5)
            return
            
        # Get audio features
        bass = self._audio_reactor.get_feature_level(AudioFeature.BASS)
        mid = self._audio_reactor.get_feature_level(AudioFeature.MID)
        high = self._audio_reactor.get_feature_level(AudioFeature.HIGH)
        
        # Apply synesthetic mapping
        synesthetic = (bass + mid + high) / 3.0
        self.shader.set_uniform("synesthetic_mapping", synesthetic)
        
        # Apply collective consciousness
        collective = bass * 0.8 + mid * 0.2
        self.shader.set_uniform("collective_consciousness", collective)
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `tex_in` | `int` (texture handle) | Input video frame | Must be valid OpenGL texture |
| `extra_textures` | `list[int]` | Additional textures (unused) | Optional |
| `chain` | `object` | Rendering chain context | Optional, may be None |

**Output:** A single texture handle containing the processed tunnel visuals.

---

## Edge Cases and Error Handling

### Audio System Unavailable
- **No audio input:** If `AudioReactor` is not initialized, use default values (0.5) for audio-driven uniforms
- **Audio feature query fails:** Log warning and fall back to defaults; do not crash
- **Audio latency:** Handle gracefully; use most recent available feature values

### Neural Network
- **PyTorch not available:** If PyTorch is not installed, use a fallback shader without neural processing
- **Model loading failure:** Log warning and use default parameters
- **Memory allocation failure:** Handle gracefully with fallback to simpler effect

### Shader Compilation
- **Dynamic shader generation failure:** If `_generate_tunnel_shader()` returns invalid GLSL, raise `RuntimeError` with shader source for debugging
- **Uniform location not found:** Cache uniform locations; if missing, log warning but continue (uniforms may be optimized out)
- **Shader compilation errors:** Capture OpenGL shader log and include in exception message

### Performance
- **High neural network load:** Neural network runs on CPU; ensure it doesn't block rendering thread
- **Shader complexity:** Moderate; use simple math operations to maintain performance
- **Memory leaks:** Ensure all OpenGL resources (textures, shaders) are properly cleaned up on effect destruction

### Silent Failure Prevention
- All audio feature queries must have fallback values
- Shader compilation errors must be raised with full log
- Never return texture handle 0 without raising exception first
- Log all neural network initialization failures at WARNING level

---

## Mathematical Formulations

### Tunnel Geometry

The tunnel effect uses polar coordinates:
```glsl
vec2 dir = uv - center;
float dist = length(dir);
float angle = atan(dir.y, dir.x);
```

### Fractal Patterns

Fractal patterns are generated using recursive sine waves:
```glsl
float fractal = 0.0;
float scale = 1.0;
for(int i = 0; i < 5; i++) {
    fractal += sin(tunnel * scale + time * 2.0) * 0.5 / scale;
    scale *= fractal_depth;
}
```

### Quantum Feedback

Quantum feedback creates phase-based recursive patterns:
```glsl
float quantum = sin(time * quantum_feedback * 0.5) * 0.5 + 0.5;
```

### Synesthetic Mapping

Audio features are mapped to visual parameters:
```python
synesthetic = (bass + mid + high) / 3.0
```

---

## Performance Characteristics

### Expected Performance
- **1080p (1920×1080):** Target ≥60 FPS on mid-range GPU
- **Shader complexity:** Moderate (many arithmetic operations, no texture lookups)
- **CPU overhead:** Low (neural network runs on CPU, but is lightweight)
- **Memory footprint:** Small (single shader program, few uniform variables)

### Bottlenecks
- **Neural network inference:** Runs on CPU; ensure it doesn't block rendering thread
- **Shader complexity:** Moderate; use simple math operations to maintain performance
- **Uniform updates:** 18 uniform calls per frame; negligible overhead

### Optimization Opportunities
- **Neural network caching:** Cache neural network output if input frame doesn't change
- **Shader optimization:** Use simpler math operations where possible
- **LOD:** Reduce shader complexity at very high resolutions if needed

---

## Test Plan

| Test Name | What It Verifies | Expected Outcome |
|-----------|------------------|------------------|
| `test_init` | Constructor initializes correctly | Effect created without errors |
| `test_shader_generation` | `_generate_tunnel_shader()` returns valid GLSL | Shader string contains required uniforms and main() |
| `test_audio_reactor_integration` | AudioReactor is used correctly | `_apply_audio_uniforms()` queries features and sets uniforms |
| `test_audio_unavailable_fallback` | Fallback values used when audio unavailable | Defaults (0.5) applied without errors |
| `test_audio_feature_ranges` | Audio features in [0,1] range | Uniforms set to values within expected range |
| `test_render_without_audio` | Render works with no audio | Output texture valid, no crashes |
| `test_performance_60fps` | Meets 60 FPS target | ≥60 FPS sustained over 1000 frames at 1080p |
| `test_shader_compilation` | Shader compiles successfully | No OpenGL errors during compilation |
| `test_uniform_locations` | Uniform locations cached correctly | All uniforms found or handled gracefully |
| `test_parameter_set_get` | Set/get methods work | Parameters can be modified and retrieved |
| `test_memory_cleanup` | No GPU memory leaks | All resources freed on destruction |
| `test_coverage_80` | Achieves ≥80% test coverage | Coverage report meets threshold |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-EXT116: NeuralTunnelNet` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES

### VJlive (Original)
File: `plugins/vdepth/tunnel_vision_2.py` (L33-52)
```python
        self.warp_phase = 0.0
        
        # Core parameters
        self.parameters = {
            'tunnel_speed': 8.0, 'rotation': 6.0, 'fractal_depth': 8.0,
            'recursion': 8.0, 'center_pull': 6.0, 'wall_warp': 7.0,
            'color_shift': 8.0, 'depth_fov': 8.0, 'mosh_stretch': 8.0,
            'grid_lines': 6.0, 'aberration': 7.0, 'eternity': 9.0,
            'neural_intensity': 9.0, 'quantum_feedback': 8.0,
            'hyper_warp': 9.0, 'dimensional_shift': 8.0,
            'synesthetic_mapping': 9.0, 'collective_consciousness': 8.0
        }
    
    def _initialize_neural_network(self):
        """Initialize the neural network for visual processing"""
        class NeuralTunnelNet(nn.Module):
            def __init__(self):
                super().__init__()
                self.conv1 = nn.Conv2d(3, 16, 3, padding=1)
                self.conv2 = nn.Conv2d(16, 32, 3, padding=1)
```

File: `plugins/vdepth/tunnel_vision_2.py` (L65-84)
```python
                x = torch.relu(self.fc2(x))
                x = torch.tanh(self.fc3(x))
                return x
        
        self.neural_model = NeuralTunnelNet()
        self.neural_model.eval()
    
    def set_parameter(self, name: str, value: float):
        """Set parameter with bounds checking"""
        self.parameters[name] = max(0.0, min(10.0, float(value)))
    
    def _quantum_feedback(self, time_val: float):
        """Apply quantum feedback to the tunnel"""
        # Update quantum state
        self.quantum_phase += time_val * 0.01 * self.parameters['quantum_feedback'] / 10.0
        
        # Apply quantum superposition
        quantum_matrix = np.array([
            [np.cos(self.quantum_phase), -np.sin(self.quantum_phase), 0, 0],
            [np.sin(self.quantum_phase), np.cos(self.quantum_phase), 0, 0],
```

### Documentation
File: `plugins/vdepth/TUNNEL_VISION_2_DOCUMENTATION.md`
```python
class NeuralTunnelNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(3, 16, 3, padding=1)  # Input: RGB frame
        self.conv2 = nn.Conv2d(16, 32, 3, padding=1) # Hidden layer 1
        self.conv3 = nn.Conv2d(32, 64, 3, padding=1) # Hidden layer 2
        self.pool = nn.MaxPool2d(2, 2)               # Pooling layer
        self.fc1 = nn.Linear(64 * 16 * 16, 128)      # Fully connected 1
        self.fc2 = nn.Linear(128, 64)                # Fully connected 2
        self.fc3 = nn.Linear(64, 3)                  # Output: RGB transformation
```

---

## Dependencies

### External Libraries
- `PyOpenGL` — OpenGL shader and texture operations
- `numpy` — Array operations (for quantum feedback matrix)
- `torch` — Neural network processing (PyTorch)

### Internal Modules
- `src/vjlive3/plugins/base.py` — `Effect` base class
- `src/vjlive3/audio/reactivity.py` — `AudioReactor` for audio feature extraction
- `src/vjlive3/audio/analyzer.py` — `AudioFeature` enum
- `src/vjlive3/render/shaders.py` — Shader compilation utilities

### Plugin Manifest
The NeuralTunnelNet must be registered in the VJLive3 plugin manifest:

```python
PLUGIN_REGISTRY = {
    'neural_tunnel_net': NeuralTunnelNet,
    # ... other plugins
}
```

---

## Notes for Implementation

1. **Neural Network:** The PyTorch model is lightweight and runs on CPU. Ensure it doesn't block the rendering thread.
2. **Parameter Scaling:** Legacy code uses 0-10 range for parameters; maintain this for consistency.
3. **Quantum Feedback:** The quantum phase is updated in `_apply_audio_uniforms()`; ensure thread safety.
4. **Shader Design:** The shader should be visually striking but computationally efficient. Use simple math operations and avoid expensive texture lookups.
5. **Documentation:** Include docstrings with type hints for all public methods.

---

## References

- **Plugin System Spec:** `docs/specs/P1-P1_plugin_registry.md`
- **Base Classes:** `src/vjlive3/plugins/base.py`
- **Audio Reactivity:** `src/vjlive3/audio/reactivity.py`
- **Original Source:** `plugins/vdepth/tunnel_vision_2.py` (VJlive)
- **Documentation:** `plugins/vdepth/TUNNEL_VISION_2_DOCUMENTATION.md`

---

**END OF SPECIFICATION**