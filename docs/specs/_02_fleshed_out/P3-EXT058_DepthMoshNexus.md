# DepthMoshNexus — Underground Rave Depth Moshing Amplifier

**Task ID:** `P3-EXT058`  
**Priority:** P3-EXT (Missing Legacy Effects Parity)  
**Module Type:** Depth Datamosh Effect Plugin  
**Architecture:** VJLive3 Clean Architecture (Effect subclass)

---

## Overview

The `DepthMoshNexus` effect creates an immersive, high-intensity depth-moshing experience inspired by underground rave culture. It combines dual depth camera streams with modular loop control, audio reactivity, and neural feedback loops to produce chaotic, hypnotic visuals that simulate the collective energy of a 3AM rave.

This module represents one of the most sophisticated depth-datamosh implementations in the legacy codebase, featuring:

- **Dual depth source processing** — Two independent depth streams create complex mosh patterns
- **Modular loop control** — Configurable loop in/out points for temporal manipulation
- **6-channel neural feedback matrix** — Multi-tap feedback with depth-dependent routing
- **Audio-reactive intensity modulation** — Bass-driven displacement and crowd energy
- **Synesthetic depth-color mapping** — Audio features mapped to color via HSV space
- **Time-evolved state machine** — Intensity builds over the duration of a rave set

The effect is designed for live VJ performance where the operator can manipulate parameters in real-time to guide the "collective consciousness" of the visual experience.

---

## What This Module Does

### Core Functionality

`DepthMoshNexus` processes video through a multi-stage pipeline that:

1. **Captures dual depth streams** from two depth sources (typically two Astra cameras or a single camera with depth + synthetic depth)
2. **Applies modular loop-based temporal displacement** using configurable loop points (normalized 0.0-1.0)
3. **Integrates audio reactivity** by analyzing bass, mid, and treble frequencies to modulate intensity, displacement, and visual effects
4. **Runs a 6-channel feedback matrix** where each channel stores previous frame data with depth-dependent routing and cross-feed capabilities
5. **Generates synesthetic color mappings** that translate audio features into HSV color space
6. **Simulates collective consciousness** through time-evolved state variables that increase intensity over the performance duration

### Visual Output

The effect produces:

- **Depth-driven pixel displacement** — Pixels shift based on depth differences between the two depth sources
- **Chaotic mosh patterns** — Random noise injection creates the "mosh pit" aesthetic
- **Neural feedback trails** — Previous frames feed back with depth-modulated routing
- **Audio-synchronized pulsing** — Bass hits cause screen-wide vibrations and intensity spikes
- **Color cycling** — Treble frequencies trigger rainbow glows mapped to depth
- **Heat distortion** — Mid-range audio creates red-channel amplification
- **Loop-based temporal artifacts** — The modular loop creates repeating patterns with optional ping-pong behavior

---

## What This Module Does NOT Do

- **Does NOT perform real compression datamoshing** — This is a simulated effect using GLSL shaders, not actual video compression manipulation
- **Does NOT replace depth camera drivers** — It consumes depth frames from external sources; it does not capture depth itself
- **Does NOT handle audio capture** — Requires an external `AudioReactor` instance to provide audio feature analysis
- **Does NOT manage texture memory automatically** — The plugin creates and manages 8 textures (2 depth + 6 feedback + 1 output) but does not implement texture pooling or garbage collection
- **Does NOT provide UI controls** — This is a backend effect; parameter adjustment happens through the effect chain API
- **Does NOT support variable resolution** — Assumes fixed resolution set at initialization; no dynamic resolution switching
- **Does NOT implement advanced depth filtering** — Uses simple normalized clipping; no bilateral filter or edge-aware smoothing
- **Does NOT handle multi-threading** — All GL operations happen on the main thread; no async texture uploads

---

## Detailed Behavior and Parameter Interactions

### Architecture

The `DepthMoshNexus` class inherits from [`Effect`](core/effects/shader_base.py) and overrides:

- `__init__()` — Generates the fragment shader, initializes state, creates texture IDs
- `apply_uniforms()` — Uploads all uniforms and triggers depth texture updates
- `_apply_mosh_uniforms()` — Maps internal parameters (0-10 range) to shader uniforms (0.0-1.0)
- `_apply_audio_modulation()` — Reads audio features and modulates parameters in real-time
- `update_mosh_state()` — Evolves time-based state variables (intensity, position, consciousness)
- `update_depth_data()` — Pulls depth frames from sources and uploads to GPU

### Shader Pipeline

The GLSL fragment shader executes the following stages per pixel:

```
1. Sample depth0 and depth1 from depth_tex0 and depth_tex1
2. Compute avgDepth = (depth0 + depth1) * 0.5
3. Sample mainSource (tex0), secondarySource (tex1), tertiarySource (tex2)
4. ApplyMoshEffects:
   - Calculate loopLength = loopOut - loopIn
   - normalizedPos = fract((moshPos - loopIn) / loopLength)
   - depthDiff = abs(depth0 - depth1)
   - displacement = depthDiff * displacementStrength * 0.1
   - Add chaos noise if chaosFactor > 0.5
   - displacedUV = uv + vec2(displacement, displacement * 0.5)
   - Apply loop modulation sine wave if loopModulation > 0.5
   - result = texture(texPrev, displacedUV)
   - Optional depthBlend: mix with current frame based on avgDepth
5. ApplyNeuralFeedback:
   - Loop i=1..6: sample feedback{i} with depth-modulated UV offset if neuralSync
   - Apply collectiveConsciousness brightness modulation
   - Mix input with averaged feedback based on neuralFeedback uniform
6. ApplySynestheticMapping:
   - bassPulse: multiply RGB by sin(time*10 + depth*3) mapped 0.8-1.3
   - trebleGlow: add HSV color from getSynestheticColor(glow)
   - midRangeHeat: boost red channel based on heat value
7. ApplyCollectiveConsciousness:
   - consciousnessFlow: modulate alpha
   - sensoryOverload: occasional RGB = vec3(1.0, 0.5, 0.8) spike
   - collectiveBeat: multiply by 0.8-1.2 on beat
8. Final: fragColor = mix(black, final, masterIntensity * 0.1)
```

### Parameter Mapping

All user-facing parameters use a **0.0-10.0 float range** from UI sliders. The `_apply_mosh_uniforms()` method normalizes them to 0.0-1.0 for shader consumption, typically via `param / 10.0`. Exceptions:

- `moshSpeed` — Direct float (default 1.0), no normalization
- `loopIn` / `loopOut` — Normalized loop points (0.0-1.0), passed as-is
- `moshPosition` — State variable (0.0-1.0), passed as-is

### Audio Reactivity

When an `AudioReactor` is set via `set_audio_reactor()`, the `_apply_audio_modulation()` method queries three features:

- `AudioFeature.BASS` — Drives `masterIntensity`, `moshIntensity`, `depthDisplacement`
- `AudioFeature.TREBLE` — Drives `lightStreaks` (note: shader has `trebleGlow`, not `lightStreaks` — potential bug)
- `AudioFeature.MID` — Drives `midRangeHeat`

Audio levels are normalized 0.0-1.0 and mapped to parameter ranges:

```python
intensity_mod = 5.0 + bass_level * 5.0  # Result: 5.0-10.0
```

This allows the effect to have a baseline intensity even with no audio, then scale up with bass hits.

### State Evolution

The `update_mosh_state()` method evolves time-based variables:

- `time_in_rave` — Elapsed seconds since plugin construction
- `intensity` — Ramps from 3.0 to 8.0 over first 60s, then slowly to 10.0 over 5 minutes
- `collective_consciousness` — Ramps from 4.0 to 10.0 over 10 minutes
- `synesthetic_mapping` — Ramps from 5.0 to 10.0 over 5 minutes
- `neural_feedback` — Ramps from 3.0 to 10.0 over 2 minutes
- `mosh_position` — Increments by `mosh_speed * delta_time` and wraps via `fract()`
- `mosh_chaos` — Set to `min(collective_consciousness / 10.0, 1.0) * 0.8`

This creates a performance that starts relatively tame and builds to maximum intensity over the course of a rave set, simulating the "collective consciousness" rising.

---

## Public Interface

### Constructor

```python
def __init__(self) -> None
```

Creates a new `DepthMoshNexus` instance with default parameters, generates the fragment shader, and initializes texture handles to 0.

**Side effects:**
- Calls `super().__init__("DepthMosh Nexus", fragment_shader_source)`
- Allocates `self.depth_textures = [0, 0]`
- Allocates `self.feedback_textures = [0, 0, 0, 0, 0, 0]`
- Sets `self.output_texture = 0`
- Initializes `self.mosh_state` dictionary with default values
- Calls `self._initialize_mosh_parameters()` to populate `self.parameters`

### Methods

#### `set_audio_reactor(audio_reactor: AudioReactor) -> None`

Attaches an audio analysis engine to the effect. The reactor must implement `get_feature_level(feature: AudioFeature) -> float`.

**Parameters:**
- `audio_reactor` — An object providing audio feature extraction (BASS, MID, TREBLE)

**Behavior:**
- Stores reference in `self.audio_reactor`
- If `None`, audio modulation is disabled (but effect continues)

#### `set_depth_sources(depth_sources: list) -> None`

Configures the two depth input sources. Each source must implement `get_filtered_depth_frame() -> np.ndarray | None`.

**Parameters:**
- `depth_sources` — List of depth source objects (length >= 2 recommended)

**Behavior:**
- If `len(depth_sources) >= 2`, stores first two: `self.depth_sources = depth_sources[:2]`
- If shorter, pads with `None`: `depth_sources + [None] * (2 - len(depth_sources))`
- Sources with `None` are skipped during `update_depth_data()`

#### `apply_uniforms(time_val: float, resolution: tuple, audio_reactor=None, semantic_layer=None) -> None`

Main entry point called by the effect chain each frame. Uploads all shader uniforms and updates textures.

**Parameters:**
- `time_val` — Global time in seconds (typically from render loop)
- `resolution` — `(width, height)` tuple for viewport calculations
- `audio_reactor` — Optional override; if provided, temporarily sets `self.audio_reactor` for this frame
- `semantic_layer` — Unused in this effect (reserved for future AI segmentation)

**Behavior:**
1. Calls `super().apply_uniforms(time_val, resolution, audio_reactor, semantic_layer)`
2. Calls `self.update_mosh_state()` to evolve time-based variables
3. Calls `self.update_depth_data()` to fetch and upload depth frames
4. For each depth texture index `i` where `self.depth_textures[i] != 0`, calls `self.shader.set_uniform(f"depth_tex{i}", 3 + i)` to bind texture unit
5. For each feedback texture index `i` where `self.feedback_textures[i] != 0`, calls `self.shader.set_uniform(f"feedback{i+1}", 5 + i)`
6. Calls `self._apply_mosh_uniforms()` to upload all parameter uniforms
7. If `self.audio_reactor` is set, calls `self._apply_audio_modulation()` to override some parameters with audio-derived values

**Note:** Texture units are hard-coded:
- `depth_tex0` → unit 3
- `depth_tex1` → unit 4
- `feedback1-6` → units 5-10

#### `update_mosh_state() -> None`

Evolves the `self.mosh_state` dictionary based on elapsed time and audio.

**Behavior:**
- Computes `time_in_rave = current_time - self.start_time`
- `intensity` ramps: 3.0→8.0 over 60s, then 5.0→10.0 over 300s
- `collective_consciousness` ramps 4.0→10.0 over 600s (10 min)
- `synesthetic_mapping` ramps 5.0→10.0 over 300s
- `neural_feedback` ramps 3.0→10.0 over 120s
- `mosh_position += mosh_speed * delta_time`, wrapped with `fract()`
- If `audio_reactor` present: `depth_displacement = bass_level * 0.8`
- `mosh_chaos = min(collective_consciousness / 10.0, 1.0) * 0.8`

**Thread safety:** Not thread-safe; must be called from render thread.

#### `update_depth_data() -> None`

Pulls depth frames from all configured sources and uploads to GPU textures.

**Behavior:**
- Iterates `enumerate(self.depth_sources)`
- For each non-None source, calls `depth_source.get_filtered_depth_frame()`
- If frame is not `None`, calls `self._upload_depth_texture(depth_frame, index)`

**Texture creation:** If `self.depth_textures[index] == 0`, generates new GL texture with `glGenTextures(1)` and sets parameters (GL_LINEAR filtering, GL_CLAMP_TO_EDGE wrap).

**Normalization:** Depth values are clipped to `[0.3, 4.0]` meters, normalized to `[0.0, 1.0]`, then converted to `uint8`:

```python
depth_normalized = np.clip((depth_frame - 0.3) / (4.0 - 0.3), 0.0, 1.0)
depth_u8 = (depth_normalized * 255).astype(np.uint8)
```

**Upload:** Uses `glTexImage2D` with `GL_RED` format (single-channel depth).

#### `_apply_mosh_uniforms() -> None`

Maps `self.parameters` and `self.mosh_state` to shader uniforms.

**Uniforms set:**

| Uniform name | Source | Normalization |
|--------------|--------|---------------|
| `masterIntensity` | `parameters['masterIntensity']` | direct (0-10) |
| `bassPulse` | `parameters['bassPulse']` | `/ 10.0` |
| `trebleGlow` | `parameters['trebleGlow']` | `/ 10.0` |
| `midRangeHeat` | `parameters['midRangeHeat']` | `/ 10.0` |
| `collectiveConsciousness` | `parameters['collectiveConsciousness']` | `/ 10.0` |
| `synestheticMapping` | `parameters['synestheticMapping']` | `/ 10.0` |
| `neuralFeedback` | `parameters['neuralFeedback']` | `/ 10.0` |
| `neuralSync` | `parameters['neuralSync']` | `/ 10.0` |
| `consciousnessFlow` | `parameters['consciousnessFlow']` | `/ 10.0` |
| `sensoryOverload` | `parameters['sensoryOverload']` | `/ 10.0` |
| `collectiveBeat` | `parameters['collectiveBeat']` | `/ 10.0` |
| `synestheticColor` | `parameters['synestheticColor']` | `/ 10.0` |
| `neuralResonance` | `parameters['neuralResonance']` | `/ 10.0` |
| `moshIntensity` | `parameters['moshIntensity']` | `/ 10.0` |
| `depthBlend` | `parameters['depthBlend']` | `/ 10.0` |
| `chaosFactor` | `parameters['chaosFactor']` | `/ 10.0` |
| `displacementStrength` | `parameters['displacementStrength']` | `/ 10.0` |
| `loopModulation` | `parameters['loopModulation']` | `/ 10.0` |
| `crowdEnergy` | `parameters['crowdEnergy']` | `/ 10.0` |
| `bassVibration` | `parameters['bassVibration']` | `/ 10.0` |
| `moshPosition` | `mosh_state['mosh_position']` | direct (0-1) |
| `moshSpeed` | `parameters['moshSpeed']` | direct float |
| `depthDisplacement` | `mosh_state['depth_displacement']` | direct (0-1) |
| `moshChaos` | `mosh_state['mosh_chaos']` | direct (0-1) |
| `loopIn` | `parameters['loopIn']` | direct (0-1) |
| `loopOut` | `parameters['loopOut']` | direct (0-1) |

#### `_apply_audio_modulation() -> None`

Overrides selected parameters based on current audio features.

**Behavior:**
- `bass_level = self.audio_reactor.get_feature_level(AudioFeature.BASS)`
- `masterIntensity = (5.0 + bass_level * 5.0) / 10.0`
- `treble_level = self.audio_reactor.get_feature_level(AudioFeature.TREBLE)`
- `lightStreaks = (5.0 + treble_level * 5.0) / 10.0` ⚠️ **Bug:** Shader uses `trebleGlow`, not `lightStreaks`
- `mid_level = self.audio_reactor.get_feature_level(AudioFeature.MID)`
- `midRangeHeat = (5.0 + mid_level * 5.0) / 10.0`
- `moshIntensity = (5.0 + bass_level * 5.0) / 10.0`
- `depthDisplacement = bass_level * 0.8`

**Note:** The `lightStreaks` uniform is never used in the shader; this is likely a copy-paste error from another effect.

#### `_initialize_mosh_parameters() -> dict`

Returns the default parameter dictionary with 24 keys (see Parameter Mapping table).

#### `create_depth_mosh_nexus() -> DepthMoshNexus`

Factory function required by plugin registry. Returns a new instance.

---

## Inputs and Outputs

### Texture Inputs (Bound by EffectChain)

The shader expects the following texture bindings:

| Texture | GL Unit | Meaning | Source |
|---------|---------|---------|--------|
| `tex0` | 0 | Main video source (RGB) | Effect chain input 0 |
| `tex1` | 1 | Secondary video source (RGB) | Effect chain input 1 (optional) |
| `tex2` | 2 | Tertiary video source (RGB) | Effect chain input 2 (optional) |
| `texPrev` | ? | Previous frame buffer | Effect chain feedback |
| `depth_tex0` | 3 | Depth map 0 (R8) | Uploaded by plugin from depth source 0 |
| `depth_tex1` | 4 | Depth map 1 (R8) | Uploaded by plugin from depth source 1 |
| `feedback1` | 5 | Feedback channel 1 (RGBA) | Internal ping-pong FBO |
| `feedback2` | 6 | Feedback channel 2 (RGBA) | Internal ping-pong FBO |
| `feedback3` | 7 | Feedback channel 3 (RGBA) | Internal ping-pong FBO |
| `feedback4` | 8 | Feedback channel 4 (RGBA) | Internal ping-pong FBO |
| `feedback5` | 9 | Feedback channel 5 (RGBA) | Internal ping-pong FBO |
| `feedback6` | 10 | Feedback channel 6 (RGBA) | Internal ping-pong FBO |

**Note:** The legacy code does NOT show feedback texture creation or management. The `self.feedback_textures` array is allocated but never populated. This is a **critical missing implementation** that must be addressed in Phase 3.

### Depth Source Interface

Depth sources must provide:

```python
class DepthSource:
    def get_filtered_depth_frame(self) -> np.ndarray | None:
        """Returns depth in meters as HxW float32, or None if unavailable."""
```

The plugin normalizes depth using hard-coded range `[0.3, 4.0]` meters.

### Audio Reactor Interface

Audio reactor must provide:

```python
class AudioReactor:
    def get_feature_level(self, feature: AudioFeature) -> float:
        """Returns normalized level 0.0-1.0 for the given feature."""
```

Supported features: `AudioFeature.BASS`, `AudioFeature.MID`, `AudioFeature.TREBLE`.

### Output

- **Color buffer:** Written to the currently bound FBO (typically the effect chain's output)
- **Alpha:** Always 1.0 (`fragColor.a = 1.0`)
- **No separate depth output** — Depth is only used internally

---

## Edge Cases and Error Handling

### Missing Depth Sources

If `depth_sources[i]` is `None` or `get_filtered_depth_frame()` returns `None`:

- The corresponding `depth_tex{i}` texture is **not updated** (remains at previous frame or 0)
- The shader still samples the texture unit; if texture ID is 0, GL returns `(0,0,0,1)` black
- This results in that depth channel contributing zero to `depth0`/`depth1`, effectively disabling dual-depth effects

**Recommended handling:** Ensure at least one depth source is always connected. The effect degrades gracefully but loses core functionality.

### Audio Reactor Not Set

If `self.audio_reactor` is `None`:

- `_apply_audio_modulation()` does nothing
- Parameters remain at their static values from `self.parameters`
- The effect still runs, but audio reactivity is disabled
- No error or warning is logged

**Recommended handling:** Set audio reactor during effect chain initialization.

### Feedback Textures Not Created

The legacy code **allocates** `self.feedback_textures = [0,0,0,0,0,0]` but **never creates** the GL textures or renders into them. The shader samples `feedback1-6` uniforms, but if all texture IDs are 0, the feedback stage contributes nothing (returns black).

This is a **critical bug** in the legacy implementation. The effect will compile and run but the "neural feedback" feature is non-functional.

**Phase 3 fix required:** Implement feedback texture creation, ping-pong FBO management, and feedback pass rendering.

### Texture Unit Exhaustion

The effect uses **11 texture units** (0-10). Modern GL supports at least 32, but some embedded systems may have fewer. If the effect chain already uses many textures, this could exceed the hardware limit and cause `GL_INVALID_OPERATION`.

**Mitigation:** VJLive3's effect chain should query `GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS` and fail gracefully if exceeded.

### Shader Compilation Failure

If `_generate_mosh_shader()` produces invalid GLSL, `super().__init__()` will attempt to compile and likely fail. The base `Effect` class should handle this by:

- Logging the shader info log
- Setting `self.shader = None` or raising an exception
- The effect chain should detect and skip broken effects

**Edge case:** The shader references `lightStreaks` uniform in `_apply_audio_modulation()` but the shader does **not** declare `lightStreaks`. This will cause `glGetUniformLocation` to return -1, and `set_uniform` may log a warning but should not crash.

### Time Wrap

`mosh_position` uses `fract()` to wrap to `[0,1)`. After ~2 billion seconds (63 years at 1.0 speed), floating-point precision may cause visible jumps, but this is not a practical concern.

### Parameter Out of Range

The legacy code does **not** clamp parameters to `[0,10]` in `_apply_mosh_uniforms()`. If a user sets `masterIntensity = 100.0`, the shader receives `100.0` (not normalized), causing extreme brightness or overflow.

**Recommended fix:** Clamp all parameters in `_initialize_mosh_parameters()` and in any setter methods (not present in legacy code).

---

## Mathematical Formulations

### Depth Normalization

```python
depth_normalized = np.clip((depth_meters - 0.3) / (4.0 - 0.3), 0.0, 1.0)
```

- Input: `depth_meters` in range approximately `[0.3, 4.0]` (Astra depth range)
- Output: `[0.0, 1.0]` where 0 = 0.3m (near), 1 = 4.0m (far)

**Note:** This linear mapping does not account for depth noise at range extremes. A better approach would use a sigmoid or adaptive histogram equalization, but the legacy code uses simple clipping.

### Mosh Displacement

```glsl
float depthDiff = abs(depth0 - depth1);
float displacement = depthDiff * displacementStrength * 0.1;
vec2 displacedUV = uv + vec2(displacement, displacement * 0.5);
```

- `displacementStrength` is a parameter (0-10) normalized to 0-1 in uniform
- The `0.1` factor scales the maximum displacement to ~0.1 UV units (10% of screen)
- The Y component is half the X, creating an anamorphic stretch effect
- If `chaosFactor > 0.5`, adds `hash(uv + time*0.1) * moshChaos * 0.05`

### Loop Modulation

```glsl
float loopLength = loopOut - loopIn;
float normalizedPos = fract((moshPos - loopIn) / loopLength);
if (loopModulation > 0.5) {
    float loopMod = sin(normalizedPos * 3.14159) * 0.1;
    displacedUV += vec2(loopMod, loopMod * 0.3);
}
```

- `loopIn` and `loopOut` are normalized positions (0-1)
- `moshPos` is a continuously increasing value (wrapped by `fract()` in Python)
- `normalizedPos` is the position within the loop segment, remapped to `[0,1)`
- `sin(normalizedPos * π)` creates a half-cycle sine wave peaking at the loop midpoint
- This adds a subtle oscillatory motion that "breathes" with the loop cycle

### Synesthetic Color Mapping

```glsl
vec3 getSynestheticColor(float audioFeature) {
    float hue = fract(audioFeature * 10.0 + time * 0.1);
    float saturation = 0.8 + sin(time * 2.0) * 0.2;
    float value = 0.6 + sin(time * 3.0) * 0.4;
    return hsv_to_rgb(vec3(hue, saturation, value));
}
```

- `audioFeature` is derived from `fract(time * 5.0 + depth * 2.0)` for treble glow
- Hue cycles with `audioFeature * 10` (10 hues per unit) plus slow time drift
- Saturation and value oscillate independently at 2Hz and 3Hz respectively
- The HSV→RGB conversion uses the standard `mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y)` algorithm

### Collective Beat

```glsl
float beat = step(fract(time * 2.0), 0.5);
result.rgb *= mix(0.8, 1.2, beat);
```

- `time * 2.0` creates a 0.5 Hz beat (120 BPM)
- `step(..., 0.5)` yields 1.0 for the first half of each beat cycle, 0.0 for the second half
- Multiplies RGB by 1.2 on the "beat" and 0.8 off-beat, creating a strobe-like effect

### Neural Feedback Mix

```python
feedback = sum(sampleFeedback(i, feedbackUV) for i in 1..6)
result = mix(input, feedback / 6, neuralFeedback)
```

- Averages all 6 feedback channels
- `neuralFeedback` uniform (0-1) controls blend factor: 0 = pure input, 1 = pure feedback
- Feedback UV coordinates are offset by `neuralSync` and `collectiveConsciousness` effects

---

## Performance Characteristics

### Texture Memory

- **2 depth textures** — R8 format, resolution = render resolution (e.g., 1920×1080 = 2.1 MB each)
- **6 feedback textures** — RGBA8 format, same resolution = 8.4 MB each = **50.4 MB total**
- **1 output texture** — RGBA8, same resolution = 8.4 MB (managed by effect chain)
- **Total plugin-owned memory:** ~54.6 MB at 1080p

**⚠️ Critical:** The legacy code does NOT allocate the 6 feedback textures. They remain at ID 0, so no memory is consumed, but the feature is broken.

### GPU Operations Per Frame

1. **Depth texture uploads** — 2× `glTexImage2D` (or `glTexSubImage2D` if using persistent textures) with `GL_RED` format
2. **Feedback texture reads** — 6× texture fetches per pixel in the feedback loop (worst case)
3. **Main shader execution** — Complex fragment shader with:
   - 13 texture reads (tex0-tex2, texPrev, depth_tex0-1, feedback1-6) = **13 taps**
   - Multiple conditionals based on feature flags (branch divergence)
   - HSV conversion, hash function, trigonometric functions
4. **Uniform uploads** — ~30 uniform calls per frame

### Computational Complexity

The fragment shader's arithmetic intensity is **high**:

- **Without feedback optimization:** 13 texture reads per pixel
- **With feedback:** Each feedback channel samples with potentially different UV offsets, but the loop is unrolled and all 6 are always sampled (even if `neuralFeedback` is 0, the loop still runs)
- **Total texture bandwidth:** At 1080p (2.1M pixels), 13 taps = **27.3 Gpixels/sec** at 60 FPS, assuming 4 bytes/pixel = **104 GB/s** bandwidth requirement

This is **extremely high** and will likely bottleneck on memory bandwidth on integrated GPUs. The legacy code may have intended conditional feedback sampling but the loop is unconditional.

### Optimization Opportunities

1. **Early-out in feedback loop** — If `neuralFeedback` is near 0, skip feedback sampling (not implemented)
2. **Feedback texture format** — Use `GL_RGBA16F` for better quality, but that increases bandwidth
3. **Depth texture resolution** — Depth could be half-resolution (e.g., 960×540) since it's only used for modulation, not display
4. **Feedback channel count** — Make `max_feedback_channels` configurable; 6 is overkill for many use cases
5. **Mosh position update** — Currently updated every frame; could be audio-synced only

---

## Test Plan

### Unit Tests (Minimum 80% Coverage)

#### Test 1: Constructor and Initialization

```python
def test_depth_mosh_nexus_initialization():
    nexus = DepthMoshNexus()
    
    # Check default parameters
    assert nexus.parameters['masterIntensity'] == 10.0
    assert nexus.parameters['moshIntensity'] == 10.0
    assert nexus.parameters['loopIn'] == 0.0
    assert nexus.parameters['loopOut'] == 1.0
    
    # Check state
    assert nexus.mosh_state['intensity'] == 0.0  # Not updated until apply_uniforms
    assert nexus.mosh_state['mosh_position'] == 0.0
    assert len(nexus.depth_textures) == 2
    assert len(nexus.feedback_textures) == 6
    
    # Check shader compiled
    assert nexus.shader is not None
    assert nexus.shader.program != 0
```

#### Test 2: Audio Reactor Integration

```python
def test_audio_modulation():
    nexus = DepthMoshNexus()
    
    class MockAudioReactor:
        def get_feature_level(self, feature):
            levels = {
                AudioFeature.BASS: 0.8,
                AudioFeature.MID: 0.5,
                AudioFeature.TREBLE: 0.3
            }
            return levels[feature]
    
    nexus.set_audio_reactor(MockAudioReactor())
    nexus.apply_uniforms(time_val=0.0, resolution=(1920, 1080))
    
    # Audio modulation should have overridden some parameters
    # masterIntensity = 5.0 + 0.8*5.0 = 9.0 → 0.9 after normalization
    # Check via shader uniform query or mock
```

#### Test 3: Depth Source Handling

```python
def test_depth_source_updates():
    nexus = DepthMoshNexus()
    
    class MockDepthSource:
        def get_filtered_depth_frame(self):
            # Return 640x480 depth in meters
            return np.random.uniform(0.5, 3.0, (480, 640)).astype(np.float32)
    
    nexus.set_depth_sources([MockDepthSource(), MockDepthSource()])
    
    # First apply_uniforms should create textures and upload
    nexus.apply_uniforms(time_val=0.0, resolution=(640, 480))
    
    # Verify texture IDs are non-zero
    assert nexus.depth_textures[0] != 0
    assert nexus.depth_textures[1] != 0
```

#### Test 4: State Evolution

```python
def test_mosh_state_evolution():
    nexus = DepthMoshNexus()
    
    # Simulate 30 seconds of rave time
    start = time.time()
    nexus.apply_uniforms(time_val=start, resolution=(1920, 1080))
    time.sleep(0.1)
    nexus.apply_uniforms(time_val=start + 30.0, resolution=(1920, 1080))
    
    # Intensity should have increased
    assert nexus.mosh_state['intensity'] > 3.0
    assert nexus.mosh_state['time_in_rave'] > 29.0
    assert nexus.mosh_state['mosh_position'] > 0.0
```

#### Test 5: Shader Uniforms

```python
def test_shader_uniforms_set():
    nexus = DepthMoshNexus()
    nexus.apply_uniforms(time_val=1.0, resolution=(1920, 1080))
    
    # Query a few uniforms to ensure they were set
    # (requires shader mock or introspection)
    master_intensity = nexus.shader.get_uniform_f('masterIntensity')
    assert master_intensity == 10.0  # Default, not audio-modulated
    
    # With audio reactor, should be different
    # ...
```

#### Test 6: Loop Normalization

```python
def test_loop_normalization():
    nexus = DepthMoshNexus()
    nexus.parameters['loopIn'] = 0.2
    nexus.parameters['loopOut'] = 0.8
    nexus.mosh_state['mosh_position'] = 0.5
    
    # The normalizedPos in shader should be (0.5 - 0.2) / (0.8 - 0.2) = 0.5
    # This is hard to test without shader introspection; test via visual output
```

### Integration Tests

1. **Dual-depth rendering test** — Render a known depth pattern (e.g., gradient) through both depth sources and verify displacement direction matches depth gradient
2. **Audio sync test** — Feed synthetic audio with known BASS envelope and verify `masterIntensity` uniform tracks it
3. **Feedback accumulation test** — Render same frame repeatedly with `neuralFeedback = 1.0` and verify output accumulates previous frames (requires feedback textures to be implemented)
4. **Loop behavior test** — Set `loopIn=0.3`, `loopOut=0.7`, animate `mosh_position` from 0→1, verify mosh effects repeat within that segment and are clamped outside

### Visual Regression

Given the artistic nature of the effect, automated pixel-diff tests are not meaningful. Instead:

- Provide a set of **golden reference images** for standard parameter sets (Underground Rave preset, 10-second animation)
- Use structural similarity index (SSIM) with threshold >0.95 for regression detection
- Flag images for manual review if SSIM < 0.90

---

## Mathematical Formulations

### Depth Displacement Field

The UV displacement is computed as:

```
d = |d0 - d1| × s × 0.1 + ξ × c × 0.05
Δu = d
Δv = d × 0.5
```

where:
- `d0, d1` ∈ [0,1] are normalized depth values
- `s` = `displacementStrength` ∈ [0,1] (from parameter /10)
- `c` = `moshChaos` ∈ [0,1]
- `ξ` = `hash(uv + time×0.1)` ∈ [0,1) pseudo-random

The anamorphic factor (0.5 on V) creates a horizontal stretch bias.

### Loop Modulation Envelope

The loop modulation adds a sinusoidal offset:

```
L(p) = sin(π × ((p - Lin) / (Lout - Lin)))
Δu += L(p) × 0.1
Δv += L(p) × 0.03
```

where `p` = `mosh_position` ∈ [0,1), `Lin`, `Lout` ∈ [0,1] define the active loop segment.

This creates a smooth "breathing" motion that peaks at the loop midpoint and returns to zero at the boundaries, ensuring seamless looping when `mosh_position` wraps.

### Synesthetic Color Generation

Audio feature `a` ∈ [0,1] is mapped to HSV:

```
h = fract(a × 10 + t × 0.1)
s = 0.8 + sin(t × 2) × 0.2
v = 0.6 + sin(t × 3) × 0.4
```

The hue cycles rapidly with audio feature and drifts slowly with time. Saturation and value oscillate at 2 Hz and 3 Hz respectively, creating a shimmering effect.

### Collective Beat Strobe

```
b = step(fract(t × 2), 0.5)
RGB *= mix(0.8, 1.2, b)
```

At 2 Hz (120 BPM), the image alternates between 80% and 120% brightness on each half-beat, creating a strobe synchronized to the beat.

### Neural Feedback Mix

For each feedback channel `i` with UV offset:

```
uv_i = uv + offset(depth0, depth1, neuralSync, consciousnessFlow)
fb_i = texture(feedback_i, uv_i)
fb_avg = (1/6) Σ fb_i
output = mix(input, fb_avg, neuralFeedback)
```

The offset depends on:

```glsl
if (neuralSync > 0.5) {
    float syncFactor = fract((depth0 + depth1) * 4.0 + time * 0.2);
    feedbackUV += vec2(sin(syncFactor * π) * 0.03, cos(syncFactor * π) * 0.03);
}
```

This creates a depth-dependent wobble that synchronizes across channels when `neuralSync` is high.

---

## Performance Characteristics

### Bottlenecks

1. **Texture bandwidth** — 13 simultaneous texture reads at full resolution is extremely high. At 1920×1080 × 60 FPS × 13 taps × 4 bytes = **~104 GB/s** required. This exceeds many integrated GPUs (Intel UHD: ~30-50 GB/s).
2. **Feedback texture writes** — Not implemented, but if they were, would require 6 additional render passes or multi-target MRT, further increasing bandwidth.
3. **Fragment shader complexity** — Multiple `if` blocks with texture reads inside cause branch divergence. On NVIDIA/AMD GPUs, this is less critical; on mobile GPUs (Adreno, Mali), it can cause significant slowdown.

### Memory Footprint

- **GPU memory:** ~55 MB for feedback textures (if implemented) + 2 depth textures (~4.2 MB) = ~60 MB at 1080p
- **CPU memory:** Negligible (state dictionaries, parameter arrays)

### Optimization Recommendations

1. **Reduce feedback channels** — Default to 2 or 3, make configurable via `max_feedback_channels`
2. **Half-resolution depth** — Depth textures can be ½ or ¼ resolution since they're only used for modulation
3. **Conditional feedback sampling** — In shader, if `neuralFeedback < 0.01`, skip the entire feedback loop
4. **Texture format optimization** — Use `GL_R8` for depth (already done) and `GL_RGBA8` for feedback (good)
5. **Precision** — Use `mediump float` in fragment shader for mobile GPUs (not `highp`)

---

## Legacy Code References

The implementation is derived from:

- **Primary source:** `/home/happy/Desktop/claude projects/vjlive/plugins/vdepth/depth_mosh_nexus.py`
- **Configuration:** `/home/happy/Desktop/claude projects/vjlive/plugins/vdepth/depth_mosh_nexus_config.ini`
- **Related concepts in Qdrant:**
  - `DepthModulatedDatamosh` — Basic depth-driven displacement
  - `DepthFeedbackMatrixDatamosh` — Multi-tap feedback (similar but separate)
  - `DepthGroovyDatamosh` — Psychedelic effects with audio reactivity
  - `QuantumDepthNexus` — More advanced version (may be superset)

**Known discrepancies:**
- The config file defines `light_streaks` parameter, but the shader uses `trebleGlow`. The Python code sets `lightStreaks` uniform which does not exist in the shader.
- The config defines `max_feedback_channels = 6` but the code never creates feedback textures.
- The config defines `mosh_chaos_base` and `mosh_chaos_audio_mod` but these are not used in the Python code; instead `mosh_chaos` is computed directly from `collective_consciousness`.

---

## Definition of Done

- [ ] Spec reviewed by Manager or User before code starts
- [ ] All tests listed above pass (≥80% coverage)
- [ ] No file over 750 lines
- [ ] No stubs in code (all functions implemented)
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-EXT058: DepthMoshNexus` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---
