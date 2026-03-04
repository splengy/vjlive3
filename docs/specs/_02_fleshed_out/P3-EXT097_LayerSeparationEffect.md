# P3-EXT097_LayerSeparationEffect.md

## Task: P3-EXT097 — LayerSeparationEffect

## Detailed Behavior and Parameter Interactions

### Core Architecture
```python
class LayerSeparationEffect(Datamosh3DEffect):
    """Layer separation effect."""
    def __init__(self, name: str = 'layer_separation'):
        super().__init__(name)
        self.parameters['mode'] = 1
```

`LayerSeparationEffect` is a convenience subclass of [`Datamosh3DEffect`](plugins/vdatamosh/datamosh_3d.py:161) that fixes the operation mode to `1` (Layer Separation). It inherits all parameters, shader code, and functionality from the parent class, but provides a simplified interface for users who only need layer separation effects.

### Parent Class: Datamosh3DEffect
```python
class Datamosh3DEffect(Effect):
    """Depth-aware 3D Datamosh effect with DUAL VIDEO INPUT."""
    
    # 4 modes: 0=displacement, 1=layers, 2=echo, 3=shatter
    PRESETS = {
        "subtle_displacement": {...},
        "layer_rip": {...},
        "ghost_echo": {...},
        "glass_shatter": {...},
        "depth_chaos": {...},
    }
    
    def __init__(self, name: str = 'datamosh_3d'):
        self.parameters = {
            'intensity': 8.0,   # 0-10 → 0-1
            'scale': 5.0,       # 0-10 → 0-2
            'speed': 5.0,       # 0-10 → 0-3
            'threshold': 5.0,   # 0-10 → 0-1 (depth threshold)
            'mix': 10.0,        # 0-10 → 0-1
            'mode': 0.0,        # 0-10 → 0-3 (overridden by subclasses)
            'fgMix': 3.0,       # 0-10 → 0-1 (foreground mix)
            'bgMix': 10.0,      # 0-10 → 0-1 (background mix)
            'glitchAmount': 5.0, # 0-10 → 0-1
            'blockSize': 5.0,   # 0-10 → 2-64
        }
```

### Layer Separation Shader Logic (Mode 1)
```glsl
} else if (u_mode == 1) {
    // Layer Separation — depth-based offset + A's motion
    float layerOff = (depth - 0.5) * u_scale * u_intensity;
    float wave = sin(time * u_speed + uv.x * 20.0);
    offset = vec2(
        layerOff * wave + motionDiff.r * 0.5,
        layerOff * cos(time * u_speed * 0.7) + motionDiff.g * 0.5
    );
    offset *= layerMix;
}
```

**Algorithm:**
1. Compute depth-based layer offset: `layerOff = (depth - 0.5) * scale * intensity`
   - `depth` from depth texture (red channel, 0=near, 1=far)
   - `depth - 0.5` centers around zero (negative=near, positive=far)
   - Near pixels get negative offset, far pixels get positive offset
2. Generate oscillating wave: `wave = sin(time * speed + uv.x * 20.0)`
   - Creates horizontal wave pattern that animates over time
3. Combine with motion from Video A: `motionDiff.r/g`
4. Apply layer mix factor: `offset *= layerMix`
   - `layerMix = isFG * fgMix + isBG * bgMix`
   - `isFG = 1.0 - smoothstep(threshold-0.1, threshold+0.1, depth)`
   - `isBG = smoothstep(threshold-0.1, threshold+0.1, depth)`

### Depth Layer Mask
```glsl
float isFG = 1.0 - smoothstep(u_threshold - 0.1, u_threshold + 0.1, depth);
float isBG = smoothstep(u_threshold - 0.1, u_threshold + 0.1, depth);
float layerMix = isFG * u_foreground_mix + isBG * u_background_mix;
```

- **`threshold`** (0-10 → 0-1): Depth value separating foreground from background
- **`fgMix`** (0-10 → 0-1): Effect intensity on foreground (depth < threshold)
- **`bgMix`** (0-10 → 0-1): Effect intensity on background (depth > threshold)
- **Smoothstep**: 0.1-wide transition band prevents hard edges

### Dual Video Input Architecture
```glsl
uniform sampler2D tex0;      // Video A — motion source
uniform sampler2D tex1;      // Video B — pixel source (gets datamoshed)
uniform sampler2D texPrev;   // Previous frame (for motion estimation)
uniform sampler2D depth_tex; // Depth map (red channel)

// Detect if Video B is connected
vec4 testB = texture(tex1, vec2(0.5));
bool hasDual = (testB.r + testB.g + testB.b) > 0.01;
```

- **Single video mode**: If Video B is not connected (all black), effect operates on Video A only
- **Dual video mode**: Video A provides motion vectors, Video B provides pixel data
- **Fallback**: `hasDual ? texture(tex1, ...) : texture(tex0, ...)`

### Parameter Remapping
```python
def _map_param(self, name, out_min, out_max):
    val = self.parameters.get(name, 5.0)
    return out_min + (val / 10.0) * (out_max - out_min)

# Examples:
intensity = _map_param('intensity', 0.0, 1.0)      # 0-10 → 0-1
scale = _map_param('scale', 0.0, 2.0)              # 0-10 → 0-2
speed = _map_param('speed', 0.0, 3.0)              # 0-10 → 0-3
threshold = _map_param('threshold', 0.0, 1.0)      # 0-10 → 0-1
mix = _map_param('mix', 0.0, 1.0)                  # 0-10 → 0-1
mode = int(_map_param('mode', 0, 3))               # 0-10 → 0,1,2,3
fgMix = _map_param('fgMix', 0.0, 1.0)              # 0-10 → 0-1
bgMix = _map_param('bgMix', 0.0, 1.0)              # 0-10 → 0-1
glitch = _map_param('glitchAmount', 0.0, 1.0)      # 0-10 → 0-1
blockSize = _map_param('blockSize', 2.0, 64.0)     # 0-10 → 2-64
```

### Audio Reactivity
```python
self.audio_mappings = {
    'intensity': 'bass',      # Bass boosts displacement intensity
    'glitchAmount': 'high',   # High frequencies increase glitch
    'speed': 'energy',        # Overall energy increases animation speed
}
```

```python
if audio_reactor is not None:
    bass = audio_reactor.get_band('bass', 0.0)
    high = audio_reactor.get_band('high', 0.0)
    energy = audio_reactor.get_energy(0.5)
    
    intensity = intensity * (1.0 + bass * 0.5)
    glitch = glitch * (1.0 + high * 0.3)
    speed = speed * (0.5 + energy)
```

## Public Interface

### Constructor
- **`LayerSeparationEffect(name: str = 'layer_separation')`**: Creates effect with mode fixed to 1

### Inherited Methods (from Datamosh3DEffect)
- **`set_mode(mode: str)`**: Set operation mode (overridden to always return 1 for this subclass)
- **`set_layer_balance(foreground: float, background: float)`**: Set fg/bg mix directly
- **`get_state() -> Dict`**: Get effect state for UI/serialization
- **`apply_uniforms(time, resolution, audio_reactor, semantic_layer)`**: Bind shader uniforms
- **`set_parameter(name, value)`**: Set parameter value (0-10)
- **`get_parameter(name) -> float`**: Get parameter value

### Presets (Inherited)
Although LayerSeparationEffect fixes mode=1, presets are still available but may need adjustment:
- `subtle_displacement` (mode 0) — not suitable
- `layer_rip` (mode 3) — not suitable
- `ghost_echo` (mode 2) — not suitable
- `glass_shatter` (mode 3) — not suitable
- `depth_chaos` (mode 10 → 3) — not suitable

**Note**: Presets are designed for the parent class's multi-mode architecture. For LayerSeparationEffect, users should manually set parameters rather than use presets.

## Inputs and Outputs

### Input Sources
- **Texture 0 (`tex0`)**: Video A — motion source for displacement vectors
- **Texture 1 (`tex1`)**: Video B — pixel source to be datamoshed (optional)
- **Texture 2 (`texPrev`)**: Previous frame of Video A for motion estimation
- **Texture 3 (`depth_tex`)**: Depth map (red channel, 0=near, 1=far)
- **Parameters**: 10 parameters controlling effect behavior

### Output Destinations
- **Fragment color**: Datamoshed output with layer-based separation
- **State dictionary**: Serialized effect configuration

## Edge Cases and Error Handling

### Missing Depth Texture
- **Behavior**: Effect may produce undefined results if depth texture is not bound
- **Expected**: Depth should be provided via `depth_tex` bound to texture unit 3
- **Fallback**: No fallback; depth is required

### Single Video Fallback
- **Detection**: Samples center pixel of `tex1`; if sum < 0.01, treats as disconnected
- **Fallback**: Uses `tex0` for both motion and pixel source
- **Implication**: Self-moshing mode (Video A datamoshes itself)

### Parameter Clamping
- **UI range**: All parameters accept 0-10 from UI sliders
- **Internal ranges**: Remapped to shader-specific ranges
- **Out of range**: Not clamped in `_map_param`; assumes UI enforces 0-10
- **Recommendation**: Add clamping: `val = max(0.0, min(10.0, val))`

### Mode Parameter
- **Fixed value**: LayerSeparationEffect sets `mode = 1` in constructor
- **User override**: `set_mode()` method exists but should not change mode for this subclass
- **Safety**: Mode is cast to int and modulo 3 for safety: `int(self._map_param('mode', 0, 3))`

### Audio Reactor Failures
- **Exception handling**: `try/except` around audio queries; falls back to no audio modulation
- **Default values**: If audio fails, uses parameter values without modulation
- **Silent failure**: No error logged; just skips audio

### Memory Management
- **Texture binding**: Depth texture bound to unit 3, Video B to unit 1
- **No leaks**: Parent class handles texture cleanup via OpenGL context
- **Potential issue**: No explicit `glDeleteTextures` for dynamically created textures (if any)

## Mathematical Formulations

### Layer Separation Offset
```
layerOff = (depth - 0.5) * scale * intensity
wave = sin(time * speed + uv.x * 20.0)
offset.x = layerOff * wave + motionDiff.r * 0.5
offset.y = layerOff * cos(time * speed * 0.7) + motionDiff.g * 0.5
offset *= layerMix
```

**Variables:**
- `depth` ∈ [0, 1] from depth texture
- `scale` ∈ [0, 2] from `scale` parameter
- `intensity` ∈ [0, 1] from `intensity` parameter
- `speed` ∈ [0, 3] from `speed` parameter
- `motionDiff` = `texture(tex0, uv).rgb - texture(texPrev, uv).rgb`
- `layerMix` = `isFG * fgMix + isBG * bgMix`

### Depth Layer Masks
```
isFG = 1.0 - smoothstep(threshold - 0.1, threshold + 0.1, depth)
isBG = smoothstep(threshold - 0.1, threshold + 0.1, depth)
```

- `threshold` ∈ [0, 1] from `threshold` parameter
- Smoothstep creates 0.1-wide transition band
- `isFG` = 1 for depth < threshold-0.1, 0 for depth > threshold+0.1
- `isBG` = 0 for depth < threshold-0.1, 1 for depth > threshold+0.1

### Layer Mix Factor
```
layerMix = isFG * fgMix + isBG * bgMix
```

- `fgMix` ∈ [0, 1] from `fgMix` parameter
- `bgMix` ∈ [0, 1] from `bgMix` parameter
- Final mix is weighted average based on depth layer

### Audio Modulation
```
intensity_mod = intensity * (1.0 + bass * 0.5)
glitch_mod = glitch * (1.0 + high * 0.3)
speed_mod = speed * (0.5 + energy)
```

- `bass` ∈ [0, 1] from audio reactor
- `high` ∈ [0, 1] from audio reactor
- `energy` ∈ [0, 1] from audio reactor
- Multiplicative boosts with different gains

### Parameter Remapping
```
remapped = out_min + (param_value / 10.0) * (out_max - out_min)
```

All parameters use linear mapping from UI range [0, 10] to shader-specific range.

## Performance Characteristics

### Computational Complexity
- **Per-pixel operations**: ~50-100 FLOPs depending on mode
- **Texture fetches**: 4-5 per pixel (tex0, tex1 optional, texPrev, depth_tex, possibly LUT)
- **Trigonometric functions**: 1-2 sin/cos calls per pixel (wave calculation)
- **Smoothstep**: 2 calls per pixel for layer masks

### Memory Requirements
- **Texture memory**: 4 texture units (tex0, tex1, texPrev, depth_tex)
- **Parameter storage**: 10 floats + audio mappings
- **Shader uniforms**: ~15 uniform variables

### Bottlenecks
- **Texture bandwidth**: 4-5 texture fetches per pixel is main bottleneck
- **Memory latency**: Depth texture and previous frame texture cause cache pressure
- **Motion estimation**: Frame difference calculation requires 2 texture reads

### Real-time Suitability
- **720p**: ~1.5M pixels × 80 FLOPs = ~120 MFLOPs (real-time on mid-range GPU)
- **1080p**: ~2M pixels × 80 FLOPs = ~160 MFLOPs (real-time on modern GPU)
- **4K**: ~8M pixels × 80 FLOPs = ~640 MFLOPs (requires high-end GPU)

### Optimization Opportunities
- **Reduce texture fetches**: Cache previous frame in framebuffer
- **Simplify wave function**: Replace sin/cos with cheaper approximation
- **Layer mask optimization**: Compute once per pixel, reuse
- **Audio modulation**: Pre-scale parameters on CPU instead of per-pixel

## Test Plan

### Unit Tests (85% coverage target)
1. **Constructor Tests**
   - Test `LayerSeparationEffect()` sets mode=1
   - Test default parameters inherited correctly
   - Test name default to 'layer_separation'

2. **Parameter Tests**
   - Test all 10 parameters accept 0-10 values
   - Test `_map_param()` for each parameter
   - Test parameter edge cases (0, 5, 10)
   - Test invalid parameter names return default

3. **Mode Tests**
   - Test `get_state()['mode']` returns 'layers'
   - Test `set_mode()` does not change mode for this subclass
   - Test mode parameter is ignored in `apply_uniforms`

4. **Layer Balance Tests**
   - Test `set_layer_balance(foreground, background)`
   - Test clamping to 0-10 range
   - Test fgMix/bgMix parameters update correctly

5. **Audio Reactivity Tests**
   - Test audio modulation with mock audio reactor
   - Test bass → intensity boost
   - Test high → glitch boost
   - Test energy → speed boost
   - Test audio failure falls back gracefully

### Integration Tests
1. **Dual Video Pipeline**
   - Test with both videos connected
   - Test with only Video A (self-moshing)
   - Test video switching behavior

2. **Depth Integration**
   - Test depth texture binding
   - Test depth threshold effects
   - Test foreground/background separation

3. **Motion Estimation**
   - Test motionDiff calculation
   - Test previous frame usage
   - Test motion-driven displacement

4. **Layer Separation**
   - Test threshold varies layer boundary
   - Test fgMix/bgMix vary effect strength per layer
   - Test smooth transition band

5. **Shader Compilation**
   - Test shader compiles with all uniforms
   - Test uniform binding
   - Test texture unit assignments

### Visual Regression Tests
1. **Layer Separation Visuals**
   - Capture output with various thresholds
   - Verify foreground/background separation
   - Test wave animation over time

2. **Parameter Sweep**
   - Test intensity 0→10
   - Test scale 0→10
   - Test speed 0→10
   - Test fgMix/bgMix combinations

3. **Dual vs Single Video**
   - Compare output with and without Video B
   - Verify fallback behavior

### Performance Tests
1. **Resolution Scaling**
   - Test 720p real-time (>30 FPS)
   - Test 1080p real-time (>30 FPS)
   - Test 4K performance

2. **Memory Usage**
   - Test texture memory footprint
   - Test no memory leaks over long runs

3. **Audio Reactivity**
   - Test audio modulation performance
   - Test audio dropout handling

### Edge Case Tests
1. **Extreme Parameters**
   - Test intensity=0 (no effect)
   - Test intensity=10 (maximum)
   - Test scale=0 (no displacement)
   - Test threshold=0 (all foreground)
   - Test threshold=10 (all background)
   - Test fgMix=0, bgMix=0 (no effect)
   - Test fgMix=10, bgMix=10 (maximum)

2. **Depth Edge Cases**
   - Test depth=0 (nearest)
   - Test depth=1 (farthest)
   - Test depth=0.5 (exact threshold)
   - Test uniform depth (no layers)

3. **Motion Edge Cases**
   - Test zero motion (static scene)
   - Test high motion (rapid changes)
   - Test previous frame missing (first frame)

4. **Video Edge Cases**
   - Test black Video B (should fallback)
   - Test white Video B (edge case)
   - Test uninitialized textures

## Definition of Done

### Technical Requirements
- [ ] LayerSeparationEffect class implemented with mode=1 fixed
- [ ] All inherited parameters work correctly
- [ ] Layer separation algorithm produces correct visual output
- [ ] Depth threshold separates layers properly
- [ ] Foreground/background mix controls work
- [ ] Dual video input architecture functional
- [ ] Single video fallback works
- [ ] Audio reactivity modulates parameters correctly
- [ ] Shader compiles and runs without errors
- [ ] Texture binding correct (depth to unit 3, Video B to unit 1)
- [ ] 85% unit test coverage achieved
- [ ] Integration tests pass
- [ ] Visual regression tests pass
- [ ] Performance meets real-time requirements

### Documentation Requirements
- [ ] Complete technical specification with all sections filled
- [ ] Mathematical formulations for layer separation algorithm
- [ ] Parameter remapping table documented
- [ ] Dual video architecture explained
- [ ] Performance analysis with complexity calculations
- [ ] Test plan with comprehensive coverage strategy
- [ ] Edge case documentation with error handling
- [ ] Public interface documentation

### Quality Requirements
- [ ] Code follows project style guidelines
- [ ] All tests pass and maintain 85% coverage
- [ ] No regressions in existing functionality
- [ ] Documentation is accurate and complete
- [ ] Performance meets real-time requirements
- [ ] Memory usage is efficient

---

*Last Updated: 2026-03-03*  
*Spec Author: desktop-roo*  
*Task ID: P3-EXT097*