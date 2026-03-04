# P3-EXT128: PixelateEffect — Fleshed Specification

## Task: P3-EXT128 — PixelateEffect

**Module Type:** Geometry Effect (WGSL Shader)  
**Priority:** P0 (Core Geometry)  
**Phase:** Pass 2 — Fleshed Specification  
**Agent:** desktop-roo  
**Date:** 2026-03-04  

---

## What This Module Does

The `PixelateEffect` is a geometry transformation effect that reduces the effective resolution of the rendered image by grouping pixels into blocks and sampling a single color for each block. This creates a retro, low-resolution aesthetic commonly used for stylistic transitions, pixel art effects, or visual distortion.

The effect operates in screen space, dividing the UV coordinates into a grid where each cell samples the same texel from the input texture. The `pixelX` and `pixelY` parameters control the block size (inverse resolution), while the `shape` parameter determines how the pixelation grid is applied (e.g., uniform blocks, circular masks, or other shape-based variations).

**Key Characteristics:**
- Non-destructive: operates as a post-process effect in the render chain
- Resolution-independent: works with any input texture size
- Real-time performance: minimal computational overhead (simple integer division and texture lookup)
- Compatible with VJLive3's Effect base class and RenderPipeline system

---

## What This Module Does NOT Do

- **NOT** a mipmap-based downsampling: does not use hardware mipmaps; performs explicit grid-based sampling
- **NOT** a pixel art upscaling: does not include nearest-neighbor upscaling filters or dithering
- **NOT** a resolution switch: does not change the framebuffer resolution; only transforms UV coordinates
- **NOT** a shape mask: the `shape` parameter modifies pixelation behavior but does not provide arbitrary masking
- **NOT** a temporal effect: does not include animation or time-based variation (those would be external parameters)
- **NOT** a depth-aware effect: operates purely on 2D UV coordinates; no depth buffer access

---

## Detailed Behavior and Parameter Interactions

### Core Algorithm

The PixelateEffect uses a grid-based approach to reduce resolution:

1. **Grid Formation:** The screen UV space `[0,1]` is divided into a grid of cells. The cell size is determined by `pixelX` and `pixelY` parameters, which represent the number of pixel blocks along each axis (or equivalently, the inverse of the block size).

2. **UV Quantization:** For each fragment, the shader computes which grid cell the fragment belongs to:
   ```wgsl
   let cell_x = floor(uv.x * pixelX);
   let cell_y = floor(uv.y * pixelY);
   ```

3. **Sample Coordinate:** The center of that cell becomes the sampling coordinate:
   ```wgsl
   let sample_uv = vec2((cell_x + 0.5) / pixelX, (cell_y + 0.5) / pixelY);
   ```

4. **Texture Lookup:** The input texture is sampled at `sample_uv`, and that color is applied to all fragments in that cell.

### Parameter Interactions

| Parameter | Type | Range | Default | Description |
|-----------|------|-------|---------|-------------|
| `pixelX` | float | [1, 256] | 16.0 | Number of horizontal pixel blocks (higher = finer pixelation) |
| `pixelY` | float | [1, 256] | 16.0 | Number of vertical pixel blocks (higher = finer pixelation) |
| `shape` | float | [0, 1] | 0.0 | Shape mode: 0=uniform blocks, 1=circular/radial pixelation (future extension) |

**Parameter Behavior:**
- `pixelX` and `pixelY` are independent; setting them to different values creates rectangular pixels (e.g., 8×16 for wide pixels)
- `shape` is currently reserved for future shape-based pixelation modes (e.g., hexagonal, triangular, or radial patterns). In the base implementation, it is ignored or used as a placeholder.
- All parameters are uniform variables updated via `apply_uniforms()` at runtime.

### Edge Cases

- **pixelX or pixelY = 1:** No pixelation (full resolution)
- **pixelX or pixelY = 0:** Clamp to minimum of 1 to avoid division by zero
- **Non-integer grid alignment:** The algorithm uses `floor()` to ensure consistent cell boundaries regardless of UV precision
- **Aspect ratio:** The effect does not correct for aspect ratio; users must provide appropriately sized `pixelX`/`pixelY` to maintain square pixels if desired

---

## Public Interface

### Class Definition

```python
from vjlive3.render.effect import Effect
from vjlive3.render.program import RenderPipeline

class PixelateEffect(Effect):
    """
    Pixelation effect - reduces resolution with shape modes.
    
    Parameters:
        pixelX (float): Horizontal pixel block count (1-256)
        pixelY (float): Vertical pixel block count (1-256)
        shape (float): Shape mode selector (0-1)
    """
    
    METADATA = {
        "name": "PixelateEffect",
        "spec": "P3-EXT128",
        "version": "1.0.0",
        "tier": "Pro-Tier Native",
        "category": "geometry",
        "description": "Grid-based pixelation effect with configurable block size"
    }
    
    def __init__(self, name: str = "pixelate") -> None:
        """
        Initialize the PixelateEffect.
        
        Args:
            name: Instance name for the effect (default: "pixelate")
        """
        fragment_source = self._get_wgsl_shader()
        super().__init__(name, fragment_source)
        
        # Initialize default parameters
        self.parameters = {
            "pixelX": 16.0,
            "pixelY": 16.0,
            "shape": 0.0,
        }
    
    def _get_wgsl_shader(self) -> str:
        """Return the WGSL shader source code."""
        return """
        @group(0) @binding(0) var tex0: texture_2d<f32>;
        @group(0) @binding(1) var s0: sampler;
        
        struct Uniforms {
            pixelX: f32,
            pixelY: f32,
            shape: f32,
            mix: f32,
            enabled: f32,
        };
        
        @binding(2) @group(0) var<uniform> uniforms: Uniforms;
        
        @fragment
        fn main(@location(0) uv: vec2<f32>) -> @location(0) vec4<f32> {
            // Clamp pixel counts to valid range
            let px = max(uniforms.pixelX, 1.0);
            let py = max(uniforms.pixelY, 1.0);
            
            // Compute cell index
            let cell_x = floor(uv.x * px);
            let cell_y = floor(uv.y * py);
            
            // Compute sample UV at cell center
            let sample_uv = vec2<f32>(
                (cell_x + 0.5) / px,
                (cell_y + 0.5) / py
            );
            
            // Sample texture
            var color = textureSample(tex0, s0, sample_uv);
            
            // Apply mix factor
            let input_color = textureSample(tex0, s0, uv);
            color = mix(input_color, color, uniforms.mix);
            
            return color;
        }
        """
    
    def apply_uniforms(self, pipeline: RenderPipeline) -> None:
        """
        Upload current parameter values to the GPU pipeline.
        
        Args:
            pipeline: RenderPipeline instance to update
        """
        pipeline.set_uniform("pixelX", self.parameters["pixelX"])
        pipeline.set_uniform("pixelY", self.parameters["pixelY"])
        pipeline.set_uniform("shape", self.parameters["shape"])
```

### Integration with VJLive3

- Inherits from [`Effect`](src/vjlive3/render/effect.py) base class
- Uses [`RenderPipeline`](src/vjlive3/render/program.py) for WGSL compilation and uniform management
- Parameters are exposed via `self.parameters` dict for GUI binding
- `apply_uniforms()` method called each frame before rendering
- Compatible with effect chaining via [`Chain`](src/vjlive3/render/chain.py)

---

## Inputs and Outputs

### Inputs

| Stream | Type | Description |
|--------|------|-------------|
| `tex0` | `texture_2d<f32>` | Input video/texture to pixelate |
| `s0` | `sampler` | Sampler for texture lookup (linear filtering recommended) |
| Uniforms | `Uniforms` struct | `pixelX`, `pixelY`, `shape`, `mix`, `enabled` |

### Outputs

| Stream | Type | Description |
|--------|------|-------------|
| Fragment output | `vec4<f32>` | RGBA color with pixelation applied |

### Data Flow

1. Input texture bound to binding 0
2. Sampler bound to binding 1
3. Uniform buffer bound to binding 2 (updated via `set_uniform`)
4. Fragment shader runs for each pixel in the output framebuffer
5. UV coordinates transformed via grid quantization
6. Sampled color blended with original via `mix` uniform
7. Output written to framebuffer attachment

---

## Edge Cases and Error Handling

### Division by Zero
- **Risk:** If `pixelX` or `pixelY` are zero, the shader would divide by zero.
- **Mitigation:** Shader uses `max(uniforms.pixelX, 1.0)` to clamp to minimum 1.0. Python-side validation in `apply_uniforms()` can also clamp values before upload.

### Out-of-Range Parameters
- **Risk:** Extremely high `pixelX`/`pixelY` (e.g., 10000) could cause precision issues or performance degradation.
- **Mitigation:** Clamp to [1, 256] range in Python before uploading to GPU. The spec recommends a hard limit of 256 for practical use.

### Texture Coordinate Wrapping
- **Behavior:** The shader uses `textureSample` which respects the sampler's wrap mode. If the sampler uses `repeat`, `sample_uv` values outside `[0,1]` will wrap. Since `sample_uv` is computed from `floor(uv * px) / px`, it should always be within `[0,1)` for UVs in `[0,1]`. Edge case: UV=1.0 exactly yields `floor(px) / px` which is <1, so safe.

### Non-Power-of-Two Textures
- **Behavior:** The algorithm works with any texture size; no requirement for power-of-two dimensions.

### Mix Parameter Edge Cases
- `mix = 0.0`: Output is original input (effect disabled)
- `mix = 1.0`: Full pixelation applied
- Values outside [0,1] are clamped by the `mix()` function in WGSL (though it's not standard; better to clamp in Python)

### Enabled Flag
- The base `Effect` class provides an `enabled` boolean. When `enabled=False`, the effect chain should skip calling `apply_uniforms()` and rendering. The shader still runs but could early-out if needed.

---

## Mathematical Formulations

### Grid Quantization

Given:
- `u, v` ∈ [0,1] — normalized UV coordinates
- `px, py` > 0 — pixel block counts

The quantized UV is:

```
cell_x = floor(u * px)
cell_y = floor(v * py)

u' = (cell_x + 0.5) / px
v' = (cell_y + 0.5) / py
```

This maps each fragment to the center of its grid cell.

### Alternative: Integer-Based Formulation

If working in pixel coordinates (not normalized UV):

```
pixel_x = floor(screen_x / block_width) * block_width + block_width/2
pixel_y = floor(screen_y / block_height) * block_height + block_height/2

sample_coord = (pixel_x / screen_width, pixel_y / screen_height)
```

### Mix Blending

Final color:
```
output = mix(input_color, pixelated_color, mix_factor)
```
where `mix(a,b,t) = a*(1-t) + b*t`.

### Shape Parameter (Future Extension)

The `shape` parameter is reserved for non-rectangular pixelation patterns. Possible formulations:
- Circular: distance from cell center determines inclusion
- Hexagonal: offset grid with 3-cell neighborhoods
- Triangular: barycentric coordinate-based cell decomposition

---

## Performance Characteristics

### Computational Complexity

- **Per-fragment operations:** 
  - 2 multiplications (`uv * px/py`)
  - 2 `floor()` calls (integer conversion)
  - 2 additions (`+ 0.5`)
  - 2 divisions (`/ px, / py`)
  - 1 texture lookup (`textureSample`)
  - 1 `mix()` operation
- **Total:** ~10 arithmetic ops + 1 texture fetch per fragment

### Memory Footprint

- **Uniform buffer:** 4 floats (pixelX, pixelY, shape, mix) + 1 float (enabled) ≈ 20 bytes
- **Texture bindings:** 2 (texture + sampler)
- **Pipeline state:** WGSL shader compiled once and cached

### GPU Utilization

- **Fragment-bound:** The effect is fragment-shader heavy; performance scales with output resolution.
- **Texture bandwidth:** 1 texture fetch per fragment (same as passthrough) — no additional overhead.
- **No vertex processing:** Uses standard full-screen quad; vertex shader unchanged.

### Optimization Opportunities

- **Early fragment kill:** If `mix == 0` or `pixelX/pixelY == 1`, could skip shader execution (but not necessary given low cost).
- **Compute shader variant:** For extremely high resolutions, a compute shader could reduce overdraw, but fragment shader is sufficient for real-time 60fps.
- **Integer arithmetic:** Could use `i32` for cell indices to avoid floating-point `floor()`, but WGSL `floor()` is efficient on modern GPUs.

### Benchmarks (Estimated)

| Resolution | pixelX/Y | Cost (relative) |
|------------|----------|-----------------|
| 1920×1080  | 16       | 1.0× (baseline) |
| 1920×1080  | 64       | 1.0× (same ops) |
| 3840×2160  | 16       | 2.0× (2× fragments) |
| 1920×1080  | 1        | 0.1× (early-out possible) |

All operations are O(1) per fragment; no loops or dynamic branching.

---

## Test Plan

### Unit Tests (Python)

1. **Parameter Validation**
   - Test that `pixelX` and `pixelY` are clamped to [1, 256] in `apply_uniforms()`
   - Test that `shape` is passed as float
   - Test default values on initialization

2. **Shader Compilation**
   - Verify WGSL source compiles without errors via `RenderPipeline`
   - Test that uniform locations are correctly bound

3. **Uniform Upload**
   - Mock `RenderPipeline.set_uniform()` and verify called with correct names/values
   - Test that `apply_uniforms()` uploads all three parameters

4. **Metadata**
   - Verify `METADATA` dict contains required keys: `name`, `spec`, `version`, `tier`, `category`
   - Verify `spec` value matches `P3-EXT128`

### Integration Tests (Render)

1. **Basic Rendering**
   - Create a test texture with known pattern (e.g., gradient)
   - Apply PixelateEffect with `pixelX=4, pixelY=4`
   - Verify output shows 4×4 blocks of uniform color
   - Check that each block samples from the center of the corresponding region

2. **Parameter Variation**
   - Test `pixelX=1, pixelY=1` → output equals input (no pixelation)
   - Test `pixelX=64, pixelY=64` → fine pixelation
   - Test `pixelX=8, pixelY=32` → rectangular pixels (2:1 aspect)

3. **Mix Blending**
   - Set `mix=0.0` → output equals input
   - Set `mix=1.0` → full pixelation
   - Set `mix=0.5` → 50/50 blend (check intermediate values)

4. **Edge Cases**
   - Input texture with non-power-of-two dimensions (e.g., 100×100)
   - UV coordinates at exact boundaries (0.0, 1.0)
   - Very small `pixelX/pixelY` (1) and very large (256)

5. **Chain Integration**
   - Insert PixelateEffect into a `Chain` with other effects
   - Verify it receives correct input texture from previous effect
   - Verify it writes to output correctly

### Visual Regression Tests

- Render a standard test pattern (e.g., SMPTE color bars) with known pixelation settings
- Compare output against golden images (per-pixel difference < 1/255)
- Store reference images in `tests/reference/P3-EXT128/`

### Performance Tests

- Measure frame time with PixelateEffect at 1920×1080, 60fps
- Ensure no dropped frames over 60-second run
- Profile shader execution via GPU debugging tools (optional)

---

## Definition of Done

- [x] Spec document completed in `docs/specs/_02_fleshed_out/P3-EXT128_PixelateEffect.md`
- [ ] WGSL shader code implemented in `src/vjlive3/plugins/pixelate_effect.py`
- [ ] Python class `PixelateEffect` inheriting from `Effect` and implementing `__init__`, `apply_uniforms`
- [ ] All unit tests passing (`tests/plugins/test_pixelate_effect.py`)
- [ ] All integration tests passing (render tests)
- [ ] Code coverage ≥ 80% for the plugin module
- [ ] Documentation updated (docstrings, README if applicable)
- [ ] No linter errors (`ruff`, `mypy` pass)
- [ ] Performance: 60fps at 1920×1080 on target hardware
- [ ] Spec reviewed and approved by Manager agent

---

## Legacy References

### VJlive (Original) — `core/effects/legacy_trash/geometry.py`

```python
class PixelateEffect(Effect):
    """Pixelation effect - reduces resolution with shape modes."""

    def __init__(self):
        super().__init__("pixelate", PIXELATE_FRAGMENT)
        self.parameters = {
            "pixelX": 0.9,
            "pixelY": 0.9,
            "shape": 0.0,
        }
```

**Notes:** 
- Legacy parameters used values 0.9 (likely normalized 0-1 range that got scaled internally). VJLive3 uses direct float values for block counts.
- The `PIXELATE_FRAGMENT` shader string was defined elsewhere in the legacy codebase; its exact contents were not retrieved but would have contained similar WGSL/GLSL logic.

### VJlive-2 (Legacy) — Same as above

The PixelateEffect appears in both VJlive and VJlive-2 with identical structure, indicating it was a stable, core geometry effect.

### Migration Notes

- **Parameter mapping:** Legacy `pixelX=0.9` likely mapped to a scale factor; in VJLive3 we use direct block counts (e.g., 16). The mapping would be: `block_count = floor(legacy_value * 256)` or similar. The default 0.9 → ~230 blocks, which is very high (fine pixelation). The VJLive3 default of 16 is more moderate.
- **Shader language:** Legacy likely used GLSL; VJLive3 uses WGSL. The algorithm translates directly.
- **Integration:** The effect fits the standard VJLive3 plugin pattern; no special handling needed.

---

## Technical Notes for Implementation

### Shader Design Rationale

The chosen WGSL implementation uses `floor(uv * px)` to compute cell indices. This is the standard approach for grid-based pixelation. Alternative methods considered:

- `i32(uv * px)` cast: equivalent but less explicit
- `trunc()` vs `floor()`: for positive UVs they are identical; `floor()` is safer if UVs could be negative (they shouldn't be)
- Using `u32` and integer division: possible but WGSL `floor()` is efficient

The `+0.5` offset centers the sample within the cell, avoiding bias toward the top-left corner.

### Uniform Buffer Layout

The `Uniforms` struct is tightly packed (4×f32 = 16 bytes). It should match the Python-side uniform uploads exactly. The base `Effect` class may provide `mix` and `enabled`; we include them in the shader for consistency with other effects.

### Thread Safety

- `PixelateEffect` instances are not thread-safe by themselves; the `Effect` base class does not use locks.
- If used from multiple threads (e.g., audio thread vs render thread), parameter updates should be protected or use double-buffering.
- The `apply_uniforms()` method should be called from the render thread only.

---
-

## References

- [`Effect` base class](src/vjlive3/render/effect.py) — VJLive3 effect foundation
- [`RenderPipeline`](src/vjlive3/render/program.py) — WGSL shader management
- [`Chain`](src/vjlive3/render/chain.py) — Effect composition
- Legacy: `core/effects/legacy_trash/geometry.py` — PixelateEffect definition (VJlive, VJlive-2)
- BOARD.md task entry: P3-EXT128

---

**Specification Status:** ✅ Fleshed — Ready for Implementation (Pass 3)
