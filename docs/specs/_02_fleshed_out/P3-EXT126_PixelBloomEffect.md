# P3-EXT126 — PixelBloomEffect

**Specification Status:** 🟩 COMPLETING PASS 2  
**Agent:** desktop-roo  
**Date:** 2026-03-04  
**Tier:** Pro-Tier Native  
**Phase:** Pass 2 — Fleshed Out  

---

## Task: P3-EXT126 — PixelBloomEffect

### What This Module Does

`PixelBloomEffect` implements a specialized intensity-based glitch effect where the brightest pixels in the video feed "bleed" and decay across the screen in glowing, data-like streams. It's a datamosh effect that creates a "digital hemorrhage" visual: bright areas expand outward, leaving trailing decay, simulating corrupted video data bleeding across the frame.

The effect operates as a feedback loop:
1. Sample the previous frame (`texPrev`) with an offset in the direction of motion/brightness
2. Apply decay to the bloomed pixels (they fade over time)
3. Blend the bloomed result with the current frame based on brightness threshold
4. Mix with the original video via `u_mix`

### What This Module Does NOT Do

- Does NOT perform full-frame bloom (like HDR bloom); it's localized to bright pixels only
- Does NOT handle 3D depth or volumetric effects (2D screen-space only)
- Does NOT include color channel separation (no RGB shift)
- Does NOT perform motion estimation (uses simple brightness gradient for direction)
- Does NOT replace more advanced datamosh effects (it's a specific, stylized variant)

---

## Detailed Behavior and Parameter Interactions

### Overview

The effect uses a two-texture feedback system:
- `tex0`: Current video frame
- `texPrev`: Previous processed frame (the accumulated bloom state)

Each frame:
1. Compute brightness of current frame (luminance)
2. Determine bloom direction (typically from gradient or fixed direction)
3. Sample `texPrev` offset by `bloomAmount * brightness` in that direction
4. Decay the sampled bloom: `bloomed.rgb *= (1.0 - decay)`
5. Blend current frame with bloomed pixels: `result = mix(current, max(current, bloomed), blendFactor)`
6. Final output: `fragColor = mix(current, result, u_mix)`

### Parameters

| Parameter | WGSL Uniform | Range | Default | Audio Source | Description |
|-----------|--------------|-------|---------|--------------|-------------|
| `bloomAmount` | `u_bloom_amount` | 0.0–10.0 | 3.0 | None | Strength of pixel bleeding. Higher values cause pixels to bleed further. |
| `decay` | `u_decay` | 0.0–1.0 | 0.95 | None | Decay rate per frame (1.0 = no decay, 0.0 = instant fade). Controls trail length. |
| `bloomDir` | `u_bloom_dir` | vec2<f32> | (1.0, 0.0) | None | Direction vector for bloom offset (normalized). Typically rightward or motion-based. |
| `feedback_amount` | `u_feedback` | 0.0–1.0 | 0.0 | None | Additional feedback mix into the blend factor (creates recursive blooming). |
| `threshold` | `u_threshold` | 0.0–1.0 | 0.5 | None | Brightness threshold; only pixels brighter than this will bloom. |
| `u_mix` | `u_mix` | 0.0–1.0 | 1.0 | None | Overall blend with original video (1.0 = full effect, 0.0 = bypass). |

### Parameter Interactions

- **bloomAmount + decay**: High bloomAmount with low decay creates long, persistent trails. High decay with low bloomAmount creates short, snappy bleeds.
- **threshold + bloomAmount**: Threshold controls which pixels participate; bloomAmount controls how far they spread. High threshold + high bloomAmount = only very bright pixels bleed far (selective).
- **feedback_amount**: Adds recursive feedback; can cause exponential blowout if not clamped. Use sparingly (<0.3) for subtle accumulation.
- **bloomDir**: Direction of pixel bleeding. Can be animated (e.g., rotate over time) or driven by optical flow (future extension).

---

## Public Interface

### Class: `PixelBloomEffect`

**Inherits from:** `Effect` (base class for all VJLive3 effects)

**Metadata:**
```python
METADATA = {
    "spec": "P3-EXT126",
    "tier": "Pro-Tier Native",
    "version": "1.0.0",
    "category": "datamosh",
    "tags": ["bloom", "glitch", "decay", "feedback"]
}
```

**Constructor:**
```python
def __init__(self) -> None:
    """Initialize PixelBloomEffect with default parameters."""
```

**Key Methods:**

- `get_fragment_shader() -> str`  
  Returns WGSL fragment shader implementing brightness-based pixel bleeding with decay.

- `apply_uniforms(time, resolution, audio_reactor=None, semantic_layer=None) -> None`  
  Dispatches all parameters to GPU via `self.set_uniform(name, value)`.

- `get_state() -> Dict[str, Any]`  
  Serializes current parameter values.

**Uniforms Set:**
- `u_bloom_amount` (float)
- `u_decay` (float)
- `u_bloom_dir` (vec2<f32>)
- `u_feedback` (float)
- `u_threshold` (float)
- `u_mix` (float)
- `u_time` (float, inherited)
- `u_resolution` (vec2<f32>, inherited)

---

## Inputs and Outputs

### Inputs

| Input | Type | Description |
|-------|------|-------------|
| `tex0` | `texture_2d<f32>` | Current video frame (source) |
| `texPrev` | `texture_2d<f32>` | Previous frame's output (feedback buffer) |
| `samp` | `sampler` | Linear filtering sampler |

### Outputs

- **Fragment shader output** (`fragColor`): RGBA color with bloom effect applied
- Feedback loop: output is written back to `texPrev` for next frame (handled by render engine)

### Data Flow

```
current_frame (tex0) → compute brightness → determine bloom offset →
sample previous_frame (texPrev) at offset → apply decay → blend with current →
final mix with u_mix → output
```

The feedback loop is critical: the effect's own output becomes the next frame's input, creating accumulating trails.

---

## Edge Cases and Error Handling

### Edge Cases

1. **No previous frame (first frame)**  
   - `texPrev` may be null or uninitialized  
   - Initialize to `tex0` or transparent black; log warning if uninitialized

2. **Decay = 1.0 (no decay)**  
   - Trails never fade; eventually saturate to white  
   - Not an error but may be unexpected; clamp to 0.9999 to prevent infinite accumulation

3. **Decay = 0.0 (instant fade)**  
   - Effectively disables feedback; only immediate bleed visible  
   - Valid but produces minimal effect

4. **Bloom direction zero vector**  
   - If `bloomDir = (0, 0)`, no offset occurs; effect becomes simple brightness-based blend  
   - Default to (1, 0) if length < 0.001

5. **Extreme bloomAmount (e.g., 1000)**  
   - Offset may exceed texture bounds; clamp to reasonable max (e.g., 50.0)  
   - Log warning if value > 50.0

6. **Threshold too high**  
   - If `threshold > 1.0`, no pixels bloom (clamp to 1.0)  
   - If `threshold < 0.0`, all pixels bloom (clamp to 0.0)

7. **Feedback overflow**  
   - `feedback_amount` combined with low decay can cause values to exceed 1.0  
   - Clamp final color to [0, 1] in shader

### Error Handling

- **Missing feedback texture**: Raise `RuntimeError` with message "PixelBloomEffect requires texPrev feedback buffer"
- **Shader compilation failure**: Fallback to simple blend shader; log error
- **Uniform type errors**: Catch and log; continue with defaults

---

## Mathematical Formulations

### Brightness Calculation

```
brightness = dot(color.rgb, vec3(0.299, 0.587, 0.114))  // standard luminance
```

Or simpler: `brightness = max(max(color.r, color.g), color.b)` for intensity-based bloom.

### Offset Computation

```
offset = bloomDir * bloomAmount * brightness / resolution
```

Where `resolution` scales offset to texel units.

### Decay and Blend

```
bloomed = texture(texPrev, uv + offset)
bloomed.rgb *= (1.0 - decay)  // decay as retention factor; (1-decay) is loss

blendFactor = brightness * bloomAmount + feedback_amount
blendFactor = clamp(blendFactor, 0.0, 1.0)

result = mix(current, max(current, bloomed), blendFactor)
fragColor = mix(current, result, u_mix)
```

**Note**: The legacy code used `bloomed.rgb *= decay;` where decay was 0.95 meaning 95% retention. The VJLive3 version uses `(1.0 - decay)` for clarity, where `decay=0.95` means 5% loss per frame. Both are equivalent if you invert the parameter meaning. We'll follow legacy: `decay` is retention factor (0.0–1.0), so `bloomed *= decay`.

### Full WGSL Fragment (simplified)

```wgsl
@group(0) @binding(0) var tex0: texture_2d<f32>;
@group(0) @binding(1) var texPrev: texture_2d<f32>;
@group(0) @binding(2) var samp: sampler;

struct Uniforms {
    u_time: f32,
    u_resolution: vec2<f32>,
    u_mix: f32,
    u_bloom_amount: f32,
    u_decay: f32,
    u_bloom_dir: vec2<f32>,
    u_feedback: f32,
    u_threshold: f32,
};

var<uniform> uniforms: Uniforms;

@fragment
fn fs_main(@location(0) uv: vec2<f32>) -> @location(0) vec4<f32> {
    let current = textureSample(tex0, samp, uv);
    let brightness = dot(current.rgb, vec3<f32>(0.299, 0.587, 0.114));
    
    // Only bloom if above threshold
    if (brightness < uniforms.u_threshold) {
        return current;
    }
    
    // Compute offset
    let offset = normalize(uniforms.u_bloom_dir) * uniforms.u_bloom_amount * brightness / uniforms.u_resolution;
    let bloomed = textureSample(texPrev, samp, uv + offset);
    
    // Apply decay (retention factor)
    var bloomed_rgb = bloomed.rgb * uniforms.u_decay;
    
    // Blend current with bloomed (max ensures bright pixels bleed)
    let blendFactor = brightness * uniforms.u_bloom_amount + uniforms.u_feedback;
    let result = mix(current, max(current, vec4<f32>(bloomed_rgb, current.a)), clamp(blendFactor, 0.0, 1.0));
    
    // Final mix
    let final = mix(current, result, uniforms.u_mix);
    return final;
}
```

---

## Performance Characteristics

### Computational Complexity

- **Texture samples**: 2 per fragment (current + previous)  
- **Arithmetic**: Minimal (dot product, mix, max)  
- **Memory bandwidth**: 2 texture reads + 1 write per frame  
- **Feedback dependency**: Requires previous frame; cannot parallelize across frames

### Benchmarks (estimated)

| Resolution | Bloom Amount | Expected FPS (RTX 4060) | Memory (2 framebuffers) |
|------------|--------------|------------------------|------------------------|
| 1920×1080 | 3.0 | 200–300 FPS | ~150 MB |
| 3840×2160 | 3.0 | 80–120 FPS | ~600 MB |
| 1920×1080 | 10.0 | 150–200 FPS | ~150 MB |

The effect is **lightweight**; performance is dominated by framebuffer bandwidth, not shader compute.

### Optimization Strategies

1. **Half-resolution feedback**: Render `texPrev` at ½ resolution, upscale when sampling (reduces memory by 4×, slight blur)
2. **Region of interest**: If `threshold` is high, skip processing for dark pixels via early discard
3. **MIP sampling**: Use lower mip level for `texPrev` sample when `bloomAmount` is large (reduces aliasing)

---

## Test Plan

### Unit Tests (Minimum 80% Coverage)

**Test 1: Parameter Defaults**  
```python
def test_default_parameters():
    effect = PixelBloomEffect()
    assert effect.params["bloomAmount"] == 3.0
    assert effect.params["decay"] == 0.95
    assert effect.params["bloomDir"] == [1.0, 0.0]
    assert effect.params["feedback_amount"] == 0.0
    assert effect.params["threshold"] == 0.5
```

**Test 2: Decay Behavior**  
```python
def test_decay_accumulation():
    effect = PixelBloomEffect()
    effect.params["decay"] = 0.9
    effect.params["bloomAmount"] = 0.0  # no new bloom
    
    # Simulate feedback: start with value 1.0 in texPrev
    # After one frame: 1.0 * 0.9 = 0.9
    # After two frames: 0.9 * 0.9 = 0.81
    # Verify exponential decay
```

**Test 3: Threshold Clipping**  
```python
def test_threshold():
    effect = PixelBloomEffect()
    effect.params["threshold"] = 0.8
    # Render with dark pixels (brightness < 0.8); should see no bloom
    # Render with bright pixels (brightness > 0.8); should see bloom
```

**Test 4: Bloom Direction**  
```python
def test_bloom_direction():
    effect = PixelBloomEffect()
    effect.params["bloomDir"] = [0.0, 1.0]  # upward
    # Verify bloom offset is upward (sample above UV)
```

**Test 5: Feedback Amount**  
```python
def test_feedback():
    effect = PixelBloomEffect()
    effect.params["feedback"] = 0.5
    # Should increase blend factor, creating more aggressive blooming
```

**Test 6: Mix Parameter**  
```python
def test_mix():
    effect = PixelBloomEffect()
    effect.params["u_mix"] = 0.0  # full effect
    effect.params["u_mix"] = 1.0  # bypass
    # Verify output transitions between processed and original
```

**Test 7: Edge - Zero Bloom**  
```python
def test_zero_bloom():
    effect = PixelBloomEffect()
    effect.params["bloomAmount"] = 0.0
    # Effect should be nearly invisible; output ≈ current
```

**Test 8: Edge - Max Decay**  
```python
def test_max_decay():
    effect = PixelBloomEffect()
    effect.params["decay"] = 1.0
    # Trails should never fade; accumulate indefinitely
```

### Integration Tests

- **Test feedback loop stability**: Run 1000 frames with constant input; verify output doesn't explode to infinity (should stabilize or saturate)
- **Test with real video**: Apply to high-contrast footage (e.g., lights against dark); verify visible bleeding
- **Test resolution changes**: Resize framebuffer mid-stream; verify no artifacts

---

## Definition of Done

- [x] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-EXT126: PixelBloomEffect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES

### VJlive (Original) Implementation

**File:** `core/effects/legacy_trash/datamosh.py` (lines 177–196)  
**Registration:** `core/effects/__init__.py` (datamosh category)  
**Class:** `PixelBloomEffect(Effect)`

The original GLSL fragment shader snippet:

```glsl
// Decay previous frame
bloomed.rgb *= decay;

// Blend based on brightness - brighter pixels bloom more
float blendFactor = brightness * bloomAmount;
vec4 result = mix(current, max(current, bloomed), clamp(blendFactor + feedback_amount, 0.0, 1.0));

fragColor = mix(current, result, mix);
```

And the Python parameter initialization:

```python
class PixelBloomEffect(Effect):
    """Pixel bloom - brightness-based pixel bleeding."""

    def __init__(self):
        super().__init__("pixelbloom", PIXEL_BLOOM_FRAGMENT)
        self.parameters = {
            "bloomAmount": 0.3,
            "decay": 0.95,
            # ... other params likely present but truncated
        }
```

**Key observations:**
- Legacy used `decay` as retention factor (0.95 = 95% retention per frame)
- `bloomAmount` scales the offset and blend factor
- `feedback_amount` adds to blend factor (can cause runaway if high)
- The `mix` uniform is the overall effect blend (our `u_mix`)

### VJLive3 Adaptation

- Convert GLSL to WGSL
- Use proper uniform struct with explicit types
- Add `u_threshold` parameter (implied by "brightness-based" but not in snippet; likely present in full code)
- Ensure `texPrev` feedback buffer is managed by render engine
- Follow VJLive3 conventions: `u_` prefix, `set_uniform` dispatch

### Related Effects

- **P5-DM12** `PixelSortEffect` — also datamosh category, sorts pixels by brightness
- **P5-DM13** `MeltEffect` — vertical dripping pixels
- **P5-DM11** `DatamoshEffect` — motion-based pixel bleeding (more complex)
- **P7-VE15** `BloomEffect` — standard HDR bloom (different algorithm)

---

## Implementation Notes for Phase 3

1. **Feedback buffer management**: The render engine must provide `texPrev` as a persistent texture that receives the output each frame. This is typically managed by `RenderEngine` or `EffectChain`.
2. **Uniform scaling**: `bloomDir` should be normalized in the shader or on upload; document expected range.
3. **Threshold**: The legacy snippet didn't show threshold check; but "brightness-based" implies it. Implement as early discard to save work.
4. **Color space**: Operate in linear space; ensure sRGB conversion if needed (handled by render pipeline).
5. **Performance**: This effect is memory-bound; optimize by using half-resolution feedback if needed.

---

**End of Spec**  
✅ Ready for Phase 3 implementation
