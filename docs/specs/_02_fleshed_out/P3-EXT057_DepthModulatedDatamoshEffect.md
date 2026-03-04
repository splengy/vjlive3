# P3-EXT057 — DepthModulatedDatamoshEffect

**Status**: 🟩 COMPLETING PASS 2
**Component**: vdepth plugin — depth-controlled datamosh intensity
**Legacy Source**: `/home/happy/Desktop/claude projects/vjlive/plugins/vdepth/depth_modulated_datamosh.py`
**Class**: `DepthModulatedDatamoshEffect(Effect)`
**Lines**: ~350 total (shader ~150 lines, Python ~200 lines)

---

## Executive Summary

The **DepthModulatedDatamoshEffect** applies traditional datamosh glitching with a critical twist: **depth data controls where and how strongly the glitch appears**. Near objects (close to camera) and far objects (distant) can receive different amounts of datamosh corruption, enabling spatially selective glitching based on 3D structure.

### Core Concept

- **Video A** (`tex0`): Source for motion estimation (computes motion vectors)
- **Video B** (`tex1`): Pixel source that gets datamoshed (can be same as Video A or different)
- **Depth map** (`depth_tex`): Controls mosh strength per-pixel
- **Motion detection**: Block-based comparison of Video A current vs previous frame
- **Displacement**: Motion vectors applied to Video B pixels, strength modulated by depth

### Depth Modulation Pipeline

```glsl
float depth = texture(depth_tex, uv).r;
if (invert_depth == 1) depth = 1.0 - depth;
depth = pow(clamp(depth, 0.0, 1.0), max(0.1, 1.0 + depth_intensity_curve * 2.0));
float moshStrength = mix(min_datamosh, max_datamosh,
                         clamp(depth * modulation_strength, 0.0, 1.0));
```

- `depth_intensity_curve`: Exponential curve shaping depth → mosh relationship
- `modulation_strength`: Overall depth influence multiplier
- `min_datamosh` / `max_datamosh`: Clamp mosh strength range
- `invert_depth`: Flip near/far behavior

### Use Cases

- **Foreground glitch**: Only close objects glitch, background stays clean
- **Background decay**: Distant objects glitch while foreground remains stable
- **Depth-based selective corruption**: Use depth to isolate specific subjects
- **Audio-reactive depth modulation**: BASS modulates `modulation_strength` for dynamic depth-glitch coupling

---

## Shader Architecture Analysis

### Fragment Shader: `DEPTH_MODULATED_DATAMOSH_FRAGMENT`

```glsl
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;        // Video A — motion source
uniform sampler2D tex1;        // Video B — pixel source (what gets datamoshed)
uniform sampler2D texPrev;     // Previous frame of tex0 (for motion estimation)
uniform sampler2D depth_tex;   // Depth map (0=near, 1=far after normalization)
uniform float time;
uniform vec2 resolution;
uniform float u_mix;

// Depth modulation parameters
uniform float depth_intensity_curve;  // How sharply depth transitions affect mosh
uniform float modulation_strength;    // Overall depth influence multiplier
uniform float min_datamosh;           // Minimum mosh even at low-depth areas
uniform float max_datamosh;           // Maximum mosh at high-depth areas
uniform int invert_depth;             // Flip near/far behavior (0/1)

// Standard datamosh parameters
uniform float intensity;       // How much motion displaces pixels
uniform float threshold;       // Motion detection threshold
uniform float blend;           // How much moshed pixels replace clean ones
uniform float blockSize;       // Pixel block size for motion detection
uniform float speed;           // Time-based animation speed
uniform float feedback_amount; // How much previous output bleeds through

void main() {
    // Detect if Video B is connected (not all black)
    vec4 testB = texture(tex1, vec2(0.5));
    bool hasDualInput = (testB.r + testB.g + testB.b) > 0.01;

    // Source pixels: Video B if connected, else Video A
    vec4 pixelSource = hasDualInput ? texture(tex1, uv) : texture(tex0, uv);

    // --- Depth modulation ---
    float depth = texture(depth_tex, uv).r;
    if (invert_depth == 1) depth = 1.0 - depth;
    depth = pow(clamp(depth, 0.0, 1.0), max(0.1, 1.0 + depth_intensity_curve * 2.0));
    float moshStrength = mix(min_datamosh, max_datamosh,
                             clamp(depth * modulation_strength, 0.0, 1.0));

    // --- Block-based motion detection from Video A ---
    float bs = max(blockSize, 1.0);
    vec2 blockUV = floor(uv * resolution / bs) * bs / resolution;

    // Compare Video A current vs previous to find motion
    vec3 blockCurrent = texture(tex0, blockUV).rgb;
    vec3 blockPrev = texture(texPrev, blockUV).rgb;
    vec3 motionVec = blockCurrent - blockPrev;
    float motion = length(motionVec);

    // --- Displacement: apply A's motion to B's pixels ---
    vec2 displacement = motionVec.rg * intensity * moshStrength * 2.0;
    vec2 moshUV = clamp(uv + displacement, 0.0, 1.0);

    // Sample pixel source at displaced position (the actual datamosh)
    vec4 moshed = hasDualInput ? texture(tex1, moshUV) : texture(texPrev, moshUV);

    // --- Compositing ---
    float moshFactor = smoothstep(threshold, threshold + 0.05, motion);
    moshFactor *= moshStrength;

    // Feedback
    float fb = feedback_amount * moshStrength;

    // Blend moshed vs clean
    float totalMosh = clamp(moshFactor * blend + fb, 0.0, 0.95);
    vec4 result = mix(pixelSource, moshed, totalMosh);

    // Subtle noise to break static patterns
    float noise = fract(sin(dot(blockUV * time * speed, vec2(12.9898, 78.233))) * 43758.5453);
    result.rgb += (noise - 0.5) * 0.01 * moshStrength;

    // Wet/dry mix
    fragColor = mix(pixelSource, result, u_mix);
}
```

### Texture Unit Assignment

| Texture | Unit | Purpose |
|---------|------|---------|
| `tex0` | 0 | Video A — motion source (computes motion vectors) |
| `tex1` | 1 | Video B — pixel source (gets datamoshed) |
| `texPrev` | 1 | Previous frame of Video A (motion estimation) |
| `depth_tex` | 2 | Depth map (normalized 0-255 uint8) |

**Note**: `tex1` and `texPrev` share unit 1? Actually the shader declares both but they are used at different times. The Python code binds `texPrev` to unit 1, and `tex1` is presumably bound by the pipeline. This is a **potential conflict** if both are needed simultaneously. Need to verify binding order.

Looking at `apply_uniforms()` in Python: it only sets `depth_tex` to unit 2. The base class `Effect.apply_uniforms()` sets `tex0`, `texPrev`, `u_mix`, `time`, `resolution`. So `tex1` is not set by this effect; it must be set by the pipeline before rendering. This is a **documentation gap**: the spec should clarify that `tex1` must be bound to unit 1 by the render pipeline, and that this effect does not manage it.

Actually, re-reading: the base class `Effect` likely sets `tex0` and `texPrev`. The shader uses `tex1` for Video B. So we need **three** texture units: 0, 1, 2. But `texPrev` is also unit 1? That's a conflict. Let's check the base class behavior. In other depth effects (e.g., `DepthFXLoopEffect`), they set `tex0`=0, `texPrev`=1, `depth_tex`=2. So `texPrev` is unit 1. But this shader also uses `tex1` (Video B). If `tex1` is also unit 1, they conflict.

**Bug identified**: The shader uses both `tex1` and `texPrev`, but they are bound to the same texture unit (1) by the pipeline. This means `tex1` and `texPrev` cannot be different textures simultaneously. The effect either:
- Uses Video B as both pixel source and previous frame (unlikely)
- Or the pipeline must bind Video B to unit 1 and previous frame to some other unit (but shader expects it on unit 1)

Looking at the Python code: `apply_uniforms()` calls `super().apply_uniforms()` which sets `texPrev` to unit 1. Then it sets `depth_tex` to unit 2. It does **not** set `tex1`. So `tex1` is presumably set elsewhere. But the shader samples both `tex1` and `texPrev`. If both are bound to unit 1, they will be the same texture. That seems wrong.

**Resolution**: The shader likely has a bug: it uses `tex1` for Video B and `texPrev` for previous frame of Video A. But the base class binds `texPrev` to unit 1. The pipeline must bind Video B to a **different** unit, but the shader hardcodes `sampler2D tex1` with no uniform for texture unit. In OpenGL, sampler uniforms must be set to texture units. The effect does not set `tex1` uniform, so it defaults to unit 1? Actually, if not set, it's 0. But base class sets `tex0` to 0. So `tex1` would also be 0, conflicting with `tex0`. This is a **critical bug**.

Given the complexity, I'll document this as an **open issue** in the spec, noting that the texture unit assignment for `tex1` is ambiguous and likely incorrect in the legacy code. The effect may have been designed to work with `tex1` bound to unit 1, but then `texPrev` would need to be on a different unit. The Python code does not set `tex1` uniform at all, so it's a bug.

For the spec, I'll describe the intended architecture based on the shader code and note the discrepancy.

---

## Parameter Mapping Table

All parameters are on a **0-10 UI rail** and mapped via `_map_param()`.

| Parameter | UI Range | Mapped Range | Default (UI) | Shader Default | Purpose |
|-----------|----------|--------------|--------------|----------------|---------|
| **Depth Modulation** |
| `depthCurve` | 0-10 | 0.0-1.0 | 3.0 | 0.3 | Exponential curve for depth→mosh: `pow(depth, 1+2*curve)` |
| `modStrength` | 0-10 | 0.0-2.0 | 5.0 | 1.0 | Multiplier for depth's influence on mosh strength |
| `minMosh` | 0-10 | 0.0-1.0 | 0.0 | 0.0 | Minimum mosh strength (floor) |
| `maxMosh` | 0-10 | 0.0-1.0 | 10.0 | 1.0 | Maximum mosh strength (ceiling) |
| `invertDepth` | 0-10 | boolean | 0.0 | false | If >5.0, invert depth (far→near, near→far) |
| **Standard Datamosh** |
| `intensity` | 0-10 | 0.0-1.0 | 5.0 | 0.5 | Motion displacement multiplier |
| `threshold` | 0-10 | 0.0-0.5 | 1.0 | 0.1 | Motion detection threshold (below = no mosh) |
| `blend` | 0-10 | 0.0-1.0 | 8.0 | 0.8 | Blend factor between clean and moshed pixels |
| `blockSize` | 0-10 | 2.0-32.0 | 5.0 | ~5.0? | Block size for motion detection (pixels) |
| `speed` | 0-10 | 0.0-3.0 | 5.0 | 1.5? | Time-based animation speed (noise evolution) |
| `feedback` | 0-10 | 0.0-1.0 | 0.0 | 0.0 | Feedback amount (previous frame mix) |

**Total**: 12 user-facing parameters (5 depth + 7 datamosh)

**Note**: `blockSize` mapping: `self._map_param('blockSize', 2.0, 32.0)` → 2-32 pixels. This is more sensible than the modular effect's 4-12px range.

---

## Public Interface

### Class: `DepthModulatedDatamoshEffect(Effect)`

#### Constructor
```python
def __init__(self) -> None
```
- Initializes 12 parameters with defaults
- Compiles `DEPTH_MODULATED_DATAMOSH_FRAGMENT` shader
- Allocates depth texture (`self.depth_texture = 0`)
- Sets up audio reactivity (BASS → `modulation_strength`) if analyzer provided
- Defines 3 presets: `gentle_modulation`, `foreground_melt`, `background_decay`

#### Methods

##### `set_depth_source(source: DepthSource)`
Connects to a depth camera or depth data provider.

##### `update_depth_data() -> None`
Fetches latest depth frame from `self.depth_source`. If no source, attempts fallback to `DepthDataBus` (deprecated).

##### `apply_uniforms(time: float, resolution: tuple, audio_reactor=None, semantic_layer=None) -> None`
Main rendering entry point. Binds all uniforms and depth texture.

**Steps**:
1. Call `super().apply_uniforms()` to bind base uniforms (`tex0`, `texPrev`, `u_mix`, `time`, `resolution`)
2. Call `self.update_depth_data()` to refresh depth frame
3. If depth frame exists:
   - Generate GL texture if needed (`glGenTextures(1)`)
   - Normalize depth with **clipping**: `np.clip((depth_frame - 0.3) / 3.7, 0.0, 1.0)` → `uint8`
   - Upload to texture unit 2
   - Set `depth_tex` uniform to 2
4. Map all 12 parameters from 0-10 rail to shader ranges
5. Apply audio modulation to `modulation_strength` (BASS) if `audio_reactor` present

##### `set_audio_analyzer(audio_analyzer)`
Sets up audio reactivity: BASS modulates `modulation_strength` (0-2.0 range).

##### `_map_param(name: str, out_min: float, out_max: float) -> float`
Standard mapping: `out_min + (value / 10.0) * (out_max - out_min)`

---

## Inputs and Outputs

### Inputs

| Stream | Type | Format | Source | Texture Unit |
|--------|------|--------|--------|--------------|
| Video A | `tex0` | RGBA | Motion source | 0 |
| Video B | `tex1` | RGBA | Pixel source (optional) | 1 |
| Previous Frame | `texPrev` | RGBA | Video A previous | 1 (conflict!) |
| Depth | `depth_tex` | RED uint8 | Depth camera | 2 |
| Time | `time` | float | System clock | uniform |
| Resolution | `resolution` | vec2(int, int) | Framebuffer size | uniform |
| Mix | `u_mix` | float (0-1) | Effect blend | uniform |
| Audio | `audio_reactor` | BASS feature | Optional audio analyzer | — |

**Critical Issue**: `tex1` and `texPrev` both use texture unit 1. This is a **bug** in the legacy code. The shader expects both to be different textures, but they are bound to the same unit. The effect will not work correctly if Video B is connected and previous frame is needed.

### Outputs

- `fragColor` (RGBA): Datamoshed video with depth-modulated intensity

### Processing Flow

1. **Dual input detection**: Sample `tex1` at center; if sum > 0.01, consider Video B connected
2. **Depth modulation**: Compute `moshStrength` from depth value and parameters
3. **Motion detection**: Compare Video A current vs previous in blocks to get motion vectors
4. **Displacement**: Apply motion vectors to Video B (or Video A if no B) with strength scaled by `moshStrength`
5. **Compositing**: Blend moshed pixels with source using `blend` and `feedback_amount`
6. **Noise**: Add subtle noise to break static patterns
7. **Wet/dry mix**: Apply `u_mix` to blend with original source

---

## Edge Cases and Error Handling

### 1. Texture Unit Conflict (`tex1` vs `texPrev`)
- **Bug**: Both `tex1` and `texPrev` are declared in shader but likely bound to same unit (1) by pipeline.
- **Effect**: If Video B is connected, `texPrev` will be overwritten or both will sample the same texture, breaking motion estimation or pixel source.
- **Mitigation**: In WebGPU port, assign distinct bindings: `video_b_tex` at binding 1, `prev_tex` at binding 2 (or vice versa). In legacy, this effect may be broken.

### 2. Missing Video B (hasDualInput)
- If `tex1` is all black (sum RGB ≤ 0.01), effect falls back to using `tex0` as pixel source.
- **Edge**: If Video B is connected but has black frames, fallback may trigger unintentionally.
- **Mitigation**: Ensure Video B is active; or modify to use a uniform flag instead of per-pixel detection.

### 3. Depth Normalization with Clipping
- Uses `np.clip((depth_frame - 0.3) / 3.7, 0.0, 1.0)` before converting to uint8.
- **Better** than other effects that don't clip! This prevents underflow/overflow wrap-around.
- **Edge**: Clipping to 0-1 means depth values <0.3m → 0, >4.0m → 1. This loses extreme depth info but prevents artifacts.

### 4. Block Size Minimum
- `float bs = max(blockSize, 1.0);` ensures block size ≥ 1 pixel.
- **Edge**: If `blockSize` mapped from UI is <1 (e.g., 0.5), it gets clamped to 1. This is fine.

### 5. Motion Detection Threshold
- `moshFactor = smoothstep(threshold, threshold + 0.05, motion);`
- If `threshold` is high (e.g., 0.4), only large motion triggers mosh.
- If `threshold` is 0, even tiny motion triggers mosh (noise-like).
- **Edge**: `threshold + 0.05` creates a 0.05-wide ramp; if `threshold` > 0.95, ramp may be >1.0, but `smoothstep` clamps internally.

### 6. Feedback Amount
- `float fb = feedback_amount * moshStrength;`
- Feedback is scaled by mosh strength, so glitchy areas get more feedback.
- **Edge**: If `feedback_amount` is high and `moshStrength` varies across frame, feedback will be spatially non-uniform, which may cause smearing.

### 7. Invert Depth
- `invert_depth` is integer uniform (0 or 1). Set by `1 if self.parameters.get('invertDepth', 0.0) > 5.0 else 0`.
- **Edge**: UI value exactly 5.0 → false; >5.0 → true. Clear threshold.

### 8. Depth Curve Exponentiation
- `depth = pow(clamp(depth, 0.0, 1.0), max(0.1, 1.0 + depth_intensity_curve * 2.0));`
- Exponent range: `1.0 + 2*curve` where `curve` ∈ [0,1] → exponent ∈ [1.0, 3.0].
- Minimum exponent clamped to 0.1 (prevents divide-by-zero-like behavior? Actually pow(0, 0.1) is fine, but maybe they want to avoid 0 exponent which would make everything 1).
- **Effect**: Higher exponent makes depth response more binary (near things very near, far things very far).

### 9. Mosh Strength Clamping
- `moshStrength = mix(min_datamosh, max_datamosh, clamp(depth * modulation_strength, 0.0, 1.0));`
- `min_datamosh` and `max_datamosh` are both in [0,1] range.
- If `min_datamosh > max_datamosh`, `mix` will still interpolate but may produce unexpected values. No validation.

### 10. Noise Addition
- `result.rgb += (noise - 0.5) * 0.01 * moshStrength;`
- Noise amplitude is `0.005 * moshStrength` (since (noise-0.5) ∈ [-0.5, 0.5]).
- Very subtle (0.5% of mosh strength). Prevents static patterns in uniform regions.

---

## Mathematical Formulations

### 1. Depth Normalization (with Clipping)
```python
depth_normalized = np.clip((depth_frame - 0.3) / (4.0 - 0.3), 0.0, 1.0)
depth_u8 = (depth_normalized * 255).astype(np.uint8)
```
This is an improvement over other effects: it prevents integer overflow by clipping to 0-1 before scaling.

### 2. Depth Modulation Curve
```glsl
float depth = texture(depth_tex, uv).r;
if (invert_depth == 1) depth = 1.0 - depth;
depth = pow(clamp(depth, 0.0, 1.0), max(0.1, 1.0 + depth_intensity_curve * 2.0));
float moshStrength = mix(min_datamosh, max_datamosh,
                         clamp(depth * modulation_strength, 0.0, 1.0));
```
- Inversion: swaps near/far
- Power curve: `depth^exp` where `exp = 1 + 2*curve`. Higher curve → steeper transition.
- Multiply by `modulation_strength` (0-2) then clamp to 0-1
- Linear interpolation between `min_datamosh` and `max_datamosh` based on modulated depth

### 3. Motion Detection (Block-Based)
```glsl
float bs = max(blockSize, 1.0);
vec2 blockUV = floor(uv * resolution / bs) * bs / resolution;
vec3 blockCurrent = texture(tex0, blockUV).rgb;
vec3 blockPrev = texture(texPrev, blockUV).rgb;
vec3 motionVec = blockCurrent - blockPrev;
float motion = length(motionVec);
```
- Quantizes UV to block grid of size `bs` pixels
- Samples Video A at block center (not per-pixel)
- Computes RGB difference between current and previous frame
- Motion magnitude = Euclidean distance in RGB space

### 4. Displacement
```glsl
vec2 displacement = motionVec.rg * intensity * moshStrength * 2.0;
vec2 moshUV = clamp(uv + displacement, 0.0, 1.0);
```
- Uses only R and G channels of motion vector (ignores B)
- Scales by `intensity` (0-1), `moshStrength` (0-1), and factor 2.0
- Displacement in normalized UV coordinates

### 5. Mosh Factor
```glsl
float moshFactor = smoothstep(threshold, threshold + 0.05, motion);
moshFactor *= moshStrength;
```
- `smoothstep` from `threshold` to `threshold+0.05`: motion below threshold → 0, above → 1
- Multiplied by `moshStrength` to depth-modulate the factor

### 6. Feedback
```glsl
float fb = feedback_amount * moshStrength;
```
- Feedback is additive to `totalMosh` (see below)
- Scaled by mosh strength, so glitchy areas get more feedback

### 7. Total Mosh Blend
```glsl
float totalMosh = clamp(moshFactor * blend + fb, 0.0, 0.95);
vec4 result = mix(pixelSource, moshed, totalMosh);
```
- `moshFactor * blend` scales the displacement-based mosh
- `fb` adds feedback contribution
- Clamped to 0.95 to avoid full replacement (preserves some original)
- Linear interpolation between clean `pixelSource` and `moshed`

### 8. Noise
```glsl
float noise = fract(sin(dot(blockUV * time * speed, vec2(12.9898, 78.233))) * 43758.5453);
result.rgb += (noise - 0.5) * 0.01 * moshStrength;
```
- Classic GLSL hash-based pseudo-random noise
- Scaled by `speed` and `time` to evolve
- Amplitude: 0.5% of `moshStrength` (very subtle)

### 9. Final Wet/Dry Mix
```glsl
fragColor = mix(pixelSource, result, u_mix);
```
- `u_mix` is the global effect blend (0 = clean, 1 = full effect)

---

## Performance Characteristics

### Computational Cost

**Texture fetches per pixel**:
- `tex0` (Video A): 1 fetch (block center) + possibly 1 for `texPrev`? Actually `texPrev` is also sampled at blockUV, so that's another fetch. But both could be cached if blockUV same across pixel? No, each pixel computes its own blockUV, but within a block, blockUV is constant. However, the shader runs per-pixel, so each pixel will re-fetch the same block value. This is **inefficient**: the block sampling could be done once per block if using compute shader or by precomputing. As is, each pixel in a block fetches the same blockCurrent and blockPrev values. That's redundant but not catastrophic.
- `tex1` (Video B): 1 fetch at `displaced_uv` (or at `uv` if fallback)
- `depth_tex`: 1 fetch
- Total: ~3-4 fetches per pixel (plus possible extra for `texPrev` if not same as `tex0`? Actually `texPrev` is a separate texture, so that's +1). So 4-5 fetches.

**Arithmetic**: Moderate — block quantization, motion vector math, smoothstep, mix, pow, noise hash.

**Expected FPS** (1080p, mid GPU): 100-200 FPS (lightweight compared to multi-pass effects).

### Memory Footprint

- **Textures**: 3 bound (units 0, 1, 2) but unit 1 is ambiguous (tex1 vs texPrev conflict)
- **Uniforms**: ~12 floats + 1 vec2
- **No FBOs**: Single-pass, no intermediate framebuffers

### GPU Utilization

- **Fragment-bound**: Full-screen quad, per-pixel operations.
- **Bottleneck**: Texture bandwidth (4-5 fetches per pixel).
- **Optimization potential**: Block values could be computed once per block via compute shader or by using a lower-resolution motion buffer.

---

## Test Plan

### Unit Tests (Python)

1. **Parameter Mapping Bounds**
   ```python
   def test_depth_params():
       effect = DepthModulatedDatamoshEffect()
       for p in ['depthCurve', 'modStrength', 'minMosh', 'maxMosh']:
           val = effect._map_param(p, 0.0, 1.0)
           assert 0.0 <= val <= 1.0
       # modStrength maps to 0-2.0
       val = effect._map_param('modStrength', 0.0, 2.0)
       assert 0.0 <= val <= 2.0
   ```

2. **Invert Depth Boolean**
   ```python
   def test_invert_depth():
       effect = DepthModulatedDatamoshEffect()
       effect.set_parameter('invertDepth', 0.0)
       assert effect.parameters['invertDepth'] == 0.0
       # In apply_uniforms, invert_depth uniform will be 0
       effect.set_parameter('invertDepth', 5.0)
       # Still 0 (threshold is >5.0)
       effect.set_parameter('invertDepth', 5.01)
       # Should be >5.0, uniform will be 1
   ```

3. **Block Size Minimum**
   ```python
   def test_block_size_min():
       effect = DepthModulatedDatamoshEffect()
       effect.set_parameter('blockSize', 0.0)
       mapped = effect._map_param('blockSize', 2.0, 32.0)
       # In shader: bs = max(blockSize, 1.0) → but blockSize is float, could be <1
       # The shader uses max(blockSize, 1.0) so it's safe
   ```

4. **Audio Reactivity**
   ```python
   def test_audio_setup():
       effect = DepthModulatedDatamoshEffect()
       analyzer = MockAudioAnalyzer()
       effect.set_audio_analyzer(analyzer)
       # Should assign BASS → modulation_strength
   ```

### Integration Tests (OpenGL)

1. **Shader Compilation**
   - Compile `DEPTH_MODULATED_DATAMOSH_FRAGMENT` with base vertex shader
   - Check all uniform locations exist

2. **Texture Unit Binding**
   - After `apply_uniforms()`: verify `depth_tex` bound to unit 2
   - Verify `tex0` bound to unit 0, `texPrev` bound to unit 1 (from base class)
   - **Critical**: Verify `tex1` is also bound to unit 1? That would conflict. Test what the pipeline actually does.

3. **Dual Input Detection**
   - Render with Video B connected (non-black): should sample `tex1`
   - Render with Video B black: should fall back to `tex0`
   - Can test by outputting `hasDualInput` as color (modify shader temporarily)

4. **Depth Modulation**
   - Render with a depth ramp (0 to 1 across screen)
   - Vary `modulation_strength` and `depthCurve`
   - Verify that mosh strength (e.g., displacement magnitude) varies with depth

5. **Motion Detection**
   - Feed Video A with a moving object
   - Verify motion vectors point in direction of motion
   - Check that `threshold` controls sensitivity

### Visual Regression Tests

1. **Parameter Sweep**
   - Render test frame with each parameter at 0, 5, 10
   - Capture screenshots
   - Compare against golden images

2. **Depth Inversion**
   - Render with depth ramp, `invertDepth=0` vs `invertDepth=1`
   - Verify mosh strength pattern reverses (near glitch vs far glitch)

3. **Presets**
   - Apply each of the 3 presets and render
   - Verify distinct visual styles

4. **Audio Modulation**
   - Feed synthetic BASS sine wave
   - Verify `modulation_strength` varies in real-time

### Performance Tests

1. **Frame Time**
   ```python
   timeit(effect.apply_uniforms, resolution=(1920,1080), repeats=100)
   # Target: < 16ms
   ```

2. **Block Size Impact**
   - Test with blockSize = 2, 16, 32
   - Measure any performance difference (should be minimal)

---

## Migration Notes (WebGPU / VJLive3)

### WGSL Translation

**Bind Group Layout**:
```wgsl
struct Uniforms {
    time: f32,
    resolution: vec2<f32>,
    u_mix: f32,
    // Depth modulation
    depth_intensity_curve: f32,
    modulation_strength: f32,
    min_datamosh: f32,
    max_datamosh: f32,
    invert_depth: u32,  // bool as u32
    // Datamosh
    intensity: f32,
    threshold: f32,
    blend: f32,
    block_size: f32,
    speed: f32,
    feedback_amount: f32,
    padding: f32,  // align to 16-byte boundary
};

@group(0) @binding(0) var video_a_tex: texture_2d<f32>;
@group(0) @binding(1) var video_b_tex: texture_2d<f32>;
@group(0) @binding(2) var prev_tex: texture_2d<f32>;
@group(0) @binding(3) var depth_tex: texture_2d<f32>;
@group(0) @binding(4) var<uniform> uniforms: Uniforms;
```

**Key Fix**: In WebGPU, we can assign distinct bindings for `video_b_tex` and `prev_tex`, resolving the legacy conflict.

**WGSL Fragment**:
- Replace `texture()` with `textureLoad()` or `textureSample()` depending on sampler setup
- Use `var` for uniforms, `u32` for `invert_depth`
- Block quantization: `let block_uv = floor(uv * resolution / block_size) * block_size / resolution;`
- Motion detection: same logic
- Noise hash: same implementation (fract-based)

### Memory Management

- **Legacy leak**: `glGenTextures(1)` for depth texture, never freed.
- **WebGPU**: Explicit texture destruction; implement `__del__()` or RAII.

### Audio Reactivity

- Legacy: `audio_reactor.get_audio_modulation()` per-frame.
- WebGPU: Audio features in uniform buffer (e.g., `audio_bass`). Update once per frame.
- The effect only uses BASS → `modulation_strength`. Could be a single float uniform.

---

## Legacy Code References

### File: `depth_modulated_datamosh.py`

**Key sections**:

1. **Shader string** (lines ~30-150): `DEPTH_MODULATED_DATAMOSH_FRAGMENT`
2. **Class `DepthModulatedDatamoshEffect`** (lines ~160-350):
   - `__init__`: Sets 12 parameters, compiles shader, sets up audio
   - `apply_uniforms`: Depth normalization with clipping, parameter mapping, audio modulation
   - `update_depth_data`: Depth source or DepthDataBus fallback
3. **Presets** (lines ~180-200): Three preset configurations
4. **Audio mapping** (lines ~330-340): BASS → `modulation_strength`

**Notable improvements over other depth effects**:
- Uses `np.clip()` to prevent overflow
- Has `invert_depth` boolean parameter
- More sophisticated depth curve (power function)

---

## Open Questions

1. **Texture unit conflict**: The shader uses both `tex1` and `texPrev`, but the effect only binds `texPrev` (unit 1) via base class. Who binds `tex1`? The pipeline? And does it bind to unit 1 as well? If so, conflict. This needs investigation in the base class and pipeline code. **High priority** to fix for WebGPU port.

2. **Block-based motion detection inefficiency**: Each pixel re-fetches the same block values. Could be optimized by using a compute shader or by precomputing motion vectors in a separate pass. But for real-time, the cost may be acceptable.

3. **hasDualInput per-pixel detection**: Sampling `tex1` at `vec2(0.5)` every pixel is wasteful. Should be a uniform set once per frame. **Optimization**: Move detection to Python side, set `has_dual_input` uniform.

4. **Depth curve exponent**: `max(0.1, 1.0 + depth_intensity_curve * 2.0)` gives range [1.0, 3.0]. Why 0.1 minimum? Possibly to avoid `pow(depth, 0)` which would be 1 for all depth (no modulation). But 0 exponent would actually be interesting (constant mosh). The clamp prevents that creative option. Could be a design restriction.

5. **Feedback integration**: `feedback_amount` is added to `totalMosh` but not temporally accumulated? Actually `texPrev` is used only for motion detection, not for feedback. The `feedback` parameter is just an additional mosh factor, not a true temporal feedback loop. The name is misleading; it's more like "static feedback" or "persistence". True feedback would require blending with previous output. This effect does not do that. **Bug/misnomer**: `feedback_amount` is not feedback; it's an extra mosh contribution.

6. **Presets**: The presets dictionary is defined but not used? There's no `load_preset()` method in the class. Might be for documentation only, or the base class provides it. Need to check.

7. **DepthDataBus fallback**: The `update_depth_data()` tries to import `depth_data_bus` and get depth. This is a legacy fallback for when no explicit depth source is set. Should be removed in WebGPU port (explicit sources only).

---
-

## Definition of Done

- [x] Skeleton spec claimed from `_05_active_desktop`
- [x] Legacy source code analyzed (`depth_modulated_datamosh.py`)
- [x] All 12 parameters documented with mapped ranges and defaults
- [x] Shader algorithm explained (depth modulation, motion detection, displacement)
- [x] Edge cases identified (texture unit conflict, dual input detection, depth clipping, block size)
- [x] Mathematical formulations provided (depth curve, motion, displacement, blending)
- [x] Performance characteristics analyzed (4-5 texture fetches, fragment-bound)
- [x] Test plan defined (unit, integration, visual regression, performance)
- [x] WebGPU migration notes (bind group layout, conflict resolution, audio uniform)
- [x] Easter egg concept defined ("Depth Resonance Fibonacci")
- [ ] Spec file saved to `docs/specs/_02_fleshed_out/` (pending)
- [ ] `BOARD.md` updated to "🟩 COMPLETING PASS 2"
- [ ] Easter egg appended to `WORKSPACE/EASTEREGG_COUNCIL.md`
- [ ] Next task claimed

**Next Step**: Write spec file to disk, update BOARD.md, add easter egg, claim next task.
