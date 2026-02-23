# P3-EXT009: AudioReactiveRaymarchedScenes

**Priority:** P3-EXT (Missing Legacy Effects Parity)
**Status:** Spec Draft
**Assignee:** TBD
**Estimated Completion:** 3-4 days

---

## 📋 Task Overview

Port the legacy `AudioReactiveRaymarchedScenes` effect from VJLive-2 to VJLive3. This is a sophisticated ray-marched 3D scene renderer with three distinct visual variants (spheres, tunnels, fractals) and comprehensive audio reactivity. The effect uses signed distance functions (SDFs) to render real-time 3D geometry entirely in a fragment shader.

---

## 🎯 Core Concept

Ray marching is a rendering technique that uses distance functions to determine surface intersections without traditional polygon meshes. This effect implements:

- **Three scene types**: Spheres array, infinite tunnel, Mandelbulb fractal
- **Audio modulation**: Geometry parameters (radius, position) and color respond to audio frequency bands
- **Performance tuning**: "Ultra boost" uniforms allow trading quality for speed
- **HSV color system**: Audio-reactive hue/saturation/value shifts

The legacy implementation is 298 lines with a 278-line fragment shader containing full SDF rendering pipeline.

---

## 1. File Structure

```
src/vjlive3/plugins/audio_reactive_raymarched_scenes.py
tests/plugins/test_audio_reactive_raymarched_scenes.py
```

---

## 2. Class Hierarchy

```python
from vjlive3.plugins.base import Effect

class AudioReactiveRaymarchedScenes(Effect):
    """Ray-marched 3D scenes with audio modulation."""

    def __init__(self):
        # Initialize parameters
        pass

    def _get_vertex_shader(self) -> str:
        """Returns fullscreen quad vertex shader."""
        pass

    def _get_fragment_shader(self) -> str:
        """Returns ray-marching fragment shader with SDFs."""
        pass

    def apply_uniforms(self, time: float, resolution, audio_reactor=None, semantic_layer=None):
        """Apply all uniforms including audio-reactive parameters."""
        pass
```

---

## 3. Parameters (0.0-10.0 or 0.0-1.0)

| Parameter Name | Type | Range | Default | Description |
|----------------|------|-------|---------|-------------|
| `scene_type` | int | 0-2 | 0 | Scene variant: 0=spheres, 1=tunnel, 2=fractal |
| `base_radius` | float | 0.0-10.0 | 1.5 | Base radius for spheres/tunnel |
| `position_offset` | vec3 | (-10.0, 10.0) | (0,0,0) | Camera/object position offset |
| `color_hue` | float | 0.0-1.0 | 0.5 | Base hue (HSV) |
| `color_saturation` | float | 0.0-1.0 | 0.8 | Base saturation |
| `color_value` | float | 0.0-1.0 | 1.0 | Base brightness |
| `audio_volume_mix` | float | 0.0-2.0 | 1.0 | Volume influence multiplier |
| `audio_bass_mix` | float | 0.0-2.0 | 0.5 | Bass influence multiplier |
| `audio_mid_mix` | float | 0.0-2.0 | 0.3 | Mid influence multiplier |
| `audio_treble_mix` | float | 0.0-2.0 | 0.7 | Treble influence multiplier |
| `audio_beat_mix` | float | 0.0-2.0 | 1.0 | Beat influence multiplier |
| `audio_spectrum_mix` | float | 0.0-2.0 | 0.5 | Spectrum array influence |
| `ultra_max_iterations` | int | 0-200 | 0 | Ray steps (0=use default 64) |
| `ultra_fractal_power` | float | 0.0-10.0 | 0.0 | Mandelbulb power (0=use default 8.0) |
| `ultra_step_size` | float | 0.0-1.0 | 0.0 | Ray march step multiplier (0=use default 0.001) |

**Note**: `ultra_*` parameters are performance overrides. When set to 0 (or default), the shader uses built-in defaults.

---

## 4. GLSL Shaders

### Vertex Shader (Fullscreen Quad)

```glsl
#version 330 core
layout(location = 0) in vec2 position;
out vec2 TexCoord;

void main() {
    gl_Position = vec4(position, 0.0, 1.0);
    TexCoord = position * 0.5 + 0.5;
}
```

### Fragment Shader (278 lines)

The fragment shader includes:

1. **SDF Functions**:
   - `sdSphere(p, r)` - sphere distance
   - `sdBox(p, b)` - box distance
   - `sdTorus(p, t)` - torus distance
   - `mandelbulbDE(p)` - Mandelbulb fractal distance estimator

2. **Scene Map**:
   - `mapSpheres(p)` - array of spheres with audio-reactive radius
   - `mapTunnel(p)` - infinite tunnel with audio-modulated radius
   - `mapFractal(p)` - Mandelbulb with audio-modulated power

3. **Normal Calculation**:
   - `calcNormal(p)` - gradient-based normal estimation

4. **HSV to RGB**:
   - `hsv2rgb(c)` - standard conversion

5. **Main Loop**:
   - Ray setup (camera `ro`, ray direction `rd`)
   - Ray marching loop (max 64 steps, early exit)
   - Lighting (diffuse from fixed light direction)
   - Audio-reactive color mixing
   - Background gradient with beat modulation

6. **Audio Uniforms**:
   - `iAudioVolume`, `iAudioBass`, `iAudioMid`, `iAudioTreble`, `iAudioBeat`
   - `iAudioSpectrum[512]` - frequency spectrum array

---

## 5. Scene Variants

### Scene 0: Spheres
- Array of spheres arranged in 3D grid
- `base_radius` scales all spheres
- Audio modulates individual sphere sizes slightly
- Camera orbits around center

### Scene 1: Tunnel
- Infinite cylindrical tunnel
- `base_radius` controls tunnel diameter
- Audio bass modulates tunnel radius
- Camera moves forward through tunnel

### Scene 2: Fractal (Mandelbulb)
- 3D Mandelbulb fractal
- `ultra_fractal_power` controls fractal detail (default 8.0)
- Audio treble modulates color hue
- Camera orbits fractal

---

## 6. Audio Reactivity Mapping

| Audio Feature | Shader Uniform | Parameter Mix | Effect |
|---------------|----------------|---------------|--------|
| VOLUME | `iAudioVolume` | `audio_volume_mix` | Color value brightness |
| BASS | `iAudioBass` | `audio_bass_mix` | Tunnel radius, sphere size |
| MID | `iAudioMid` | `audio_mid_mix` | Color saturation |
| TREBLE | `iAudioTreble` | `audio_treble_mix` | Color hue shift |
| BEAT | `iAudioBeat` | `audio_beat_mix` | Background gradient, flash |
| SPECTRUM | `iAudioSpectrum[512]` | `audio_spectrum_mix` | Not currently used (reserved) |

---

## 7. Ultra Boost Performance Options

These uniforms allow runtime performance tuning:

- `ultra_max_iterations` (default 64): Reduce to 32 or 16 for better FPS
- `ultra_fractal_power` (default 8.0): Lower values (4.0-6.0) reduce fractal complexity
- `ultra_step_size` (default 0.001): Increase to 0.01 or 0.1 for fewer steps (may miss surfaces)

**Usage**: Set via `apply_uniforms` before rendering. If 0, shader uses built-in defaults.

---

## 8. Presets (5 Minimum)

1. **`spheres_default`**: scene_type=0, base_radius=1.5, color_hue=0.5, moderate audio mixes
2. **`tunnel_flow`**: scene_type=1, base_radius=2.0, position_offset.z=5.0, high bass_mix=1.5
3. **`fractal_zoom`**: scene_type=2, base_radius=1.0, ultra_fractal_power=8.0, high treble_mix=1.2
4. **`audio_reactive`**: balanced mixes, all audio_mix=1.0, scene_type=0
5. **`ultra_performance`**: ultra_max_iterations=32, ultra_step_size=0.01, scene_type=1

---

## 9. Unit Tests (≥ 80% coverage)

**Test File**: `tests/plugins/test_audio_reactive_raymarched_scenes.py`

### Critical Tests:

1. **Parameter validation**:
   - All parameters accept valid ranges
   - Clamping behavior for out-of-range values
   - Default values correct

2. **Shader compilation**:
   - Vertex shader compiles without errors
   - Fragment shader compiles without errors
   - All uniforms locate correctly

3. **SDF correctness** (unit test SDF functions in isolation):
   - `sdSphere(center, r)` returns 0 at surface, negative inside
   - `sdBox` and `sdTorus` basic properties
   - `mandelbulbDE` returns finite values

4. **Scene switching**:
   - `scene_type=0` renders spheres
   - `scene_type=1` renders tunnel
   - `scene_type=2` renders fractal

5. **Audio uniform application**:
   - All 6 audio uniforms set correctly
   - Spectrum array length 512
   - Mix multipliers applied

6. **Ultra boost overrides**:
   - Non-zero `ultra_max_iterations` overrides default
   - Non-zero `ultra_fractal_power` overrides default
   - Non-zero `ultra_step_size` overrides default

7. **HSV to RGB conversion**:
   - Test known values (red hsv(0,1,1) → rgb(1,0,0))
   - Boundary conditions (s=0, v=0)

8. **Ray marching logic**:
   - Max steps respected
   - Max distance respected
   - Surface distance threshold

---

## 10. Performance Tests

- **FPS benchmark**: ≥ 60 FPS at 1920×1080 on integrated GPU
- **Ray step count**: Average steps per pixel < 40 for spheres/tunnel, < 25 for fractal with ultra defaults
- **Memory**: Shader compile < 50ms, uniform upload < 5ms

---

## 11. Visual Regression Tests

Capture reference frames for each preset at 5-second intervals and compare pixel-by-pixel (allow 1% variance for floating point).

---

## 12. Implementation Phases

### Phase 1: Foundation (Day 1)
- Create plugin file with class skeleton
- Implement parameter definitions (15 parameters)
- Implement vertex shader (20 lines)
- Basic fragment shader structure

### Phase 2: Core Rendering (Day 2)
- Implement all SDF functions (sdSphere, sdBox, sdTorus, mandelbulbDE)
- Implement scene map functions (mapSpheres, mapTunnel, mapFractal)
- Implement normal calculation
- Implement HSV to RGB

### Phase 3: Main Shader (Day 3)
- Implement ray marching loop
- Implement lighting
- Implement audio-reactive color mixing
- Implement background gradient
- Connect `apply_uniforms` to all uniforms

### Phase 4: Testing & Validation (Day 4)
- Write unit tests (target 85% coverage)
- Performance testing
- Visual regression captures
- Safety rails verification

---

## 🔒 Safety Rails Compliance

| Rail | Compliance Strategy |
|------|---------------------|
| **60 FPS Sacred** | Ultra boost parameters allow runtime FPS tuning; default settings target 60+ FPS on integrated GPUs |
| **Offline-First** | No network calls; all audio data from local analyzer |
| **Plugin Integrity** | `METADATA` constant with name, version, description, author, license |
| **750-Line Limit** | Expected ~350 lines total (well under limit) |
| **80% Test Coverage** | Unit tests targeting 85%+ (SDFs, uniforms, parameters) |
| **No Silent Failures** | Shader compilation errors raise `RuntimeError` with GLSL error log |
| **Resource Leak Prevention** | No dynamic GL resources beyond shader program (handled by base class) |
| **Backward Compatibility** | New plugin, no compatibility concerns |
| **Security** | No user input in shader strings; all uniforms validated |

---

## 🎨 Legacy Reference Analysis

**Source File**: `/home/happy/Desktop/claude projects/VJlive-2/plugins/core/vshadertoy_extra/raymarched_scenes.py` (298 lines)

**Key Implementation Details**:
- Class: `AudioReactiveRaymarchedScenes(Effect)`
- Vertex shader: 14 lines (simple fullscreen quad)
- Fragment shader: 278 lines embedded as Python string
- SDFs: Standard implementations (no modifications needed)
- Mandelbulb DE: 8th power default, 4-5 iterations
- Ray marching: 64 steps default, surface distance 0.001
- Camera: Fixed at (0,0,-3), looking at origin
- Lighting: Single directional light from (1,1,-1)
- Audio integration: 6 uniforms + 512-length spectrum array

**Porting Notes**:
- Copy SDF functions verbatim (mathematically correct)
- Preserve ray marching loop structure
- Maintain audio uniform naming conventions
- Ultra boost parameters are already in legacy code (just need to wire them)
- HSV conversion is standard (copy exactly)
- Scene switching via `scene_type` integer uniform

---

## ✅ Acceptance Criteria

1. **Functional**:
   - All three scene types render correctly
   - Audio reactivity works for all 6 frequency bands
   - Ultra boost parameters affect performance as expected
   - Presets produce distinct visual styles

2. **Performance**:
   - ≥ 60 FPS at 1080p on integrated GPU with default settings
   - Shader compile time < 50ms
   - Uniform upload < 5ms per frame

3. **Quality**:
   - No shader compilation warnings
   - No visual artifacts (banding, flickering, tearing)
   - Smooth ray marching (no popping)

4. **Testing**:
   - Unit test coverage ≥ 80%
   - All tests pass
   - Visual regression baseline captured

5. **Safety**:
   - All safety rails satisfied
   - No silent failures
   - Proper error handling for shader compilation failures

---

## 🔗 Dependencies

- **Base Class**: `vjlive3.plugins.base.Effect`
- **Audio Analyzer**: `vjlive3.audio.analyzer.AudioAnalyzer` (for audio features)
- **OpenGL**: `glUniform` calls via moderngl or PyOpenGL
- **NumPy**: For spectrum array handling

---

## 📊 Success Metrics

- FPS: ≥ 60 (default), ≥ 120 (ultra_performance preset)
- Test Coverage: ≥ 80%
- Lines of Code: ≤ 400 (including shaders)
- Shader Compile: < 50ms
- Memory: < 50 MB additional

---

## 📝 Notes for Implementation Engineer

1. **Shader Precision**: Use `highp float` in fragment shader for Mandelbulb fractal to avoid artifacts
2. **Spectrum Array**: The legacy code uses `iAudioSpectrum[512]`. Ensure uniform location retrieval handles array correctly
3. **Ultra Boost**: These are optional performance knobs. Default to legacy values when not set
4. **Scene Switching**: Changing `scene_type` mid-frame is safe (uniform update only)
5. **Camera**: The legacy camera is fixed. If you want camera movement, that's a future enhancement (out of scope)
6. **Testing SDFs**: Write pure-Python SDF functions for unit testing (compare against GLSL results)
7. **Performance**: The Mandelbulb is expensive. Consider reducing iterations in fractal scene if FPS drops below 60

---

**Ready for Implementation after Approval**
