# P7-VE60: Silver Visions Video Output

> **Task ID:** `P7-VE60`
> **Priority:** P0 (Critical)
> **Source:** VJlive-2 (`plugins/silver_visions.py`)
> **Class:** `VideoOutEffect`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
A signal-passing and conditioning effect from VJlive-2's silver_visions suite.
This effect acts as a monitor/probe point, allowing monitoring, color space
conversion, and optional signal stretching. Essential for hybrid video pipeline
work.

## Technical Requirements
- Manifest-registered `Effect` subclass, inheriting from standard `Effect`.
- Parameters: `brightness`, `contrast`, `saturation`, `color_space_mode`,
  `stretch`, `opacity`.
- GPU color grading pass; CPU fallback via NumPy color transforms.
- Maintain 60 FPS at 1080p across all color space modes.
- ≥80 % test coverage; explicit color range validation.
- Keep spec <750 lines.

## Public Interface
```python
class VideoOutEffect(Effect):
    """Video monitoring and signal conditioning."""

    def __init__(self, width=1920, height=1080, use_gpu=True):
        super().__init__("VideoOut",
                         vertex_shader=VIDEOOUT_VERT,
                         fragment_shader=VIDEOOUT_FRAG)
        self.effect_category = "monitoring"
        self.effect_tags = ["output", "probe", "conditioning"]
        self.features = ["GPU_NATIVE", "COLOR_SPACE"]
        self.parameters = {
            'brightness': 5.0,
            'contrast': 5.0,
            'saturation': 5.0,
            'color_space_mode': 1.0,
            'stretch': 0.0,
            'opacity': 10.0
        }
        self._parameter_ranges = {
            'brightness': (0.0, 10.0),
            'contrast': (0.0, 10.0),
            'saturation': (0.0, 10.0),
            'color_space_mode': (0.0, 4.0),
            'stretch': (0.0, 10.0),
            'opacity': (0.0, 10.0)
        }
        self._param_desc = {
            'brightness': 'Video level offset.',
            'contrast': 'Video contrast (slope).',
            'saturation': 'Color saturation.',
            'color_space_mode': '0=RGB, 1=YCbCr, 2=HSV, 3=LAB, 4=Linear',
            'stretch': 'Black/white stretching (auto-contrast).',
            'opacity': 'Blend with source.'
        }
        self.use_gpu = use_gpu

    def render(self, tex_in, extra_textures=None, chain=None):
        # Apply color correction and optional color space conversion
        pass

    def apply_uniforms(self, time, resolution, audio=None, semantic=None):
        # Remap parameters for color grading pipeline
        pass
```

### Parameter Remaps
- `brightness` → B = map_linear(x, 0, 10, -1, 1)
- `contrast` → C = map_linear(x, 0, 10, 0, 2.5)
- `saturation` → S = map_linear(x, 0, 10, 0, 2)
- `color_space_mode` → M = int(map_linear(x, 0, 4, 0, 4))
- `stretch` → T = map_linear(x, 0, 10, 0, 1)  (auto-stretch)
- `opacity` → α = x / 10

## Shader Uniforms
```glsl
uniform float brightness;
uniform float contrast;
uniform float saturation;
uniform int color_space;
uniform float stretch;
uniform sampler2D tex_in;
```

## Effect Math
```glsl
vec3 col = texture(tex_in, uv).rgb;
// Brightness and contrast
col = (col - 0.5) * contrast + 0.5;
col += brightness;
// Saturation
vec3 gray = vec3(dot(col, vec3(0.299, 0.587, 0.114)));
col = mix(gray, col, saturation);
// Auto-stretch
if (stretch > 0.0) {
    float minc = min(min(col.r, col.g), col.b);
    float maxc = max(max(col.r, col.g), col.b);
    float range = max(0.001, maxc - minc);
    col = (col - minc) / range * mix(1.0, stretch, stretch);
}
return vec4(clamp(col, 0.0, 1.0), 1.0);
```

## CPU Fallback
```python
import numpy as np

def video_out_cpu(frame, brightness, contrast, saturation, cs_mode, stretch, opacity):
    frame = frame.astype(np.float32) / 255.0
    # Brightness and contrast
    frame = (frame - 0.5) * contrast + 0.5 + brightness
    # Saturation
    gray = 0.299 * frame[..., 0] + 0.587 * frame[..., 1] + 0.114 * frame[..., 2]
    frame = (1 - saturation) * gray[..., np.newaxis] + saturation * frame
    # Auto-stretch
    if stretch > 0:
        minc = frame.min(axis=2, keepdims=True)
        maxc = frame.max(axis=2, keepdims=True)
        frame = (frame - minc) / (maxc - minc + 1e-6)
    return np.clip(frame * 255, 0, 255).astype(np.uint8)
```

## Presets
- `Bright Monitor`: brightness=2, contrast=1
- `Crushed Blacks`: brightness=-1, contrast=2
- `Desaturated`: saturation=0
- `Auto Stretch`: stretch=1

## Edge Cases
- contrast = 0: linear gray output
- saturation > 1: over-saturation allowed for creative effect
- stretch with low-range input requires epsilon for stability

## Test Plan
- `test_brightness_offset`
- `test_contrast_slope`
- `test_saturation_range`
- `test_auto_stretch_bounds`
- `test_cpu_gpu_agreement`

## Verification Checklist
- [ ] Brightness offsets correctly
- [ ] Contrast scales properly
- [ ] Auto-stretch normalizes correctly

---

**Note:** Stateless monitoring pass; primary use is signal conditioning.


