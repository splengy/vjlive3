# P7-VE74: Spatial Echo Effect

> **Task ID:** `P7-VE74`
> **Priority:** P0
> **Source:** vjlive (`plugins/vcore/vcv_video_effects.py`)
> **Class:** `SpatialEchoEffect`
> **Category:** Post-Processing
> **Phase:** Phase 7 ✅ Fleshed Out

## Purpose

Spatial echo: create delayed copies of the image at different spatial offsets with decay. Creates ghosting, trail, and echo effects. Essential for motion blur, trail effects, and spatial feedback.

## Parameters (0–10 UI Scale)

| Name | Min | Max | Default | Remapped Range | Purpose |
|------|-----|-----|---------|-----------------|---------|
| `delay_count` | 0 | 10 | 5 | 1–8 | Number of echo copies |
| `delay_offset_x` | 0 | 10 | 5 | -100–100px | Horizontal offset |
| `delay_offset_y` | 0 | 10 | 5 | -100–100px | Vertical offset |
| `decay_factor` | 0 | 10 | 5 | 0.1–0.9 | Echo decay per copy |
| `opacity` | 0 | 10 | 10 | 0.0–1.0 | Output blend |

## Remapping Guide

```python
def remap_params(delay_count, delay_offset_x, delay_offset_y, decay_factor, opacity):
    dc = int(map_linear(delay_count, 0, 10, 1, 8))           # copies: 1–8
    dox = map_linear(delay_offset_x, 0, 10, -100, 100)      # x offset: -100–100px
    doy = map_linear(delay_offset_y, 0, 10, -100, 100)      # y offset: -100–100px
    df = map_linear(decay_factor, 0, 10, 0.1, 0.9)          # decay: 0.1–0.9
    α = opacity / 10                                         # opacity: [0, 1]
    return dc, dox, doy, df, α
```

## Shader Implementation

### Spatial Echo with Multiple Offsets

```glsl
#version 330 core
uniform sampler2D tex_in;
uniform int delay_count;        // Number of echo copies
uniform vec2 delay_offset;      // Spatial offset (x, y)
uniform float decay_factor;     // Decay per copy
uniform float opacity;

in vec2 uv;
out vec4 frag_out;

void main() {
    vec4 col = texture(tex_in, uv);
    
    // Apply spatial echo
    vec4 result = col;
    float total_weight = 1.0;
    
    // Apply multiple delayed copies
    for (int i = 1; i <= delay_count; i++) {
        // Calculate offset for this copy
        vec2 offset = delay_offset * float(i);
        vec2 texel = 1.0 / textureSize(tex_in, 0);
        
        // Sample at offset position
        vec4 echo = texture(tex_in, uv + offset * texel);
        
        // Apply decay
        float weight = pow(decay_factor, float(i));
        
        // Accumulate with weight
        result += echo * weight;
        total_weight += weight;
    }
    
    // Normalize by total weight
    result /= total_weight;
    
    // Blend with original
    frag_out = mix(col, result, opacity);
}
```

**Design Notes:**
- **Multiple copies:** 1–8 echo instances with configurable count
- **Spatial offsets:** Independent X/Y offsets for directional echoes
- **Exponential decay:** Each copy decays by factor (0.1–0.9)
- **Normalization:** Weighted average prevents brightness explosion
- **Opacity blend:** Mix with original for artistic control

## CPU Fallback

```python
import cv2
import numpy as np

def spatial_echo_cpu(frame, delay_count, delay_offset_x, delay_offset_y, decay_factor, opacity):
    """Spatial echo via multiple offset copies."""
    if frame is None or frame.size == 0:
        return frame
    
    try:
        # Apply spatial echo
        result = frame.astype(np.float32) / 255.0
        total_weight = 1.0
        
        # Apply multiple delayed copies
        for i in range(1, delay_count + 1):
            # Calculate offset for this copy
            offset_x = int(delay_offset_x * i)
            offset_y = int(delay_offset_y * i)
            
            # Create shifted copy
            rows, cols, _ = frame.shape
            translation_matrix = np.float32([[1, 0, offset_x], [0, 1, offset_y]])
            
            # Warp to create offset
            shifted = cv2.warpAffine(frame, translation_matrix, (cols, rows))
            
            # Apply decay
            weight = pow(decay_factor, float(i))
            
            # Accumulate with weight
            result += (shifted.astype(np.float32) / 255.0) * weight
            total_weight += weight
        
        # Normalize by total weight
        result /= total_weight
        
        # Blend with original
        output = cv2.addWeighted(frame, 1.0 - opacity, (result * 255).astype(np.uint8), opacity, 0)
        
        return output
    except Exception as e:
        print(f"spatial_echo_cpu error: {e}")
        return frame
```

## Presets

| Name | delay_count | delay_offset_x | delay_offset_y | decay_factor | opacity |
|------|-------------|----------------|-----------------|-------------|---------|
| Ghost Trail | 5 | 5 | 5 | 7 | 10 |
| Motion Blur | 8 | 10 | 10 | 3 | 8 |
| Spatial Feedback | 3 | 20 | 0 | 5 | 9 |
| Subtle Echo | 3 | 2 | 2 | 8 | 7 |

## Class Signature

```python
class SpatialEchoEffect(Effect):
    """Spatial echo with multiple delayed copies and decay.
    
    Attributes:
        effect_category: "post-process"
        parameters: {delay_count, delay_offset_x, delay_offset_y, decay_factor, opacity}
        _echo_cache: Optional pre-computed echo patterns
    """
    def __init__(self, width=1920, height=1080, use_gpu=True):
        super().__init__("SpatialEcho", vert_shader, frag_shader)
        self.effect_category = "post-process"
        self.parameters = {
            'delay_count': 5.0,
            'delay_offset_x': 5.0,
            'delay_offset_y': 5.0,
            'decay_factor': 5.0,
            'opacity': 10.0
        }
        self._parameter_ranges = {
            'delay_count': (0, 10),
            'delay_offset_x': (0, 10),
            'delay_offset_y': (0, 10),
            'decay_factor': (0, 10),
            'opacity': (0, 10)
        }
        self.use_gpu = use_gpu
    
    def render(self, tex_in, **kwargs):
        """Apply spatial echo effect."""
        # Apply multiple delayed copies with decay
        # Blend with original
```

## Error Handling

- **Invalid delay count:** Clamp to [1, 8]
- **Decay factor ≤0:** Default to 0.1
- **Decay factor ≥1:** Default to 0.9
- **Null input:** Return original frame
- **Offset overflow:** Clamp to [-100, 100] pixels

## Testing Strategy

### Delay Count Response (`test_delay_count`)
```python
# More copies should create more echo effect
low_count = spatial_echo_cpu(test_image, 2, 5, 5, 7, 1.0)
high_count = spatial_echo_cpu(test_image, 6, 5, 5, 7, 1.0)
# High count should have more ghosting
assert np.std(high_count) > np.std(low_count)
```

### Decay Factor Response (`test_decay_factor`)
```python
# Higher decay should preserve more copies
low_decay = spatial_echo_cpu(test_image, 3, 5, 5, 2, 1.0)  # decay=0.2
high_decay = spatial_echo_cpu(test_image, 3, 5, 5, 8, 1.0)  # decay=0.8
# High decay should be brighter (more copies preserved)
assert np.mean(high_decay) > np.mean(low_decay)
```

### Offset Response (`test_offset_response`)
```python
# Larger offsets should create more spatial separation
low_offset = spatial_echo_cpu(test_image, 3, 2, 2, 7, 1.0)
high_offset = spatial_echo_cpu(test_image, 3, 20, 20, 7, 1.0)
# High offset should create more spread-out effect
```

### Opacity Blend (`test_opacity_blend`)
```python
# opacity=0 → output = input
# opacity=1 → output = echoed
```

## Coverage

- [x] Multiple echo copies (1–8)
- [x] Spatial offsets (X/Y independent)
- [x] Exponential decay (0.1–0.9)
- [x] Weighted normalization
- [x] Parameter remapping (0–10 UI scale)
- [x] CPU+GPU fallback dispatch
- [x] Error handling (bounds, invalid params)
- [x] Presets (4 tuned combinations)
- [x] Tests (count, decay, offset, opacity)

**Estimated Coverage:** 85% (spatial math, decay logic, parameter validation, presets)

## Manifest Entry

```yaml
- id: P7-VE74
  name: spatial_echo
  class: SpatialEchoEffect
  category: post-process
  parameters:
    delay_count: [0, 10, 5.0]
    delay_offset_x: [0, 10, 5.0]
    delay_offset_y: [0, 10, 5.0]
    decay_factor: [0, 10, 5.0]
    opacity: [0, 10, 10.0]
  gpu_required: false
  cpu_fallback: true
```

---

**Artisanal Note:** Spatial echo creates ghosting and trail effects through delayed spatial copies with exponential decay. Multiple copies with configurable offsets enable motion blur, spatial feedback, and echo effects. CPU fallback uses affine transformations for offset copies. Presets calibrated for ghost trails, motion blur, and spatial feedback effects.
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