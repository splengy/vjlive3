# P3-EXT119: OscilloscopeEffect — Classic Oscilloscope Waveform Visualization

> **Task ID:** `P3-EXT119`  
> **Priority:** P3 (Standard)  
> **Source:** VJlive (Original)  
> **Class:** `OscilloscopeEffect`  
> **Phase:** Phase 3  
> **Status:** ⬜ Todo  

---

## Mission Context

Port the `OscilloscopeEffect` from the VJlive codebase into VJLive3's modern plugin architecture. This effect creates a classic oscilloscope waveform visualization that displays audio in the time domain, providing real-time visual feedback of audio amplitude and frequency characteristics.

The OscilloscopeEffect is a foundational visualization component that converts audio waveforms into graphical representations, enabling VJs to display and manipulate audio signals visually during live performances.

---

## Technical Requirements

- Implement as a VJLive3 plugin following the manifest-based registry system
- Inherit from `Effect` base class in `src/vjlive3/plugins/base.py`
- Support real-time audio waveform visualization with minimal latency
- Ensure 60 FPS performance at 1080p (Safety Rail 1)
- Achieve ≥80% test coverage (Safety Rail 5)
- File size ≤750 lines (Safety Rail 4)
- No silent failures, proper error handling (Safety Rail 7)
- Support OpenGL shader-based rendering with configurable waveform parameters

---

## Implementation Notes

### Original Location
- **VJlive (Original):** `core/effects/legacy_trash/visualizer.py` and `core/effects/oscilloscope.py`
- **Legacy Codebase:** Also referenced in `core/effects/__init__.py` (visualizer registry)

### Description
The OscilloscopeEffect converts audio signals into waveform visualizations. It samples audio amplitude over time and renders it as a 2D waveform on screen. The effect supports multiple visualization modes (line, bar, fill) and offers parameters for customization including color, thickness, and display mode.

Key features include:
- Real-time waveform display with low latency
- Multiple display modes (line, bar, fill)
- Color customization with per-channel control
- Peak hold functionality for amplitude visualization
- Integration with VJLive3's audio reactor system

### Porting Strategy
1. Extract the waveform generation logic from legacy visualizer code
2. Map legacy parameters to VJLive3's parameter system (0.0-10.0 range)
3. Create proper class inheriting from `Effect` with appropriate metadata
4. Implement parameter validation and clamping
5. Register the plugin in the VJLive3 plugin manifest
6. Write comprehensive tests covering waveform rendering, parameter handling, and edge cases
7. Verify against original behavior with test audio vectors

---

## Detailed Behavior and Parameter Interactions

### Core Functionality
The OscilloscopeEffect:
1. Samples audio amplitude using `AudioReactor`
2. Generates waveform points based on amplitude over time
3. Renders the waveform using OpenGL shaders
4. Supports multiple display modes and visual styles

### Parameter System
All parameters use VJLive3's standard 0.0-10.0 range:
- **wave_color:** RGB color values (0-10 per channel) mapped to 0-1 internally
- **thickness:** Waveform line thickness (0-10 range)
- **mode:** Display mode (0=line, 1=bar, 2=fill)
- **peak_hold:** Peak amplitude hold time (0-10)
- **release:** Release time for decay effect (0-10)
- **style:** Visual style variant (0-10)
- **left_level/right_level:** Stereo channel levels
- **left_peak/right_peak:** Peak amplitude per channel

### Waveform Generation
The effect uses a circular buffer to store recent audio samples:
```python
# Pseudocode for waveform generation
buffer_index = (buffer_index + 1) % buffer_size
buffer[buffer_index] = current_sample * scale_factor
```

The waveform is then rendered as a series of connected line segments.

### Audio Reactivity
The effect queries audio features through `AudioReactor`:
```python
left_peak = self._audio_reactor.get_feature_level(AudioFeature.LEFT_PEAK)
right_peak = self._audio_reactor.get_feature_level(AudioFeature.RIGHT_PEAK)
```

These values drive parameters like peak hold, release time, and color intensity.

---

## Public Interface

```python
from vjlive3.plugins.base import Effect
from vjlive3.audio.reactivity import AudioReactor
from vjlive3.audio.analyzer import AudioFeature

class OscilloscopeEffect(Effect):
    """
    Classic oscilloscope waveform visualization.
    
    Converts audio signals into real-time waveform visualizations
    with configurable display modes and styling options.
    """
    
    def __init__(self):
        """Initialize the OscilloscopeEffect."""
        fragment_shader = self._generate_oscilloscope_shader()
        vertex_shader = self._get_default_vertex_shader()
        super().__init__("oscilloscope", fragment_shader, vertex_shader)
        
        # Effect metadata
        self.effect_category = "visualizer"
        self.effect_tags = ["oscilloscope", "visualizer", "audio_reactive"]
        self.features = ["TIME_DOMAIN_VISUALIZATION", "AUDIO_REACTIVE"]
        
        # Parameter ranges (0.0-10.0)
        self._parameter_ranges = {
            'wave_color_r': (0.0, 10.0),
            'wave_color_g': (0.0, 10.0),
            'wave_color_b': (0.0, 10.0),
            'thickness': (0.0, 10.0),
            'mode': (0.0, 2.0),  # 0=line, 1=bar, 2=fill
            'peak_hold': (0.0, 10.0),
            'release': (0.0, 10.0),
            'style': (0.0, 10.0),
            'left_level': (0.0, 10.0),
            'right_level': (0.0, 10.0),
            'left_peak': (0.0, 10.0),
            'right_peak': (0.0, 10.0)
        }
        
        # Default parameter values
        self.parameters = {
            'wave_color_r': 0.0,
            'wave_color_g': 10.0,
            'wave_color_b': 0.0,
            'thickness': 1.6,
            'mode': 0.0,
            'peak_hold': 2.0,
            'release': 1.0,
            'style': 0.0,
            'left_level': 1.0,
            'right_level': 1.0,
            'left_peak': 1.0,
            'right_peak': 1.0
        }
        
        # Parameter descriptions
        self._parameter_descriptions = {
            'wave_color_r': "Red channel intensity (0-10)",
            'wave_color_g': "Green channel intensity (0-10)",
            'wave_color_b': "Blue channel intensity (0-10)",
            'thickness': "Waveform line thickness (0-10)",
            'mode': "Display mode (0=line, 1=bar, 2=fill)",
            'peak_hold': "Peak amplitude hold time (0-10)",
            'release': "Release time for decay effect (0-10)",
            'style': "Visual style variant (0-10)",
            'left_level': "Left audio channel level (0-10)",
            'right_level': "Right audio channel level (0-10)",
            'left_peak': "Left channel peak amplitude (0-10)",
            'right_peak': "Right channel peak amplitude (0-10)"
        }
        
        # Initialize audio reactor
        self._audio_reactor = AudioReactor()
        
        # Initialize waveform buffer
        self._initialize_waveform_buffer()
    
    def _initialize_waveform_buffer(self):
        """Initialize the waveform sampling buffer."""
        # Implementation details follow
    
    def _generate_oscilloscope_shader(self) -> str:
        """
        Generate the GLSL fragment shader source.
        
        Returns:
            Complete fragment shader source code as string
        """
        return """
            // Oscilloscope shader implementation
            uniform sampler2D u_waveform_texture;
            uniform float u_thickness;
            uniform vec3 u_wave_color;
            uniform float u_peak_hold;
            uniform float u_release;
            uniform float u_mode;
            uniform float u_left_level;
            uniform float u_right_level;
            uniform float u_left_peak;
            uniform float u_right_peak;
            uniform float u_style;
            uniform float u_time;
            
            void main() {
                // Oscilloscope rendering implementation
                // Sample waveform texture and apply visual parameters
                // Handle different modes (line, bar, fill)
                // Apply color tinting and thickness
                // Implement peak hold and release effects
                // Apply style variations
            }
        """
    
    def render(self, tex_in: int, extra_textures: list = None, chain=None) -> int:
        """
        Render the oscilloscope waveform.
        
        Args:
            tex_in: Input texture handle (typically the current frame)
            extra_textures: Additional textures (unused)
            chain: Optional rendering chain context
            
        Returns:
            Output texture handle
        """
        # Update audio parameters
        self._update_audio_parameters()
        
        # Update waveform buffer
        self._update_waveform_buffer()
        
        # Call parent render method
        return super().render(tex_in, extra_textures, chain)
    
    def _update_audio_parameters(self):
        """Query audio reactor and update shader uniforms."""
        if not self._audio_reactor.is_initialized():
            # Use default values if audio not available
            self.shader.set_uniform("left_peak", 1.0)
            self.shader.set_uniform("right_peak", 1.0)
            return
            
        # Get audio peak levels
        left_peak = self._audio_reactor.get_feature_level(AudioFeature.LEFT_PEAK)
        right_peak = self._audio_reactor.get_feature_level(AudioFeature.RIGHT_PEAK)
        
        # Apply to parameters
        self.shader.set_uniform("left_peak", left_peak)
        self.shader.set_uniform("right_peak", right_peak)
        
        # Update level parameters
        self.shader.set_uniform("left_level", self.parameters['left_level'])
        self.shader.set_uniform("right_level", self.parameters['right_level'])
    
    def _update_waveform_buffer(self):
        """Update the waveform sampling buffer with new audio data."""
        # Implementation details follow
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `tex_in` | `int` (texture handle) | Input video frame | Must be valid OpenGL texture |
| `extra_textures` | `list[int]` | Additional textures (unused) | Optional |
| `chain` | `object` | Rendering chain context | Optional, may be None |

**Output:** A single texture handle containing the processed waveform visualization.

---

## Edge Cases and Error Handling

### Audio System Unavailable
- **No audio input:** If `AudioReactor` is not initialized, use default values (1.0) for peak parameters
- **Audio feature query fails:** Log warning and fall back to defaults; do not crash
- **Audio latency:** Handle gracefully; use most recent available feature values

### Waveform Buffer
- **Buffer overflow:** Implement circular buffer with fixed size; handle overflow gracefully
- **Buffer underflow:** Handle empty buffer state with fallback waveform
- **Memory allocation failure:** Handle gracefully with fallback to simpler rendering

### Shader Compilation
- **Dynamic shader generation failure:** If `_generate_oscilloscope_shader()` returns invalid GLSL, raise `RuntimeError` with shader source for debugging
- **Uniform location not found:** Cache uniform locations; if missing, log warning but continue (uniforms may be optimized out)
- **Shader compilation errors:** Capture OpenGL shader log and include in exception message

### Silent Failure Prevention
- All audio feature queries must have fallback values
- Shader compilation errors must be raised with full log
- Never return texture handle 0 without raising exception first
- Log all initialization failures at WARNING level

---

## Mathematical Formulations

### Waveform Sampling

The effect uses a circular buffer to store audio samples:
```python
# Pseudocode for waveform buffer update
buffer_index = (buffer_index + 1) % buffer_size
buffer[buffer_index] = current_sample * scale_factor
```

### Peak Detection

Peak hold and release effects are implemented using exponential decay:
```glsl
// Peak hold effect
float peak = max(peak, abs(sample));
float decay = exp(-release * delta_time);
peak *= decay;
```

### Color Mapping

Waveform color is mapped from parameters:
```glsl
vec3 color = vec3(u_wave_color / 10.0);  // Convert 0-10 to 0-1
```

### Display Modes

Different rendering modes:
- **Line mode (0):** Simple line drawing
- **Bar mode (1):** Vertical bars representing amplitude
- **Fill mode (2):** Filled areas between waveform points

---

## Performance Characteristics

### Expected Performance
- **1080p (1920×1080):** Target ≥60 FPS on mid-range GPU
- **Shader complexity:** Low (simple texture sampling and line drawing)
- **CPU overhead:** Minimal (buffer updates are lightweight)
- **Memory footprint:** Small (fixed-size waveform buffer)

### Bottlenecks
- **Texture sampling:** Primary operation; ensure efficient sampling
- **Buffer updates:** Must be completed within frame budget
- **Shader compilation:** One-time cost at initialization

### Optimization Opportunities
- **Buffer size tuning:** Adjust waveform buffer size based on performance needs
- **Shader optimization:** Use simpler line drawing algorithms
- **Level of detail:** Reduce waveform resolution at high frame rates

---

## Test Plan

| Test Name | What It Verifies | Expected Outcome |
|-----------|------------------|------------------|
| `test_init` | Constructor initializes correctly | Effect created without errors |
| `test_shader_generation` | `_generate_oscilloscope_shader()` returns valid GLSL | Shader string contains required uniforms and main() |
| `test_audio_reactor_integration` | AudioReactor is used correctly | `_update_audio_parameters()` queries features and sets uniforms |
| `test_audio_unavailable_fallback` | Fallback values used when audio unavailable | Defaults applied without errors |
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
- [ ] Git commit with `[Phase-3] P3-EXT119: OscilloscopeEffect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES

### VJlive (Original)
File: `core/effects/legacy_trash/visualizer.py` (L305-324)
```glsl
// Oscilloscope fragment shader
precision mediump float;
uniform sampler2D u_waveform;
uniform float u_thickness;
uniform vec3 u_color;
varying vec2 v_texCoord;
void main() {
    vec4 color = vec4(u_color, 1.0);
    gl_FragColor = color;
}
```

File: `core/effects/oscilloscope.py` (L1-20)
```python
class OscilloscopeEffect(Effect):
    """Time-domain waveform visualization.
    
    All parameters use 0-10 range from UI sliders.
    Shader remaps internally to the values the math needs.
    """
```

### Visualizer Registry
File: `core/effects/__init__.py` (L177-196)
```python
'visualizer': {
    'spectrum_analyzer': ('.visualizer', 'SpectrumAnalyzerEffect'),
    'oscilloscope': ('.visualizer', 'OscilloscopeEffect'),
    'vu_meter': ('.visualizer', 'VUMeterEffect'),
},
```

### Documentation
File: `core/effects/legacy_trash/visualizer.py` (L705-724)
```python
class OscilloscopeEffect(VisualizerEffect):
    """Classic oscilloscope waveform display.
    All parameters use 0-10 range.
    """
    
    def __init__(self):
        super().__init__("oscilloscope", OSCILLOSCOPE_FRAGMENT, OSCILLOSCOPE_VERTEX)
        
        # All parameters in 0-10 range
        self.wave_color = (0.0, 10.0, 0.0)  # Green (0-10 per channel -> 0-1)
        self.thickness = 1.6      # 0-10 -> 0.5-10 (default ~2.0)
```

---

## Dependencies

### External Libraries
- `PyOpenGL` — OpenGL shader and texture operations
- `numpy` — Array operations (if needed for buffer management)

### Internal Modules
- `src/vjlive3/plugins/base.py` — `Effect` base class
- `src/vjlive3/audio/reactivity.py` — `AudioReactor` for audio feature extraction
- `src/vjlive3/audio/analyzer.py` — `AudioFeature` enum
- `src/vjlive3/render/shaders.py` — Shader compilation utilities

### Plugin Manifest
The OscilloscopeEffect must be registered in the VJLive3 plugin manifest:

```python
PLUGIN_REGISTRY = {
    'oscilloscope': OscilloscopeEffect,
    # ... other plugins
}
```

---

## Notes for Implementation

1. **Audio Reactivity:** The effect relies on `AudioReactor` being initialized with an audio source. Ensure proper error handling when audio is not available.
2. **Shader Design:** The shader should be efficient but visually appealing. Use simple line drawing algorithms to maintain performance.
3. **Parameter Scaling:** Legacy code uses 0-10 range for parameters; maintain this for consistency with other VJLive3 effects.
4. **Buffer Management:** Implement circular buffer with appropriate size (e.g., 1024 samples) to balance memory usage and visual quality.
5. **Thread Safety:** Audio feature queries may come from a separate thread; ensure uniform updates are thread-safe.
6. **Documentation:** Include docstrings with type hints for all public methods.

---

## References

- **Plugin System Spec:** `docs/specs/P1-P1_plugin_registry.md`
- **Base Classes:** `src/vjlive3/plugins/base.py`
- **Audio Reactivity:** `src/vjlive3/audio/reactivity.py`
- **Original Source:** `core/effects/legacy_trash/visualizer.py` (VJlive)
- **Visualizer Registry:** `core/effects/__init__.py` (VJlive)

---

**END OF SPECIFICATION**