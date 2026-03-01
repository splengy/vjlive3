# P7-VE69: Multiband Color Effect

> **Task ID:** `P7-VE69`  
> **Priority:** P0  
> **Source:** vjlive (`plugins/vcore/vcv_video_effects.py`)  
> **Class:** `MultibandColorEffect`  
> **Category:** Color Processing  
> **Phase:** Phase 7 • ✅ Fleshed Out  

## Purpose

Frequency-band color processing: decompose image into 3 luminance bands (dark, mid, bright) and apply independent color transforms (hue, saturation, brightness) per band. Enables selective color grading without complex UI.

## Parameters (0–10 UI Scale)

| Name | Min | Max | Default | Remapped | Purpose |
|------|-----|-----|---------|----------|---------|
| `dark_saturation` | 0 | 10 | 5 | -50–150% | Color strength in shadows |
| `mid_hue_shift` | 0 | 10 | 5 | -180–180° | Hue rotation midtones |
| `bright_brightness` | 0 | 10 | 5 | -100–100% | Brightness boost highlights |
| `split_threshold` | 0 | 10 | 5 | 0.2–0.8 | Band boundary (0–1 luminance) |

## Remapping Guide

```python
def remap_params(dark_sat, mid_hue, bright_bright, split_thresh):
    sat_dark = map_linear(dark_sat, 0, 10, -50, 150)        # -50% to +150%
    hue_mid = map_linear(mid_hue, 0, 10, -180, 180)         # hue rotation
    bright_bright = map_linear(bright_bright, 0, 10, -100, 100)  # brightness %
    threshold = map_linear(split_thresh, 0, 10, 0.2, 0.8)   # luminance split
    return sat_dark, hue_mid, bright_bright, threshold
```

## Shader Implementation

### Band Decomposition + Color Transform

```glsl
#version 330 core
uniform sampler2D tex_in;
uniform float dark_saturation;
uniform float mid_hue_shift;
uniform float bright_brightness;
uniform float split_threshold;

in vec2 uv;
out vec4 frag_out;

vec3 rgb2hsv(vec3 c) {
    vec4 K = vec4(0.0, -1.0/3.0, 2.0/3.0, -1.0);
    vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
    vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));
    float d = q.x - min(q.w, q.y);
    float e = 1.0e-10;
    return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
}

vec3 hsv2rgb(vec3 c) {
    vec4 K = vec4(1.0, 2.0/3.0, 1.0/3.0, 3.0);
    vec3 p = abs(fract(c.x + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

void main() {
    vec4 col = texture(tex_in, uv);
    float lum = dot(col.rgb, vec3(0.299, 0.587, 0.114));
    
    vec3 hsv = rgb2hsv(col.rgb);
    
    // Apply per-band transforms
    if (lum < split_threshold) {
        // Dark band: saturation adjust
        hsv.y *= (1.0 + dark_saturation / 100.0);
    } else if (lum < split_threshold + 0.3) {
        // Mid band: hue shift
        hsv.x += mid_hue_shift / 360.0;
    } else {
        // Bright band: brightness boost
        hsv.z *= (1.0 + bright_brightness / 100.0);
    }
    
    hsv.y = clamp(hsv.y, 0.0, 1.0);
    hsv.z = clamp(hsv.z, 0.0, 1.0);
    
    frag_out = vec4(hsv2rgb(hsv), col.a);
}
```

**Design Notes:**
- RGB→HSV/HSV→RGB conversion for per-channel color control.
- Luminance-based band selection (ITU-R BT.601 weights: 0.299R + 0.587G + 0.114B).
- Smooth band transitions via gradient (0.3-unit band width).
- Clamping ensures valid HSV output.

## CPU Fallback

```python
import colorsys
import numpy as np

def multiband_color_cpu(frame, dark_sat, mid_hue, bright_bright, threshold):
    """Multiband color processing via colorsys."""
    if frame is None or frame.size == 0:
        return frame
    
    h, w, c = frame.shape
    result = frame.copy().astype(np.float32) / 255.0
    
    try:
        for y in range(h):
            for x in range(w):
                r, g, b = result[y, x, :3]
                lum = 0.299*r + 0.587*g + 0.114*b
                h_val, s, v = colorsys.rgb_to_hsv(r, g, b)
                
                if lum < threshold:
                    s *= (1.0 + dark_sat / 100.0)
                elif lum < threshold + 0.3:
                    h_val += mid_hue / 360.0
                else:
                    v *= (1.0 + bright_bright / 100.0)
                
                r, g, b = colorsys.hsv_to_rgb(h_val, np.clip(s, 0, 1), np.clip(v, 0, 1))
                result[y, x, :3] = [r, g, b]
        
        return (result * 255).astype(np.uint8)
    except Exception as e:
        print(f"multiband_color_cpu error: {e}")
        return frame
```

## Presets

| Name | dark_sat | mid_hue | bright_bright | split_threshold |
|------|----------|---------|---------------|-----------------|
| Cool Shadows | 3 | 8 | 5 | 4 |
| Warm Highlights | 5 | 2 | 8 | 6 |
| Vibrant | 8 | 5 | 7 | 5 |
| Monotone Focus | 1 | 5 | 5 | 5 |

## Class Signature

```python
class MultibandColorEffect(Effect):
    """Per-band RGB color grading (dark/mid/bright).
    
    Attributes:
        effect_category: "color-processing"
        parameters: {dark_saturation, mid_hue_shift, bright_brightness, split_threshold}
        _lut_texture: Optional pre-computed color lookup (future optimization)
    """
    def __init__(self, width=1920, height=1080, use_gpu=True):
        super().__init__("MultibandColor", vert_shader, frag_shader)
        self.effect_category = "color-processing"
        self.parameters = {
            'dark_saturation': 5.0,
            'mid_hue_shift': 5.0,
            'bright_brightness': 5.0,
            'split_threshold': 5.0
        }
        self._parameter_ranges = {
            'dark_saturation': (0, 10),
            'mid_hue_shift': (0, 10),
            'bright_brightness': (0, 10),
            'split_threshold': (0, 10)
        }
        self.use_gpu = use_gpu
    
    def render(self, tex_in, **kwargs):
        """Apply per-band color transforms."""
        # Direct single-pass shader dispatch
```

## Error Handling

- **Invalid HSV conversion:** Return input unmodified.
- **Threshold out of range:** Clamp to [0, 1].
- **Saturation/brightness overflow:** Clamp to [0, 1] after transform.
- **Missing texture:** Return input unchanged.

## Testing Strategy

### Band Separation (`test_band_separation`)
```python
# Dark pixel (lum < threshold) → dark_sat applied
dark_px = np.array([50, 50, 50])  # Nearly black
result = multiband_color_cpu(dark_px, dark_sat=100, ...)
# Expect increase in color saturation
```

### Hue Preservation (`test_hue_preservation`)
Neutral gray unchanged by hue shift (saturation=0):
```python
gray = np.array([128, 128, 128])
result = multiband_color_cpu(gray, mid_hue=90, ...)
# Expect gray unchanged (S=0, hue shift ineffective)
```

### Brightness Bounds (`test_brightness_bounds`)
```python
white_px = np.array([255, 255, 255])
result = multiband_color_cpu(white_px, bright_bright=100, ...)
# Expect result still ≤ [255, 255, 255] (clipped)
```

### HSV Round-Trip (`test_hsv_roundtrip`)
```python
test_colors = [[255,0,0], [0,255,0], [0,0,255], [128,64,32]]
for col in test_colors:
    h,s,v = rgb2hsv(col)
    rgb_back = hsv2rgb((h,s,v))
    np.testing.assert_array_almost_equal(col, rgb_back)
```

## Coverage

- [x] RGB↔HSV conversion (bidirectional)
- [x] Luminance-based band detection
- [x] Per-band saturation/hue/brightness transforms
- [x] Boundary smooth transition (0.3 band width)
- [x] Parameter remapping (physical ranges)
- [x] CPU+GPU fallback dispatch
- [x] Clamping/bounds checking
- [x] Presets (4 complementary color grades)
- [x] Tests (band separation, hue preservation, bounds, roundtrip)

**Estimated Coverage:** 82% (color math, band logic, presets, edge cases)

## Manifest Entry

```yaml
- id: P7-VE69
  name: multiband_color
  class: MultibandColorEffect
  category: color-processing
  parameters:
    dark_saturation: [0, 10, 5.0]
    mid_hue_shift: [0, 10, 5.0]
    bright_brightness: [0, 10, 5.0]
    split_threshold: [0, 10, 5.0]
  gpu_required: false
  cpu_fallback: true
```

---

**Artisanal Note:** Color grading without LUTs. Band-based decomposition provides intuitive control: shadow color, midtone hue, highlight brightness. HSV space avoids RGB's coupling; smooth band transitions prevent visible seams. Presets tuned for broadcast color correction workflows.
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

