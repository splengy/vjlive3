````markdown
# P7-VE27: RGB Shift Effect (Chromatic Displacement)

> **Task ID:** `P7-VE27`
> **Priority:** P0 (Critical)
> **Source:** vjlive (`plugins/vcore/color.py`)
> **Class:** `RGBShiftEffect`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
Provide a complete Pass 2 specification for the `RGBShiftEffect`—a chromatic
displacement effect that offsets the red, green, and blue channels separately.
It creates a “glitch” or 3D anaglyph look by shifting each channel by an
adjustable amount. Commonly used for vintage or sabotage aesthetics in VJ
performances. The spec includes exact displacement math, parameter remaps, CPU
fallback, and tests for parity with vjlive.

## Technical Requirements
- Implement as a VJLive3 effect plugin (per-channel spatial offsets)
- Sustain 60 FPS with three texture samples per pixel (Safety Rail 1)
- Achieve ≥80% unit/test coverage (Safety Rail 5)
- Keep code under 750 lines (Safety Rail 4)
- Graceful pass-through if shift is zero (Safety Rail 7)
- Provide CPU fallback using NumPy and affine transforms

## Implementation Notes / Porting Strategy
1. Accept X/Y offsets for each of R, G, B channels.
2. Sample texture three times with uv offset per channel.
3. Combine into output color.
4. Support opacity blending with original.

## Public Interface
```python
class RGBShiftEffect(Effect):
    """
    RGB Shift Effect: Chromatic channel displacement.

    Offsets the red, green, and blue channels by independent X/Y amounts to
    create a chromatic aberration or glitch look. Parameters allow negative
    shifts for creative control.
    """

    def __init__(self, width: int = 1920, height: int = 1080,
                 use_gpu: bool = True):
        super().__init__("RGB Shift", RGBSHIFT_VERTEX_SHADER,
                         RGBSHIFT_FRAGMENT_SHADER)
        
        self.effect_category = "color"
        self.effect_tags = ["rgb", "shift", "chromatic", "aberration"]
        self.features = ["RGB_SHIFT"]
        self.usage_tags = ["GLITCH", "VINTAGE", "3D"]
        
        self.use_gpu = use_gpu

        # UI sliders 0-10 map to offsets [-50,50] pixels
        self._parameter_ranges = {
            'r_x': (0.0, 10.0), 'r_y': (0.0, 10.0),
            'g_x': (0.0, 10.0), 'g_y': (0.0, 10.0),
            'b_x': (0.0, 10.0), 'b_y': (0.0, 10.0),
            'opacity': (0.0, 10.0)
        }

        self.parameters = {
            'r_x': 5.0, 'r_y': 5.0,
            'g_x': 5.0, 'g_y': 5.0,
            'b_x': 5.0, 'b_y': 5.0,
            'opacity': 10.0
        }

        self._parameter_descriptions = {
            'r_x': "Red channel horizontal shift (-50..50 px)",
            'r_y': "Red channel vertical shift (-50..50 px)",
            'g_x': "Green channel horizontal shift",
            'g_y': "Green channel vertical shift",
            'b_x': "Blue channel horizontal shift",
            'b_y': "Blue channel vertical shift",
            'opacity': "Effect opacity"
        }

        self._sweet_spots = {
            'r_x': [4.0, 5.0, 6.0],
            'b_x': [4.0, 5.0, 6.0]
        }

    def render(self, tex_in: int = None, extra_textures: list = None,
              chain = None) -> int:
        # compute uv offsets for each channel
        # sample texture with those offsets
        # pack into rgb, clamp, blend with original
        pass

    def apply_uniforms(self, time: float, resolution: tuple,
                      audio_reactor=None, semantic_layer=None):
        # convert UI slider to pixel offsets
        pass
```

### Parameters and Remaps
For each channel shift parameter (UI 0–10):
```
offset_px = map_linear(x, 0,10, -50, 50)
```
Opacity as usual `α = x/10`.

## Shader Uniforms
- `uniform vec2 r_offset;`
- `uniform vec2 g_offset;`
- `uniform vec2 b_offset;`
- `uniform float opacity;`
- `uniform vec2 resolution;`
- `uniform sampler2D tex_in;`

## Effect Math

```
vec2 uv = gl_FragCoord.xy / resolution;
vec3 rcol = texture(tex_in, uv + r_offset/resolution).rgb;
vec3 gcol = texture(tex_in, uv + g_offset/resolution).rgb;
vec3 bcol = texture(tex_in, uv + b_offset/resolution).rgb;
vec3 shifted = vec3(rcol.r, gcol.g, bcol.b);
vec3 orig = texture(tex_in, uv).rgb;
vec3 outc = mix(orig, shifted, opacity);
```

CPU fallback sketch:
```python
def rgbshift_cpu(frame, r_offset, g_offset, b_offset, opacity):
    h,w = frame.shape[:2]
    def shift(channel, offset):
        M = np.float32([[1,0,offset[0]],[0,1,offset[1]]])
        return cv2.warpAffine(channel, M, (w,h), borderMode=cv2.BORDER_REFLECT)
    r = shift(frame[:,:,0], r_offset)
    g = shift(frame[:,:,1], g_offset)
    b = shift(frame[:,:,2], b_offset)
    shifted = np.stack([r,g,b],axis=2)
    return ((1-opacity)*frame + opacity*shifted).astype(np.uint8)
```

## Presets
- `Subtle Aberration`: r_x=5,g_x=5,b_x=5 (small offset)
- `Glitch Pop`: r_x=10,g_x=0,b_x=-10 (horizontal displacement)
- `Vertical Split`: r_y=10,g_y=0,b_y=-10
- `Extreme RGB`: offsets at ±50

## Edge Cases
- All offsets zero → passthrough
- Offsets beyond frame → border reflect

## Test Plan
- `test_no_shift_passthrough`
- `test_offsets_apply_correctly`
- `test_opacity_blend`
- `test_cpu_gpu_parity`
- `test_performance_60fps`

## Verification
- [ ] Offsets convert correctly
- [ ] Border handling fine
- [ ] CPU fallback match

````
