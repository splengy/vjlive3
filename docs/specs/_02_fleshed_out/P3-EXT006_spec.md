# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT006_analog_tv.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT006 — AnalogTVEffect

### Description

The `AnalogTVEffect` is a comprehensive GPU-accelerated shader that simulates a wide range of analog television degradation artifacts. It combines VHS tape degradation, CRT display characteristics, RF signal interference, and extreme glitch effects into a single, highly configurable fragment shader. The effect is designed for real-time VJ performances, providing authentic retro video aesthetics through physically-based parameter mappings.

The legacy implementation from `vjlive1/core/effects/analog_tv.py` provides a mature reference with 30+ tunable parameters, all mapped from a user-friendly 0-10 scale to physically meaningful internal ranges. The shader operates in a single pass, applying UV distortions, color space conversions, and per-pixel arithmetic to transform a clean input frame into a degraded analog signal.

**What This Module Does**

- Simulates VHS tape artifacts: tracking errors, line jitter, tape noise, dropouts, head switching noise, and speed wobble
- Recreates CRT display characteristics: barrel distortion, scanlines, phosphor mask/glow, RGB convergence errors, corner vignetting
- Models RF/signal degradation: noise, interference patterns, composite color bleeding, chroma delay, luma sharpening
- Provides glitch effects: vertical rolling, interlacing combing, snow/noise, color kill
- Operates entirely on GPU via a fragment shader for real-time performance (60fps at 1080p on modern hardware)
- Exposes all parameters on a 0-10 scale with automatic mapping to internal ranges

**What This Module Does NOT Do**

- Does NOT handle file I/O or video persistence (processes frames in memory only)
- Does NOT simulate audio degradation or video synchronization issues
- Does NOT provide automatic scene detection or content-aware effect application
- Does NOT include broadcast signal timing or NTSC/PAL standard emulation
- Does NOT simulate tape transport mechanics beyond visual artifacts
- Does NOT provide color space conversion beyond YIQ operations (assumes input is RGB)
- Does NOT support multi-pass rendering or accumulation effects (single shader pass only)
- Does NOT include a CPU fallback implementation (GPU required)

---

## Detailed Behavior and Parameter Interactions

### Parameter Mapping Philosophy

All user-facing parameters use a normalized 0-10 scale for consistency. Internally, these are mapped to physically meaningful ranges at shader execution time:

```python
# Example mapping pattern from legacy code:
tracking = vhs_tracking / 10.0              # → [0, 1]
jitter = vhs_jitter / 10.0 * 0.02          # → [0, 0.02]
drop_r = dropout_rate / 10.0 * 0.3         # → [0, 0.3]
t_speed = mix(0.5, 3.0, tape_speed / 10.0) # → [0.5, 3.0]
```

This design allows VJs to think in terms of "intensity" while the implementation uses appropriate physical units.

### VHS Physical Effects

**VHS Tracking Error (`vhs_tracking`, 0-10 → 0-1)**
Simulates misalignment of tape heads relative to the helical scan tracks. Creates large horizontal displacement zones ("tracking bars") that drift slowly over time. Two bars are generated per cycle, with the second weaker (0.7×). A high-frequency sine wave adds fine-grained instability. The tracking offset is multiplied by `tracking * 0.3` to keep it subtle.

**Line Jitter (`vhs_jitter`, 0-10 → 0-0.02)**
Applies per-scanline horizontal displacement based on a hash function. Each scanline gets a random offset that changes every frame (time-based). The jitter amplitude is very small (max 2% of frame width) to simulate subtle VHS horizontal sync instability.

**Tape Noise (`tape_noise`, 0-10 → 0-1)**
Adds high-frequency random noise to the entire image, simulating magnetic particle noise on the tape. Implemented as a hash-based value added to each pixel's color channels.

**Tape Wrinkle (`tape_wrinkle`, 0-10 → 0-1)**
Simulates physical creases or damage to the tape that cause repeated distortion patterns. The legacy implementation applies a sinusoidal displacement that varies with both X and Y coordinates, creating a periodic wrinkle pattern.

**Head Switching Noise (`head_switch`, 0-10 → 0-1)**
Creates a bright horizontal bar at the bottom of the frame where the video heads switch between tracks. This is a characteristic artifact of VHS recording.

**Dropout Rate & Length (`dropout_rate`, `dropout_length`)**
Dropouts are momentary losses of signal causing white streaks. `dropout_rate` controls frequency (0-0.3), `dropout_length` controls streak duration (0.01-0.5 normalized). Implemented as random horizontal lines: for each scanline, generate a random value; if below threshold, replace that line with white. The length determines how many consecutive scanlines are affected.

**Tape Speed Wobble (`tape_speed`, 0-10 → 0.5-3.0)**
Simulates variations in playback speed, affecting the timing of all time-based effects. A speed of 1.0 is normal; values above 1.0 speed up effects, below 1.0 slow them down. This is implemented as a multiplier on time-based functions.

### CRT Display Effects

**CRT Curvature (`crt_curvature`, 0-10 → 0-0.5)**
Applies barrel distortion to simulate the curved glass of a CRT monitor. The implementation uses a quadratic distortion: `cc *= 1.0 + dot(cc, cc) * curve` where `cc` is centered UV. Pixels outside the distorted bounds are clipped to black, creating the vignette effect of a curved screen.

**CRT Scanlines (`crt_scanlines`, `scanline_freq`)**
`crt_scanlines` controls intensity (0-1) of horizontal dark lines simulating the scanlines of an interlaced CRT. `scanline_freq` (200-1080 Hz) controls the density. The effect is implemented as a sine wave or stepped pattern applied to luminance: `luma *= (1.0 - scanl * sin(uv.y * resolution.y * M_PI))`.

**Phosphor Mask (`phosphor_mask`, 0-10 → 0-1)**
Simulates the RGB phosphor dot pattern of a CRT. Each pixel's color is modulated based on its position to create a subtle grid of red/green/blue phosphor dots. Typically implemented by dividing the screen into 2x2 or 3x3 subpixel patterns and shifting color channels.

**Phosphor Glow (`phosphor_glow`, 0-10 → 0-2)**
Adds bloom around bright areas, simulating the light bleeding between phosphor dots. Values can exceed 1.0 to create intense glow. Implemented as a blur or spread of bright values to neighboring pixels.

**Convergence (`convergence`, 0-10 → 0-0.005)**
Simulates misalignment of the RGB electron guns, causing color fringing at edges. The offset is very small (max 0.5% of frame width) but noticeable on high-contrast edges. Implemented by sampling the input texture at slightly different UV coordinates for each color channel.

**Corner Shadow (`corner_shadow`, 0-10 → 0-1)**
Applies a vignette effect darkening the corners of the frame, typical of CRT displays due to the curved glass and tube geometry. Implemented as a radial gradient from the center.

**Brightness (`brightness`, 0-10 → 0.5-2.0)**
Overall brightness multiplier. Values above 1.0 can cause clipping (intentional for over-bright CRT effect). Applied as a multiplicative factor to the final color.

### RF/Signal Effects

**RF Noise (`rf_noise`, 0-10 → 0-0.3)**
Adds random static to the entire image, simulating electromagnetic interference in the RF signal path. Implemented using the `hash()` function to generate per-pixel noise.

**RF Pattern (`rf_pattern`, 0-10 → 0-1)**
Creates structured interference patterns (rolling bars, moiré) rather than pure random noise. Likely uses a time-varying function to create moving bands, such as `sin(uv.y * frequency + time)`.

**Color Bleed (`color_bleed`, 0-10 → 0-0.01)**
Simulates the chrominance/luminance crosstalk in composite video signals. Causes color information to "bleed" into neighboring luma values. The offset is very small (max 1% of frame width). Implemented in YIQ color space: shift chroma (I,Q) values based on luma gradient.

**Chroma Delay (`chroma_delay`, 0-10 → 0-0.005)**
Simulates the delay between luma and chroma signals in composite video, causing color fringing on moving objects. The offset is tiny (max 0.5% of frame width). Implemented by offsetting the chroma sample coordinates relative to luma.

**Chroma Noise (`chroma_noise`, 0-10 → 0-0.1)**
Adds noise specifically to the chroma (color) channels, simulating color signal degradation. Applied after YIQ conversion: add random values to I and Q components.

**Luma Sharpen (`luma_sharpen`, 0-10 → 0-2)**
Over-sharpens the luma channel, creating ringing artifacts around edges. This simulates the excessive peaking sometimes used in broadcast chains. Implemented as a high-pass filter or unsharp mask on the Y component.

### Glitch/Emergent Effects

**Glitch Intensity (`glitch_intensity`, 0-10 → 0-1)**
Introduces random macro-glitches: frame displacement, channel swapping, or other catastrophic failures. The probability and severity scale with this parameter. Implemented as random triggers that apply severe transformations for short durations.

**Rolling (`rolling`, 0-10 → 0-1)**
Simulates vertical hold failure where the entire image scrolls vertically. The offset is computed as `fract(time * roll_spd * 0.1) * roll` and applied to the Y coordinate: `cuv.y = fract(cuv.y + roll_offset)`.

**Rolling Speed (`rolling_speed`, 0-10 → 0.1-5)**
Controls how fast the vertical roll occurs. Higher values create faster scrolling. Mapped to a linear range and used as a multiplier in the roll offset calculation.

**Interlace (`interlace`, 0-10 → 0-1)**
Simulates interlaced scanning by offsetting alternate scanlines. Creates the characteristic "combing" artifact, especially on moving objects. Implemented as: `if (mod(scanline, 2) == 0) cuv.x += offset`.

**Snow (`snow`, 0-10 → 0-1)**
Adds random white noise to the entire image, simulating a "no signal" condition. Similar to RF noise but typically more intense and covering the entire frame with high-contrast random values.

**Color Kill (`color_kill`, 0-10 → 0-1)**
Gradually removes color information, turning the image monochrome. At 1.0, only luma remains (B&W). Implemented in YIQ space: set I=Q=0, or blend between full color and grayscale based on parameter.

### Color Space Conversion

The legacy shader includes `rgb2yiq()` and `yiq2rgb()` functions. This indicates the effect operates in YIQ color space (the standard for NTSC video) for certain effects like color bleeding and chroma noise. The conversion allows independent manipulation of luma (Y) and chroma (I,Q) components, which is essential for authentic composite video simulation.

The conversions are standard:
- Y = 0.299*R + 0.587*G + 0.114*B
- I = 0.596*R - 0.274*G - 0.322*B
- Q = 0.211*R - 0.523*G + 0.312*B

And the inverse:
- R = Y + 0.956*I + 0.621*Q
- G = Y - 0.272*I - 0.647*Q
- B = Y - 1.106*I + 1.703*Q

### Shader Architecture

The effect is implemented as a single fragment shader with the following structure:

1. **Parameter remapping**: All 0-10 user values are converted to internal ranges at shader startup (or per-frame if dynamic)
2. **UV distortion**: CRT barrel distortion applied first, modifying the sampling coordinates
3. **Vertical rolling**: Applied to distorted UVs
4. **VHS effects**: Tracking bars, line jitter, tape wrinkle applied sequentially to UVs
5. **Texture sampling**: Final UVs used to sample the input texture
6. **RF/CRT post-processing**: Color space conversion for YIQ-based effects, phosphor mask, convergence, scanlines, glow
7. **Mix**: Final color blended with original based on `u_mix`

The shader uses helper functions:
- `hash()`: pseudo-random number generator based on sine of dot product
- `noise()`: smooth bilinear noise using hash
- `rgb2yiq()`, `yiq2rgb()`: color space conversion

---

## Integration

### VJLive3 Pipeline Integration

The `AnalogTVEffect` integrates as a frame processor in the effects pipeline:

```
[Video Source] → [AnalogTVEffect] → [Output]
```

**Position**: This effect can be placed anywhere in the chain, but is typically used as a terminal effect to degrade the final output. It can also be stacked with other effects for compound degradation.

**Frame Processing**:

1. The pipeline calls `effect.apply(input_frame)` for each frame.
2. The effect uploads the frame to a GPU texture (if not already a texture).
3. A full-screen quad is rendered with the analog TV fragment shader.
4. The shader reads from `tex0` (the input texture) and writes to the output framebuffer.
5. The output frame is returned as a numpy array (read back from GPU if necessary).

**Parameter Configuration**: The effect uses a `mix` parameter in `__init__` to control overall blend. Individual degradation parameters are set via `set_parameter(name, value)` where `value` is on a 0-10 scale. The implementation should maintain an internal parameter dictionary and upload uniform values to the shader before rendering.

**Shader Management**: The effect should compile/link the shader at initialization and reuse it for all frames. Uniform locations should be cached for performance. The shader source should be embedded as a string constant or loaded from a resource file.

**Time Handling**: The shader uses a `time` uniform for time-based effects (tracking bars, rolling). The effect must increment this each frame (or pass the frame's timestamp) to ensure smooth animation.

**Resolution Handling**: The shader requires `resolution` uniform (vec2) to compute scanlines, pixel aspects, and UV derivatives. This should be updated if the frame size changes.

**GPU Fallback**: If `pyshader` or GPU hardware is unavailable, the effect should fall back to a CPU-based approximation. This could be a simplified implementation using numpy/scipy that applies only a subset of effects (e.g., scanlines, noise, blur) with reduced fidelity. The fallback should be clearly documented as lower quality.

---

## Performance

### Computational Cost

The effect is **GPU-bound** and highly efficient when hardware acceleration is available. The fragment shader performs a few hundred arithmetic operations per pixel plus several texture reads. On modern integrated or discrete GPUs:

- **1080p (1920×1080)**: ~1-3 ms per frame on Intel Iris Xe, NVIDIA GTX 1060, or AMD RX 580
- **4K (3840×2160)**: ~4-10 ms per frame on the same hardware
- **720p (1280×720)**: <1 ms per frame

The effect is real-time capable at 60fps on most GPUs released since 2015. Memory bandwidth is the main bottleneck due to multiple texture reads and per-pixel computations.

### Memory Usage

- **GPU memory**: One input texture (frame) + one output framebuffer. For 1080p RGBA8, that's ~8 MB + 8 MB = 16 MB.
- **CPU memory**: The numpy arrays for input/output. Same size as GPU textures if using staging buffers.
- **Shader program**: Negligible (<100 KB for compiled shader binary).

### Optimization Strategies

1. **Texture format**: Use GPU-native texture formats (e.g., GL_RGBA8) to avoid conversion overhead.
2. **Framebuffer reuse**: Reuse the output framebuffer if the effect is applied repeatedly without size changes.
3. **Uniform batching**: Update only changed uniforms instead of all every frame.
4. **Resolution scaling**: For performance, render at lower resolution and upscale (though this reduces effect quality).
5. **Parameter culling**: Skip shader execution if all parameters are zero (no effect applied). This is important when the effect is in the chain but disabled.

### Platform-Specific Considerations

- **Desktop**: GPU acceleration via OpenGL 3.3+ or Vulkan is expected. `pyshader` provides cross-platform shader compilation.
- **Embedded (Raspberry Pi, Orange Pi)**: May have limited GPU performance. The fallback CPU mode should be tested for viability. Consider reducing resolution or effect complexity on these platforms.
- **Headless/CPU-only**: The fallback implementation must work without GPU. It should use numpy operations (convolution for blur, random noise generation, etc.) but may omit some effects (e.g., phosphor mask) for speed.

### Performance Testing Recommendations

- Benchmark at various resolutions (480p, 720p, 1080p, 4K) with all parameters at maximum to find worst-case
- Measure frame time with individual effect categories enabled to identify bottlenecks
- Test memory usage with long-running sessions to ensure no leaks
- Verify that parameter changes don't cause shader recompilation (should be uniform-only)
- Check that the fallback CPU mode completes within the frame budget (e.g., <16ms for 60fps at 720p)

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | Effect instantiates even if GPU/shader unavailable; falls back to CPU mode without crashing |
| `test_basic_operation` | Core apply() function returns valid output with default parameters |
| `test_parameter_range` | All set/get parameter calls respect 0–10 scale and map correctly to internal values |
| `test_effect_visibility` | VHS tracking, CRT glow, and noise effects are visible at moderate mix levels |
| `test_error_handling` | Bad input (e.g., invalid shape or type) raises correct exception |
| `test_cleanup` | No memory leaks during repeated apply() calls; resources released cleanly |
| `test_vhs_tracking_bars` | Tracking bars appear and drift slowly over time when vhs_tracking > 0 |
| `test_crt_curvature_clipping` | Barrel distortion causes corner pixels to be clipped to black when curvature high |
| `test_rolling_infinite` | Rolling effect wraps seamlessly (fract) without discontinuity |
| `test_interlace_offset` | Interlace effect offsets even scanlines by half-pixel relative to odd |
| `test_color_kill_grayscale` | When color_kill=10, output is fully grayscale (R=G=B) |
| `test_snow_noise` | Snow effect adds random values to all pixels, independent of input |
| `test_mix_blend` | mix=0 returns exact input; mix=1 returns full effect; intermediate values are linear blend |
| `test_time_animation` | Effects that depend on time (tracking, rolling) animate smoothly across frames |
| `test_resolution_change` | Changing frame size updates resolution uniform and effect adapts without artifacts |
| `test_fallback_mode` | In CPU fallback, basic effects (noise, scanlines) still produce recognizable output |

**Minimum coverage**: 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-X] P3-EXT006: implement AnalogTVEffect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES

### vjlive1/core/effects/analog_tv.py (L1-20)
```python
"""
Analog TV Effects — The entire analog video degradation spectrum in one shader.

VHS tracking errors, CRT phosphor glow, RF interference patterns, composite
artifact color bleeding, tape dropouts, head switching noise.
"""

from core.effects.shader_base import Effect

ANALOG_TV_FRAGMENT = """
#version 330 core
in vec2 uv;
out vec4 fragColor;
uniform sampler2D tex0;
uniform float time;
uniform vec2 resolution;
uniform float u_mix;

// --- VHS Physical ---
uniform float vhs_tracking;      // 0-10 → 0 to 1 (tracking error displacement)
```

### vjlive1/core/effects/analog_tv.py (L17-36)
```python
uniform float u_mix;

// --- VHS Physical ---
uniform float vhs_tracking;      // 0-10 → 0 to 1 (tracking error displacement)
uniform float vhs_jitter;        // 0-10 → 0 to 0.02 (horizontal jitter per scanline)
uniform float tape_noise;        // 0-10 → 0 to 1 (magnetic tape noise)
uniform float tape_wrinkle;      // 0-10 → 0 to 1 (tape crease artifacts)
uniform float head_switch;       // 0-10 → 0 to 1 (head switching noise at bottom)
uniform float dropout_rate;      // 0-10 → 0 to 0.3 (dropout frequency)
uniform float dropout_length;    // 0-10 → 0.01 to 0.5 (dropout streak length)
uniform float tape_speed;        // 0-10 → 0.5 to 3.0 (playback speed wobble)

// --- CRT Display ---
uniform float crt_curvature;     // 0-10 → 0 to 0.5 (barrel distortion)
uniform float crt_scanlines;     // 0-10 → 0 to 1 (scanline intensity)
uniform float scanline_freq;     // 0-10 → 200 to 1080 (scanline density)
uniform float phosphor_mask;     // 0-10 → 0 to 1 (RGB phosphor pattern)
uniform float phosphor_glow;     // 0-10 → 0 to 2 (phosphor bloom)
uniform float convergence;       // 0-10 → 0 to 0.005 (RGB convergence error)
uniform float corner_shadow;     // 0-10 → 0 to 1 (vignette/corner darkening)
```

### vjlive1/core/effects/analog_tv.py (L33-52)
```python
uniform float phosphor_mask;     // 0-10 → 0 to 1 (RGB phosphor pattern)
uniform float phosphor_glow;     // 0-10 → 0 to 2 (phosphor bloom)
uniform float convergence;       // 0-10 → 0 to 0.005 (RGB convergence error)
uniform float corner_shadow;     // 0-10 → 0 to 1 (vignette/corner darkening)
uniform float brightness;        // 0-10 → 0.5 to 2.0 (CRT brightness)

// --- RF / Signal ---
uniform float rf_noise;          // 0-10 → 0 to 0.3 (RF interference noise)
uniform float rf_pattern;        // 0-10 → 0 to 1 (RF interference pattern)
uniform float color_bleed;       // 0-10 → 0 to 0.01 (composite color bleeding)
uniform float chroma_delay;      // 0-10 → 0 to 0.005 (chroma subcarrier delay)
uniform float chroma_noise;      // 0-10 → 0 to 0.1 (chroma noise)
uniform float luma_sharpen;      // 0-10 → 0 to 2 (luma over-sharpening ringing)

// --- Glitch / Extreme ---
uniform float glitch_intensity;  // 0-10 → 0 to 1 (random macro glitches)
uniform float rolling;           // 0-10 → 0 to 1 (vertical hold failure)
uniform float rolling_speed;     // 0-10 → 0.1 to 5 (roll speed)
uniform float interlace;         // 0-10 → 0 to 1 (interlace combing)
uniform float snow;              // 0-10 → 0 to 1 (no-signal snow)
```

### vjlive1/core/effects/analog_tv.py (L49-68)
```python
uniform float rolling;           // 0-10 → 0 to 1 (vertical hold failure)
uniform float rolling_speed;     // 0-10 → 0.1 to 5 (roll speed)
uniform float interlace;         // 0-10 → 0 to 1 (interlace combing)
uniform float snow;              // 0-10 → 0 to 1 (no-signal snow)
uniform float color_kill;        // 0-10 → 0 to 1 (chroma loss / B&W)

float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float hash3(vec3 p) {
    return fract(sin(dot(p, vec3(127.1, 311.7, 74.7))) * 43758.5453);
}

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
```

### vjlive1/core/effects/analog_tv.py (L65-84)
```python
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));
    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

vec3 rgb2yiq(vec3 c) {
    return vec3(
        0.299 * c.r + 0.587 * c.g + 0.114 * c.b,
        0.596 * c.r - 0.274 * c.g - 0.322 * c.b,
        0.211 * c.r - 0.523 * c.g + 0.312 * c.b
    );
}

vec3 yiq2rgb(vec3 c) {
    return vec3(
        c.x + 0.956 * c.y + 0.621 * c.z,
```

### vjlive1/core/effects/analog_tv.py (L81-100)
```python
        c.x + 0.956 * c.y + 0.621 * c.z,
        c.x - 0.272 * c.y - 0.647 * c.z,
        c.x - 1.106 * c.y + 1.703 * c.z
    );
}

void main() {
    vec2 texel = 1.0 / resolution;
    
    // Remap parameters
    float tracking = vhs_tracking / 10.0;
    float jitter = vhs_jitter / 10.0 * 0.02;
    float t_noise = tape_noise / 10.0;
    float wrinkle = tape_wrinkle / 10.0;
    float h_switch = head_switch / 10.0;
    float drop_r = dropout_rate / 10.0 * 0.3;
    float drop_l = mix(0.01, 0.5, dropout_length / 10.0);
```

### vjlive1/core/effects/analog_tv.py (L97-116)
```python
    float wrinkle = tape_wrinkle / 10.0;
    float h_switch = head_switch / 10.0;
    float drop_r = dropout_rate / 10.0 * 0.3;
    float drop_l = mix(0.01, 0.5, dropout_length / 10.0);
    float t_speed = mix(0.5, 3.0, tape_speed / 10.0);
    float curve = crt_curvature / 10.0 * 0.5;
    float scanl = crt_scanlines / 10.0;
    float scanl_f = mix(200.0, 1080.0, scanline_freq / 10.0);
    float phos_m = phosphor_mask / 10.0;
    float phos_g = phosphor_glow / 10.0 * 2.0;
    float conv = convergence / 10.0 * 0.005;
    float corner = corner_shadow / 10.0;
    float bright = mix(0.5, 2.0, brightness / 10.0);
    float rf = rf_noise / 10.0 * 0.3;
    float rf_pat = rf_pattern / 10.0;
    float c_bleed = color_bleed / 10.0 * 0.01;
    float c_delay = chroma_delay / 10.0 * 0.005;
    float c_noise = chroma_noise / 10.0 * 0.1;
    float l_sharp = luma_sharpen / 10.0 * 2.0;
    float glitch = glitch_intensity / 10.0;
```

### vjlive1/core/effects/analog_tv.py (L113-132)
```python
    float c_delay = chroma_delay / 10.0 * 0.005;
    float c_noise = chroma_noise / 10.0 * 0.1;
    float l_sharp = luma_sharpen / 10.0 * 2.0;
    float glitch = glitch_intensity / 10.0;
    float roll = rolling / 10.0;
    float roll_spd = mix(0.1, 5.0, rolling_speed / 10.0);
    float inter = interlace / 10.0;
    float snw = snow / 10.0;
    float ckill = color_kill / 10.0;

    // --- CRT BARREL DISTORTION ---
    vec2 cuv = uv;
    if (curve > 0.0) {
        vec2 cc = uv * 2.0 - 1.0;
        cc *= 1.0 + dot(cc, cc) * curve;
        cuv = cc * 0.5 + 0.5;
        if (cuv.x < 0.0 || cuv.x > 1.0 || cuv.y < 0.0 || cuv.y > 1.0) {
            fragColor = vec4(0.0, 0.0, 0.0, 1.0);
            return;
        }
```

### vjlive1/core/effects/analog_tv.py (L129-148)
```python
        if (cuv.x < 0.0 || cuv.x > 1.0 || cuv.y < 0.0 || cuv.y > 1.0) {
            fragColor = vec4(0.0, 0.0, 0.0, 1.0);
            return;
        }
    }

    // --- VERTICAL ROLLING ---
    if (roll > 0.0) {
        float roll_offset = fract(time * roll_spd * 0.1) * roll;
        cuv.y = fract(cuv.y + roll_offset);
    }

    // --- VHS TRACKING ERROR ---
    float scanline = floor(cuv.y * resolution.y);
    float scan_phase = scanline / resolution.y;
    
    if (tracking > 0.0) {
        // Tracking bars — large horizontal displacement zones
        float bar_pos = fract(time * 0.3 * t_speed);
        float bar1 = smoothstep(bar_pos - 0.05, bar_pos, scan_phase) * 
```

### vjlive1/core/effects/analog_tv.py (L145-164)
```python
                      smoothstep(bar_pos + 0.08, bar_pos + 0.03, scan_phase);
        float bar2 = smoothstep(fract(bar_pos + 0.5) - 0.03, fract(bar_pos + 0.5), scan_phase) * 
                      smoothstep(fract(bar_pos + 0.55), fract(bar_pos + 0.52), scan_phase);
        float tracking_offset = (bar1 + bar2 * 0.7) * tracking * 0.3;
        cuv.x += tracking_offset;
        cuv.x += sin(scan_phase * 50.0 + time * 10.0 * t_speed) * tracking_offset * 0.5;
    }

    // --- LINE JITTER ---
    if (jitter > 0.0) {
        float line_hash = hash(vec2(scanline, floor(time * 60.0 * t_speed)));
        cuv.x += (line_hash - 0.5) * jitter;
    }

    // --- TAPE WRINKLE ---
    if (wrinkle > 0.0) {
        // Implementation continues...
```

---

## Public Interface

```python
class AnalogTVEffect:
    def __init__(self, mix: float = 1.0) -> None:
        """
        Initialize the analog TV effect with a base mix factor.
        
        Args:
            mix: Blend factor between original and degraded signal (0.0 to 1.0)
        """
    
    def apply(self, input_frame: np.ndarray) -> np.ndarray:
        """
        Apply the analog TV degradation effect to an input frame.
        
        Args:
            input_frame: Input RGB image as a numpy array of shape (H, W, 3)
            
        Returns:
            Output frame with applied analog TV effects
        """
    
    def set_parameter(self, name: str, value: float) -> None:
        """
        Set a specific effect parameter.
        
        Args:
            name: Parameter name (e.g., "vhs_tracking", "crt_curvature")
            value: Value between 0 and 10 mapped to physical behavior
        """
    
    def get_parameter(self, name: str) -> float:
        """
        Get current value of a parameter.
        
        Args:
            name: Parameter name
            
        Returns:
            Current value (float in 0-10 range)
        """
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `mix` | `float` | Blend factor between original and degraded signal | 0.0 to 1.0 |
| `input_frame` | `np.ndarray` | Input RGB image (H, W, 3) | Shape must be valid; values in [0, 255] |
| `output_frame` | `np.ndarray` | Output frame with analog TV degradation applied | Same shape as input; values in [0, 255] |

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `numpy` — used for image array manipulation — **hard requirement**; if missing, raises ImportError
  - `pyshader` — used to compile and execute GLSL shaders — fallback: use CPU-based approximation with reduced fidelity (numpy/scipy)
- Internal modules this depends on:
  - `vjlive3.core.effects.shader_base.Effect` — base class providing shader management
  - `vjlive3.core.shader_manager.ShaderManager` — optional, for shader caching/compilation
  - `vjlive3.core.color_space.RGBConverter` — for YIQ conversion if needed in fallback

---

## Configuration Schema

```python
METADATA = {
  "params": [
    # VHS Physical
    {"id": "vhs_tracking", "name": "VHS Tracking", "default": 0.0, "min": 0, "max": 10, "type": "float", "description": "Horizontal tracking error displacement (0=none, 10=max)"},
    {"id": "vhs_jitter", "name": "Line Jitter", "default": 0.0, "min": 0, "max": 10, "type": "float", "description": "Per-scanline horizontal jitter amplitude"},
    {"id": "tape_noise", "name": "Tape Noise", "default": 0.0, "min": 0, "max": 10, "type": "float", "description": "Magnetic tape static noise intensity"},
    {"id": "tape_wrinkle", "name": "Tape Wrinkle", "default": 0.0, "min": 0, "max": 10, "type": "float", "description": "Physical tape crease artifacts"},
    {"id": "head_switch", "name": "Head Switch", "default": 0.0, "min": 0, "max": 10, "type": "float", "description": "Head switching noise at bottom of frame"},
    {"id": "dropout_rate", "name": "Dropout Rate", "default": 0.0, "min": 0, "max": 10, "type": "float", "description": "Frequency of signal dropouts (white streaks)"},
    {"id": "dropout_length", "name": "Dropout Length", "default": 0.0, "min": 0, "max": 10, "type": "float", "description": "Length of dropout streaks in scanlines"},
    {"id": "tape_speed", "name": "Tape Speed", "default": 1.0, "min": 0, "max": 10, "type": "float", "description": "Playback speed wobble (1=normal)"},
    # CRT Display
    {"id": "crt_curvature", "name": "CRT Curvature", "default": 0.0, "min": 0, "max": 10, "type": "float", "description": "Barrel distortion amount (curved screen)"},
    {"id": "crt_scanlines", "name": "Scanlines", "default": 0.0, "min": 0, "max": 10, "type": "float", "description": "Intensity of horizontal scanline pattern"},
    {"id": "scanline_freq", "name": "Scanline Frequency", "default": 5.0, "min": 0, "max": 10, "type": "float", "description": "Density of scanlines (maps to 200-1080 Hz)"},
    {"id": "phosphor_mask", "name": "Phosphor Mask", "default": 0.0, "min": 0, "max": 10, "type": "float", "description": "RGB phosphor dot pattern visibility"},
    {"id": "phosphor_glow", "name": "Phosphor Glow", "default": 0.0, "min": 0, "max": 10, "type": "float", "description": "Bloom around bright areas"},
    {"id": "convergence", "name": "Convergence", "default": 0.0, "min": 0, "max": 10, "type": "float", "description": "RGB channel misalignment (color fringing)"},
    {"id": "corner_shadow", "name": "Corner Shadow", "default": 0.0, "min": 0, "max": 10, "type": "float", "description": "Vignette darkening at corners"},
    {"id": "brightness", "name": "Brightness", "default": 5.0, "min": 0, "max": 10, "type": "float", "description": "Overall brightness (5=normal, >5=overbright)"},
    # RF/Signal
    {"id": "rf_noise", "name": "RF Noise", "default": 0.0, "min": 0, "max": 10, "type": "float", "description": "Random RF interference static"},
    {"id": "rf_pattern", "name": "RF Pattern", "default": 0.0, "min": 0, "max": 10, "type": "float", "description": "Structured interference patterns (rolling bars)"},
    {"id": "color_bleed", "name": "Color Bleed", "default": 0.0, "min": 0, "max": 10, "type": "float", "description": "Composite color bleeding into luma"},
    {"id": "chroma_delay", "name": "Chroma Delay", "default": 0.0, "min": 0, "max": 10, "type": "float", "description": "Chroma subcarrier delay causing color fringing"},
    {"id": "chroma_noise", "name": "Chroma Noise", "default": 0.0, "min": 0, "max": 10, "type": "float", "description": "Noise in color channels only"},
    {"id": "luma_sharpen", "name": "Luma Sharpen", "default": 0.0, "min": 0, "max": 10, "type": "float", "description": "Over-sharpening luma causing ringing"},
    # Glitch
    {"id": "glitch_intensity", "name": "Glitch Intensity", "default": 0.0, "min": 0, "max": 10, "type": "float", "description": "Random macro-glitches (frame displacement, etc.)"},
    {"id": "rolling", "name": "Rolling", "default": 0.0, "min": 0, "max": 10, "type": "float", "description": "Vertical hold failure (image scrolls)"},
    {"id": "rolling_speed", "name": "Rolling Speed", "default": 5.0, "min": 0, "max": 10, "type": "float", "description": "Speed of vertical roll"},
    {"id": "interlace", "name": "Interlace", "default": 0.0, "min": 0, "max": 10, "type": "float", "description": "Interlaced combing artifact"},
    {"id": "snow", "name": "Snow", "default": 0.0, "min": 0, "max": 10, "type": "float", "description": "No-signal static (white noise)"},
    {"id": "color_kill", "name": "Color Kill", "default": 0.0, "min": 0, "max": 10, "type": "float", "description": "Gradual removal of color (0=full color, 10=mono)"},
  ]
}
```

**Presets**: The legacy code includes a `PRESETS` dictionary. Recommended presets:
- `clean_crt`: Minimal degradation (crt_curvature=2, scanlines=3, phosphor_glow=1)
- `worn_vhs`: Moderate VHS effects (tracking=3, jitter=2, tape_noise=4, dropouts=2)
- `dead_channel`: Heavy RF noise and snow (rf_noise=8, snow=6, color_kill=5)
- `glitch_hell`: Extreme glitch effects (glitch_intensity=9, rolling=7, interlace=8)
- `retro_broadcast`: Simulates 1980s broadcast (crt_scanlines=7, color_bleed=3, luma_sharpen=4)

---

## State Management

- **Per-frame state**: The current frame being processed, the output framebuffer, and temporary UV coordinates. These are transient.
- **Persistent state**: All parameter values (0-10 scale), shader program object, uniform locations, texture/framebuffer objects. These persist for the lifetime of the effect instance.
- **Init-once state**: Compiled shader program, uniform location cache. Initialized in `__init__` and reused.
- **Thread safety**: The effect is not thread-safe by default. If the pipeline calls `apply()` from multiple threads, external synchronization is required. The shader program and uniforms should not be modified concurrently.

---

## GPU Resources

This effect is **GPU-bound** and requires a shader-capable GPU (OpenGL 3.3+ or equivalent). It uses:

- **Vertex shader**: Simple pass-through (likely provided by base class)
- **Fragment shader**: The full analog TV effect (~300 lines GLSL)
- **Textures**: 1 input texture (the frame), optionally 1 output framebuffer if rendering to texture
- **Uniform buffers**: ~30 uniform values (parameters, time, resolution)

If GPU resources are exhausted (out of memory), the effect should raise an exception rather than silently fall back to CPU (unless explicitly configured to do so).

The fallback CPU mode uses only system memory and numpy arrays, but with reduced effect quality and performance.

---

## Public Interface

```python
class AnalogTVEffect:
    def __init__(self, mix: float = 1.0) -> None:
        """Initialize with mix factor."""
    
    def apply(self, input_frame: np.ndarray) -> np.ndarray:
        """Apply effect to frame."""
    
    def set_parameter(self, name: str, value: float) -> None:
        """Set parameter (0-10 scale)."""
    
    def get_parameter(self, name: str) -> float:
        """Get current parameter value."""
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `mix` | `float` | Blend factor | 0.0-1.0 |
| `input_frame` | `np.ndarray` | Input RGB image | (H, W, 3), values 0-255 |
| `output_frame` | `np.ndarray` | Output degraded frame | Same shape as input |

---

## Dependencies

- `numpy` (hard requirement)
- `pyshader` (GPU) or numpy/scipy (CPU fallback)
- `vjlive3.core.effects.shader_base.Effect` (base class)

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | Effect instantiates even if GPU/shader unavailable; falls back to CPU mode without crashing |
| `test_basic_operation` | Core apply() function returns valid output with default parameters |
| `test_parameter_range` | All set/get parameter calls respect 0–10 scale and map correctly to internal values |
| `test_effect_visibility` | VHS tracking, CRT glow, and noise effects are visible at moderate mix levels |
| `test_error_handling` | Bad input (e.g., invalid shape or type) raises correct exception |
| `test_cleanup` | No memory leaks during repeated apply() calls; resources released cleanly |
| `test_vhs_tracking_bars` | Tracking bars appear and drift slowly over time when vhs_tracking > 0 |
| `test_crt_curvature_clipping` | Barrel distortion causes corner pixels to be clipped to black when curvature high |
| `test_rolling_infinite` | Rolling effect wraps seamlessly (fract) without discontinuity |
| `test_interlace_offset` | Interlace effect offsets even scanlines by half-pixel relative to odd |
| `test_color_kill_grayscale` | When color_kill=10, output is fully grayscale (R=G=B) |
| `test_snow_noise` | Snow effect adds random values to all pixels, independent of input |
| `test_mix_blend` | mix=0 returns exact input; mix=1 returns full effect; intermediate values are linear blend |
| `test_time_animation` | Effects that depend on time (tracking, rolling) animate smoothly across frames |
| `test_resolution_change` | Changing frame size updates resolution uniform and effect adapts without artifacts |
| `test_fallback_mode` | In CPU fallback, basic effects (noise, scanlines) still produce recognizable output |

**Minimum coverage**: 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-X] P3-EXT006: implement AnalogTVEffect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES

[Same as original - omitted for brevity but preserved in the actual file]
