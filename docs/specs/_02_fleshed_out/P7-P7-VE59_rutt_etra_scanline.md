# P7-VE59: Rutt-Etra Scanline Effect

> **Task ID:** `P7-VE59`
> **Priority:** P0 (Critical)
> **Source:** vjlive (`plugins/vcore/rutt_etra_scanline.py`)
> **Class:** `RuttEtraScanlineEffect`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
The Rutt-Etra Scanline is a classic analog video synthesis technique emulating
oscilloscope vector graphics and CRT raster effects. It remaps scanlines based on
audio or procedural input, creating stuttering, ghosting, and prismatic
distortions. This iconic VJ effect must be faithfully ported.

## Technical Requirements
- Manifest-registered `Effect` subclass with feedback capability.
- Parameters: `scanline_shift`, `scanline_width`, `feedbackamt`, `jitter`,
  `color_shift`, `opacity`.
- GPU scanline remap shader; CPU fallback via NumPy row/column shifts.
- Maintain 60 FPS at 1080p; explicit bounds on jitter to prevent aliasing.
- ≥80 % test coverage; validate feedback decay and edge handling.
- Keep spec <750 lines.

## Public Interface
```python
class RuttEtraScanlineEffect(Effect):
    """Analog-style scanline distortion with feedback emulation."""

    def __init__(self, width=1920, height=1080, use_gpu=True):
        super().__init__("RuttEtraScanline",
                         vertex_shader=SCANLINE_VERT,
                         fragment_shader=SCANLINE_FRAG)
        self.effect_category = "distortion"
        self.effect_tags = ["analog", "scanline", "feedback", "retro"]
        self.features = ["FEEDBACK", "CRT_EMULATION"]
        self.parameters = {
            'scanline_shift': 5.0,
            'scanline_width': 5.0,
            'feedbackamt': 5.0,
            'jitter': 3.0,
            'color_shift': 5.0,
            'opacity': 10.0
        }
        self._parameter_ranges = {
            'scanline_shift': (0.0, 10.0),
            'scanline_width': (0.1, 10.0),
            'feedbackamt': (0.0, 10.0),
            'jitter': (0.0, 10.0),
            'color_shift': (0.0, 10.0),
            'opacity': (0.0, 10.0)
        }
        self._param_desc = {
            'scanline_shift': 'Amount of scanline row displacement.',
            'scanline_width': 'Width/height of scanline bands.',
            'feedbackamt': 'Feedback layer strength.',
            'jitter': 'Random frame jitter.',
            'color_shift': 'Chromatic aberration magnitude.',
            'opacity': 'Blend with source.'
        }
        self._state = {'feedback_tex': None}
        self.use_gpu = use_gpu

    def render(self, tex_in, extra_textures=None, chain=None):
        # Apply scanline remap and feedback ping-pong
        pass

    def apply_uniforms(self, time, resolution, audio=None, semantic=None):
        # Remap parameters and manage feedback state
        pass
```

### Parameter Remaps
- `scanline_shift` → Ss = map_linear(x, 0, 10, 0, 20)
- `scanline_width` → Sw = map_linear(x, 0.1, 10, 1, 50)
- `feedbackamt` → F = map_linear(x, 0, 10, 0, 1)
- `jitter` → J = map_linear(x, 0, 10, 0, 0.05)
- `color_shift` → C = map_linear(x, 0, 10, 0, 0.02)
- `opacity` → α = x / 10

## Shader Uniforms
```glsl
uniform float scanline_shift;
uniform float scanline_width;
uniform float feedbackamt;
uniform float jitter;
uniform float chroma_shift;
uniform sampler2D feedback_tex;
```

## Effect Math
```glsl
vec2 uv = fragCoord / resolution;
// Apply scanline remap
float scanline_idx = mod(uv.y * scanline_width, 1.0);
float shift_amount = sin(scanline_idx * 3.14159) * scanline_shift * 0.01;
uv.x += shift_amount;
// Apply jitter
uv += vec2(hash(uv * sin(time)) - 0.5) * jitter;
// Sample with chroma shift
vec3 col_r = texture(tex_in, uv + vec2(chroma_shift, 0)).r;
vec3 col_g = texture(tex_in, uv).g;
vec3 col_b = texture(tex_in, uv - vec2(chroma_shift, 0)).b;
vec3 col = vec3(col_r, col_g, col_b);
// Add feedback
vec3 fb = texture(feedback_tex, uv).rgb * feedbackamt;
return vec4(col + fb, 1.0);
```

## CPU Fallback
```python
import numpy as np

def rutt_etra_cpu(frame, params, feedback_buf):
    h, w = frame.shape[:2]
    shift, width, fb_amt, jitter, chroma, opacity = params
    
    # Scanline shift per row
    shifted = np.zeros_like(frame)
    for y in range(h):
        scanline_val = (y % int(width)) / max(1, int(width))
        shift_px = int(np.sin(scanline_val * np.pi) * shift)
        shifted[y] = np.roll(frame[y], shift_px, axis=0)
    
    # Apply jitter
    jitter_x = np.random.randint(-int(jitter*w), int(jitter*w))
    shifted = np.roll(shifted, jitter_x, axis=1)
    
    # Feedback blend
    if feedback_buf is not None:
        shifted = shifted * (1 - fb_amt) + feedback_buf * fb_amt
    
    return np.clip(shifted, 0, 255).astype(np.uint8)
```

## Presets
- `Classic CRT`: scanline_shift=3, scanline_width=10
- `Stuttering Feedback`: feedbackamt=7, jitter=5
- `Chromatic Glitch`: color_shift=8, jitter=4
- `Gentle Flicker`: jitter=2, scanline_shift=1

## Edge Cases
- Large scanline_width wraps correctly (use modulo).
- Jitter clamped to prevent excessive displacement.
- Missing feedback texture: initialize as black.

## Test Plan
- `test_scanline_periodicity`
- `test_feedback_decay`
- `test_chroma_separation`
- `test_jitter_bounds`
- `test_cpu_gpu_agreement`

## Verification Checklist
- [ ] Scanlines move and shift correctly
- [ ] Feedback layer decays smoothly
- [ ] Chromatic aberration visible and separable

---

**Note:** Stateful; feedback texture must be reset between sequences.


