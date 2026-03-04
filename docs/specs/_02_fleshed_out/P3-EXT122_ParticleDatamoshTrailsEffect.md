# P3-EXT122 — ParticleDatamoshTrailsEffect

**Specification Status:** 🟩 COMPLETING PASS 2  
**Agent:** desktop-roo  
**Date:** 2026-03-04  
**Tier:** Pro-Tier Native  
**Phase:** Pass 2 — Fleshed Out  

---

## Task: P3-EXT122 — ParticleDatamoshTrailsEffect

### What This Module Does

`ParticleDatamoshTrailsEffect` implements a 3D particle system where particles leave persistent datamosh trails that accumulate and decay over time. The effect combines depth-aware particle positioning with glitch-style trail persistence, creating a volumetric, motion-blurred particle field that exhibits datamosh characteristics (frame hold, temporal displacement, and decay).

The effect is designed to work within the VJLive3 plugin architecture, inheriting from the `DepthParticle3DEffect` base class (which provides depth-camera integration and 3D particle positioning) and overriding the shader to implement the datamosh trail accumulation.

### What This Module Does NOT Do

- Does NOT provide a full 3D physics simulation (particles follow simple velocity/acceleration models)
- Does NOT replace the depth camera system (requires an external `AstraDepthSource` or similar)
- Does NOT handle audio analysis directly (delegates to `AudioReactor` via the base class)
- Does NOT implement advanced datamosh effects like block corruption or macroblock tearing (focuses on trail persistence)

---

## Detailed Behavior and Parameter Interactions

### Overview

The effect maintains two framebuffer textures:
1. **Current frame** (`tex0`): The current particle rendering
2. **Trail accumulation** (`texPrev`): Accumulated trails from previous frames

Each frame:
1. Render particles to `tex0` using depth data for positioning
2. Blend `tex0` with `texPrev` based on `trail_mix` parameter
3. Add a portion of the accumulated trails to create persistence
4. Decay the trail buffer by `datamosh_decay` to gradually fade old trails
5. Store the result back into `texPrev` for the next frame

### Parameters

| Parameter | WGSL Uniform | Range | Default | Audio Source | Description |
|-----------|--------------|-------|---------|--------------|-------------|
| `trail_mix` | `u_mix` | 0.0–1.0 | 0.5 | None | Blend factor between current frame and accumulated trails. Higher values preserve more trail history. |
| `datamosh_decay` | `u_datamosh_decay` | 0.0–1.0 | 0.95 | None | Decay rate per frame. 1.0 = no decay (infinite trails), 0.0 = instant fade. |
| `particle_count` | `u_particle_count` | 100–10000 | 1000 | None | Number of particles to render (affects performance). |
| `depth_scale` | `u_depth_scale` | 0.0–10.0 | 2.0 | None | Multiplier for depth values to control particle Z-displacement. |
| `trail_strength` | `u_trail_strength` | 0.0–5.0 | 1.5 | None | Multiplier applied to trail accumulation before blending. |
| `color_shift` | `u_color_shift` | 0.0–1.0 | 0.0 | None | Hue rotation applied to trails vs. current frame (creates chromatic trail effect). |
| `glitch_intensity` | `u_glitch_intensity` | 0.0–1.0 | 0.1 | None | Probability of random UV offset per frame (simulates datamosh corruption). |
| `audio_react` | `u_audio_react` | 0.0–2.0 | 0.0 | `energy` | Audio reactivity multiplier for particle size/velocity. |

### Parameter Interactions

- **Trail persistence** is controlled by the interplay of `trail_mix` and `datamosh_decay`. High `trail_mix` + low `decay` creates long, ghostly trails; low `trail_mix` + high `decay` creates short, snappy trails.
- **Depth scaling** affects how particles emerge from the depth map. Higher values push particles further into Z-space, affecting their screen-space size and parallax.
- **Glitch intensity** introduces random UV offsets that simulate datamosh corruption. This is independent of the trail accumulation and affects both current frame and trails.
- **Audio react** scales particle velocity and size based on audio energy, creating a reactive effect where bass hits cause particle bursts.

---

## Public Interface

### Class: `ParticleDatamoshTrailsEffect`

**Inherits from:** `DepthParticle3DEffect` (provides depth integration, particle system management)

**Metadata:**
```python
METADATA = {
    "spec": "P3-EXT122",
    "tier": "Pro-Tier Native",
    "version": "1.0.0",
    "category": "datamosh",
    "tags": ["particles", "datamosh", "trails", "depth"]
}
```

**Constructor:**
```python
def __init__(self) -> None:
    """Initialize effect with default parameters."""
```

**Key Methods:**

- `get_fragment_shader() -> str`  
  Returns the WGSL fragment shader source that implements the trail accumulation logic.

- `apply_uniforms(time, resolution, audio_reactor=None, semantic_layer=None) -> None`  
  Dispatches all parameters to the GPU via `self.set_uniform(name, value)`.  
  Audio modulation: `audio_react` parameter is boosted by `audio_reactor.get_energy()`.

- `load_preset(preset_name: str) -> None`  
  Presets: `"default"`, `"long_trails"` (high mix, low decay), `"glitchy"` (high glitch intensity).

- `get_state() -> Dict[str, Any]`  
  Serializes current parameter values for preset saving/loading.

**Uniforms Set:**
- `u_mix` (float)
- `u_datamosh_decay` (float)
- `u_particle_count` (float)
- `u_depth_scale` (float)
- `u_trail_strength` (float)
- `u_color_shift` (float)
- `u_glitch_intensity` (float)
- `u_audio_react` (float)
- Plus inherited uniforms from `DepthParticle3DEffect` (time, resolution, depth texture, particle positions/velocities)

---

## Inputs and Outputs

### Inputs

| Input | Type | Description |
|-------|------|-------------|
| `tex0` | `texture_2d<f32>` | Current video frame (background texture) |
| `texPrev` | `texture_2d<f32>` | Trail accumulation buffer from previous frame |
| `depth_tex` | `texture_2d<f32>` | Depth map from Astra or other depth camera |
| `tex1` | `texture_2d<f32>` (optional) | Secondary video input for crossfading (if `hasDual` enabled) |
| `sampler` | `sampler` | Linear filtering sampler for all textures |

### Outputs

- **Fragment shader output** (`fragColor`): RGBA color with trail-blended result
- **Uniform updates**: All parameters pushed to GPU via `set_uniform()`
- **State serialization**: `get_state()` returns dict for persistence

### Data Flow

```
depth_tex → particle positioning (vertex shader) → particle rendering → tex0
tex0 + texPrev → trail blend + decay → new texPrev (feedback loop)
final_color = mix(current_frame, trails, u_mix) + trails * decay
```

---

## Edge Cases and Error Handling

### Edge Cases

1. **No depth camera connected**  
   - `depth_tex` may be all zeros or uninitialized  
   - Effect should render particles at default Z=0 plane (no depth modulation)  
   - Log warning: `"ParticleDatamoshTrailsEffect: depth_tex empty, using flat plane"`

2. **Particle count exceeds GPU limits**  
   - Clamp `u_particle_count` to maximum supported by vertex buffer (typically 100,000)  
   - Log warning if user requests > max: `"Requested 50000 particles, clamping to 100000"`

3. **Trail buffer not allocated**  
   - On first frame, `texPrev` may be null  
   - Initialize to transparent black (`vec4<f.0>`)  
   - Ensure `RenderPipeline` creates the feedback texture with same resolution as `tex0`

4. **Extreme decay values**  
   - `datamosh_decay = 0.0` → trails vanish instantly (effectively disables trail accumulation)  
   - `datamosh_decay = 1.0` → trails never fade (infinite accumulation, may cause memory/performance issues)  
   - Clamp to [0.01, 1.0] range in `apply_uniforms()` with log warnings for out-of-range values

5. **Audio reactor not available**  
   - `audio_react` parameter defaults to 0.0  
   - No audio modulation occurs; particles move at base velocity

6. **Resolution mismatch**  
   - If `texPrev` resolution differs from `tex0`, reallocate `texPrev` to match `tex0`  
   - This can happen on window resize or output resolution change

### Error Handling

- **Shader compilation failure**: Raise `RuntimeError` with WGSL error log; fallback to simple blend shader if available
- **Uniform setting errors**: Catch and log `ValueError` (type mismatch) but do not crash
- **Depth texture format mismatch**: Verify `depth_tex` is `r32float` or `rgba8`; convert if necessary (performance warning)

---

## Mathematical Formulations

### Trail Accumulation

The core fragment shader logic (WGSL):

```wgsl
// Sample current frame and accumulated trails
let current = textureSample(tex0, samp, uv);
let trails = textureSample(texPrev, samp, uv);

// Apply glitch offset if enabled
var glitch_uv = uv;
if (uniforms.u_glitch_intensity > 0.0) {
    let offset = (random(uv + time) - 0.5) * uniforms.u_glitch_intensity * 0.1;
    glitch_uv = uv + offset;
}

// Blend current frame with trails
var color = mix(current, trails, uniforms.u_mix);

// Add decayed trails for persistence
color += trails * uniforms.u_datamosh_decay * uniforms.u_trail_strength;

// Apply color shift to trails (chromatic separation)
if (uniforms.u_color_shift > 0.0) {
    let shift = uniforms.u_color_shift * 0.1;
    color.r = mix(color.r, trails.b, shift);
    color.b = mix(color.b, trails.r, shift);
}

// Final mix with audio reactivity
fragColor = color;
```

**Mathematical expression:**

Let:
- `C_t` = current frame color at time t
- `T_{t-1}` = accumulated trails from previous frame
- `m` = `u_mix` ∈ [0, 1]
- `d` = `u_datamosh_decay` ∈ [0, 1]
- `s` = `u_trail_strength` ≥ 0
- `g` = `u_glitch_intensity` ∈ [0, 1]

Then:

```
T_t = (1 - d) * (mix(C_t, T_{t-1}, m) + s * T_{t-1})
Output = T_t
```

Where `mix(a, b, α) = a * (1-α) + b * α`.

### Particle Positioning (from DepthParticle3DEffect)

Particle screen-space position derived from depth map:

```
uv_sample = particle_uv + offset * depth_scale
depth = texture(depth_tex, uv_sample).r
z = depth * u_depth_scale
screen_pos = project(particle_uv, z)
```

### Audio Reactivity

```
audio_factor = 1.0 + audio_reactor.get_energy() * u_audio_react
particle_velocity *= audio_factor
particle_size *= min(audio_factor, 1.5)  // cap size growth
```

---

## Performance Characteristics

### Computational Complexity

- **Vertex shader**: O(N) where N = particle count (typically 1K–10K)
- **Fragment shader**: O(resolution) per frame for full-screen trail blend + O(N) for particle rendering
- **Memory**: 2× framebuffer size (current + trail buffer) + particle vertex buffer

### Benchmarks (estimated, based on similar effects)

| Particle Count | Resolution | Expected FPS (RTX 4060) | Memory Usage |
|----------------|------------|------------------------|--------------|
| 1,000 | 1920×1080 | 60–120 FPS | ~150 MB |
| 5,000 | 1920×1080 | 30–60 FPS | ~200 MB |
| 10,000 | 1920×1080 | 15–30 FPS | ~300 MB |

### Optimization Strategies

1. **Particle culling**: Skip particles outside view frustum (reduces vertex count)
2. **Trail resolution scaling**: Render trail buffer at ½ resolution, upscale in final blend (reduces full-screen pass cost)
3. **Decay clamping**: If `d ≥ 0.99`, skip explicit decay pass (trails effectively permanent)
4. **Glitch as compute shader**: Offload random offset generation to compute pass for large particle counts

---

## Test Plan

### Unit Tests (Minimum 80% Coverage)

**Test 1: Parameter Mapping**  
```python
def test_parameter_ranges():
    effect = ParticleDatamoshTrailsEffect()
    effect.apply_uniforms(0.0, (1920, 1080))
    
    # Verify all uniforms set within expected ranges
    assert 0.0 <= effect.params["trail_mix"] <= 1.0
    assert 0.01 <= effect.params["datamosh_decay"] <= 1.0
    assert 100 <= effect.params["particle_count"] <= 10000
```

**Test 2: Trail Accumulation Logic**  
```python
def test_trail_accumulation():
    effect = ParticleDatamoshTrailsEffect()
    effect.params["trail_mix"] = 0.5
    effect.params["datamosh_decay"] = 0.9
    effect.params["trail_strength"] = 1.0
    
    # Simulate two frames with known colors
    # Frame 1: white current, black trails → expect 0.5*white + 0.9*0*trails
    # Frame 2: black current, white trails from frame 1 → expect mix + decay
    # Verify mathematical correctness
```

**Test 3: Audio Reactivity**  
```python
def test_audio_reactivity():
    effect = ParticleDatamoshTrailsEffect()
    effect.params["audio_react"] = 1.0
    
    class MockAudioReactor:
        def get_energy(self):
            return 0.8
    
    effect.apply_uniforms(0.0, (1920, 1080), audio_reactor=MockAudioReactor())
    # Verify u_audio_react uniform boosted by ~0.8 * 1.0 = 0.8
```

**Test 4: Preset Loading**  
```python
def test_presets():
    effect = ParticleDatamoshTrailsEffect()
    effect.load_preset("long_trails")
    assert effect.params["trail_mix"] > 0.8
    assert effect.params["datamosh_decay"] < 0.5
    
    effect.load_preset("glitchy")
    assert effect.params["glitch_intensity"] > 0.5
```

**Test 5: Shader Compilation**  
```python
def test_shader_compiles():
    effect = ParticleDatamoshTrailsEffect()
    shader_source = effect.get_fragment_shader()
    # Compile through RenderPipeline (mock or real)
    pipeline = RenderPipeline(shader_source, "test")
    assert pipeline is not None
```

**Test 6: Edge Case - Zero Particles**  
```python
def test_zero_particles():
    effect = ParticleDatamoshTrailsEffect()
    effect.params["particle_count"] = 0
    # Should not crash; render only trail buffer
```

**Test 7: Edge Case - Max Decay**  
```python
def test_max_decay():
    effect = ParticleDatamoshTrailsEffect()
    effect.params["datamosh_decay"] = 1.0
    # Trails should accumulate indefinitely without fading
```

**Test 8: State Serialization**  
```python
def test_get_state():
    effect = ParticleDatamoshTrailsEffect()
    state = effect.get_state()
    assert "name" in state
    assert "params" in state
    assert isinstance(state["params"], dict)
```

### Integration Tests

- **Test with real depth camera**: Feed synthetic depth map (gradient) and verify particles disperse in Z
- **Test trail feedback loop**: Run 10 frames, verify trail buffer evolves correctly (no NaN/Inf values)
- **Test resolution change**: Resize output from 1080p to 4K, verify trail buffer reallocation

---

## Definition of Done

- [x] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-EXT122: ParticleDatamoshTrailsEffect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES

### VJlive (Original) Implementation

**File:** `core/effects/particle_datamosh_trails.py` (partial)  
**Plugin registration:** `plugins/vdatamosh/__init__.py`  
**Spec reference:** `plans/3d_datamosh_plugin_specifications.md`

The original implementation showed the trail blend pattern:

```glsl
// Blend trails with current frame
fragColor = mix(current, trail_color, u_mix * 0.5);

// Add some of the accumulated trails for persistence
fragColor += trails * datamosh_decay * u_mix;
```

The VJLive3 version expands this with:
- Full WGSL uniform struct
- Audio reactivity via `AudioReactor`
- Depth-camera integration via `DepthParticle3DEffect` base
- Configurable particle count and glitch effects

### Related Effects

- **P3-EXT013** `BadTripDatamoshEffect` — similar 12-param datamosh pattern, provides template for `apply_uniforms()` and preset system
- **P3-EXT111** `MoshPitDatamoshEffect` — panic attack + camera shake pattern
- **P7-VE43** `MirrorEffect` — simple WGSL blend example
- **P3-EXT112** `MultibandColorEffect` — multi-parameter uniform dispatch

---

## Implementation Notes for Phase 3

1. **Base class location**: `DepthParticle3DEffect` should be defined in `src/vjlive3/plugins/particle_3d.py` or similar. If not present, create as subclass of `Effect` with depth integration.
2. **Vertex shader**: Inherit from base; particles should be positioned using depth map as heightfield.
3. **Framebuffer management**: The effect needs access to `texPrev` feedback texture. The render engine (`RenderEngine`) should provide this via `get_framebuffer("trails")` or similar.
4. **Uniform naming**: Follow convention `u_<parameter>`; all floats.
5. **Audio integration**: Use `audio_reactor.get_energy()` and `audio_reactor.get_band("bass")` if needed.
6. **Performance**: Default `particle_count = 1000` is safe for 60 FPS on mid-range GPUs.

---

**End of Spec**  
✅ Ready for Phase 3 implementation
