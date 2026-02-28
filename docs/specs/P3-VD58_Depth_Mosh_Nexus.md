# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-VD58_Depth_Mosh_Nexus.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD58 — DepthMoshNexus

## Description

The DepthMoshNexus is an underground rave depth-moshing amplifier that combines multiple datamosh techniques with intense audio reactivity. It's designed to produce hypnotic, high-energy visuals that pulse and distort in response to audio frequencies. The effect uses depth data to control displacement and corruption, creating a 3D-aware mosh that respects scene geometry while delivering raw, chaotic visual energy.

This effect is the ultimate VJ tool for high-intensity performances, especially in electronic music contexts. It combines block corruption, I-frame loss, color quantization, scanlines, and depth displacement into a single, audio-reactive package. The nexus architecture allows different audio frequency bands to control different aspects of the effect, creating complex, multi-layered mosh visuals.

## What This Module Does

- Applies comprehensive datamosh corruption (blocks, I-frames, quantization, scanlines)
- Uses depth for displacement and depth-aware corruption modulation
- Audio reactive: bass controls mosh intensity and displacement, mid controls heat distortion, treble controls light streaks
- Dynamically generates shader code based on enabled features
- Supports debug mode for visual troubleshooting
- GPU-accelerated with extensive uniform controls

## What This Module Does NOT Do

- Does NOT provide modular routing (all effects combined)
- Does NOT include CPU fallback (GPU required)
- Does NOT store persistent state across sessions
- Does NOT implement external effect injection points
- Does NOT include preset management (may be added later)
- Does NOT provide per-frequency individual controls (bands are mapped to specific parameters)

---

## Detailed Behavior

### Audio-Reactive Datamosh Pipeline

1. **Audio Analysis**:
   - Extract bass, mid, and treble levels (0-1)
   - Map each band to effect parameters in real-time

2. **Depth Displacement**:
   - Compute depth gradient
   - Displace UV coordinates based on depth and audio-driven displacement strength
   - Bass frequency controls displacement magnitude

3. **Block Corruption**:
   - Divide image into blocks
   - Randomly shift blocks based on mosh intensity
   - Intensity modulated by bass

4. **I-Frame Loss Simulation**:
   - Freeze blocks for multiple frames
   - Creates stuttering, frozen artifacts

5. **Color Quantization**:
   - Reduce color bit depth
   - Creates posterization and banding

6. **Scanline Corruption**:
   - Drop or corrupt alternating lines
   - Creates CRT-like degradation

7. **Light Streaks**:
   - Add horizontal/vertical streaks based on treble
   - Simulates light trails or bloom

8. **Mid-Range Heat**:
   - Add color shift or distortion based on mid frequencies
   - Creates heat haze or thermal effect

9. **Depth-Aware Modulation**:
   - Near vs far objects may have different corruption levels
   - Depth influences displacement and some corruption methods

### Audio Band Mapping

| Audio Band | Controlled Parameters | Effect |
|------------|----------------------|--------|
| **Bass** | `moshIntensity`, `depthDisplacement` | Heavy thump-driven corruption and warping |
| **Mid** | `midRangeHeat` | Warm distortion, thermal haze |
| **Treble** | `lightStreaks` | Sharp, bright streaks and flashes |

### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `moshIntensity` | float | 5.0 | 0.0-10.0 | Base datamosh intensity (bass-modulated) |
| `depthDisplacement` | float | 0.5 | 0.0-1.0 | Depth-based UV displacement (bass-modulated) |
| `blockCorruption` | float | 6.0 | 0.0-10.0 | Block shifting strength |
| `iframeLoss` | float | 4.0 | 0.0-10.0 | I-frame freezing probability |
| `colorQuantization` | float | 3.0 | 0.0-10.0 | Color bit depth reduction |
| `scanlineIntensity` | float | 2.0 | 0.0-10.0 | Scanline corruption strength |
| `lightStreaks` | float | 5.0 | 0.0-10.0 | Treble-driven light streak intensity |
| `midRangeHeat` | float | 5.0 | 0.0-10.0 | Mid-driven heat distortion |
| `depthInfluence` | float | 5.0 | 0.0-10.0 | How much depth modulates corruption |
| `feedbackAmount` | float | 0.3 | 0.0-10.0 | Temporal feedback strength |
| `feedbackDecay` | float | 0.9 | 0.0-10.0 | Feedback decay per frame |
| `debugMode` | float | 0.0 | 0.0-10.0 | Enable debug visualization (0=off) |

**Inherited from Effect**: `u_mix`, `resolution`

---

## Public Interface

```python
class DepthMoshNexus(Effect):
    def __init__(self) -> None: ...
    def set_depth_sources(self, depth_sources: List[DepthSource]) -> None: ...
    def set_audio_reactor(self, audio_reactor: AudioReactor) -> None: ...
    def set_parameter(self, name: str, value: float) -> None: ...
    def get_parameter(self, name: str) -> float: ...
    def apply_uniforms(self, time: float, resolution: Tuple[int, int], audio_reactor=None) -> None: ...
    def process_frame(self, frame: np.ndarray) -> np.ndarray: ...
    def set_debug(self, debug: bool) -> None: ...
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description |
|------|------|-------------|
| `frame` | `np.ndarray` | Input video frame (HxWxC, RGB) |
| **Output** | `np.ndarray` | Mosh output (HxWxC, RGB) |

---

## State Management

**Persistent State:**
- `_depth_sources: List[DepthSource]` — Connected depth sources (multiple)
- `_depth_frames: List[np.ndarray]` — Latest depth frames from each source
- `_depth_textures: List[int]` — GL textures for depth data
- `_audio_reactor: Optional[AudioReactor]` — Audio analysis engine
- `_parameters: dict` — All mosh parameters
- `_shader: ShaderProgram` — Compiled dynamically generated shader
- `_previous_frame_texture: int` — For temporal feedback
- `_framebuffer: int` — For off-screen rendering
- `_debug_mode: bool` — Debug visualization flag

**Per-Frame:**
- Update depth data from all sources (blend or select one)
- Upload depth textures
- Analyze audio (if reactor set) → get bass, mid, treble levels
- Update shader uniforms with audio-modulated values
- Render mosh effect
- Store output in previous frame texture for feedback
- Return result

**Initialization:**
- Create depth textures (lazy, one per source)
- Create previous frame texture (ping-pong)
- Create framebuffer
- Generate initial shader
- Default parameters: moshIntensity=5.0, depthDisplacement=0.5, blockCorruption=6.0, iframeLoss=4.0, colorQuantization=3.0, scanlineIntensity=2.0, lightStreaks=5.0, midRangeHeat=5.0, depthInfluence=5.0, feedbackAmount=0.3, feedbackDecay=0.9, debugMode=0.0

**Cleanup:**
- Delete all depth textures
- Delete previous frame texture
- Delete framebuffer
- Delete shader
- Call `super().cleanup()`

---

## GPU Resources

| Resource | Type | Format | Dimensions | Lifecycle |
|----------|------|--------|------------|-----------|
| Depth textures (N) | GL_TEXTURE_2D | GL_RED, GL_UNSIGNED_BYTE | depth_frame size | Updated each frame |
| Previous frame texture | GL_TEXTURE_2D | GL_RGBA8 | frame size | Updated each frame |
| Framebuffer | GL_FRAMEBUFFER | N/A | frame size | Persistent |
| Shader program | GLSL | vertex + fragment | N/A | Regenerated when params change |

**Memory Budget (640×480, 1 depth source):**
- Depth texture: 307,200 bytes
- Previous frame texture: 921,600 bytes
- Shader: ~40-80 KB (large, dynamic)
- Total: ~1.2-1.3 MB

---

## Error Cases

| Error Condition | Response | Recovery |
|-----------------|----------|----------|
| No depth source | Use zero depth (no displacement) | Normal operation |
| Depth texture upload fails | `RuntimeError("GPU error")` | Check GL errors |
| Audio reactor not set | Use default values (5.0) | Normal operation |
| Shader generation fails | `ShaderCompilationError` | Log and fall back to simpler shader |
| Invalid parameter | Clamp to range or raise `ValueError` | Document valid ranges |

---

## Thread Safety

The effect is **not thread-safe**. All GPU operations, texture updates, and shader compilation must occur on the thread with the OpenGL context. The effect updates multiple textures and recompiles shaders when parameters change, so concurrent `process_frame()` calls will cause race conditions. Use one instance per thread or protect with a mutex.

---

## Performance

**Expected Frame Time (640×480):**
- Depth texture upload: ~0.5-1 ms per source
- Audio analysis: ~0.1-0.5 ms
- Shader execution (comprehensive mosh): ~8-15 ms
- Texture copy for feedback: ~0.5-1 ms
- Total: ~9-17 ms on GPU (may vary with audio reactivity)

**Optimization Strategies:**
- Reduce number of enabled corruption methods via shader defines
- Use simpler block corruption (larger blocks)
- Disable feedback if not needed
- Cache shader program (only regenerate when critical params change)
- Lower resolution for depth texture
- Use compute shader for parallel processing

---

## Integration Checklist

- [ ] Depth source(s) set and providing depth frames
- [ ] Audio reactor set (optional but recommended)
- [ ] Mosh parameters configured
- [ ] Debug mode tested if needed
- [ ] `process_frame()` called each frame
- [ ] `cleanup()` called on shutdown

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init` | Effect initializes with default parameters |
| `test_set_parameter` | All parameters can be set and clamped |
| `test_get_parameter` | All parameters can be retrieved |
| `test_set_depth_sources` | Multiple depth sources can be set |
| `test_set_audio_reactor` | Audio reactor can be attached |
| `test_set_debug` | Debug mode can be toggled |
| `test_shader_generation` | Shader code generated without errors |
| `test_audio_mapping` | Audio levels correctly modulate parameters |
| `test_block_corruption` | Block artifacts appear with intensity |
| `test_iframe_loss` | I-frame loss freezes blocks |
| `test_color_quantization` | Reduces color depth when enabled |
| `test_scanlines` | Scanline corruption adds line artifacts |
| `test_light_streaks` | Treble adds light streaks |
| `test_mid_range_heat` | Mid adds heat distortion |
| `test_depth_displacement` | Depth displaces pixels (bass-modulated) |
| `test_feedback` | Temporal feedback creates recursion |
| `test_depth_influence` | Depth modulates corruption intensity |
| `test_process_frame_no_audio` | Falls back to default values |
| `test_process_frame_with_audio` | Audio modulates effect in real-time |
| `test_debug_mode` | Debug visualization shows depth or other info |
| `test_cleanup` | All GPU resources released |
| `test_no_memory_leak` | Repeated init/cleanup cycles don't leak |

**Minimum coverage:** 85%

---

## Definition of Done

- [ ] Spec reviewed
- [ ] All tests pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint checked
- [ ] Git commit with `[Phase-3] P3-VD58: depth_mosh_nexus` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Legacy Code Mapping

Key references:
- `plugins/vdepth/depth_mosh_nexus.py` — VJLive Original implementation
- `plugins/core/depth_mosh_nexus/__init__.py` — VJLive-2 implementation
- `plugins/core/depth_mosh_nexus/plugin.json` — Effect manifest
- `plugins/vdepth/DEPTH_MOSH_DOCUMENTATION.md` — Legacy documentation
- `gl_leaks.txt` — Shows `DepthMoshNexus` allocates `glGenTextures` and must free them

Design decisions inherited:
- Effect name: `depth_mosh_nexus`
- Inherits from `Effect` (not `DepthEffect`)
- Uses depth texture for displacement and modulation
- Audio reactive with 3 frequency bands (bass, mid, treble)
- Parameters: `moshIntensity`, `depthDisplacement`, `blockCorruption`, `iframeLoss`, `colorQuantization`, `scanlineIntensity`, `lightStreaks`, `midRangeHeat`, `depthInfluence`, `feedbackAmount`, `feedbackDecay`, `debugMode`
- Allocates GL resources: depth textures (multiple sources), previous frame texture, framebuffer
- Shader is dynamically generated based on enabled features
- Method `_generate_mosh_shader()` creates GLSL code
- Audio reactor provides `get_feature_level(AudioFeature.BASS/MID/TREBLE)`

---

## Notes for Implementers

1. **Core Concept**: This is a "kitchen sink" datamosh effect that combines many corruption techniques with deep audio reactivity. It's designed for high-energy VJ performances where the visuals should pulse and distort with the music.

2. **Dynamic Shader Generation**: The legacy uses `_generate_mosh_shader()` to build the shader source code dynamically based on which features are enabled. This allows for flexible optimization but adds complexity. Consider:
   - Building shader string with conditional sections
   - Using `#define` flags to enable/disable features at compile time
   - Caching shader programs for different parameter combinations

3. **Audio Reactivity**:
   ```python
   if self.audio_reactor:
       bass = self.audio_reactor.get_feature_level(AudioFeature.BASS)
       mid = self.audio_reactor.get_feature_level(AudioFeature.MID)
       treble = self.audio_reactor.get_feature_level(AudioFeature.TREBLE)
   else:
       bass = mid = treble = 0.0
   
   # Map to parameters (0-1 audio → 0-10 parameter)
   mosh_intensity = 5.0 + bass * 5.0  # 5-10
   displacement = bass * 0.8  # 0-0.8
   light_streaks = 5.0 + treble * 5.0  # 5-10
   mid_heat = 5.0 + mid * 5.0  # 5-10
   
   self.shader.set_uniform("moshIntensity", mosh_intensity / 10.0)
   self.shader.set_uniform("depthDisplacement", displacement)
   self.shader.set_uniform("lightStreaks", light_streaks / 10.0)
   self.shader.set_uniform("midRangeHeat", mid_heat / 10.0)
   ```

4. **Multiple Depth Sources**: The effect can accept multiple depth sources. How to combine them?
   - Average: `depth = mean(depths)`
   - Closest: `depth = min(depths)`
   - Farthest: `depth = max(depths)`
   - Weighted: `depth = sum(weights[i] * depths[i])`
   The legacy likely uses the first source or averages. Document the behavior.

5. **Shader Structure**: The generated shader will be large. Organize it as:
   ```glsl
   #version 330 core
   // Uniforms
   // Random function
   // Block corruption function
   // I-frame loss function
   // Color quantization function
   // Scanline function
   // Light streak function
   // Heat distortion function
   void main() {
       // Sample depth
       // Compute displacement (bass-modulated)
       // Apply block corruption
       // Apply I-frame loss
       // Apply color quantization
       // Apply scanlines
       // Apply light streaks (treble)
       // Apply heat (mid)
       // Apply feedback
       // Final mix
   }
   ```

6. **Feedback**: The effect includes temporal feedback to create recursive blur/trails. Use ping-pong textures:
   ```python
   self.prev_tex = glGenTextures(2)
   self.current_prev = 0
   # Each frame: read from prev_tex[current], render to other, swap
   ```

7. **I-Frame Loss**: To simulate I-frame loss properly, you need to track which blocks are frozen across frames. Could use:
   - Random per-block "freeze until" timestamp stored in a texture
   - Simplified: just skip updating some blocks (they persist via feedback)
   The legacy likely uses a simpler approach.

8. **Light Streaks**: Could be implemented as horizontal/vertical blur or additive streaks:
   ```glsl
   if (lightStreaks > 0.0) {
       float streak = 0.0;
       for (int i = 1; i <= 4; i++) {
           streak += texture(tex0, uv + vec2(0.0, i * 0.01)).r;
       }
       color += streak * lightStreaks * 0.1;
   }
   ```

9. **Mid-Range Heat**: Could be a color shift or distortion:
   ```glsl
   if (midRangeHeat > 0.0) {
       // Shift red/orange
       color.r = texture(tex0, uv + vec2(midRangeHeat*0.01, 0.0)).r;
       color.g = texture(tex0, uv - vec2(midRangeHeat*0.01, 0.0)).g;
   }
   ```

10. **Debug Mode**: When enabled, visualize depth or corruption masks:
    ```glsl
    if (debugMode > 0.0) {
        fragColor = vec4(depth, depth, depth, 1.0);  // Show depth
        // or show corruption mask
    }
    ```

11. **Parameter Ranges**:
    - `moshIntensity`: 0-10 → corruption multiplier
    - `depthDisplacement`: 0-1 → displacement strength (already 0-1)
    - `blockCorruption`, `iframeLoss`, etc.: 0-10 → probability multipliers
    - `lightStreaks`, `midRangeHeat`: 0-10 → effect strength (0-1 after divide)
    - `depthInfluence`: 0-10 → how much depth modulates corruption
    - `feedbackAmount`: 0-10 → 0-1 (divide by 10)
    - `feedbackDecay`: 0-10 → 0-1 (divide by 10)

12. **Shader Generation Pattern**:
    ```python
    def _generate_mosh_shader(self):
        shader = """
        #version 330 core
        in vec2 uv;
        out vec4 fragColor;
        uniform sampler2D tex0;
        uniform sampler2D depth_tex;
        uniform sampler2D texPrev;
        uniform vec2 resolution;
        uniform float u_mix;
        uniform float time;
        uniform float moshIntensity;
        uniform float depthDisplacement;
        uniform float blockCorruption;
        uniform float iframeLoss;
        uniform float colorQuantization;
        uniform float scanlineIntensity;
        uniform float lightStreaks;
        uniform float midRangeHeat;
        uniform float depthInfluence;
        uniform float feedbackAmount;
        uniform float feedbackDecay;
        uniform float debugMode;
        
        float random(vec2 st) { ... }
        
        void main() {
            vec4 source = texture(tex0, uv);
            float depth = texture(depth_tex, uv).r;
            
            // Depth displacement
            float dx = dFdx(depth);
            float dy = dFdy(depth);
            vec2 disp = vec2(dx, dy) * depthDisplacement * 10.0;
            vec2 uv_disp = uv + disp;
            
            vec4 color = texture(tex0, uv_disp);
            
            // Block corruption
            if (blockCorruption > 0.0) {
                // ... block shifting
            }
            
            // I-frame loss
            if (iframeLoss > 0.0) {
                // ... freeze blocks
            }
            
            // Color quantization
            if (colorQuantization > 0.0) {
                float levels = pow(2.0, 8.0 - colorQuantization * 0.5);
                color.rgb = floor(color.rgb * levels) / levels;
            }
            
            // Scanlines
            if (scanlineIntensity > 0.0) {
                // ... drop lines
            }
            
            // Light streaks (treble)
            if (lightStreaks > 0.0) {
                // ... additive streaks
            }
            
            // Mid-range heat
            if (midRangeHeat > 0.0) {
                // ... color shift
            }
            
            // Depth influence on corruption
            if (depthInfluence > 0.0) {
                float depth_mod = mix(1.0, depth, depthInfluence * 0.1);
                // Apply to corruption parameters or final mix
            }
            
            // Feedback
            if (feedbackAmount > 0.0) {
                vec4 prev = texture(texPrev, uv);
                color = mix(color, prev, feedbackAmount * feedbackDecay);
            }
            
            // Debug
            if (debugMode > 0.0) {
                color = vec4(depth, depth, depth, 1.0);
            }
            
            fragColor = mix(source, color, u_mix);
        }
        """
        return shader
    ```

13. **PRESETS**: The legacy mentions "chaos_mode". Define presets:
    ```python
    PRESETS = {
        "clean": {
            "moshIntensity": 0.0, "depthDisplacement": 0.0,
            "blockCorruption": 0.0, "iframeLoss": 0.0,
            "colorQuantization": 0.0, "scanlineIntensity": 0.0,
            "lightStreaks": 0.0, "midRangeHeat": 0.0,
            "depthInfluence": 0.0, "feedbackAmount": 0.0,
        },
        "rave_chaos": {
            "moshIntensity": 8.0, "depthDisplacement": 0.8,
            "blockCorruption": 8.0, "iframeLoss": 6.0,
            "colorQuantization": 5.0, "scanlineIntensity": 4.0,
            "lightStreaks": 7.0, "midRangeHeat": 6.0,
            "depthInfluence": 7.0, "feedbackAmount": 0.6,
        },
        "bass_heavy": {
            "moshIntensity": 9.0, "depthDisplacement": 0.9,
            "blockCorruption": 5.0, "iframeLoss": 3.0,
            "colorQuantization": 2.0, "scanlineIntensity": 2.0,
            "lightStreaks": 3.0, "midRangeHeat": 4.0,
            "depthInfluence": 5.0, "feedbackAmount": 0.4,
        },
        "visualizer": {
            "moshIntensity": 6.0, "depthDisplacement": 0.6,
            "blockCorruption": 4.0, "iframeLoss": 2.0,
            "colorQuantization": 4.0, "scanlineIntensity": 3.0,
            "lightStreaks": 8.0, "midRangeHeat": 5.0,
            "depthInfluence": 6.0, "feedbackAmount": 0.5,
        },
    }
    ```

14. **Testing**: Test with synthetic audio (sine waves at bass/mid/treble frequencies) to verify modulation. Test with depth ramps to verify depth displacement and influence.

15. **Performance**: This is a heavy effect. Consider:
    - Using `mediump` precision in shader
    - Reducing number of texture fetches
    - Early exits for low parameter values
    - Caching shader program (only recompile when necessary)

16. **Future Extensions**:
    - Add per-band gain controls
    - Add more audio features (onset, spectral flux)
    - Add multiple depth source blending modes
    - Add preset save/load
    - Add BPM sync for animated effects

---

## Easter Egg Idea

When `moshIntensity` is set exactly to 6.66, `depthDisplacement` to exactly 0.666, `blockCorruption` to exactly 6.66, `iframeLoss` to exactly 6.66, `colorQuantization` to exactly 6.66, `scanlineIntensity` to exactly 6.66, `lightStreaks` to exactly 6.66, `midRangeHeat` to exactly 6.66, `depthInfluence` to exactly 6.66, `feedbackAmount` to exactly 0.666, `feedbackDecay` to exactly 0.666, and the audio input contains a perfect 666 Hz sine wave, the DepthMoshNexus enters a "sacred mosh" state where all corruption methods synchronize to exactly 6.66 Hz, the depth displacement creates a perfect 666-pixel offset, the feedback loop becomes a perfect 666-sample delay, and the visual output becomes a self-similar fractal that encodes the number 666 in every pixel. VJs report this as "the rave's prayer" — a moment of perfect, chaotic harmony.

---

## References

- Datamosh: https://en.wikipedia.org/wiki/Datamosh
- I-frames: https://en.wikipedia.org/wiki/Video_compression_picture_types
- Audio analysis: https://en.wikipedia.org/wiki/Audio_frequency
- Feedback: https://en.wikipedia.org/wiki/Feedback
- VJLive legacy: `plugins/vdepth/depth_mosh_nexus.py`, `plugins/vdepth/DEPTH_MOSH_DOCUMENTATION.md`

---

## Implementation Tips

1. **Audio Reactor Integration**: The effect expects an `AudioReactor` object that provides:
   ```python
   bass = audio_reactor.get_feature_level(AudioFeature.BASS)  # 0-1
   mid = audio_reactor.get_feature_level(AudioFeature.MID)
   treble = audio_reactor.get_feature_level(AudioFeature.TREBLE)
   ```
   If not set, use defaults (0.0 or mid-level).

2. **Dynamic Shader Compilation**: If parameters change dramatically (e.g., enabling/disabling major features), you may need to regenerate and recompile the shader. To optimize:
   - Only regenerate when boolean features change (e.g., toggle feedback)
   - For continuous parameters (intensity), just update uniforms
   - Cache shader programs keyed by parameter hash

3. **Multiple Depth Sources**: Implement a strategy for combining multiple depth frames:
   ```python
   def _get_combined_depth(self):
       if not self._depth_frames:
           return None
       if len(self._depth_frames) == 1:
           return self._depth_frames[0]
       # Average all depth frames
       combined = np.mean(self._depth_frames, axis=0)
       return combined
   ```

4. **Feedback Implementation**: Use ping-pong textures:
   ```python
   def _ensure_feedback(self, width, height):
       if self._prev_tex[0] == 0:
           self._prev_tex = glGenTextures(2)
           self._fbo = glGenFramebuffers(2)
           for i in range(2):
               glBindTexture(GL_TEXTURE_2D, self._prev_tex[i])
               glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
               # ... setup FBO
   ```

5. **I-Frame Loss State**: To track which blocks are frozen, you could:
   - Use a separate texture as a "freeze mask" that persists across frames
   - Each frame, randomly set some blocks to "freeze" for N frames
   - In shader, check freeze mask and skip updating frozen blocks
   Simplified: just rely on feedback to naturally persist some blocks.

6. **Light Streaks**: Could be implemented as a horizontal blur that accumulates over time, or as additive streaks from bright areas. The treble modulation suggests quick, sharp flashes.

7. **Mid-Range Heat**: Could be a color temperature shift (toward red/orange) or a refractive distortion. Mid frequencies are often associated with "body" or "warmth".

8. **Debug Mode**: When enabled, output a debug visualization:
   - Show depth map
   - Show corruption mask
   - Show block boundaries
   - Show freeze mask
   This helps tune parameters.

9. **Shader Optimization**: The shader will be large. Use:
   ```glsl
   #ifdef BLOCK_CORRUPTION
   // block code
   #endif
   ```
   And compile with defines based on which features are heavily used. However, dynamic audio modulation means all parameters are always present, just with varying values.

10. **Parameter Smoothing**: Audio levels can jump quickly. Consider smoothing:
    ```python
    self.smoothed_bass = 0.9 * self.smoothed_bass + 0.1 * bass
    ```
    Then use smoothed values for uniforms to reduce flicker.

11. **Testing Strategy**:
    - Test each corruption method individually (set others to 0)
    - Test audio reactivity by feeding known audio levels
    - Test depth displacement with depth ramp
    - Test feedback by checking for trails
    - Test debug mode output

12. **Performance**: The effect is one of the heaviest. Profile to find bottlenecks:
    - Block corruption: O(1) per pixel but with random branching
    - I-frame loss: similar
    - Color quantization: cheap
    - Scanlines: cheap
    - Light streaks: may require multiple texture fetches
    - Heat distortion: may require offset sampling
    - Feedback: one extra texture fetch
    Consider simplifying some effects if performance is inadequate.

---

## Conclusion

The DepthMoshNexus is the ultimate audio-reactive datamosh effect, combining multiple corruption techniques with depth awareness and intense music-driven modulation. It's designed for high-energy VJ performances where visuals should pulse, distort, and mosh in sync with the music. With its comprehensive parameter set and dynamic shader generation, it offers unparalleled control over the chaos of datamosh.

---
>>>>>>> REPLACE