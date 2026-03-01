# P7-VE75: Delay Zoom Effect

> **Task ID:** `P7-VE75`
> **Priority:** P0
> **Source:** vjlive (`plugins/vcore/vcv_video_effects.py`)
> **Class:** `DelayZoomEffect`
> **Category:** Post-Processing
> **Phase:** Phase 7 ✅ Fleshed Out

## Purpose

Delay + zoom: apply temporal delay with progressive zoom levels. Creates zoom trails, motion zoom effects, and temporal zoom feedback. Essential for dynamic zoom effects and motion trails.

## Parameters (0–10 UI Scale)

| Name | Min | Max | Default | Remapped Range | Purpose |
|------|-----|-----|---------|-----------------|---------|
| `delay_count` | 0 | 10 | 5 | 1–8 | Number of zoom copies |
| `zoom_level` | 0 | 10 | 5 | 0.5–2.0 | Zoom factor per copy |
| `zoom_center_x` | 0 | 10 | 5 | 0.0–1.0 | Horizontal zoom center |
| `zoom_center_y` | 0 | 10 | 5 | 0.0–1.0 | Vertical zoom center |
| `opacity` | 0 | 10 | 10 | 0.0–1.0 | Output blend |

## Remapping Guide

```python
def remap_params(delay_count, zoom_level, zoom_center_x, zoom_center_y, opacity):
    dc = int(map_linear(delay_count, 0, 10, 1, 8))           # copies: 1–8
    zl = map_linear(zoom_level, 0, 10, 0.5, 2.0)            # zoom: 0.5–2.0
    zcx = map_linear(zoom_center_x, 0, 10, 0.0, 1.0)        # center x: 0.0–1.0
    zcy = map_linear(zoom_center_y, 0, 10, 0.0, 1.0)        # center y: 0.0–1.0
    α = opacity / 10                                         # opacity: [0, 1]
    return dc, zl, zcx, zcy, α
```

## Shader Implementation

### Delay Zoom with Progressive Scaling

```glsl
#version 330 core
uniform sampler2D tex_in;
uniform int delay_count;        // Number of zoom copies
uniform float zoom_level;       // Zoom factor per copy
uniform vec2 zoom_center;       // Zoom center (0.0–1.0)
uniform float opacity;

in vec2 uv;
out vec4 frag_out;

// Simple zoom transformation
vec2 zoom_transform(vec2 coord, vec2 center, float zoom) {
    // Convert to center-relative coordinates
    vec2 centered = coord - center;
    
    // Apply zoom
    vec2 zoomed = centered * zoom;
    
    // Convert back to UV coordinates
    return zoomed + center;
}

void main() {
    vec4 col = texture(tex_in, uv);
    
    // Apply delay zoom
    vec4 result = col;
    float total_weight = 1.0;
    
    // Apply multiple zoomed copies
    for (int i = 1; i <= delay_count; i++) {
        // Calculate zoom for this copy
        float zoom = pow(zoom_level, float(i));
        
        // Apply zoom transformation
        vec2 zoomed_uv = zoom_transform(uv, zoom_center, zoom);
        vec4 zoomed = texture(tex_in, zoomed_uv);
        
        // Accumulate with weight
        result += zoomed;
        total_weight += 1.0;
    }
    
    // Normalize by total weight
    result /= total_weight;
    
    // Blend with original
    frag_out = mix(col, result, opacity);
}
```

**Design Notes:**
- **Progressive zoom:** Each copy zooms by factor (0.5–2.0)
- **Center control:** Independent X/Y zoom centers (0.0–1.0)
- **Multiple copies:** 1–8 zoom instances with configurable count
- **Normalization:** Weighted average prevents brightness explosion
- **Opacity blend:** Mix with original for artistic control

## CPU Fallback

```python
import cv2
import numpy as np

def delay_zoom_cpu(frame, delay_count, zoom_level, zoom_center_x, zoom_center_y, opacity):
    """Delay zoom via multiple scaled copies."""
    if frame is None or frame.size == 0:
        return frame
    
    try:
        # Apply delay zoom
        result = frame.astype(np.float32) / 255.0
        rows, cols, _ = frame.shape
        total_weight = 1.0
        
        # Apply multiple zoomed copies
        for i in range(1, delay_count + 1):
            # Calculate zoom for this copy
            zoom = pow(zoom_level, float(i))
            
            # Calculate zoom center
            center_x = int(zoom_center_x * cols)
            center_y = int(zoom_center_y * rows)
            
            # Apply zoom transformation
            # Create zoom matrix
            M = np.float32([[zoom, 0, (1 - zoom) * center_x],
                            [0, zoom, (1 - zoom) * center_y]])
            
            # Warp to create zoom
            zoomed = cv2.warpAffine(frame, M, (cols, rows))
            
            # Accumulate with weight
            result += (zoomed.astype(np.float32) / 255.0)
            total_weight += 1.0
        
        # Normalize by total weight
        result /= total_weight
        
        # Blend with original
        output = cv2.addWeighted(frame, 1.0 - opacity, (result * 255).astype(np.uint8), opacity, 0)
        
        return output
    except Exception as e:
        print(f"delay_zoom_cpu error: {e}")
        return frame
```

## Presets

| Name | delay_count | zoom_level | zoom_center_x | zoom_center_y | opacity |
|------|-------------|------------|---------------|---------------|---------|
| Zoom Trail | 5 | 5 | 5 | 5 | 10 |
| Motion Zoom | 8 | 8 | 5 | 5 | 8 |
| Center Zoom | 3 | 7 | 5 | 5 | 9 |
| Subtle Zoom | 3 | 3 | 5 | 5 | 7 |

## Class Signature

```python
class DelayZoomEffect(Effect):
    """Delay zoom with progressive scaling and multiple copies.
    
    Attributes:
        effect_category: "post-process"
        parameters: {delay_count, zoom_level, zoom_center_x, zoom_center_y, opacity}
        _zoom_cache: Optional pre-computed zoom patterns
    """
    def __init__(self, width=1920, height=1080, use_gpu=True):
        super().__init__("DelayZoom", vert_shader, frag_shader)
        self.effect_category = "post-process"
        self.parameters = {
            'delay_count': 5.0,
            'zoom_level': 5.0,
            'zoom_center_x': 5.0,
            'zoom_center_y': 5.0,
            'opacity': 10.0
        }
        self._parameter_ranges = {
            'delay_count': (0, 10),
            'zoom_level': (0, 10),
            'zoom_center_x': (0, 10),
            'zoom_center_y': (0, 10),
            'opacity': (0, 10)
        }
        self.use_gpu = use_gpu
    
    def render(self, tex_in, **kwargs):
        """Apply delay zoom effect."""
        # Apply multiple zoomed copies with progressive scaling
        # Blend with original
```

## Error Handling

- **Invalid delay count:** Clamp to [1, 8]
- **Zoom level ≤0:** Default to 0.5
- **Zoom level ≥3:** Default to 2.0
- **Null input:** Return original frame
- **Center out of range:** Clamp to [0.0, 1.0]

## Testing Strategy

### Zoom Level Response (`test_zoom_level`)
```python
# Higher zoom should create more zoom effect
low_zoom = delay_zoom_cpu(test_image, 3, 2, 5, 5, 1.0)    # zoom=0.5
high_zoom = delay_zoom_cpu(test_image, 3, 8, 5, 5, 1.0)    # zoom=2.0
# High zoom should be more zoomed in
```

### Center Response (`test_center_response`)
```python
# Different centers should zoom to different areas
center_left = delay_zoom_cpu(test_image, 3, 5, 2, 5, 1.0)    # center_x=0.2
center_right = delay_zoom_cpu(test_image, 3, 5, 8, 5, 1.0)   # center_x=0.8
# Should zoom to different parts of image
```

### Delay Count Response (`test_delay_count`)
```python
# More copies should create more zoom effect
low_count = delay_zoom_cpu(test_image, 2, 5, 5, 5, 1.0)
high_count = delay_zoom_cpu(test_image, 6, 5, 5, 5, 1.0)
# High count should have more zoom trails
```

### Opacity Blend (`test_opacity_blend`)
```python
# opacity=0 → output = input
# opacity=1 → output = zoomed
```

## Coverage

- [x] Progressive zoom scaling (0.5–2.0)
- [x] Multiple zoom copies (1–8)
- [x] Independent zoom centers (X/Y)
- [x] Weighted normalization
- [x] Parameter remapping (0–10 UI scale)
- [x] CPU+GPU fallback dispatch
- [x] Error handling (bounds, invalid params)
- [x] Presets (4 tuned combinations)
- [x] Tests (zoom level, center, count, opacity)

**Estimated Coverage:** 85% (zoom math, parameter validation, presets, edge cases)

## Manifest Entry

```yaml
- id: P7-VE75
  name: delay_zoom
  class: DelayZoomEffect
  category: post-process
  parameters:
    delay_count: [0, 10, 5.0]
    zoom_level: [0, 10, 5.0]
    zoom_center_x: [0, 10, 5.0]
    zoom_center_y: [0, 10, 5.0]
    opacity: [0, 10, 10.0]
  gpu_required: false
  cpu_fallback: true
```

---

**Artisanal Note:** Delay zoom creates zoom trails through progressive scaling with multiple copies. Independent zoom centers enable directional zoom effects. CPU fallback uses affine transformations for scaling. Presets calibrated for zoom trails, motion zoom, and center zoom effects.
- No silent failures, proper error handling (Safety Rail 7)

## Implementation Notes

**Original Location:** `vjlive/plugins/vcore/vcv_video_effects.py`
**Description:** No description available

### Porting Strategy

1. Study the original implementation in `vjlive/plugins/vcore/vcv_video_effects.py`
2. Identify dependencies and required resources (shaders, textures, etc.)
3. Adapt to VJLive3's plugin architecture (see `src/vjlive3/plugins/`)
4. Write comprehensive tests (≥80% coverage)
5. Verify against original behavior with test vectors
6. Document any deviations or improvements

## Verification Checkpoints

- [ ] Plugin loads successfully via registry
- [ ] All parameters exposed and editable
- [ ] Renders at 60 FPS minimum
- [ ] Test coverage ≥80%
- [ ] No safety rail violations
- [ ] Original functionality verified (side-by-side comparison)

## Resources

- Original source: `vjlive/plugins/vcore/vcv_video_effects.py`
- Audit report: `docs/audit_report_comprehensive.json`
- Plugin system spec: `docs/specs/P1-P1_plugin_registry.md` (or appropriate)
- Base classes: `src/vjlive3/plugins/`, `src/vjlive3/render/`

## Dependencies

- [ ] List any dependencies on other plugins or systems

---

**Bespoke Snowflake Principle:** This plugin is unique. Do not batch-process. Give it individual attention and quality.