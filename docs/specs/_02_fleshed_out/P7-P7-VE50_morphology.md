# P7-VE50: Morphology Effect (Erode/Dilate)

> **Task ID:** `P7-VE50`
> **Priority:** P0 (Critical)
> **Source:** vjlive (`plugins/vcore/morphology.py`)
> **Class:** `MorphologyEffect`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
Morphological operations such as erosion, dilation, opening, and closing are
fundamental in image processing for shape manipulation and noise removal. The
VJlive version provides a square/diamond kernel whose size is adjustable. We'll
port this to allow creative blurs and sharpening in the VJLive3 set.

## Technical Requirements
- Plugin registration via manifest; subclass `Effect`
- Parameters: `operation` (`erode`,`dilate`,`open`,`close`), `kernel_size`,
  `iterations`, `opacity`
- GPU implementation via separable convolution or multiple texture samples;
  CPU fallback using OpenCV’s morphology functions
- Maintain 60 FPS at 1080p for kernel sizes up to 21×21 (Safety Rail 1)
- ≥80 % test coverage (Safety Rail 5)
- Spec <750 lines (Safety Rail 4)
- Validate kernel size odd positive integer; clamp iterations; handle unknown
  operation gracefully (Safety Rail 7)

## Public Interface
```python
class MorphologyEffect(Effect):
    """Performs erosion/dilation style operations on the image."""

    def __init__(self,width=1920,height=1080,use_gpu=True):
        super().__init__("Morphology", MORPH_VERTEX_SHADER,
                         MORPH_FRAGMENT_SHADER)
        self.effect_category="geometry"
        self.effect_tags=["morphology","erode","dilate"]
        self.features=["MORPH_OPS"]
        self.usage_tags=["STYLING","PROCESSING"]
        self.use_gpu=use_gpu

        self._parameter_ranges={'operation':(0.0,10.0),
                                 'kernel_size':(0.0,10.0),
                                 'iterations':(0.0,10.0),
                                 'opacity':(0.0,10.0)}
        self.parameters={'operation':0.0,'kernel_size':3.0,
                         'iterations':1.0,'opacity':10.0}
        self._parameter_descriptions={
            'operation':'0=erode,1=dilate,2=open,3=close',
            'kernel_size':'Size of square kernel (odd,1..21)',
            'iterations':'How many times to apply',
            'opacity':'Blend with original'}
        self._sweet_spots={'kernel_size':[3,5,7],'iterations':[1,2,3]}

    def render(self,tex_in,extra_textures=None,chain=None):
        # apply morphological kernel using multiple samples
        pass

    def apply_uniforms(self,time,resolution,audio_reactor=None,
                      semantic_layer=None):
        # remap and upload operation code, kernel size, iterations, opacity
        pass
```

### Parameter Remaps
- `operation` → op = int(map_linear(x,0,10,0,3))
- `kernel_size` → k = int(map_linear(x,0,10,1,21)) | 1 (make odd)
- `iterations` → it = int(map_linear(x,0,10,1,10))
- `opacity` → α = x/10

## Shader Uniforms
- `uniform int operation;`
- `uniform int kernel_size;`
- `uniform int iterations;`
- `uniform float opacity;`
- `uniform vec2 resolution;`

Fragment shader will sample neighbors determined by `kernel_size` and combine
using min/max for erode/dilate and composed ops for open/close.

## Effect Math (GLSL sketch)
```
vec2 uv = gl_FragCoord.xy/resolution;
vec3 acc = texture(tex_in, uv).rgb;
for (int i = 0; i < iterations; ++i) {
    if (operation == 0) { // erode
        acc = min(acc, sampleNeighbors(uv, kernel_size));
    } else if (operation == 1) { // dilate
        acc = max(acc, sampleNeighbors(uv, kernel_size));
    } else if (operation == 2) { // open
        acc = max(acc, sampleNeighbors(uv, kernel_size));
        acc = min(acc, sampleNeighbors(uv, kernel_size));
    } else if (operation == 3) { // close
        acc = min(acc, sampleNeighbors(uv, kernel_size));
        acc = max(acc, sampleNeighbors(uv, kernel_size));
    }
}
vec3 orig = texture(tex_in, uv).rgb;
return mix(orig, acc, opacity);
```

`sampleNeighbors` loops offsets within kernel and picks min/max accordingly.

## CPU Fallback
```python
import cv2

def morphology_cpu(frame, operation, kernel_size, iterations, opacity):
    op_map = {'erode':cv2.MORPH_ERODE,
              'dilate':cv2.MORPH_DILATE,
              'open':cv2.MORPH_OPEN,
              'close':cv2.MORPH_CLOSE}
    ker = cv2.getStructuringElement(cv2.MORPH_RECT,(kernel_size,kernel_size))
    res = cv2.morphologyEx(frame, op_map[operation], ker, iterations=iterations)
    return ((1-opacity)*frame + opacity*res).astype(np.uint8)
```

## Presets
- `Erode1`: operation=erode, kernel_size=3, iterations=1
- `DilateBig`: operation=dilate, kernel_size=7, iterations=2
- `OpenNoise`: operation=open, kernel_size=5, iterations=1

## Edge Cases
- kernel_size even: increment to next odd
- operation code outside [0,3]: clamp
- iterations <1: set to 1

## Test Plan
- `test_operation_enum`
- `test_kernel_size_odd`
- `test_iterations`
- `test_cpu_gpu_equivalence`
- `test_performance_1080p`

## Verification Checklist
- [ ] Basic morph ops produce expected shapes on simple test images
- [ ] Open/close behave as dilate/erode combos
- [ ] CPU fallback matches within tolerance

---

**Note:** Morphology can be expensive when kernel is large—document
performance degradation and suggest using GPU path.

