# P3-EXT114: NeuralRaveNexus — Underground Rave Consciousness Amplifier

> **Task ID:** `P3-EXT114`  
> **Priority:** P3 (Standard)  
> **Source:** VJlive (Original)  
> **Class:** `NeuralRaveNexus`  
> **Phase:** Phase 3  
> **Status:** ⬜ Todo  

---

## Mission Context

Port the `NeuralRaveNexus` effect from the VJlive codebase into VJLive3's modern plugin architecture. This effect is an "underground rave consciousness amplifier" that creates immersive, audio-reactive visual experiences inspired by rave culture and neural network processing.

The NeuralRaveNexus combines audio analysis with generative shader techniques to produce dynamic, rhythm-synced visual patterns that respond to bass, mid-range, and high-frequency audio features.

---

## Technical Requirements

- Implement as a VJLive3 plugin following the manifest-based registry system
- Inherit from `Effect` base class in `src/vjlive3/plugins/base.py`
- Integrate with VJLive3's audio reactor system for real-time audio analysis
- Ensure 60 FPS performance at 1080p (Safety Rail 1)
- Achieve ≥80% test coverage (Safety Rail 5)
- File size ≤750 lines (Safety Rail 4)
- No silent failures, proper error handling (Safety Rail 7)
- Support OpenGL shader-based rendering with dynamic shader generation

---

## Implementation Notes

### Original Location
- **VJlive (Original):** `plugins/vdepth/neural_rave_nexus.py`
- **Legacy Codebase:** Also referenced in `plugins/vdepth/tunnel_vision_3.py` as a component

### Description
The NeuralRaveNexus is an audio-reactive visual effect that generates rave-inspired patterns. It uses the `AudioReactor` to analyze audio features (bass, mid, high) and maps them to shader uniforms that control visual parameters like light streaks, heat, and color modulation.

The effect dynamically generates its fragment shader during initialization, creating a unique visual experience that responds to music in real-time.

### Porting Strategy
1. Extract the shader generation logic (`_generate_rave_shader()` method)
2. Map audio feature inputs to shader uniforms using VJLive3's audio reactor system
3. Create proper class inheriting from `Effect` with appropriate metadata
4. Implement parameter validation for audio feature levels
5. Register the plugin in the VJLive3 plugin manifest
6. Write comprehensive tests covering audio reactivity, rendering, and edge cases
7. Verify against original behavior with test audio vectors

---

## Detailed Behavior and Parameter Interactions

### Core Functionality
The NeuralRaveNexus effect:
1. Analyzes audio input using `AudioReactor` to extract features:
   - Bass levels (low frequencies)
   - Mid-range levels
   - High-frequency content
2. Maps these features to shader uniforms:
   - `lightStreaks` — controlled by bass modulation
   - `midRangeHeat` — controlled by mid-range audio
   - Additional parameters for high-frequency response
3. Renders a procedurally generated shader that creates rave-style visuals

### Audio Reactivity
The effect uses the `AudioReactor` singleton to query audio feature levels:
```python
bass_level = self.audio_reactor.get_feature_level(AudioFeature.BASS)
mid_level = self.audio_reactor.get_feature_level(AudioFeature.MID)
high_level = self.audio_reactor.get_feature_level(AudioFeature.HIGH)
```

These levels (typically 0.0 to 1.0) are then scaled and passed to the shader as uniform values.

### Shader Generation
The `_generate_rave_shader()` method constructs a GLSL fragment shader string dynamically. This allows for:
- Customizable visual parameters
- Audio-reactive uniform variables
- Procedural pattern generation using noise functions and time-based animations

---

## Public Interface

```python
from vjlive3.plugins.base import Effect
from vjlive3.audio.reactivity import AudioReactor
from vjlive3.audio.analyzer import AudioFeature

class NeuralRaveNexus(Effect):
    """
    Underground rave consciousness amplifier.
    
    Generates immersive, audio-reactive rave visuals that respond to
    bass, mid-range, and high-frequency audio features in real-time.
    """
    
    def __init__(self):
        """Initialize the NeuralRaveNexus effect."""
        fragment_shader = self._generate_rave_shader()
        super().__init__("Neural Rave Nexus", fragment_shader)
        
        # Effect metadata
        self.effect_category = "generative"
        self.effect_tags = ["rave", "audio_reactive", "neural", "generative"]
        self.features = ["AUDIO_REACTIVE", "PROCEDURAL"]
        
        # Audio reactivity parameters
        self._audio_reactor = AudioReactor()
        
    def _generate_rave_shader(self) -> str:
        """
        Generate the GLSL fragment shader source.
        
        Returns:
            Complete fragment shader source code as string
        """
        # Returns a shader with uniforms for audio reactivity
        return """
            uniform float lightStreaks;
            uniform float midRangeHeat;
            uniform float highSparkle;
            uniform float time;
            
            void main() {
                // Shader implementation with audio-reactive parameters
                vec2 uv = gl_FragCoord.xy / resolution.xy;
                
                // Create rave pattern based on audio features
                vec3 color = vec3(0.0);
                
                // Bass-driven light streaks
                color += vec3(lightStreaks * 0.5, lightStreaks * 0.2, lightStreaks);
                
                // Mid-range heat
                color += vec3(midRangeHeat, midRangeHeat * 0.5, 0.0);
                
                // High-frequency sparkle
                color += highSparkle * vec3(1.0, 0.8, 0.2);
                
                // Add time-based animation
                float wave = sin(uv.x * 10.0 + time) * 0.5 + 0.5;
                color *= wave;
                
                fragColor = vec4(color, 1.0);
            }
        """
    
    def render(self, tex_in: int, extra_textures: list = None, chain=None) -> int:
        """
        Render the audio-reactive rave effect.
        
        Args:
            tex_in: Input texture handle (typically the current frame)
            extra_textures: Additional textures (not used by this effect)
            chain: Optional rendering chain context
            
        Returns:
            Output texture handle
        """
        # Update audio-reactive uniforms
        self._apply_audio_uniforms()
        
        # Call parent render method
        return super().render(tex_in, extra_textures, chain)
    
    def _apply_audio_uniforms(self):
        """Query audio reactor and update shader uniforms."""
        if not self._audio_reactor.is_initialized():
            # Use default values if audio not available
            self.shader.set_uniform("lightStreaks", 0.5)
            self.shader.set_uniform("midRangeHeat", 0.5)
            self.shader.set_uniform("highSparkle", 0.5)
            return
            
        bass = self._audio_reactor.get_feature_level(AudioFeature.BASS)
        mid = self._audio_reactor.get_feature_level(AudioFeature.MID)
        high = self._audio_reactor.get_feature_level(AudioFeature.HIGH)
        
        # Scale and apply
        self.shader.set_uniform("lightStreaks", bass)
        self.shader.set_uniform("midRangeHeat", mid)
        self.shader.set_uniform("highSparkle", high)
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `tex_in` | `int` (texture handle) | Input video frame | Must be valid OpenGL texture |
| `extra_textures` | `list[int]` | Additional textures (unused) | Optional |
| `chain` | `object` | Rendering chain context | Optional, may be None |

**Output:** A single texture handle containing the processed rave visuals.

---

## Edge Cases and Error Handling

### Audio System Unavailable
- **No audio input:** If `AudioReactor` is not initialized, use default values (0.5) for all audio-driven uniforms
- **Audio feature query fails:** Log warning and fall back to defaults; do not crash
- **Audio latency:** Handle gracefully; use most recent available feature values

### Shader Compilation
- **Dynamic shader generation failure:** If `_generate_rave_shader()` returns invalid GLSL, raise `RuntimeError` with shader source for debugging
- **Uniform location not found:** Cache uniform locations; if missing, log warning but continue (uniforms may be optimized out)
- **Shader compilation errors:** Capture OpenGL shader log and include in exception message

### Performance
- **High audio reactivity load:** Audio analysis runs in separate thread; ensure thread-safe uniform updates
- **Shader recompilation:** Shader is generated once at init; no runtime recompilation
- **Memory leaks:** Ensure all OpenGL resources (textures, shaders) are properly cleaned up on effect destruction

### Silent Failure Prevention
- All audio feature queries must have fallback values
- Shader compilation errors must be raised with full log
- Never return texture handle 0 without raising exception first
- Log all audio reactor initialization failures at WARNING level

---

## Mathematical Formulations

### Audio Feature Scaling

Audio features from `AudioReactor` are typically in range [0.0, 1.0] and are passed directly to shader uniforms:

```python
bass_scaled = bass  # [0.0, 1.0]
mid_scaled = mid    # [0.0, 1.0]
high_scaled = high  # [0.0, 1.0]
```

### Visual Pattern Generation (Shader)

The fragment shader uses time-based sinusoidal patterns mixed with audio-reactive colors:

```glsl
vec2 uv = gl_FragCoord.xy / resolution.xy;
float wave = sin(uv.x * 10.0 + time) * 0.5 + 0.5;
vec3 color = vec3(
    lightStreaks * 0.5 + highSparkle,  // Red channel
    lightStreaks * 0.2 + midRangeHeat * 0.5,  // Green channel
    lightStreaks + midRangeHeat  // Blue channel
);
fragColor = vec4(color * wave, 1.0);
```

---

## Performance Characteristics

### Expected Performance
- **1080p (1920×1080):** Target ≥60 FPS on mid-range GPU
- **Shader complexity:** Low to moderate (few arithmetic operations, no texture lookups beyond input)
- **CPU overhead:** Minimal (audio feature queries and uniform updates)
- **Memory footprint:** Small (single shader program, few uniform variables)

### Bottlenecks
- **Audio analysis:** Runs in separate thread; should not block rendering
- **Shader compilation:** One-time cost at initialization; keep shader simple to avoid long compile times
- **Uniform updates:** 3 uniform calls per frame; negligible overhead

### Optimization Opportunities
- **Shader caching:** If shader generation is deterministic, cache the compiled program
- **Audio smoothing:** Apply temporal smoothing to audio features to avoid jittery visuals
- **LOD:** Reduce shader complexity at very high resolutions if needed

---

## Test Plan

| Test Name | What It Verifies | Expected Outcome |
|-----------|------------------|------------------|
| `test_init` | Constructor initializes correctly | Effect created without errors |
| `test_shader_generation` | `_generate_rave_shader()` returns valid GLSL | Shader string contains required uniforms and main() |
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
- [ ] Git commit with `[Phase-3] P3-EXT114: NeuralRaveNexus` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES

### VJlive (Original)
File: `plugins/vdepth/neural_rave_nexus.py` (L17-36)
```python
class NeuralRaveNexus(Effect):
    """Neural Rave Nexus - Underground rave consciousness amplifier."""
    
    def __init__(self):
        fragment_shader_source = self._generate_rave_shader()
        super().__init__("Neural Rave Nexus", fragment_shader_source)
```

File: `plugins/vdepth/neural_rave_nexus.py` (L465-475)
```python
        self.shader.set_uniform("lightStreaks", light_mod / 10.0)
        
        # Mid-range for heat
        mid_level = self.audio_reactor.get_feature_level(AudioFeature.MID)
        heat_mod = 5.0 + mid_level * 5.0
        self.shader.set_uniform("midRangeHeat", heat_mod / 10.0)

# Register the plugin
if __name__ == "__main__":
    from core.plugin_registry import register_plugin
    register_plugin(NeuralRaveNexus)
```

### Referenced in Tunnel Vision 3
File: `plugins/vdepth/tunnel_vision_3.py` (L81-100)
```python
        # Initialize rave effects
        self.rave_effects = NeuralRaveNexus()
```

---

## Dependencies

### External Libraries
- `PyOpenGL` — OpenGL shader and texture operations
- `numpy` — Array operations (if needed for audio processing)

### Internal Modules
- `src/vjlive3/plugins/base.py` — `Effect` base class
- `src/vjlive3/audio/reactivity.py` — `AudioReactor` for audio feature extraction
- `src/vjlive3/audio/analyzer.py` — `AudioFeature` enum
- `src/vjlive3/render/shaders.py` — Shader compilation utilities

### Plugin Manifest
The NeuralRaveNexus must be registered in the VJLive3 plugin manifest:

```python
PLUGIN_REGISTRY = {
    'neural_rave_nexus': NeuralRaveNexus,
    # ... other plugins
}
```

---

## Notes for Implementation

1. **Audio Reactivity:** The effect relies on `AudioReactor` being initialized with an audio source. Ensure proper error handling when audio is not available.
2. **Shader Design:** The shader should be visually striking but computationally efficient. Use simple math operations and avoid expensive texture lookups.
3. **Thread Safety:** Audio feature queries may come from a separate thread; ensure uniform updates are thread-safe (use mutex or call from main thread).
4. **Parameter Scaling:** Legacy code divides audio mod by 10.0; verify if this scaling is still appropriate or if direct [0,1] mapping is better.
5. **Documentation:** Include docstrings with type hints for all public methods.

---

## References

- **Plugin System Spec:** `docs/specs/P1-P1_plugin_registry.md`
- **Base Classes:** `src/vjlive3/plugins/base.py`
- **Audio Reactivity:** `src/vjlive3/audio/reactivity.py`
- **Original Source:** `plugins/vdepth/neural_rave_nexus.py` (VJlive)
- **Related Effect:** `plugins/vdepth/tunnel_vision_3.py` (uses NeuralRaveNexus as component)

---

**END OF SPECIFICATION**