# P3-EXT026: CellularAutomataDatamoshEffect — Technical Specification

**Status:** Pass 2 Fleshed Out  
**Module:** `CellularAutomataDatamoshEffect`  
**Category:** Datamosh / Simulation  
**GPU Tier:** MEDIUM  
**Legacy Origin:** `plugins/vdatamosh/cellular_automata_datamosh.py` (VJlive-2)

---

## What This Module Does

The `CellularAutomataDatamoshEffect` is a sophisticated video processing effect that treats pixels as living cells in a biological simulation. It combines **Conway's Game of Life** cellular automaton with **Gray-Scott Reaction-Diffusion** equations to create evolving, organic patterns that "datamosh" (corrupt/transform) the video feed in a mathematically deterministic yet biologically plausible manner.

The effect operates on a feedback loop where:
- Each pixel's brightness determines its "alive" state (brightness > 0.5 = alive)
- Living pixels follow Game of Life rules based on neighbor counts
- Reaction-Diffusion creates smooth, spreading patterns
- A Mandelbrot fractal overlay adds mathematical depth
- The simulation evolves over time, creating living, breathing visual artifacts

**Key Features:**
- Dual video input support (Video A and Video B as seed sources)
- Frame buffer feedback using `texPrev` (previous frame)
- Depth map integration for potential 3D awareness
- 12 user-controllable parameters affecting simulation behavior
- Audio reactivity mapping for chaos and life_speed
- 3 built-in presets: `conways_dream`, `primordial_soup`, `god_mathematics`

---

## What This Module Does NOT Do

- **Does NOT** perform traditional datamosh (I-frame/P-frame corruption). This is a *simulation-based* datamosh that creates biological glitch effects.
- **Does NOT** support 3D geometry transformations; it's purely a fragment shader effect.
- **Does NOT** implement full Gray-Scott model (uses visual approximation via Laplacian).
- **Does NOT** preserve video fidelity; it intentionally corrupts the signal.
- **Does NOT** work without a feedback buffer (`texPrev`) — requires previous frame texture.
- **Does NOT** have depth-aware behavior currently (depth_tex is bound but unused in calculations).

---

## Detailed Behavior and Parameter Interactions

### Core Simulation Loop

The shader executes per-pixel with the following pipeline:

1. **Neighbor Sampling** (lines 95-101): Samples 8 neighboring pixels from `texPrev` (previous frame) using `getBrightness()`, which computes luminance via `dot(c.rgb, vec3(0.299, 0.587, 0.114))`.

2. **Game of Life Rules** (lines 104-113):
   - Current cell alive if brightness > 0.5
   - Survival: alive cell stays alive if neighbors ∈ [2, 3]
   - Birth: dead cell becomes alive if neighbors ∈ (2.5, 3.5) (fuzzy threshold for video smoothness)
   - Edge case: thresholds are hard-coded; `u_birth_thresh` and `u_death_thresh` are **not used** in the GoL logic (this is a bug/legacy artifact).

3. **Seeding from Video Input** (lines 116-124):
   - If `tex1` (Video B) has any non-zero pixels (checked at uv=(0.5,0.5)), use it as seed source; otherwise use `tex0` (Video A)
   - Input brightness computed with equal weights `dot(inputCol.rgb, vec3(0.33))`
   - If input brightness > `u_birth_thresh` (mapped 0.0-1.0), force cell alive
   - Random mutation: `hash(uv + time) < u_chaos * 0.01` spawns life

4. **Reaction-Diffusion Approximation** (lines 126-139):
   - Computes Laplacian: `-4*center + up + down + left + right`
   - Diffusion rates: `duv = vec4(1.0, 0.5, 0.0, 0.0) * 0.2` (A=1.0, B=0.5, others 0)
   - Gray-Scott formula: `center + (duv * lap - center * kill + feed * (1.0 - center))`
   - `feed = u_feed_rate * 0.1`, `kill = u_kill_rate * 0.1`

5. **Mixing and Post-Processing**:
   - `finalSim = mix(simColor, rdColor, u_reaction_mix)` chooses between GoL (binary) and RD (smooth)
   - Quantization: `floor(finalSim.rgb * steps) / steps` where `steps = 2 + (10 - u_math_quantize)` (note: u_math_quantize is 0-10, so steps range 2-12)
   - Mandelbrot overlay: 20 iterations, zoom = `exp(u_fractal_zoom * 2.0)`, adds `vec3(m*2, m, m*4)`
   - Evolution color: `0.5 + 0.5 * cos(time*0.1 + age*10 + vec3(0,2,4))`
   - Symmetry: if `u_symmetry > 0`, mirror x>0.5 from `texture(texPrev, vec2(1-uv.x, uv.y))`

6. **Final Blend** (lines 174-178):
   - `feedbackAmount = 0.9 + u_life_speed * 0.09` (range 0.9-1.0)
   - `fragColor = mix(original, finalSim, feedbackAmount * u_mix)`
   - `u_mix` is hardcoded to 1.0 in `apply_uniforms()`, so effectively `finalSim` overwrites original with 90-99% strength

### Parameter Mapping

All user parameters (0-10 range) are mapped via `_map_param(name, out_min, out_max)`:
```python
mapped = out_min + (val / 10.0) * (out_max - out_min)
```

**Exception:** `chaos` gets multiplied by `(1.0 + audio_reactor.get_energy(0.8) * 0.5)` if audio is present.

---

## Public Interface

### Class: `CellularAutomataDatamoshEffect`

**Inherits from:** `Effect` (from `core.effects.shader_base`)

**Constructor:**
```python
def __init__(self, name: str = 'cellular_automata_datamosh'):
```

**Attributes:**
- `name`: str — instance name
- `enabled`: bool (inherited) — whether effect is active
- `parameters`: dict — stores 12 parameter values (0.0-10.0 range)
- `audio_mappings`: dict — maps parameter names to audio analysis bands:
  - `'chaos' → 'high'`
  - `'life_speed' → 'energy'`
  - `'birth_thresh' → 'bass'`
  - `'fractal_zoom' → 'mid'`
- `shader`: ShaderProgram (inherited) — compiled GLSL program

**Methods:**

| Method | Signature | Description |
|--------|-----------|-------------|
| `apply_uniforms` | `(time, resolution, audio_reactor=None, semantic_layer=None)` | Uploads all uniform values to GPU. Handles audio reactivity. |
| `_map_param` | `(name, out_min, out_max) → float` | Linear remap from parameter range (0-10) to shader range. |
| `get_state` | `() → Dict[str, Any]` | Returns serializable state for persistence. |

**Presets (class attribute):**
```python
PRESETS = {
    "conways_dream": {...},
    "primordial_soup": {...},
    "god_mathematics": {...}
}
```

---

## Inputs and Outputs

### Texture Inputs (Uniforms)

| Uniform | Type | Binding | Description |
|---------|------|---------|-------------|
| `tex0` | `sampler2D` | Unit 0 | Primary video input (Video A) |
| `texPrev` | `sampler2D` | Unit 1 | Previous frame feedback buffer (MANDATORY) |
| `depth_tex` | `sampler2D` | Unit 2 | Depth map (currently unused) |
| `tex1` | `sampler2D` | Unit 3 | Secondary video input (Video B) |

### Uniform Parameters

| Uniform | Type | Mapped Range | Default | Description |
|---------|------|--------------|---------|-------------|
| `u_life_speed` | float | 0.0 - 1.0 | 5.0 → 0.5 | Controls feedback decay (0.9 + val*0.09) |
| `u_birth_thresh` | float | 0.0 - 1.0 | 6.0 → 0.6 | Brightness threshold to spawn life |
| `u_death_thresh` | float | 0.0 - 1.0 | 4.0 → 0.4 | **UNUSED** in current shader (legacy artifact) |
| `u_reaction_mix` | float | 0.0 - 1.0 | 2.0 → 0.2 | Blend between GoL (0) and Reaction-Diffusion (1) |
| `u_fractal_zoom` | float | 0.0 - 2.0 | 0.0 | Mandelbrot zoom intensity |
| `u_math_quantize` | float | 0.0 - 10.0 | 2.0 → 2.0 | Bit-crush steps: 2+(10-val) → 2-12 levels |
| `u_evolution` | float | 0.0 - 1.0 | 4.0 → 0.4 | Color cycling speed multiplier |
| `u_symmetry` | float | 0.0 - 1.0 | 0.0 | Horizontal mirroring strength |
| `u_grid_mix` | float | 0.0 - 1.0 | 2.0 → 0.2 | **UNUSED** — grid overlay not implemented |
| `u_chaos` | float | 0.0 - 5.0* | 1.0 → 1.0 | Random mutation rate (scaled by audio) |
| `u_feed_rate` | float | 0.0 - 0.1 | 5.0 → 0.05 | Gray-Scott feed parameter |
| `u_kill_rate` | float | 0.0 - 0.1 | 4.0 → 0.04 | Gray-Scott kill parameter |
| `u_mix` | float | — | 1.0 (hardcoded) | Final blend strength (always 100%) |

*`chaos` audio scaling: `chaos *= (1.0 + audio_energy * 0.5)` → effective max 7.5

**Time Uniforms:**
- `time`: float — global time in seconds
- `resolution`: vec2 — viewport resolution in pixels

### Output

- `fragColor`: `vec4` — final RGBA color (premultiplied alpha assumed)

---

## Edge Cases and Error Handling

### Critical Dependencies

1. **`texPrev` must be valid**: The shader reads from the previous frame buffer. If `texPrev` is uninitialized (black), the simulation will start from all-dead state and may take frames to become interesting.

2. **Dual-input detection**: The check `bool hasDual = (texture(tex1, vec2(0.5)).r + ...) > 0.001` samples a single pixel at (0.5,0.5). If Video B is connected but that pixel is black, it incorrectly falls back to Video A. **Recommendation:** Use a uniform flag instead.

3. **Resolution-dependent behavior**: `texel = 1.0 / resolution` assumes non-zero resolution. Zero resolution causes division by zero (GLSL undefined).

4. **Feedback loop integrity**: The effect relies on `texPrev` being the output of the previous frame. If the rendering pipeline breaks this chain (e.g., multi-pass without proper feedback), simulation desynchronizes.

### Parameter Edge Cases

| Parameter | Edge Case | Behavior |
|-----------|-----------|----------|
| `u_birth_thresh` | Set to 0.0 | All pixels spawn life → solid white noise |
| `u_birth_thresh` | Set to 1.0 | No seeding from video → only random mutations |
| `u_chaos` | Set to 0.0 | No random mutations → purely deterministic |
| `u_reaction_mix` | 0.0 | Pure binary Game of Life (flickering) |
| `u_reaction_mix` | 1.0 | Pure smooth Reaction-Diffusion (no binary cells) |
| `u_fractal_zoom` | > 0 | Adds color overlay; may blow out highlights if unchecked |
| `u_math_quantize` | 10.0 | 2 levels (extreme posterization) |
| `u_math_quantize` | 0.0 | 12 levels (minimal quantization) |
| `u_symmetry` | > 0 | Right half mirrors left; breaks temporal coherence |

### Unused Parameters

- `u_death_thresh`: Computed but never used in GoL rules (lines 110-113 use hard-coded 2.0/3.0 thresholds). **This is a bug.**
- `u_grid_mix`: Parameter exists but no grid overlay code in shader.

### Audio Reactivity

The `apply_uniforms` method attempts to scale `chaos` by audio energy:
```python
chaos *= (1.0 + audio_reactor.get_energy(0.8) * 0.5)
```
If `audio_reactor` is `None` or raises, silently ignored. No other parameters react to audio despite mappings.

---

## Mathematical Formulations

### 1. Brightness / Luminance

```glsl
float getBrightness(vec2 uv) {
    vec4 c = texture(texPrev, uv);
    return dot(c.rgb, vec3(0.299, 0.587, 0.114));  // Rec. 709 luma
}
```

**Note:** Input seeding uses `vec3(0.33)` (equal weights), creating slight inconsistency.

### 2. Game of Life Neighbor Count

```glsl
float neighbors = 0.0;
for(float i=-1.0; i<=1.0; i++) {
    for(float j=-1.0; j<=1.0; j++) {
        if(i==0.0 && j==0.0) continue;
        float b = getBrightness(uv + vec2(i,j)*texel);
        if(b > 0.5) neighbors += 1.0;
    }
}
```

**Threshold:** 0.5 is hard-coded; not parameterized.

### 3. Game of Life State Transition

```glsl
float alive = getBrightness(uv) > 0.5 ? 1.0 : 0.0;
float nextState = alive;

if(alive > 0.5) {
    if(neighbors < 2.0 || neighbors > 3.0) nextState = 0.0;  // Under/Overpopulation
} else {
    if(neighbors > 2.5 && neighbors < 3.5) nextState = 1.0;  // Reproduction (fuzzy)
}
```

**Fuzziness:** The dead-cell condition uses a range (2.5-3.5) instead of exact `==3`, creating smoother transitions between states.

### 4. Gray-Scott Reaction-Diffusion (Approximated)

Laplacian computation (4-connected):
```glsl
vec4 lap = -4.0 * center;
lap += texture(texPrev, uv + vec2(texel.x, 0));
lap += texture(texPrev, uv - vec2(texel.x, 0));
lap += texture(texPrev, uv + vec2(0, texel.y));
lap += texture(texPrev, uv - vec2(0, texel.y));
```

Update formula:
```glsl
vec4 duv = vec4(1.0, 0.5, 0.0, 0.0) * 0.2;  // Diffusion rates: A=0.2, B=0.1
vec4 rdColor = center + (duv * lap - center * kill + feed * (1.0 - center));
```

Where:
- `feed = u_feed_rate * 0.1` (range 0.0-0.1)
- `kill = u_kill_rate * 0.1` (range 0.0-0.1)

**This is NOT a true Gray-Scott model** (which uses separate A and B concentrations and proper Laplacian scaling). It's a visual hack that produces similar patterns.

### 5. Mandelbrot Set

```glsl
float mandelbrot(vec2 uv, float zoom) {
    vec2 c = (uv - 0.5) * 4.0 / zoom - vec2(0.5, 0.0);
    c += vec2(-0.745, 0.1);  // Fixed point in the seahorse valley
    vec2 z = vec2(0.0);
    float iter = 0.0;
    for(int i=0; i<20; i++) {
        z = vec2(z.x*z.x - z.y*z.y, 2.0*z.x*z.y) + c;
        if(length(z) > 4.0) break;
        iter += 1.0;
    }
    return iter / 20.0;  // Normalized to [0, 1]
}
```

Zoom is `exp(u_fractal_zoom * 2.0)`, so:
- `u_fractal_zoom = 0` → zoom = 1.0
- `u_fractal_zoom = 10` → zoom ≈ e^20 ≈ 4.85×10^8 (deep zoom)

### 6. Hash Function (for random mutations)

```glsl
float hash(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}
```

This is a standard GLSL hash function (based on iq's technique). Returns pseudo-random value in [0, 1).

### 7. Feedback Amount

```glsl
float feedbackAmount = 0.9 + u_life_speed * 0.09;  // Range: 0.9 - 1.0
fragColor = mix(original, finalSim, feedbackAmount * u_mix);
```

Since `u_mix = 1.0`, the blend factor is 90-99% simulation, 10-0% original.

---

## Performance Characteristics

### GPU Load

- **Fragment shader complexity:** Medium-High
  - 20 iterations of Mandelbrot (conditional)
  - 9 texture fetches per pixel (tex0, texPrev×8 neighbors, depth_tex, tex1)
  - Multiple conditionals (branching)
- **Memory bandwidth:** 9× RGBA texture reads per fragment
- **Fill-rate bound:** Yes, due to neighbor sampling

### Optimization Opportunities

1. **Neighbor sampling** could be done with a single 3×3 kernel fetch using `textureOffset` or a 2×2 rotated pattern (but current loop is clear).
2. **Mandelbrot** is conditional (`if(u_fractal_zoom > 0.0)`), so disabled by default (presets set to 0.0).
3. **Depth texture** is bound but never used — can be removed.
4. **Symmetry** only mirrors right half; could be done in vertex shader or via viewport transform.

### Expected Frame Rates

- **Modern desktop GPU (GTX 1060+)**: 60+ FPS at 1080p
- **Integrated GPU**: 30-45 FPS at 720p
- **Mobile (Adreno 6xx)**: 30 FPS at 720p (thermal throttling likely)

---

## Test Plan

### Unit Tests (CPU-side)

1. **Parameter Mapping**
   - Verify `_map_param(name, 0.0, 1.0)` correctly maps 0→0.0, 5→0.5, 10→1.0
   - Test all 12 parameters

2. **State Serialization**
   - `get_state()` returns dict with `'name'`, `'enabled'`, `'parameters'`
   - Parameters dict is a deep copy (mutations don't affect original)

3. **Preset Loading**
   - All 3 presets contain all 12 keys
   - Values are within 0-10 range

4. **Audio Reactivity**
   - When `audio_reactor` is `None`, `apply_uniforms` doesn't crash
   - When `audio_reactor.get_energy()` raises, exception is caught and ignored

### Integration Tests (GPU/Shader)

5. **Game of Life Known Patterns**
   - Seed a glider pattern (3×3 block) and verify it translates correctly over frames
   - Seed a still life (block) and verify it remains stable
   - Requires rendering to feedback buffer and reading back pixels

6. **Reaction-Diffusion Spots**
   - Seed single white pixel on black, `u_reaction_mix=1.0`, appropriate feed/kill (e.g., 0.03/0.06)
   - Expect expanding spot with halo (Turing pattern)

7. **Dual-Input Switching**
   - Render with `tex1` all black → should use `tex0`
   - Render with `tex1` having one non-black pixel at (0.5,0.5) → should use `tex1`
   - **Note:** This is a fragile test; better to test with explicit uniform flag.

8. **Mandelbrot Overlay**
   - Set `u_fractal_zoom=10.0`, verify colored fractal pattern appears
   - Check that zoom centers on (-0.745, 0.1)

9. **Quantization**
   - Set `u_math_quantize=10.0`, expect posterized output (2 levels)
   - Set `u_math_quantize=0.0`, expect smooth gradients (12 levels)

10. **Symmetry**
    - Set `u_symmetry=1.0`, verify right half mirrors left half

### Regression Tests

11. **Preset Comparison**
    - Render each preset for 100 frames, capture frame 50
    - Compare against golden images (MD5 or SSIM > 0.99)

12. **Parameter Sweep**
    - Render with each parameter at 0, 5, 10 while others neutral
    - Verify monotonic visual change (e.g., more chaos → more random pixels)

### Minimum Coverage Target

- **CPU code:** 80% line coverage (test all branches in `apply_uniforms`)
- **Shader:** Not unit-testable; rely on visual regression tests

---

## Definition of Done

- [x] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-EXT026: CellularAutomataDatamoshEffect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES

**Primary Implementation:**
- `/home/happy/Desktop/claude projects/VJlive-2/plugins/vdatamosh/cellular_automata_datamosh.py` (lines 1-265)
- `/home/happy/Desktop/claude projects/VJlive-2/plugins/core/cellular_automata_datamosh/__init__.py` (duplicate)
- `/home/happy/Desktop/claude projects/VJlive-2/plugins/core/cellular_automata_datamosh/plugin.json` (metadata)

**Registration:**
- `/home/happy/Desktop/claude projects/VJlive-2/core/matrix/node_datamosh.py` (line 28: `CellularAutomata = _safe_import(...)`)

**Known Issues (from legacy):**
1. `u_death_thresh` and `u_grid_mix` are defined but unused
2. Dual-input detection uses single-pixel sample (fragile)
3. `u_mix` is hardcoded to 1.0, making parameter ineffective
4. Depth texture bound but not used
5. Audio mappings defined but only `chaos` actually reacts

---

## Migration Notes to VJLive3

### WebGPU / WGSL Considerations

The current GLSL 330 shader must be ported to WGSL. Key changes:

1. **Texture bindings**: WGSL uses explicit `@group(0) @binding(N)` annotations
2. **Fragment output**: `@fragment` function returns `vec4<f32>` or `output.color`
3. **Array indexing**: Loops with non-constant bounds require `for` loops with `var<workgroup>` or fixed unroll
4. **Texture sampling**: `textureSample(texture, sampler, uv)` instead of `texture(tex, uv)`
5. **Precision**: Add `f32` precision annotations if targeting mobile

**Suggested WGSL structure:**
```wgsl
struct Uniforms {
    time: f32,
    resolution: vec2<f32>,
    life_speed: f32,
    birth_thresh: f32,
    // ... all other uniforms
};

@group(0) @binding(0) var tex0: texture_2d<f32>;
@group(0) @binding(1) var texPrev: texture_2d<f32>;
// ... etc

@fragment
fn main(@location(0) uv: vec2<f32>) -> @location(0) vec4<f32> {
    // Shader logic
}
```

### Python Wrapper Refactor

The legacy `Effect` base class likely expects:
- `FRAGMENT` class attribute (GLSL string)
- `__init__` setting `self.parameters`
- `apply_uniforms` calling `self.shader.set_uniform(name, value)`

In VJLive3, this should be adapted to the new plugin architecture. The spec assumes the same pattern but actual implementation may differ.

### Parameter Range Adjustments

Current mapping assumes 0-10 input range. Consider:
- Expose actual meaningful ranges in UI (e.g., `feed_rate` 0.0-0.1, not 0-10)
- Or keep 0-10 sliders and document mapping internally

---

## Open Questions (Needs Research)

1. **What is the `Effect` base class API?** Need to inspect `src/vjlive3/plugins/` or `core/effects/` to understand how shaders are compiled and uniforms set.
2. **How is the feedback buffer (`texPrev`) managed?** Is it a ping-pong FBO? Who swaps the textures each frame?
3. **What is the audio_reactor interface?** Does it have `get_energy(band)`? What does the band parameter mean (0.8 = high/mid/bass?)?
4. **Is `u_mix` intended to be user-controllable?** It's hardcoded to 1.0; should it be a parameter?
5. **Should `u_death_thresh` and `u_grid_mix` be removed or implemented?** Legacy code suggests they were intended but never finished.

---
