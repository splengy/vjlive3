````markdown
# P7-VE28: Color Correct Effect (Per-Channel Adjustment)

> **Task ID:** `P7-VE28`
> **Priority:** P0 (Critical)
> **Source:** vjlive (`plugins/vcore/color.py`)
> **Class:** `ColorCorrectEffect`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
Provide a complete Pass 2 specification for the `ColorCorrectEffect`—a
detailed per-channel color grading tool offering gain, lift, and gamma controls
for red, green, and blue channels independently. Used for fine-tuning white
balance, color casts, and creative looks in live shows. The effect must expose
10+ parameters and maintain precise control while remaining efficient. This
spec documents all math, parameter remaps, CPU fallback, and tests for parity
with vjlive.

## Technical Requirements
- Implement as a VJLive3 plugin (per-channel lift/gain/gamma)
- Sustain 60 FPS with additional arithmetic per channel (Safety Rail 1)
- ≥80% test coverage (Safety Rail 5)
- Total spec <750 lines (Safety Rail 4)
- Graceful bypass when all adjustments neutral (Safety Rail 7)
- Provide CPU fallback using NumPy per-channel operations

## Implementation Notes / Porting Strategy
1. Expose UI sliders for lift/gain/gamma on R, G, B channels.
2. Map sliders to internal adjustments: lift [-0.5,0.5], gain [0.5,2], gamma [0.5,2].
3. Apply color correction formula: `out = pow((in + lift) * gain, gamma)` per channel.
4. Blend with original according to opacity.

## Public Interface
```python
class ColorCorrectEffect(Effect):
    """
    Color Correct Effect: Per-channel lift/gain/gamma.
    """
    def __init__(self, width: int = 1920, height: int = 1080,
                 use_gpu: bool = True):
        super().__init__("Color Correct", COLORCORRECT_VERTEX_SHADER,
                         COLORCORRECT_FRAGMENT_SHADER)
        
        self.effect_category = "color_grading"
        self.effect_tags = ["color_correct", "lift", "gain", "gamma"]
        self.features = ["COLOR_CORRECT"]
        self.usage_tags = ["GRADING", "BALANCE"]
        
        self.use_gpu = use_gpu

        # UI sliders for each of R/G/B lift/gain/gamma plus opacity
        self._parameter_ranges = {}
        names = ['r_lift','r_gain','r_gamma',
                 'g_lift','g_gain','g_gamma',
                 'b_lift','b_gain','b_gamma',
                 'opacity']
        for n in names:
            self._parameter_ranges[n] = (0.0, 10.0)

        self.parameters = {n:5.0 for n in names}

        self._parameter_descriptions = {
            'r_lift': "Red channel lift (-0.5..0.5)",
            'r_gain': "Red channel gain (0.5..2)",
            'r_gamma': "Red channel gamma (0.5..2)",
            'g_lift': "Green channel lift",
            'g_gain': "Green channel gain",
            'g_gamma': "Green channel gamma",
            'b_lift': "Blue channel lift",
            'b_gain': "Blue channel gain",
            'b_gamma': "Blue channel gamma",
            'opacity': "Effect opacity"
        }

        self._sweet_spots = {
            'r_gain': [4.0,5.0,6.0],
            'g_gain': [4.0,5.0,6.0],
            'b_gain': [4.0,5.0,6.0]
        }

    def render(self, tex_in: int=None, extra_textures: list=None,
              chain=None) -> int:
        # sample color
        # apply per-channel correction
        # blend with original based on opacity
        pass

    def apply_uniforms(self, time: float, resolution: tuple,
                      audio_reactor=None, semantic_layer=None):
        # compute internal lift/gain/gamma for each channel
        pass
```

### Parameter Remaps
- `*_lift` (UI 0–10) → `L = map_linear(x,0,10,-0.5,0.5)`
- `*_gain` → `G = map_linear(x,0,10,0.5,2.0)`
- `*_gamma` → `Γ = map_linear(x,0,10,0.5,2.0)`
- `opacity` → α = x/10

## Shader Uniforms
- `uniform vec3 lift;`     // per-channel lift
- `uniform vec3 gain;`     // per-channel gain
- `uniform vec3 gamma;`    // per-channel gamma
- `uniform float opacity;`
- `uniform sampler2D tex_in;`

## Effect Math

```
vec3 c = texture(tex_in, uv).rgb;
vec3 corrected;
for(int i=0;i<3;i++){
    float v = c[i] + lift[i];
    v = max(v, 0.0);
    v *= gain[i];
    corrected[i] = pow(v, 1.0 / gamma[i]);
}
vec3 outc = mix(c, corrected, opacity);
```

CPU fallback:
```python
def colorcorrect_cpu(frame, lift, gain, gamma, opacity):
    img = frame.astype(np.float32)/255.0
    out = np.empty_like(img)
    for i in range(3):
        v = img[:,:,i] + lift[i]
        v = np.clip(v,0,1)
        v *= gain[i]
        out[:,:,i] = np.power(v, 1.0/gamma[i])
    return ((1-opacity)*img + opacity*out)*255
```

## Presets
- `Neutral`: all parameters 5
- `Warm`: r_gain=6,g_gain=5,b_gain=4
- `Cool`: r_gain=4,g_gain=5,b_gain=6
- `High Lift`: r_lift=6,g_lift=6,b_lift=6

## Edge Cases
- Gains below 0.5 clamp to 0.5
- Gamma extremes prevent divide-by-zero

## Test Plan
- `test_neutral_no_change`
- `test_per_channel_lift`
- `test_per_channel_gain`
- `test_per_channel_gamma`
- `test_opacity_blend`
- `test_cpu_gpu_parity`
- `test_60fps_performance`

## Verification
- [ ] Parameters remapped correctly
- [ ] Per-channel operations occur in right order
- [ ] CPU fallback consistent

````
