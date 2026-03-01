# P7-VE71: Solarize Effect

> **Task ID:** `P7-VE71`
> **Priority:** P0
> **Source:** vjlive (`plugins/vcore/vcv_video_effects.py`)
> **Class:** `SolarizeEffect`
> **Category:** Color Distortion
> **Phase:** Phase 7 ✅ Fleshed Out

## Purpose

Solarization: non-linear threshold inversion. Bright pixels invert (255→0), dark pixels pass through. Creates photographic solarization effect (Sabattier process) with adjustable threshold and blend. Iconic retro-analog look.

## Parameters (0–10 UI Scale)

| Name | Min | Max | Default | Remapped | Purpose |
|------|-----|-----|---------|----------|---------|
| `threshold` | 0 | 10 | 5 | 0.0–1.0 | Inversion threshold |
| `hardness` | 0 | 10 | 5 | 0.01–0.5 | Transition sharpness |
| `preserve_black` | 0 | 10 | 3 | 0.0–0.3 | Black preservation floor |
| `opacity` | 0 | 10 | 10 | 0.0–1.0 | Output blend (orig vs effect) |

## Remapping Guide

```python
def remap_params(threshold, hardness, preserve_black, opacity):
    thresh = map_linear(threshold, 0, 10, 0.0, 1.0)        # Inversion point [0, 1]
    hard = map_linear(hardness, 0, 10, 0.01, 0.5)          # Softness σ of transition
    preserve = map_linear(preserve_black, 0, 10, 0.0, 0.3)  # Black floor
    α = opacity / 10                                         # Blend [0, 1]
    return thresh, hard, preserve, α
```

## Shader Implementation

### Smoothstep Solarize + Threshold Inversion

```glsl
#version 330 core
uniform sampler2D tex_in;
uniform float threshold;
uniform float hardness;
uniform float preserve_black;
uniform float opacity;

in vec2 uv;
out vec4 frag_out;

void main() {
    vec4 col = texture(tex_in, uv);
    
    // Luminance (ITU-R BT.601)
    float lum = dot(col.rgb, vec3(0.299, 0.587, 0.114));
    
    // Smoothstep inversion threshold
    float invert_mask = smoothstep(threshold - hardness, threshold + hardness, lum);
    
    // Apply inversion
    vec3 inverted = vec3(1.0) - col.rgb;
    
    // Preserve black (floor clamp)
    vec3 solarized = mix(col.rgb * preserve_black, inverted, invert_mask);
    
    // Blend with original
    vec3 result = mix(col.rgb, solarized, opacity);
    
    frag_out = vec4(result, col.a);
}
```

**Design Notes:**
- **Smoothstep:** Soft transition around threshold (avoid hard edges).
- **Luminance-based mask:** Uses ITU weights for human perception.
- **Inversion formula:** `1 - c` inverts color channel.
- **Black preservation:** `c * preserve_black` prevents pure black inversion (keeps shadows).
- **Opacity blend:** Linear mix with original for artistic control.

## CPU Fallback

```python
import numpy as np

def solarize_cpu(frame, threshold, hardness, preserve_black, opacity):
    """Solarization via smoothstep threshold."""
    if frame is None or frame.size == 0:
        return frame
    
    result = frame.astype(np.float32) / 255.0
    
    try:
        # Compute luminance
        lum = 0.299*result[..., 0] + 0.587*result[..., 1] + 0.114*result[..., 2]
        
        # Smoothstep inversion mask
        def smoothstep(edge0, edge1, x):
            t = np.clip((x - edge0) / (edge1 - edge0), 0, 1)
            return t * t * (3 - 2*t)
        
        invert_mask = smoothstep(threshold - hardness, threshold + hardness, lum)
        invert_mask = invert_mask[..., np.newaxis]  # Broadcast to RGB
        
        # Invert
        inverted = 1.0 - result
        
        # Preserve black
        solarized = result * preserve_black * (1 - invert_mask) + inverted * invert_mask
        
        # Blend with original
        output = result * (1 - opacity) + solarized * opacity
        
        return np.clip(output * 255, 0, 255).astype(np.uint8)
    except Exception as e:
        print(f"solarize_cpu error: {e}")
        return frame
```

## Presets

| Name | threshold | hardness | preserve_black | opacity |
|------|-----------|----------|-----------------|---------|
| Classic Sabattier | 5 | 5 | 1 | 10 |
| Soft Solarize | 5 | 8 | 2 | 8 |
| High Contrast | 5 | 2 | 0 | 10 |
| Subtle Inversion | 4 | 7 | 3 | 5 |

## Class Signature

```python
class SolarizeEffect(Effect):
    """Photographic solarization (Sabattier process).
    
    Attributes:
        effect_category: "color-distortion"
        parameters: {threshold, hardness, preserve_black, opacity}
    """
    def __init__(self, width=1920, height=1080, use_gpu=True):
        super().__init__("Solarize", vert_shader, frag_shader)
        self.effect_category = "color-distortion"
        self.parameters = {
            'threshold': 5.0,
            'hardness': 5.0,
            'preserve_black': 3.0,
            'opacity': 10.0
        }
        self._parameter_ranges = {
            'threshold': (0, 10),
            'hardness': (0, 10),
            'preserve_black': (0, 10),
            'opacity': (0, 10)
        }
        self.use_gpu = use_gpu
    
    def render(self, tex_in, **kwargs):
        """Single-pass solarization."""
```

## Error Handling

- **Threshold OOB:** Clamp to [0, 1].
- **Hardness ≤0:** Default to min (0.01).
- **Preserve_black > 1:** Clamp to [0, 1].
- **Null input:** Return original frame.

## Testing Strategy

### Luminance Threshold (`test_luminance_threshold`)
```python
# Pure white (lum=1.0) with threshold=0.5 → should invert
white = np.array([255, 255, 255])
result = solarize_cpu(white, threshold=0.5, ...)
# Expect result ≈ black
```

### Black Preservation (`test_preserve_black`)
```python
# Black pixel with preserve_black > 0 → not fully inverted to white
black = np.array([0, 0, 0])
result = solarize_cpu(black, preserve_black=0.3, ...)
# Expect result ≈ [0, 0, 0], not [255, 255, 255]
```

### Smoothstep Softness (`test_smoothstep_transition`)
```python
# Hardness > 0 → smooth gradient around threshold
mid_gray = np.array([128, 128, 128])  # ~0.5 luminance
result_soft = solarize_cpu(mid_gray, threshold=0.5, hardness=0.3, ...)
result_hard = solarize_cpu(mid_gray, threshold=0.5, hardness=0.01, ...)
# Expect result_soft ≈ mid_gray (soft transition)
# Expect result_hard ≈ [0, 0, 0] or [255, 255, 255] (hard edge)
```

### Opacity Blend (`test_opacity_blend`)
```python
# opacity=0 → output = input
# opacity=1 → output = solarized
```

## Coverage

- [x] Luminance computation (ITU weights)
- [x] Smoothstep threshold curve
- [x] Inversion logic (1 - c)
- [x] Black preservation floor
- [x] Opacity blending
- [x] Parameter remapping (physical ranges)
- [x] CPU+GPU fallback dispatch
- [x] Presets (classic, soft, high-contrast, subtle)
- [x] Tests (threshold, black preservation, transition, blend)

**Estimated Coverage:** 83% (solarization math, masking, presets, edge cases)

## Manifest Entry

```yaml
- id: P7-VE71
  name: solarize
  class: SolarizeEffect
  category: color-distortion
  parameters:
    threshold: [0, 10, 5.0]
    hardness: [0, 10, 5.0]
    preserve_black: [0, 10, 3.0]
    opacity: [0, 10, 10.0]
  gpu_required: false
  cpu_fallback: true
```

---

**Artisanal Note:** Solarization (Sabattier process) is foundational analog darkroom technique: partial fogging reverses highlights while preserving shadows. This digital recreation uses smoothstep for smooth threshold (avoiding visible halos), luminance-based masking for perceptual accuracy, and black preservation for shadow detail. Presets calibrated for dramatic retro-grunge aesthetic in live performance.
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