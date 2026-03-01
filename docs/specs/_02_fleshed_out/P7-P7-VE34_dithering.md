````markdown
# P7-VE34: Dithering Effect (Ordered & Noise)

> **Task ID:** `P7-VE34`
> **Priority:** P0 (Critical)
> **Source:** vjlive (`plugins/vcore/dithering.py`)
> **Class:** `DitheringEffect`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
Dithering is used to reduce color banding by introducing controlled noise or
patterned quantization. `DitheringEffect` offers ordered (Bayer matrix) and
noise-based modes with adjustable strength and grayscale/color options. This
spec documents the matrices, strength remaps, GPU/CPU algorithms, and tests
ensuring parity with vjlive.

## Technical Requirements
- Implement as plugin with two modes: ordered (Bayer) and random noise
- Adjustable strength (0–1) and mode selector
- Maintain 60 FPS at 1080p (Safety Rail 1)
- ≥80 % unit test coverage (Safety Rail 5)
- <750 lines spec (Safety Rail 4)
- Fallback to pass-through when strength=0 (Safety Rail 7)

## Implementation Notes
1. For ordered dithering use 4×4 Bayer matrix normalized to [0,1].
2. For noise dithering sample uniform noise per pixel.
3. Add dithering value multiplied by strength to each channel before quantization.
4. CPU fallback generates equivalent values using NumPy.

## Public Interface
```python
class DitheringEffect(Effect):
    """
    Dithering Effect: Reduce banding via noise or pattern.
    """
    def __init__(self, width:int=1920, height:int=1080,
                 use_gpu:bool=True):
        super().__init__("Dithering", DITHER_VERTEX_SHADER,
                         DITHER_FRAGMENT_SHADER)
        self.effect_category = "texture"
        self.effect_tags = ["dither","noise","bayer"]
        self.features = ["DITHER"]
        self.usage_tags = ["BANDREDUCE","RETRO"]

        self.use_gpu = use_gpu
        self._parameter_ranges = {
            'mode':(0.0,10.0),
            'strength':(0.0,10.0),
            'grayscale':(0.0,10.0),
            'opacity':(0.0,10.0)
        }
        self.parameters={'mode':0.0,'strength':5.0,'grayscale':0.0,'opacity':10.0}
        self._parameter_descriptions={
            'mode':'0=ordered(bayer),10=noise',
            'strength':'0=none,10=max',
            'grayscale':'0=color,10=grayscale',
            'opacity':'effect opacity'
        }
        self._sweet_spots={'strength':[4,5,6]}

    def render(self, tex_in:int=None, extra_textures:list=None, chain=None)->int:
        # sample color
        # compute dithering value via mode/position
        # add to color channels, clamp
        # convert to gray if necessary
        # blend with original
        pass

    def bayer_value(self, uv:tuple)->float:
        # compute 4x4 Bayer matrix index from pixel coords
        pass

    def apply_uniforms(self, time:float, resolution:tuple,
                      audio_reactor=None, semantic_layer=None):
        # map strength/grayscale/mode
        pass
```

### Parameter Remaps
- `mode`: <5 ordered, ≥5 noise
- `strength` → `s = map_linear(x,0,10,0,1)`
- `grayscale` → `g = x/10` (mix factor with luminance)
- `opacity` → α = x/10

## Shader Uniforms
- `uniform int mode;`
- `uniform float strength;`
- `uniform float grayscale;`
- `uniform float opacity;`
- `uniform vec2 resolution;`
- `uniform sampler2D tex_in;`

## Effect Math

```
float dither;
if(mode<5){
    // ordered 4x4 Bayer matrix
dither = bayer_value(floor(gl_FragCoord.xy)) - 0.5;
} else {
    dither = fract(sin(dot(gl_FragCoord.xy,vec2(12.9898,78.233)))*43758.5453) - 0.5;
}
dither *= strength;
vec3 c = texture(tex_in, uv).rgb + vec3(dither);
c = clamp(c,0,1);
if(grayscale>0.5){
    float l = dot(c,vec3(0.2126,0.7152,0.0722));
    c = mix(c, vec3(l), grayscale);
}
vec3 orig = texture(tex_in, uv).rgb;
return mix(orig, c, opacity);
```

Bayer matrix function:
```
float bayer_value(vec2 pos){
    int x=int(pos.x)%4, y=int(pos.y)%4;
    int idx = y*4 + x;
    float m[16] = float[16](
        0,8,2,10,
        12,4,14,6,
        3,11,1,9,
        15,7,13,5);
    return m[idx]/16.0;
}
```

## CPU Fallback
```python
def dithering_cpu(frame, mode, strength, grayscale, opacity):
    img = frame.astype(np.float32)/255.0
    h,w=img.shape[:2]
    # create dither map
    if mode<5:
        bayer = np.array([[0,8,2,10],[12,4,14,6],[3,11,1,9],[15,7,13,5]])/16.0-0.5
        tile = np.tile(bayer,(h//4+1,w//4+1,1))[:h,:w]
        dmap = tile
    else:
        dmap = np.random.rand(h,w)-0.5
    dmap *= strength
    c = img + dmap[:,:,None]
    c = np.clip(c,0,1)
    if grayscale>0.5:
        l = img.dot(np.array([0.2126,0.7152,0.0722]))
        c = c*(1-grayscale) + l[:,:,None]*grayscale
    return ((1-opacity)*img + opacity*c)*255
```

## Presets
- `Subtle Ordered`: mode=0,strength=2
- `Heavy Noise`: mode=10,strength=8
- `Gray Ordered`: mode=0,strength=5,grayscale=10
- `Color Noise`: mode=10,strength=5,grayscale=0

## Edge Cases
- strength=0 → passthrough
- Grayscale blend ensures correct luma calculation

## Test Plan
- `test_ordered_pattern`
- `test_noise_pattern`
- `test_strength_scale`
- `test_grayscale_mix`
- `test_cpu_gpu_parity`
- `test_60fps_performance`

## Verification
- [ ] Bayer matrix correct
- [ ] Noise reproducibility via hash
- [ ] CPU fallback matches

````
