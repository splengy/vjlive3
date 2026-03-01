# P7-VE58: Resize Effect

> **Task ID:** `P7-VE58`
> **Priority:** P0 (Critical)
> **Source:** vjlive (`plugins/vcore/resize_effect.py`)
> **Class:** `ResizeEffect`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
A fundamental geometry transform: scale, translate, and crop the input frame.
Despite its simplicity, Resize was heavily used in VJLive mixdowns and must be
preserved for backward compatibility with legacy sessions.

## Technical Requirements
- Manifest-registered `Effect` subclass, inheriting from standard `Effect`.
- Parameters: `scale_x`, `scale_y`, `offset_x`, `offset_y`, `crop`, `opacity`.
- GPU rendering via texture sampling with adjusted UV coordinates;
  CPU fallback via OpenCV/PIL resizing.
- Maintain 60 FPS at 1080p across all scale/offset ranges.
- ≥80 % test coverage; validate bounds on scale (no divide-by-zero).
- Keep spec <750 lines.

## Public Interface
```python
class ResizeEffect(Effect):
    """Scale, translate, and crop video frame."""

    def __init__(self, width=1920, height=1080, use_gpu=True):
        super().__init__("Resize",
                         vertex_shader=RESIZE_VERT,
                         fragment_shader=RESIZE_FRAG)
        self.effect_category = "geometry"
        self.effect_tags = ["spatial", "transform"]
        self.features = ["GPU_NATIVE"]
        self.parameters = {
            'scale_x': 10.0,
            'scale_y': 10.0,
            'offset_x': 5.0,
            'offset_y': 5.0,
            'crop': 0.0,
            'opacity': 10.0
        }
        self._parameter_ranges = {
            'scale_x': (0.1, 10.0),
            'scale_y': (0.1, 10.0),
            'offset_x': (0.0, 10.0),
            'offset_y': (0.0, 10.0),
            'crop': (0.0, 10.0),
            'opacity': (0.0, 10.0)
        }
        self._param_desc = {
            'scale_x': 'Horizontal scaling factor.',
            'scale_y': 'Vertical scaling factor.',
            'offset_x': 'Horizontal pan.',
            'offset_y': 'Vertical pan.',
            'crop': 'Edge crop amount.',
            'opacity': 'Blend with source.'
        }
        self.use_gpu = use_gpu

    def render(self, tex_in, extra_textures=None, chain=None):
        # Apply scaling and translation via MVP matrix or texture coordinate xform
        pass

    def apply_uniforms(self, time, resolution, audio=None, semantic=None):
        # Remap parameters to texture coordinates
        pass
```

### Parameter Remaps
- `scale_x` → Sx = map_linear(x, 0.1, 10, 0.1, 3.0)
- `scale_y` → Sy = map_linear(x, 0.1, 10, 0.1, 3.0)
- `offset_x` → Ox = map_linear(x, 0, 10, -1, 1)
- `offset_y` → Oy = map_linear(x, 0, 10, -1, 1)
- `crop` → C = map_linear(x, 0, 10, 0, 0.45)
- `opacity` → α = x / 10

## Shader Uniforms
```glsl
uniform float scale_x;
uniform float scale_y;
uniform float offset_x;
uniform float offset_y;
uniform float crop;
uniform float opacity;
```

## Effect Math
```glsl
vec2 uv = fragCoord / resolution;
// Apply crop
if (uv.x < crop || uv.x > 1.0 - crop ||
    uv.y < crop || uv.y > 1.0 - crop) {
    return vec4(0.0);  // black border
}
// Rescale and offset
uv -= 0.5;  // center
uv /= vec2(scale_x, scale_y);
uv += vec2(offset_x, offset_y);  // pan
uv += 0.5;  // uncenter
vec3 col = texture(tex_in, uv).rgb;
return vec4(mix(old_col, col, opacity), 1.0);
```

## CPU Fallback
```python
import cv2
import numpy as np

def resize_cpu(frame, scale_x, scale_y, offset_x, offset_y, crop, opacity):
    h, w = frame.shape[:2]
    # Apply crop
    crop_px = int(crop * min(h, w))
    cropped = frame[crop_px:h-crop_px, crop_px:w-crop_px]
    # Resize
    new_h, new_w = int(h / scale_y), int(w / scale_x)
    resized = cv2.resize(cropped, (new_w, new_h), interp=cv2.INTER_LINEAR)
    # Pad back to original size
    pad_h = (h - new_h) // 2
    pad_w = (w - new_w) // 2
    padded = cv2.copyMakeBorder(resized, pad_h, h - new_h - pad_h,
                                 pad_w, w - new_w - pad_w,
                                 cv2.BORDER_CONSTANT, value=0)
    # Apply pan via circular shift
    shift_x = int(offset_x * w * 0.1)
    shift_y = int(offset_y * h * 0.1)
    padded = np.roll(padded, (shift_y, shift_x), axis=(0, 1))
    return (frame * (1 - opacity) + padded * opacity).astype(np.uint8)
```

## Presets
- `Zoom In`: scale_x=1.5, scale_y=1.5
- `Zoom Out`: scale_x=0.7, scale_y=0.7
- `Pan Right`: offset_x=7, offset_y=5
- `Crop`: crop=3

## Edge Cases
- scale_x/y == 0: clamp to min (0.1)
- crop > 0.45: clamp to 0.45 (prevent black frame)
- offset_x/y outside bounds: wrap or clamp

## Test Plan
- `test_scale_symmetry`
- `test_offset_bounds`
- `test_crop_symmetry`
- `test_cpu_gpu_agreement`
- `test_performance_1080p`

## Verification Checklist
- [ ] Scaling is reversible (2x then 0.5x = identity)
- [ ] Offset wraps correctly
- [ ] Crop maintains aspect ratio

---

**Note:** Simple geometry effect; stateless.


