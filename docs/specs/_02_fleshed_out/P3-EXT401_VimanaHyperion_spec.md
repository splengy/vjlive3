# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT401_VimanaHyperion.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT401 — VimanaHyperion

**What This Module Does**

The `VimanaHyperion` effect is a multi-pass video synthesizer that combines sacred geometry rendering with a feedback loop engine. It processes input video through three distinct stages: (1) a geometry pass that renders signed-distance-field (SDF) sacred geometry patterns (Flower of Life, Metatron's Cube, Merkaba) and composites them with the source, (2) a feedback pass that applies transformations (zoom, rotation, shift) and decay to create recursive visual loops, and (3) a composite pass that applies final color adjustments (hue, saturation, brightness, contrast). The effect supports audio reactivity, Astra depth integration, and hot-reloadable Lumen shader chains for procedural geometry generation.

**What This Module Does NOT Do**

- Perform file I/O or persistent storage operations
- Process audio streams directly (relies on EffectChain's AudioReactor)
- Implement 3D geometry extrusion or volumetric rendering (2D SDF only)
- Provide MIDI/OSC control interfaces (controlled via parameter updates)
- Support arbitrary non-rectangular framebuffer operations

---

## Detailed Behavior and Parameter Interactions

The effect operates as a three-pass GPU pipeline with manual framebuffer management. Each frame, the following sequence executes:

1. **Geometry Pass**: Renders sacred geometry SDFs onto the input frame. The geometry is generated procedurally using mathematical SDF functions (no texture atlases). Audio features modulate geometry parameters in real-time: bass expands the Flower of Life, beat pulses the Metatron's Cube intensity, treble accelerates Merkaba spin, and mids shift the chakra frequency color.

2. **Feedback Pass**: Takes the geometry output and blends it with the previous frame's feedback buffer using a ping-pong double-buffer scheme. The transformation matrix applies zoom (exponential scaling), rotation (radial), and shift (linear translation). Decay gradually desaturates and darkens the feedback loop to prevent runaway accumulation. Audio can modulate decay rate (treble increases decay).

3. **Composite Pass**: Applies final color correction in HSV space to the feedback result before outputting to the screen.

**Parameter Interpolation**: All parameters are expected to be updated in real-time via `set_parameter()`. The shader reads these values directly each frame. Audio-derived modulations are computed on the CPU side (in `render()`) and passed as augmented parameter values to the geometry and feedback passes.

**Astra Depth Integration**: If an AstraSource is active and providing depth data, the geometry shader receives `depth_tex` (texture unit 2) and can use depth values to modulate geometry placement, scale, or color. The current implementation passes depth_min=0.0 and depth_max=1.0 as uniform values.

**Lumen Hot-Reload**: The geometry fragment shader can be replaced at runtime via `load_lumen_chain(hydra_string)`. The Hydra code is preprocessed and injected into a template file `core/shaders/templates/lumen_geometry.frag` at the designated live-coding area. The shader is then recompiled without restarting the effect.

---

## Public Interface

```python
class VimanaHyperion(Effect):
    """
    Vimana Hyperion - The Next Generation Video Synthesizer.
    
    Architecture:
    [Input] -> [Geometry Pass (SDFs)] -> [Feedback Loop (Transform/Decay)] -> [Composite (Color/Post)] -> [Output]
    
    Features:
    - Modular Shader Graph (3 Passes)
    - Internal Double-Buffered Feedback (Native, no EffectChain dependency)
    - High-Performance Architect Engine
    """
    
    def __init__(self) -> None:
        """Initialize effect with default parameters and allocate GPU resources."""
        
    def render(self, input_texture: int, extra_textures: list = None) -> int:
        """
        Execute the three-pass render pipeline.
        
        Args:
            input_texture: OpenGL texture ID of the input frame
            extra_textures: Unused (reserved for future extensions)
            
        Returns:
            OpenGL texture ID of the output frame (the current feedback buffer)
        """
        
    def pre_process(self, chain, input_texture) -> None:
        """
        Capture AudioReactor from the EffectChain before rendering.
        
        Args:
            chain: The EffectChain instance (may have .audio_reactor attribute)
            input_texture: Input texture ID (unused in current implementation)
        """
        
    def load_lumen_chain(self, hydra_string: str) -> None:
        """
        Hot-reload the geometry shader with new Hydra code.
        
        Args:
            hydra_string: Hydra shader code string to preprocess and inject
        """
        
    def set_parameter(self, name: str, value: float) -> None:
        """Inherited from Effect base class. Updates effect parameters in real-time."""
        
    def get_parameter(self, name: str) -> float:
        """Inherited from Effect base class. Retrieves current parameter value."""
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `input_texture` | `int` (OpenGL texture ID) | Input video frame to process | Must be a valid GL texture with `GL_TEXTURE_2D` target |
| `output` | `int` (OpenGL texture ID) | Rendered output frame | Returned from `render()`, valid for current GL context |

**Parameters** (all float, range 0.0-10.0 unless specified):

| Parameter | Description | Default | Audio Modulation |
|-----------|-------------|---------|-----------------|
| `sacred_geometry_mix` | Geometry overlay intensity (0=source only, 1=geometry only) | 0.0 | No |
| `flower_of_life` | Flower of Life pattern intensity | 0.0 | Bass expands (+0.3 per unit) |
| `metatron_cube` | Metatron's Cube pattern intensity | 0.0 | Beat pulses (+0.2 per unit) |
| `merkaba_spin` | Merkaba rotation speed (rad/sec) | 0.1 | Treble accelerates (+0.5 per unit) |
| `chakra_freq` | Color frequency offset for chakra colors | 0.0 | Mids shift (+0.2 per unit) |
| `zoom` | Zoom factor (1.0 = neutral, >1 = zoom in, <1 = zoom out) | 1.0 | No |
| `rotate` | Rotation angle in degrees | 0.0 | No |
| `shift_x` | Horizontal shift in UV space (-1 to 1) | 0.0 | No |
| `shift_y` | Vertical shift in UV space (-1 to 1) | 0.0 | No |
| `feedback_amt` | Feedback blend amount (0=no feedback, 1=full feedback) | 0.95 | No |
| `decay` | Signal decay per loop (0=none, 1=instant) | 0.05 | Treble increases (+0.1 per unit) |
| `hue_shift` | Hue rotation in 0-1 range (1=360°) | 0.0 | No |
| `saturation` | Saturation multiplier (1=neutral) | 1.0 | No |
| `brightness` | Brightness offset (-0.5 to 0.5) | 0.0 | No |
| `contrast` | Contrast multiplier (1=neutral) | 1.0 | No |

---

## Edge Cases and Error Handling

- **Missing AudioReactor**: If `chain.audio_reactor` is `None` or missing methods, audio modulation values default to 0.0. The effect continues rendering without audio reactivity. Errors are logged at warning level but do not interrupt execution.

- **Shader Compilation Failure**: If any shader fails to compile during `_ensure_initialized()`, the exception is logged with shader source and re-raised. The effect will not be usable until the shader code is corrected and the application restarted.

- **Framebuffer Incompleteness**: Framebuffer creation checks completeness after attachment. If incomplete, an error is logged and the effect fails to initialize. This typically indicates insufficient GPU memory or driver issues.

- **AstraSource Failure**: If `AstraSource()` fails to initialize or `self.astra.active` is `False`, depth integration is silently skipped. No error is raised; the effect operates without depth data.

- **Lumen Code Injection Failure**: If `load_lumen_chain()` fails to load the template or preprocess the Hydra code, the error is logged and the existing geometry shader remains active. The effect continues using the default SDF geometry.

- **Resource Cleanup**: The `__del__()` method attempts to delete the internal VAO and calls `super().__del__()` if available. Errors during cleanup are caught and ignored to prevent crashes during interpreter shutdown.

- **NaN/Inf Protection**: The feedback shader clamps intermediate results to [0.0, 10.0] to prevent propagation of invalid values that could corrupt the feedback loop.

---

## Mathematical Formulations

### Geometry Pass SDF Functions

The sacred geometry patterns are rendered using signed distance functions (SDFs) defined in `core/effects/utils/sacred_geometry.py` (referenced via `SACRED_GEOMETRY_LIB`). The exact implementations are:

- **Flower of Life**: Concentric circles arranged in a hexagonal pattern. Base radius scaled by `scale` parameter. Distance field computed as minimum distance to any circle boundary.
- **Metatron's Cube**: Derived from the Flower of Life pattern, includes additional connecting lines and geometric constructs. Rotation applied via 2D rotation matrix with angle `time * merkaba_spin`.
- **Merkaba**: Star tetrahedron projection, also rotation-dependent.

**Glow Calculation**: `glow = 0.005 / (abs(d) + 0.0001)`, clamped to [0.0, 1.0]. This creates a soft glow that falls off inversely with distance from the SDF surface.

**Chakra Color Mapping**: `getChakraColor(local_freq)` maps a frequency value to a 7-color chakra spectrum (red, orange, yellow, green, blue, indigo, violet). The mapping uses `local_freq = chakra_freq + length(p) * 0.5` to create radial color variation.

**Final Geometry Composite**: `final_col.rgb += geo_rgb * sacred_geometry_mix * 2.0` (additive blending).

### Feedback Pass Transformations

Given input UV `uv` and transformation parameters:

1. **Center**: `tc = uv - 0.5`
2. **Scale**: `scale = 1.0 / (zoom + 0.001)`, then `tc *= scale`
3. **Rotate**: `angle = radians(rotate)`, `tc = (tc.x * cos(angle) - tc.y * sin(angle), tc.x * sin(angle) + tc.y * cos(angle))`
4. **Shift**: `tc += [shift_x, shift_y]`
5. **De-center**: `tc += 0.5`

**Feedback Mix**: `result = mix(input_color, feedback_color, feedback_amt)`

**Decay Application**: `feedback_color.rgb *= (1.0 - decay)` before mixing. Additional decay effects include:
- Desaturation: `luma = dot(feedback_color.rgb, vec3(0.299, 0.587, 0.114))`, then `feedback_color.rgb = mix(feedback_color.rgb, vec3(luma), decay_amt * 0.15)`
- Brightness reduction: `feedback_color.rgb *= (1.0 - decay_amt * 0.05)`
- Chroma shift: `feedback_color.r` samples with horizontal offset `shift_amt = decay_amt * 0.003`
- Saturation buildup: `sat = dot(abs(feedback_color.rgb - vec3(luma)), vec3(1.0))`, then `feedback_color.rgb = mix(feedback_color.rgb, feedback_color.rgb * (1.0 + sat * 0.15), fb_amt * 0.5)`

### Composite Pass Color Adjustments

1. **Contrast**: `col.rgb = (col.rgb - 0.5) * contrast + 0.5`
2. **Brightness**: `col.rgb += brightness`
3. **HSV Shift**: Convert to HSV, add `hue_shift` to hue (wrapped via `fract`), multiply saturation by `saturation`, convert back to RGB.

### Audio Modulation (CPU-side)

Audio features are retrieved from `audio_reactor`:

- `bass_val = audio_reactor.get_bass_level()` (normalized 0.0-1.0)
- `mid_val = audio_reactor.get_mid_level()`
- `treble_val = audio_reactor.get_treble_level()`
- `beat_pulse = audio_reactor.get_beat_strength()`

These values augment geometry parameters before uniform upload:

```
target_fol = flower_of_life + (bass_val * 0.3)
target_met = metatron_cube + (beat_pulse * 0.2)
target_spin = merkaba_spin + (treble_val * 0.5)
target_freq = chakra_freq + (mid_val * 0.2)
target_decay = decay + (treble_val * 0.1)
```

All augmented values are clamped to valid ranges (0.0-1.0 for intensity parameters, no clamp for spin/decay which are naturally bounded by subsequent operations).

---

## Performance Characteristics

- **GPU-Bound**: The effect is entirely GPU-driven with three full-screen passes per frame. CPU overhead is minimal (uniform updates, audio feature retrieval).
- **Memory**: Uses three framebuffers at full resolution (geometry output, feedback ping, feedback pong). Each framebuffer includes a color texture (RGBA8 or RGBA16F depending on context). Total VRAM usage ≈ 3 × (width × height × 4 bytes) for 8-bit textures, or 3 × (width × height × 8 bytes) for 16-bit float.
- **Fill Rate**: Three passes × full-screen quad = 3× overdraw. At 1920×1080, this is ~6.2 million fragments per pass, ~18.6 million total per frame.
- **Shader Complexity**: Geometry pass includes multiple SDF evaluations per fragment (Flower of Life, Metatron's Cube, Merkaba). These are computationally intensive but use simple math (distance functions, trigonometric rotations).
- **Audio Reactivity**: Audio feature retrieval adds negligible CPU overhead (assumes AudioReactor already running).
- **Lumen Hot-Reload**: Shader recompilation can cause a brief hitch (10-50ms) depending on shader complexity. Should be done during loading or paused state, not mid-performance.

---

## Dependencies

- **External Libraries**:
  - `OpenGL` (via PyOpenGL) — required for all rendering operations; effect fails to initialize without GL context
  - `numpy` — used for quad vertex data in `_setup_internal_quad()`
  - `ctypes` — for OpenGL pointer operations

- **Internal Modules**:
  - `core.effects.shader_base.Effect` — base class providing shader management, uniform setting, and lifecycle
  - `core.effects.shader_base.ShaderProgram` — wrapper for GLSL compilation and uniform location caching
  - `core.effects.shader_base.Framebuffer` — framebuffer object management with texture attachment
  - `core.effects.shader_base.BASE_VERTEX_SHADER` — standard full-screen quad vertex shader
  - `core.effects.shader_base.PASSTHROUGH_FRAGMENT` — simple passthrough fragment shader (used as base)
  - `core.vision.astra_source.AstraSource` — optional depth camera integration
  - `core.lumen_hydra_preprocessor.inject_hydra_code` — Hydra shader preprocessing for Lumen chains
  - `core.effects.utils.sacred_geometry.SACRED_GEOMETRY_LIB` — GLSL SDF functions for sacred geometry patterns

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_gl_context` | Effect raises appropriate error if initialized without valid OpenGL context |
| `test_init_creates_resources` | `_ensure_initialized()` creates 3 FBOs, 3 shaders, and VAO without errors |
| `test_render_three_passes` | `render()` executes all three passes and returns a valid texture ID |
| `test_feedback_pingpong` | Feedback buffers swap correctly (current_fb_idx toggles between 0 and 1) |
| `test_parameter_application` | Setting parameters via `set_parameter()` affects shader uniforms on next render |
| `test_audio_modulation` | Provided audio_reactor values correctly augment geometry/decay parameters |
| `test_astra_integration` | When AstraSource.active=True, depth texture is bound to unit 2 and uniforms set |
| `test_lumen_hot_reload` | `load_lumen_chain()` recompiles geometry shader with injected code without crashing |
| `test_lumen_fallback` | Invalid Hydra code logs error but keeps existing shader functional |
| `test_decay_clamping` | Decay-augmented values are clamped to safe ranges (0.0-1.0) |
| `test_framebuffer_completeness` | All FBOs report complete after creation and after each render pass |
| `test_output_dimensions` | Output texture dimensions match initialized width/height |
| `test_cleanup` | `__del__()` deletes VAO without raising exceptions |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-EXT401: VimanaHyperion` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES

Use these to fill in the spec. These are the REAL implementations:

### vjlive2/core/effects/vimana.py (L1-799)
```python
# Unified Vimana Fragment Shader — All processing in one pass
# This is the base Vimana effect providing feedback engine, color processing,
# oscillator, audio integration, composite simulation, and patchbay routing.

VIMANA_FRAGMENT = """
#version 330 core
... (full shader code with 50+ parameters)
"""

class VimanaEffect(Effect):
    def __init__(self):
        self.parameters = {
            # Feedback Engine
            "shift_up": 0.0,
            "shift_down": 0.0,
            ...
            "u_audio_level": 0.0,
            "u_bass": 0.0,
            "u_mid": 0.0,
            "u_high": 0.0
        }
```

### vjlive2/core/effects/vimana_hyperion.py (L1-595)
```python
from core.effects.shader_base import Effect, ShaderProgram, Framebuffer, BASE_VERTEX_SHADER, PASSTHROUGH_FRAGMENT
from core.effects.utils.sacred_geometry import SACRED_GEOMETRY_LIB
from core.vision.astra_source import AstraSource
from core.lumen_hydra_preprocessor import inject_hydra_code

# PASS 1: GEOMETRY ENGINE
GEOMETRY_FRAGMENT = """
#version 330 core
... (SDF rendering with sacred geometry)
"""

# PASS 2: FEEDBACK ENGINE
FEEDBACK_FRAGMENT = """
#version 330 core
... (transform + decay + ping-pong)
"""

# PASS 3: COMPOSITE
COMPOSITE_FRAGMENT = """
#version 330 core
... (HSV color adjustments)
"""

class VimanaHyperion(Effect):
    def __init__(self):
        # Manual render, 3-pass pipeline
        self.manual_render = True
        self.fbo_geo = None
        self.fbo_feedback_1 = None
        self.fbo_feedback_2 = None
        self.current_fb_idx = 0
        self.shader_geo = None
        self.shader_fb = None
        self.shader_comp = None
        self.vao = 0
        
        # Parameters (geometry, feedback, composite)
        self._init_hyperion_parameters()
        
        # Astra + Lumen
        self.astra = AstraSource()
        self.lumen_code = None
        
    def render(self, input_texture, extra_textures=None):
        # 1. Geometry Pass: Input -> fbo_geo (with SDF overlay)
        # 2. Feedback Pass: fbo_geo + previous_fb -> current_fb (ping-pong)
        # 3. Composite Pass: current_fb -> screen
        # Returns current_fb.texture
        
    def pre_process(self, chain, input_texture):
        self.audio_reactor = getattr(chain, 'audio_reactor', None)
        
    def load_lumen_chain(self, hydra_string):
        # Preprocess Hydra, inject into template, recompile geometry shader
        
    def _update_uniforms_geo(self, shader, curr_time, res, input_texture_unit):
        # Sets uniforms: time, resolution, texSource, audio_*, depth_*, agent_*
```

### vjlive2/plugins/core/vimana_hyperion_quantum/plugin.json (L1-210)
```json
{
    "id": "vimana_hyperion_quantum",
    "name": "Vimana Hyperion+",
    "parameters": [
        { "id": "quantum_entanglement", ... },
        { "id": "neural_link_strength", ... },
        { "id": "holographic_intensity", ... },
        { "id": "sacred_geometry_overlay", ... },
        { "id": "dimensional_fold", ... },
        { "id": "quantum_fluctuation", ... },
        { "id": "consciousness_field", ... },
        { "id": "ai_suggestion_strength", ... },
        { "id": "partner_quantum_state", ... },
        { "id": "flower_of_life_scale", ... },
        { "id": "merkaba_spin", ... },
        { "id": "mandala_folds", ... },
        { "id": "golden_spiral", ... },
        { "id": "particle_energy", ... },
        { "id": "particle_r", ... },
        { "id": "particle_g", ... },
        { "id": "particle_b", ... },
        { "id": "brainwave_alpha", ... },
        { "id": "brainwave_beta", ... },
        { "id": "brainwave_theta", ... },
        { "id": "brainwave_delta", ... }
    ]
}
```

Note: The plugin.json defines a "Vimana Hyperion+" variant with additional quantum/consciousness parameters. The core `VimanaHyperion` class implements the base effect without these extended parameters. The spec above documents the core implementation. Extended parameters would be added as a wrapper or subclass in VJLive3.

---

## Integration Notes

- The effect should be registered as a node in the VJLive3 node graph with a single video input and single video output.
- Parameters are exposed as node properties with the ranges specified above. The 0.0-10.0 legacy scale should be preserved for compatibility; internal shader code maps these to appropriate ranges (e.g., `zoom` maps from 1.0 neutral, but legacy used 5.0 scale).
- The effect requires an active OpenGL context during initialization. If the context is lost, the effect must be re-initialized (handled by base Effect class in VJLive3).
- Audio reactivity depends on the EffectChain providing an `audio_reactor` object with methods: `get_bass_level()`, `get_mid_level()`, `get_treble_level()`, `get_beat_strength()`, `get_volume()`.
- Astra depth integration is optional; if no Astra device is present, `AstraSource.active` is `False` and depth uniforms are not set.
- Lumen hot-reload is an advanced feature; the Hydra string should be validated before calling `load_lumen_chain()` to avoid shader compilation errors.

---

## Memory Layout and Resource Management

**Framebuffer Objects**:
- `fbo_geo`: RGBA texture, size = (width, height). Used as geometry pass output.
- `fbo_feedback_1`: RGBA texture, size = (width, height). Ping buffer.
- `fbo_feedback_2`: RGBA texture, size = (width, height). Pong buffer.

**Vertex Array Object**:
- Single VAO stores quad vertex buffer (4 vertices, 6 indices) with interleaved position (2 floats) and texcoord (2 floats). Created once in `_setup_internal_quad()`.

**Shader Programs**:
- `shader_geo`: Geometry pass shader (vertex + fragment). Fragment includes `SACRED_GEOMETRY_LIB` and optional Lumen code.
- `shader_fb`: Feedback pass shader (vertex + `FEEDBACK_FRAGMENT`).
- `shader_comp`: Composite pass shader (vertex + `COMPOSITE_FRAGMENT`).

**Texture Units**:
- Geometry pass: `texSource` at unit 0, `depth_tex` at unit 2 (if Astra active)
- Feedback pass: `texInput` at unit 0, `texFeedback` at unit 1
- Composite pass: `texMain` at unit 0

**Double-Buffering Logic**:
```
if current_fb_idx == 0:
    read_fb = fbo_feedback_1
    write_fb = fbo_feedback_2
else:
    read_fb = fbo_feedback_2
    write_fb = fbo_feedback_1

# After feedback pass:
current_fb_idx = 1 - current_fb_idx
```

---

## Open Questions / [NEEDS RESEARCH]

- [NEEDS RESEARCH] Exact implementation of `SACRED_GEOMETRY_LIB` GLSL functions (flowerOfLife, metatronsCube, getChakraColor). These should be extracted from the actual sacred_geometry.py file to complete the spec.
- [NEEDS RESEARCH] `VideoConstants.DEFAULT_WIDTH` and `DEFAULT_HEIGHT` values in VJLive3; legacy used 1920×1080 but should be configurable.
- [NEEDS RESEARCH] `Effect` base class API in VJLive3: how are parameters registered, how does `apply_uniforms()` work, what is the expected lifecycle? The legacy `VimanaEffect` had `apply_uniforms()`; `VimanaHyperion` overrides `render()` directly.
- [NEEDS RESEARCH] `AstraSource` class details: how is depth data provided (texture format, update rate)? The legacy code assumes `self.astra.texture_id` is a valid GL texture.
- [NEEDS RESEARCH] `inject_hydra_code` preprocessing: what transformations are applied to Hydra code? What is the expected format of the Hydra string?
- [NEEDS RESEARCH] Lumen template file location: `core/shaders/templates/lumen_geometry.frag` — does this exist in VJLive3? Should be created if missing.

---

## Implementation Notes for VJLive3

1. **Parameter Ranges**: The legacy Vimana effect used a 0.0-10.0 scale for most parameters. `VimanaHyperion` uses different internal scales (e.g., `zoom` uses 1.0 as neutral, `feedback_amt` uses 0.0-1.0). The VJLive3 implementation should define a clear parameter mapping. Suggested: expose all parameters as 0.0-10.0 floats, then map internally:
   - `zoom`: `internal_zoom = pow(2.0, (param - 5.0) / 5.0)` to map 0→0.25, 5→1.0, 10→4.0
   - `feedback_amt`: `param / 10.0`
   - `decay`: `param / 10.0`
   - `rotate`: `param * 36.0` to map 0-10 → 0-360°
   - `shift_x/y`: `(param - 5.0) / 10.0` to map 0→-0.5, 5→0.0, 10→0.5
   - Composite params: `hue_shift = param / 10.0`, `saturation = param / 5.0` (5=1.0), `brightness = (param - 5.0) / 10.0`, `contrast = param / 5.0`

2. **Shader Organization**: Store the three fragment shaders as separate `.glsl` files or embedded strings. The `SACRED_GEOMETRY_LIB` should be imported from a common GLSL utility module.

3. **Error Handling**: Wrap OpenGL calls in try-except blocks where appropriate. Use the `opengl_safe` module if available (as in legacy code).

4. **Resource Management**: Implement proper cleanup in `__del__()` or a dedicated `destroy()` method. Delete FBOs, shaders, VAO, VBO, EBO.

5. **Thread Safety**: Rendering must occur on the main thread with a current GL context. The effect should not spawn worker threads.

6. **Testing Strategy**: Use a headless GL context (e.g., `pyglet` offscreen) for unit tests. Mock `audio_reactor` and `AstraSource` to test integration logic without hardware.

---
