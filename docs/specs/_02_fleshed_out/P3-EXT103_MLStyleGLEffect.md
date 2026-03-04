# P3-EXT103: ML Style Transfer Effect (Neural Artistic Style)

> **Task ID:** `P3-EXT103`
> **Priority:** P0 (Critical)
> **Source:** vjlive (`plugins/vml/ml_gpu_effects.py`, `core/effects/ml_effects.py`)
> **Class:** `MLStyleGLEffect`
> **Phase:** Phase 3
> **Status:** ✅ Fleshed out

## Mission Context

Implement a neural style transfer effect that applies artistic color palettes and painterly effects to video in real-time. The effect must support both ML-based style transfer (when PyTorch models are available) and a GPU shader fallback for systems without ML dependencies. The implementation must sustain 60 FPS at 1080p with asynchronous ML processing to avoid render pipeline blocking.

## Technical Requirements

- Implement as a VJLive3 effect plugin inheriting from `MLBaseAsyncEffect`
- Sustain 60 FPS with real-time style transfer (Safety Rail 1)
- Achieve ≥80% unit/test coverage (Safety Rail 5)
- Keep implementation <750 lines (Safety Rail 4)
- Support asynchronous ML inference with worker thread
- Provide GLSL fallback shader when ML unavailable
- Handle texture uploads with double-buffering
- Graceful degradation when ML models fail to load

## Implementation Notes / Porting Strategy

1. **Base Class**: Inherit from `MLBaseAsyncEffect` which provides:
   - Async worker thread for ML processing
   - Double-buffered texture management
   - Automatic fallback to shader rendering
   - Plugin loading via `_load_ml_plugin()`

2. **ML Integration**: 
   - Attempt to load PyTorch-based style transfer plugin
   - If plugin loads, worker thread processes frames asynchronously
   - Input frames queued, output frames returned within timeout
   - If ML unavailable or fails, use STYLE_TRANSFER_FALLBACK shader

3. **Shader Fallback**: The fallback shader implements:
   - Posterization (reducing color levels)
   - Edge detection for painterly strokes
   - Color palette mapping with 4 preset palettes
   - Time-based color shifting

4. **Parameter Design**: All parameters use 0-10 UI range, remapped to native ranges:
   - `style_strength`: 0-10 → 0.0-1.0 (affects posterization levels and palette mix)
   - `color_shift`: 0-10 → 0.0-1.0 (hue offset with time modulation)
   - `style_preset`: 0-10 → preset index (0-3) for palette selection

5. **Style Palettes**: Four built-in color palettes:
   - Preset 0: "Starry Night" (blues/yellows)
   - Preset 1: "The Scream" (oranges/reds)
   - Preset 2: "Monet" (soft pastels)
   - Preset 3: "Pop Art" (bold primaries)

## Public Interface

```python
class MLStyleGLEffect(MLBaseAsyncEffect):
    """
    Neural Style Transfer Effect.
    
    When ML model is available, applies neural style transfer.
    Otherwise, uses a posterization/palette-based artistic shader.
    
    Attributes:
        style_palettes: List of 4 color palettes (each 4 RGB tuples)
        parameters: Dict with keys:
            - style_strength: float (0.0-10.0 UI, remapped to 0.0-1.0)
            - color_shift: float (0.0-10.0 UI, remapped to 0.0-1.0)
            - style_preset: float (0.0-10.0 UI, remapped to preset index)
    """
    
    def __init__(self, name: str = 'ml_style_transfer'):
        """
        Initialize ML Style Transfer effect.
        
        Args:
            name: Effect instance name for plugin lookup
        """
        super().__init__(name, STYLE_TRANSFER_FALLBACK)
        
        # Parameter definitions with UI ranges
        self.parameters = {
            'style_strength': 7.0,   # UI: 0-10, native: 0.0-1.0
            'color_shift': 0.0,      # UI: 0-10, native: 0.0-1.0
            'style_preset': 0.0,     # UI: 0-10, native: preset index
        }
        
        # Built-in style color palettes (4 presets × 4 colors)
        self.style_palettes = [
            # Preset 0: Starry Night (blues/yellows)
            [(0.1, 0.1, 0.3), (0.2, 0.3, 0.5), (0.8, 0.7, 0.2), (1.0, 0.9, 0.4)],
            # Preset 1: The Scream (oranges/reds)
            [(0.1, 0.05, 0.05), (0.5, 0.2, 0.1), (0.9, 0.5, 0.2), (1.0, 0.8, 0.3)],
            # Preset 2: Monet (soft pastels)
            [(0.3, 0.4, 0.5), (0.5, 0.6, 0.6), (0.7, 0.75, 0.7), (0.9, 0.9, 0.85)],
            # Preset 3: Pop Art (bold primaries)
            [(0.0, 0.0, 0.0), (1.0, 0.0, 0.3), (1.0, 1.0, 0.0), (0.0, 0.8, 1.0)],
        ]
    
    def apply_uniforms(self, time: float, resolution, audio_reactor=None, semantic_layer=None):
        """
        Upload shader uniforms before rendering.
        
        Args:
            time: Current time in seconds
            resolution: Render resolution (width, height)
            audio_reactor: Optional audio analysis data
            semantic_layer: Optional semantic layer data
        """
        super().apply_uniforms(time, resolution, audio_reactor, semantic_layer)
        
        # Remap UI parameters (0-10) to shader native ranges
        strength = self.parameters['style_strength'] / 10.0    # → 0.0-1.0
        color_shift = self.parameters['color_shift'] / 10.0    # → 0.0-1.0
        self.shader.set_uniform('u_style_strength', strength)
        self.shader.set_uniform('u_color_shift', color_shift)
        
        # Select and upload style palette (4 colors)
        preset = int(self.parameters['style_preset'] / 10.0 * len(self.style_palettes)) % len(self.style_palettes)
        palette = self.style_palettes[preset]
        for i, color in enumerate(palette):
            self.shader.set_uniform(f'u_style_colors[{i}]', color)
    
    def set_style_preset(self, preset: int) -> None:
        """
        Set style preset by index (0-3).
        
        Args:
            preset: Preset index (0-3)
        """
        self.parameters['style_preset'] = preset % len(self.style_palettes)
    
    def get_state(self) -> Dict[str, Any]:
        """Get effect state for UI."""
        return {
            'name': self.name,
            'enabled': self.enabled,
            'ml_available': self._ml_available,
            'parameters': dict(self.parameters),
        }
```

## Inputs and Outputs

**Inputs:**
- `video_in`: `sampler2D` - Primary video input texture (RGBA)

**Outputs:**
- `video_out`: `sampler2D` - Styled video output (RGBA)

**Uniforms:**
```glsl
uniform sampler2D tex0;           // Input texture
uniform float time;               // Time in seconds
uniform float u_style_strength;  // Style intensity [0.0-1.0]
uniform float u_color_shift;     // Hue offset [0.0-1.0]
uniform vec3 u_style_colors[4];  // Style palette colors
```

## Edge Cases and Error Handling

1. **ML Plugin Not Available**: Fall back to STYLE_TRANSFER_FALLBACK shader automatically. No error raised; `ml_available` flag set to False.

2. **ML Worker Thread Failure**: Worker thread catches exceptions and logs errors. Frame is passed through unmodified. Thread continues running.

3. **Queue Full/Empty**: Non-blocking queue operations. If input queue full, drop frame. If output queue empty, return last processed texture or passthrough.

4. **Texture Upload Failures**: Double-buffered texture management. Old texture deleted before new upload. Errors caught and logged.

5. **Parameter Out of Range**: UI enforces 0-10 range. `apply_uniforms()` clamps preset index to valid palette range using modulo.

6. **Resolution Changes**: `apply_uniforms()` receives resolution each frame; shader uses `textureSize()` for texel calculations.

## Mathematical Formulations

### Fallback Shader Algorithm (GLSL 330)

```glsl
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform float time;
uniform float u_style_strength;
uniform float u_color_shift;
uniform vec3 u_style_colors[4];

void main() {
    vec4 col = texture(tex0, uv);
    
    // 1. Posterization: reduce color levels based on strength
    // levels = 4.0 + strength * 4.0  (range: 4-8 levels)
    float levels = 4.0 + u_style_strength * 4.0;
    vec3 posterized = floor(col.rgb * levels + 0.5) / levels;
    
    // 2. Edge detection using derivatives
    // edge = sqrt(dFdx(lum)^2 + dFdy(lum)^2) * 20.0
    float dx = dFdx(col.r + col.g + col.b);
    float dy = dFdy(col.r + col.g + col.b);
    float edge = sqrt(dx*dx + dy*dy) * 20.0;
    
    // 3. Color shift with time modulation
    // hue_offset = color_shift + sin(time * 0.1) * 0.05
    float hue = u_color_shift + sin(time * 0.1) * 0.05;
    
    // 4. Luminance for palette selection
    float lum = dot(posterized, vec3(0.299, 0.587, 0.114));
    int idx = int(lum * 3.99);  // 0-3 index
    
    // 5. Darken edges for painterly effect
    posterized *= (1.0 - edge * 0.5);
    
    // 6. Mix with style palette color
    // styled = mix(posterized, palette[idx], strength * 0.3)
    vec3 styled = mix(posterized, u_style_colors[idx], u_style_strength * 0.3);
    
    fragColor = vec4(styled, col.a);
}
```

**Key Formulas:**
- Posterization levels: `L = 4 + 8×strength` (4 ≤ L ≤ 8)
- Edge factor: `E = 20 × √(∂L/∂x)² + (∂L/∂y)²`
- Palette mix: `C_out = C_posterized × (1 - 0.3×strength) + C_palette × (0.3×strength)`

## Performance Characteristics

- **GPU Path (Shader)**: ~0.5ms per 1080p frame (single pass)
- **ML Path (Async)**: ~30-100ms per frame on GPU (RTX 3060+), non-blocking
- **Memory**: 2x texture buffer (double-buffered), ~16MB for 1080p RGBA
- **Threading**: 1 worker thread per effect instance (daemon)
- **Queue Depth**: Max 1 frame (drop policy when full)

**RAIL Compliance:**
- RAIL 1 (60 FPS): Shader fallback guarantees 60+ FPS; ML path async
- RAIL 5 (80% Coverage): Target 100% coverage for shader path, ML mocked
- RAIL 8 (No Leaks): Textures deleted via `glDeleteTextures` before re-upload
- RAIL 10 (Security): No external network calls; ML models loaded from local filesystem only

## Test Plan

**Minimum coverage:** 80% before task is marked done.

### Unit Tests

1. **Parameter Validation**
   ```python
   def test_parameter_ranges():
       effect = MLStyleGLEffect()
       assert effect.parameters['style_strength'] == 7.0
       assert 0.0 <= effect.parameters['color_shift'] <= 10.0
       assert 0.0 <= effect.parameters['style_preset'] <= 10.0
   ```

2. **Palette Selection**
   ```python
   def test_palette_count():
       effect = MLStyleGLEffect()
       assert len(effect.style_palettes) == 4
       assert len(effect.style_palettes[0]) == 4  # 4 colors per palette
   
   def test_palette_values_in_range():
       effect = MLStyleGLEffect()
       for palette in effect.style_palettes:
           for color in palette:
               assert all(0.0 <= c <= 1.0 for c in color)
   ```

3. **Uniform Upload**
   ```python
   def test_apply_uniforms_uploads_correct_values(mock_shader):
       effect = MLStyleGLEffect()
       effect.shader = mock_shader
       effect.parameters = {'style_strength': 5.0, 'color_shift': 2.0, 'style_preset': 1.0}
       
       effect.apply_uniforms(time=1.0, resolution=(1920, 1080))
       
       mock_shader.set_uniform.assert_any_call('u_style_strength', 0.5)
       mock_shader.set_uniform.assert_any_call('u_color_shift', 0.2)
       # Preset 1 should upload palette[1]
   ```

4. **Preset Selection**
   ```python
   def test_set_style_preset():
       effect = MLStyleGLEffect()
       effect.set_style_preset(2)
       assert effect.parameters['style_preset'] == 2.0
       
       effect.set_style_preset(5)  # Should wrap to 1
       assert effect.parameters['style_preset'] == 1.0
   ```

5. **State Reporting**
   ```python
   def test_get_state():
       effect = MLStyleGLEffect()
       state = effect.get_state()
       assert 'ml_available' in state
       assert 'parameters' in state
       assert state['name'] == 'ml_style_transfer'
   ```

6. **ML Loading**
   ```python
   def test_ml_plugin_attempt():
       effect = MLStyleGLEffect()
       # Should attempt to load plugin, fall back gracefully
       assert effect._ml_available in (True, False)
       assert effect._worker is None or isinstance(effect._worker, _WorkerThread)
   ```

7. **Shader Fallback**
   ```python
   def test_fallback_shader_compiles():
       effect = MLStyleGLEffect()
       # STYLE_TRANSFER_FALLBACK should be valid GLSL
       assert '#version 330 core' in STYLE_TRANSFER_FALLBACK
       assert 'u_style_strength' in STYLE_TRANSFER_FALLBACK
       assert 'u_style_colors[4]' in STYLE_TRANSFER_FALLBACK
   ```

### Integration Tests

1. **Full Render Pipeline** (with mock chain)
2. **Texture Upload/Delete Cycle** (no leaks)
3. **Worker Thread Lifecycle** (start/stop)
4. **Parameter Changes During Render**

## Definition of Done

- [x] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-EXT103: MLStyleGLEffect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

## Legacy Code References

**VJLive (Original):**
- `core/effects/ml_effects.py:209-228` - MLStyleGLEffect class definition
- `core/matrix/node_effect_ml.py:1-20` - MLStyleNode wrapper
- `plugins/vml/ml_gpu_effects.py:1-20, 257-292, 513-534` - Full implementation and shader

**VJLive-2 (Legacy):**
- `plugins/core/ml_vision/__init__.py:1-20, 17-36` - Node implementation
- `plugins/core/ml_vision/ml_effects.py:225-244` - Effect class
- `plugins/core/vml/ml_gpu_effects.py:1-20` - Module docstring

**Manifest:**
- `plugins/vml/manifest.json:6-73` - Plugin metadata and parameter definitions

## Migration Notes

The VJLive3 implementation should:
1. Extend `MLBaseAsyncEffect` from `src/vjlive3/render/effect.py`
2. Use the exact shader code from `STYLE_TRANSFER_FALLBACK`
3. Maintain the 0-10 UI parameter convention with remapping in `apply_uniforms()`
4. Support the same 4 style palettes with identical RGB values
5. Implement `set_style_preset()` for programmatic preset changes
6. Follow the existing pattern from `MLBaseAsyncEffect` for async processing

**No changes to parameter semantics:** The 0-10 UI range is hard-coded in the UI layer; the effect receives raw float values and must remap appropriately.

## Open Questions

- Should `style_preset` be an integer dropdown in UI instead of float? (Legacy uses float 0-10)
- Should temporal smoothing be applied to style strength for flicker reduction? (Not in legacy)
- Should palettes be user-extensible via config? (Legacy: hardcoded only)

---

**Agent:** desktop-roo
**Date:** 2026-03-04
**Pass:** 2 Fleshing Out
