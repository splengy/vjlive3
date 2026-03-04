# Spec: P3-EXT044 — DepthDistanceFilterEffect

**File naming:** `docs/specs/P3-EXT044_DepthDistanceFilterEffect.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT044 — DepthDistanceFilterEffect

**What This Module Does**

DepthDistanceFilterEffect is a depth-based masking and compositing utility that isolates pixels within a specified depth range. It functions as a virtual green screen using depth data instead of color, allowing selective processing of foreground/background elements. The effect supports multiple fill modes for pixels outside the depth window (transparent, solid color, blurred, or secondary input), edge softening, mask inversion, and real-time depth visualization.

**What This Module Does NOT Do**

- Does not perform actual depth-based 3D reconstruction
- Does not generate depth data (requires external depth input)
- Does not support audio reactivity (depth-only processing)
- Does not include temporal smoothing beyond basic mask smoothing parameter

---

## Detailed Behavior and Parameter Interactions

### Core Algorithm

1. **Depth Sampling**: Sample depth value from depth texture at current UV coordinate
   ```glsl
   float depth = texture(depth_tex, uv).r;
   ```

2. **Mask Calculation**: Create binary mask based on near/far clip range with soft edges:
   ```glsl
   // Soft near clip
   mask *= smoothstep(near_clip - edge_softness * 0.1,
                      near_clip + edge_softness * 0.1, depth);
   
   // Soft far clip
   mask *= 1.0 - smoothstep(far_clip - edge_softness * 0.1,
                            far_clip + edge_softness * 0.1, depth);
   ```

3. **Edge Refinement** (optional): Erode or dilate mask edges by sampling 4-connected neighbors:
   - Positive `edge_refine` → dilate (max of neighbors)
   - Negative `edge_refine` → erode (min of neighbors)

4. **Inversion** (optional): If `invert > 0.5`, mask is inverted: `mask = 1.0 - mask`

5. **Fill Outside Mask**: Pixels where mask is low are replaced based on `fill_mode`:
   - `0.0-3.3`: Transparent (black with alpha=0)
   - `3.3-6.6`: Solid color (`fill_color`)
   - `6.6-8.3`: Blurred version of source (9-tap box blur with distance weighting)
   - `8.3-10.0`: Secondary input (`tex_b`)

6. **Compositing**: Final result blends fill and source using mask:
   ```glsl
   vec4 result = mix(fill, source, mask);
   ```

7. **Visualization Modes** (debug):
   - `show_mask > 0.5`: Display mask as grayscale
   - `depth_colorize > 0.0`: Apply false-color depth map with mask edge overlay

8. **Mix**: Final output blended with original source: `fragColor = mix(source, result, u_mix)`

### Parameter Interactions

- **near_clip** and **far_clip** define the depth window. Near values (0.0) are close to camera; far values (1.0) are distant.
- **edge_softness** controls feathering at clip boundaries (0.0 = hard edges, 10.0 = very soft)
- **edge_refine** allows morphological operations: positive dilates, negative erodes
- **fill_mode** determines how excluded pixels are handled; each mode has distinct visual characteristics
- **smoothing** parameter is present but not fully implemented in shader (reserved for temporal smoothing)

---

## Public Interface

### Class Definition
```python
class DepthDistanceFilterEffect(Effect):
    """
    Depth Distance Filter — isolate pixels by depth range.
    Essential utility for depth-based compositing, virtual green screen,
    and selective processing.
    """
    
    def __init__(self):
        super().__init__("depth_distance_filter", DEPTH_DISTANCE_FILTER_FRAGMENT)
        self.depth_source = None
        self.depth_frame = None
        self.depth_texture = 0
        # Parameters initialized in shader uniforms
```

### Parameters (from manifest)

| Parameter | Type | Range | Default | Description |
|------------|------|-------|---------|-------------|
| `near_clip` | float | 0.0-10.0 | 1.0 | Near distance threshold (0=camera, 1=far) |
| `far_clip` | float | 0.0-10.0 | 8.0 | Far distance threshold |
| `edge_softness` | float | 0.0-10.0 | 3.0 | Feathering at clip boundaries |
| `invert` | float | 0.0-10.0 | 0.0 | Invert mask (show outside instead) |
| `fill_mode` | float | 0.0-10.0 | 0.0 | Fill type: 0=transparent, 6.6=blur, 10=input B |
| `fill_color_r` | float | 0.0-10.0 | 0.0 | Fill color red component |
| `fill_color_g` | float | 0.0-10.0 | 0.0 | Fill color green component |
| `fill_color_b` | float | 0.0-10.0 | 0.0 | Fill color blue component |
| `edge_refine` | float | 0.0-10.0 | 5.0 | Erode/dilate mask edges (neg=erode) |
| `smoothing` | float | 0.0-10.0 | 3.0 | Temporal smoothing of mask (reserved) |
| `show_mask` | float | 0.0-10.0 | 0.0 | Preview mask as grayscale |
| `depth_colorize` | float | 0.0-10.0 | 0.0 | False-color depth visualization |

**Note**: All parameters use 0.0-10.0 range but are normalized in shader (e.g., `near_clip` maps to 0.0-1.0 depth range via division by 10.0 in usage).

---

## Inputs and Outputs

### Inputs
- **signal_in** (video): Primary video input to be filtered
- **depth_tex** (depth): Depth texture (single-channel, normalized 0.0-1.0)
- **tex_b** (video, optional): Secondary input for fill mode (when `fill_mode >= 8.3`)

### Outputs
- **signal_out** (video): Filtered/composited video output

### Input Requirements
- Depth texture must be single-channel (R) format
- Depth values should be normalized (0.0 = near, 1.0 = far)
- Video and depth textures must have matching resolution
- Secondary input (tex_b) must be provided when using fill_mode >= 8.3

---

## Edge Cases and Error Handling

### Edge Cases
1. **near_clip >= far_clip**: Results in empty mask (no pixels satisfy both clips)
2. **near_clip = 0, far_clip = 10**: Effectively passthrough (all pixels included)
3. **edge_softness = 0**: Hard clipping with no feathering
4. **fill_mode = 0**: Transparent fill produces alpha=0 outside mask
5. **edge_refine extreme values**: Can completely erode or dilate mask to binary state
6. **depth_colorize > 0**: Overlays false-color map; mask edges highlighted with white

### Error Handling
- If depth texture is missing, effect should fall back to passthrough or solid color
- Invalid fill_mode values default to transparent behavior
- No bounds checking on neighbor sampling in edge refinement (assumes valid UV coordinates)

---

## Mathematical Formulations

### Mask Calculation
```glsl
// Near clip: mask *= smoothstep(near - soft, near + soft, depth)
// Far clip: mask *= 1.0 - smoothstep(far - soft, far + soft, depth)
float near_edge0 = near_clip - edge_softness * 0.1;
float near_edge1 = near_clip + edge_softness * 0.1;
float far_edge0 = far_clip - edge_softness * 0.1;
float far_edge1 = far_clip + edge_softness * 0.1;
mask = smoothstep(near_edge0, near_edge1, depth) * 
       (1.0 - smoothstep(far_edge0, far_edge1, depth));
```

### Edge Refinement (Erode/Dilate)
```glsl
// Sample 4-connected neighbors
float d_up = texture(depth_tex, uv + vec2(0, texel)).r;
float d_dn = texture(depth_tex, uv - vec2(0, texel)).r;
float d_lt = texture(depth_tex, uv - vec2(texel, 0)).r;
float d_rt = texture(depth_tex, uv + vec2(texel, 0)).r;

// Compute neighbor masks
float m_up = smoothstep(near_clip, near_clip + 0.01, d_up) * 
             (1.0 - smoothstep(far_clip - 0.01, far_clip, d_up));
// ... similarly for m_dn, m_lt, m_rt

if (edge_refine > 0.0) {
    // Dilate: mask = max(mask, max(max(m_up, m_dn), max(m_lt, m_rt)) * edge_refine)
    mask = max(mask, max(max(m_up, m_dn), max(m_lt, m_rt)) * edge_refine);
} else {
    // Erode: mask = mix(mask, min(mask, neighbors_min), -edge_refine)
    float neighbors_min = min(min(m_up, m_dn), min(m_lt, m_rt));
    mask = mix(mask, min(mask, neighbors_min), -edge_refine);
}
```

### Blur Fill Mode
```glsl
// 9-tap weighted blur (Manhattan distance weighting)
vec4 blurred = vec4(0.0);
float total = 0.0;
for (int x = -4; x <= 4; x++) {
    for (int y = -4; y <= 4; y++) {
        vec2 offset = vec2(float(x), float(y)) * 4.0 / resolution;
        float w = 1.0 / (1.0 + float(abs(x) + abs(y)));
        blurred += texture(tex0, uv + offset) * w;
        total += w;
    }
}
fill = blurred / total;
```

### Depth Colorization
```glsl
// Rainbow gradient across depth range
if (depth < 0.2)
    depth_color = mix(vec3(1,0,0), vec3(1,0.5,0), depth * 5.0);
else if (depth < 0.4)
    depth_color = mix(vec3(1,0.5,0), vec3(1,1,0), (depth-0.2) * 5.0);
else if (depth < 0.6)
    depth_color = mix(vec3(1,1,0), vec3(0,1,0), (depth-0.4) * 5.0);
else if (depth < 0.8)
    depth_color = mix(vec3(0,1,0), vec3(0,0.5,1), (depth-0.6) * 5.0);
else
    depth_color = mix(vec3(0,0.5,1), vec3(0.2,0,0.8), (depth-0.8) * 5.0);

// Add mask edge overlay
float mask_edge = abs(fract(mask * 4.0) - 0.5) < 0.05 ? 1.0 : 0.0;
depth_color += vec3(mask_edge);
```

---

## Performance Characteristics

### Computational Complexity
- **Base mask calculation**: ~6 texture samples (1 depth, 1 source, optional 1 tex_b)
- **Edge refinement**: +4 depth texture samples (neighbors)
- **Blur fill mode**: +81 texture samples (9x9 grid) — **expensive**
- **Depth colorize**: Minimal overhead (branching on depth value)

### Performance Optimizations
- Early fragment discard not used (need to compute fill for all pixels)
- Edge refinement uses fixed 4-sample pattern (efficient)
- Blur mode uses distance-weighted kernel (avoids full Gaussian)

### Bottlenecks
- **Blur fill mode**: 81 additional texture samples can be bandwidth-limited
- **Edge refinement**: 4 extra depth samples per pixel (moderate cost)
- **Multiple uniform updates**: 12+ uniforms per draw call

### Memory Usage
- No additional framebuffers required (single-pass)
- Depth texture must be bound separately
- Secondary input texture optional

---

## Test Plan

### Unit Tests
1. **Mask Boundary**: Test that mask=1.0 inside depth window, mask=0.0 outside
2. **Edge Softness**: Test feathering creates smooth transition at boundaries
3. **Inversion**: Test `invert > 0.5` flips mask
4. **Fill Modes**: Test each fill mode produces correct output
5. **Edge Refine**: Test erode (negative) and dilate (positive) operations
6. **Depth Colorize**: Test false-color map produces correct rainbow gradient
7. **Show Mask**: Test grayscale mask visualization

### Integration Tests
1. **Basic Filtering**: Test with simple depth ramp (linear depth gradient)
2. **Sharp Edges**: Test with binary depth mask (object against background)
3. **Fill Mode Switching**: Test all fill modes with same input
4. **Parameter Ranges**: Test extreme values (0.0 and 10.0) for all parameters
5. **Secondary Input**: Test fill_mode=10 with valid/invalid tex_b

### Visual Tests
1. **Depth Isolation**: Verify only pixels within depth range are preserved
2. **Edge Softness**: Verify feathering smoothness varies with parameter
3. **Blur Quality**: Verify blur fill produces smooth background
4. **Colorization**: Verify depth rainbow map is continuous and correct

**Minimum coverage:** 85% before task is marked done.

---

## Definition of Done

- [x] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-EXT044: DepthDistanceFilterEffect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES  

Based on VJlive v1/v2 implementations:
- Main implementation: `plugins/vdepth/depth_distance_filter.py` (lines 1-164)
- Shader fragment: `DEPTH_DISTANCE_FILTER_FRAGMENT` string (lines 17-148)
- Plugin manifest: `plugins/core/depth_distance_filter/plugin.json`
- VJLive-2 version: `plugins/core/depth_distance_filter/__init__.py`

**Note**: This is a core depth utility effect, part of the `vdepth` plugin system. It is a foundational building block for more complex depth-based compositing.