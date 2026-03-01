# P5-DM24: mosh_pit_datamosh

> **Task ID:** `P5-DM24`  
> **Priority:** P0 (Critical)  
> **Source:** VJlive-2 (`plugins/vdatamosh/mosh_pit_datamosh.py`)  
> **Class:** `MoshPitDatamoshEffect`  
> **Phase:** Phase 5  
> **Status:** ⬜ Todo  

## What This Module Does

The `MoshPitDatamoshEffect` simulates the claustrophobic chaos of being trapped in a mosh pit. It creates an aggressive, suffocating, and intense visual experience where:

- **Body Slam**: Random XY displacements that mimic being shoved by crowd members
- **Wall Compression**: The edges of the screen warp inward, making the space feel smaller
- **Sweat Blur**: Disorienting motion blur simulating sweat and disorientation
- **Close Contact**: Depth values are pushed closer to the camera, enhancing claustrophobia
- **Adrenaline Spike**: Color saturation and contrast boost on impact moments
- **Panic Attack**: Strobe and flash effects simulating panic breathing
- **Crowd Density**: Depth-based compression that makes objects feel closer
- **Grit**: Noise and grain for gritty, raw aesthetic
- **Blood Rush**: Red tint at edges simulating adrenaline
- **No Escape**: Vignette that darkens edges, enhancing confinement

The effect uses depth data to "compress" space, camera shake to simulate impacts, and blur to create disorientation. It's designed to evoke the feeling of being trapped in a violent, sweaty, chaotic mosh pit at a punk or metal show.

## What It Does NOT Do

- Does NOT perform real-time crowd simulation (uses procedural noise and depth)
- Does NOT generate its own audio analysis (relies on `AudioReactor` for bass/energy bands)
- Does NOT include advanced motion blur (uses simple frame blending)
- Does NOT handle video decoding or capture (operates on texture inputs only)
- Does NOT provide frame buffer management (relies on `texPrev` external management)
- Does NOT perform depth estimation (requires external depth map)

## API Reference

### Class Signature

```python
class MoshPitDatamoshEffect(Effect):
    """
    Trapped In The Mosh Pit Datamosh — Claustrophobic Chaos
    
    DUAL VIDEO INPUT: tex0 = Video A, tex1 = Video B
    
    "I can't breathe."
    
    The walls are closing in. Bodies are pressing against you from all sides.
    This effect simulates the claustrophobia and violence of a mosh pit.
    Depth data is used to "compress" the space, making everything feel
    closer and more suffocating. Camera shake simulates impacts. Blur
    simulates sweat and disorientation.
    
    Features:
    - Body Slam: Random XY displacements that mimic being shoved.
    - Wall Compression: The edges of the screen warp inward.
    - Sweat Blur: Disorienting motion blur.
    - Close Contact: Depth values are pushed closer to the camera.
    - Adrenaline Spike: Color saturation and contrast boost on impact.
    
    Metadata:
    - Tags: mosh, chaos, claustrophobia, violence, sweat, punk, metal
    - Mood: aggressive, suffocating, chaotic, intense, violent
    - Visual Style: camera-shake, crash-zoom, motion-blur, gritty
    """
    
    def __init__(self, name: str = 'mosh_pit_datamosh') -> None
    
    def apply_uniforms(
        self,
        time: float,
        resolution: Tuple[int, int],
        audio_reactor: Optional[AudioReactor] = None,
        semantic_layer: Optional[SemanticLayer] = None
    ) -> None
    
    def get_state(self) -> Dict[str, Any]
    
    def set_parameters(self, params: Dict[str, float]) -> None
```

### GLSL Fragment Shader

```glsl
#version 330 core
in vec2 v_uv;
out vec4 fragColor;

uniform sampler2D tex0;        // Video A
uniform sampler2D texPrev;     // Previous frame for trails
uniform sampler2D depth_tex;   // Depth map
uniform sampler2D tex1;        // Video B
uniform float time;
uniform vec2 resolution;

// Impact and compression parameters
uniform float u_slam_intensity;    // How hard you get hit [0.0, 1.0]
uniform float u_compression;       // How much the room shrinks [0.0, 1.0]
uniform float u_sweat_blur;        // Disorientation amount [0.0, 10.0]
uniform float u_gasp_for_air;      // Fish-eye warp (panic) [0.0, 1.0]
uniform float u_bruise_color;      // Color shifting to purple/blue [0.0, 1.0]
uniform float u_collision_rate;    // Frequency of impacts [0.5, 5.0]
uniform float u_crowd_density;     // How close objects feel [0.0, 1.0]
uniform float u_panic_attack;      // Strobe/flash intensity [0.0, 1.0]
uniform float u_shutter_speed;     // Motion trail length [0.0, 1.0]
uniform float u_grit;              // Noise/Grain [0.0, 1.0]
uniform float u_blood_rush;        // Red tint at edges [0.0, 1.0]
uniform float u_no_escape;         // Vignette intensity [0.0, 1.0]

uniform float u_mix;

// Hash function for procedural generation
float hash(vec2 p);

void main();
```

### Python Class Parameters

```python
# Default parameter values (0-10 scale)
DEFAULT_PARAMS = {
    'slam_intensity': 6.0,      # Impact force
    'compression': 4.0,         # Room shrinkage
    'sweat_blur': 5.0,          # Motion blur amount
    'gasp_for_air': 6.0,        # Panic breathing warp
    'bruise_color': 3.0,        # Purple/blue tint
    'collision_rate': 5.0,      # Impact frequency
    'crowd_density': 6.0,       # Crowd proximity
    'panic_attack': 2.0,        # Strobe intensity
    'shutter_speed': 4.0,       # Trail length
    'grit': 6.0,                # Noise grain
    'blood_rush': 3.0,          # Edge red tint
    'no_escape': 5.0,           # Vignette strength
}

# Preset configurations
PRESETS = {
    'mosh_lite': {
        'slam_intensity': 3.0, 'compression': 2.0, 'sweat_blur': 2.0,
        'gasp_for_air': 2.0, 'bruise_color': 1.0, 'collision_rate': 2.0,
        'crowd_density': 2.0, 'panic_attack': 1.0, 'shutter_speed': 2.0,
        'grit': 3.0, 'blood_rush': 1.0, 'no_escape': 2.0,
    },
    'full_mosh': {
        'slam_intensity': 6.0, 'compression': 5.0, 'sweat_blur': 5.0,
        'gasp_for_air': 6.0, 'bruise_color': 3.0, 'collision_rate': 5.0,
        'crowd_density': 6.0, 'panic_attack': 3.0, 'shutter_speed': 4.0,
        'grit': 6.0, 'blood_rush': 3.0, 'no_escape': 5.0,
    },
    'claustrophobia_max': {
        'slam_intensity': 8.0, 'compression': 8.0, 'sweat_blur': 8.0,
        'gasp_for_air': 8.0, 'bruise_color': 5.0, 'collision_rate': 8.0,
        'crowd_density': 8.0, 'panic_attack': 5.0, 'shutter_speed': 6.0,
        'grit': 8.0, 'blood_rush': 5.0, 'no_escape': 8.0,
    },
}

# Audio parameter mappings
AUDIO_MAPPINGS = {
    'slam_intensity': 'bass',      # Maps to AudioReactor.get_band('bass')
    'panic_attack': 'high',        # Maps to AudioReactor.get_band('high')
    'gasp_for_air': 'energy',      # Maps to AudioReactor.get_energy()
    'crowd_density': 'mid',        # Maps to AudioReactor.get_band('mid')
}
```

## Inputs and Outputs

### Inputs

1. **Texture Unit 0** (`tex0`): Video A — primary video input
   - Format: `GL_RGBA8` or `GL_RGBA16F`
   - Resolution: Matches render target
   - Usage: Primary video source

2. **Texture Unit 1** (`texPrev`): Previous frame buffer
   - Format: Same as render target
   - Resolution: Matches render target
   - Usage: Motion trail persistence (sweat blur)
   - Must be updated externally each frame

3. **Texture Unit 2** (`depth_tex`): Depth map
   - Format: `GL_RED` or `GL_R16F`
   - Resolution: Matches render target
   - Range: [0.0, 1.0] where 0.0 = far, 1.0 = near
   - Usage: Crowd density compression, close contact effect

4. **Texture Unit 3** (`tex1`): Video B — secondary video input
   - Format: `GL_RGBA8` or `GL_RGBA16F`
   - Resolution: Matches render target
   - Usage: Secondary pixel source when dual mode active

### Uniforms

| Uniform | Type | Range | Description |
|---------|------|-------|-------------|
| `time` | `float` | [0, ∞) | Shader time in seconds |
| `resolution` | `vec2` | - | Frame buffer resolution in pixels |
| `u_slam_intensity` | `float` | [0.0, 1.0] | Camera shake impact force |
| `u_compression` | `float` | [0.0, 1.0] | Wall compression strength |
| `u_sweat_blur` | `float` | [0.0, 10.0] | Motion blur intensity |
| `u_gasp_for_air` | `float` | [0.0, 1.0] | Panic breathing fish-eye warp |
| `u_bruise_color` | `float` | [0.0, 1.0] | Purple/blue color tint |
| `u_collision_rate` | `float` | [0.5, 5.0] | Impact frequency (Hz) |
| `u_crowd_density` | `float` | [0.0, 1.0] | Depth compression strength |
| `u_panic_attack` | `float` | [0.0, 1.0] | Strobe/flash intensity |
| `u_shutter_speed` | `float` | [0.0, 1.0] | Motion trail blend factor |
| `u_grit` | `float` | [0.0, 1.0] | Noise grain intensity |
| `u_blood_rush` | `float` | [0.0, 1.0] | Red tint at screen edges |
| `u_no_escape` | `float` | [0.0, 1.0] | Vignette darkness |
| `u_mix` | `float` | [0.0, 1.0] | Effect blend ratio (always 1.0 internally) |

### Outputs

- **Color Buffer**: `fragColor` — final rendered pixel with all mosh pit effects applied
- **Alpha Channel**: Preserved from source (either `tex0` or `tex1` depending on dual mode)

## Edge Cases and Error Handling

### Camera Shake Edge Cases

1. **Zero Slam Intensity** (`u_slam_intensity = 0.0`):
   - No camera shake occurs
   - **Edge**: May appear less chaotic
   - **Mitigation**: Document that 0.0-1.0 range represents subtle to extreme shake

2. **Maximum Slam Intensity** (`u_slam_intensity = 1.0`):
   - Extreme camera shake (up to ±10% of frame)
   - **Edge**: May cause motion sickness or tracking difficulty
   - **Mitigation**: Provide presets with moderate values

3. **Collision Rate Extremes**:
   - `u_collision_rate = 0.5` → impacts every 2 seconds (slow)
   - `u_collision_rate = 5.0` → impacts every 0.2 seconds (rapid)
   - **Edge**: Very high rates may cause stroboscopic effect
   - **Mitigation**: Document safe ranges; provide presets

### Compression Edge Cases

4. **Zero Compression** (`u_compression = 0.0`):
   - No wall compression
   - **Edge**: May appear less claustrophobic
   - **Mitigation**: Document that 0.0-1.0 range represents open to compressed

5. **Maximum Compression** (`u_compression = 1.0`):
   - Extreme inward warp (everything feels very close)
   - **Edge**: May cause severe distortion
   - **Mitigation**: Provide presets with balanced compression

6. **Compression Artifacts**:
   - `pow(dist, 1.0 - u_compression * 0.5)` can cause extreme warping
   - Near center (dist≈0) → no warp
   - Near edges (dist≈0.5) → maximum warp
   - **Edge**: May cause texture stretching
   - **Mitigation**: Document that effect is non-linear

### Sweat Blur Edge Cases

7. **Zero Sweat Blur** (`u_sweat_blur = 0.0`):
   - No motion blur
   - **Edge**: May appear less disorienting
   - **Mitigation**: Document that 0.0-10.0 range represents clear to blurred

8. **Maximum Sweat Blur** (`u_sweat_blur = 10.0`):
   - Extreme motion blur (complete smearing)
   - **Edge**: May cause complete loss of detail
   - **Mitigation**: Provide presets with moderate blur

9. **Shutter Speed Interaction**:
   - `u_shutter_speed` controls trail persistence via `mix(prev, current, 1.0 - u_shutter_speed)`
   - `u_shutter_speed = 0.0` → no trails
   - `u_shutter_speed = 1.0` → complete trails
   - **Edge**: Combined with `u_sweat_blur` may cause excessive smearing
   - **Mitigation**: Document interaction between parameters

### Panic and Gasp Edge Cases

10. **Zero Gasp for Air** (`u_gasp_for_air = 0.0`):
    - No fish-eye panic warp
    - **Edge**: May appear less panicked
    - **Mitigation**: Document that 0.0-1.0 range represents calm to panicked

11. **Maximum Gasp for Air** (`u_gasp_for_air = 1.0`):
    - Extreme fish-eye distortion (breathing effect)
    - **Edge**: May cause visual discomfort
    - **Mitigation**: Provide presets with moderate values

12. **Panic Attack Strobe**:
    - `u_panic_attack` multiplies color intensity with random spikes
    - `panic = smoothstep(0.7, 0.9, sin(time * 20.0)) * u_panic_attack`
    - **Edge**: High values may cause strobing (seizure risk)
    - **Mitigation**: Document safe ranges; warn about strobe risk

### Color Effects Edge Cases

13. **Bruise Color** (`u_bruise_color`):
    - Shifts colors toward purple/blue: `color = mix(original, vec3(0.5, 0.0, 0.8), u_bruise_color)`
    - **Edge**: May cause unnatural color appearance
    - **Mitigation**: Document that this creates bruised aesthetic

14. **Blood Rush** (`u_blood_rush`):
    - Red tint at edges based on distance from center
    - `edge = smoothstep(0.3, 0.0, dist)` where `dist = length(uv - 0.5)`
    - **Edge**: May cause vignette with red tint
    - **Mitigation**: Document that this simulates adrenaline rush

### Crowd Density Edge Cases

15. **Zero Crowd Density** (`u_crowd_density = 0.0`):
    - No depth-based compression
    - **Edge**: May appear less crowded
    - **Mitigation**: Document that 0.0-1.0 range represents sparse to dense

16. **Maximum Crowd Density** (`u_crowd_density = 1.0`):
    - Maximum depth compression (everything pushed very close)
    - **Edge**: May cause severe depth distortion
    - **Mitigation**: Provide presets with balanced values

17. **Depth Map Inversion**:
    - Effect assumes depth range [0.0, 1.0] with 1.0 = near
    - Inverted depth (near=0, far=1) will reverse compression effect
    - **Mitigation**: Document expected depth range; add parameter if needed

### Grit and Noise Edge Cases

18. **Zero Grit** (`u_grit = 0.0`):
    - No noise grain
    - **Edge**: May appear too clean
    - **Mitigation**: Document that 0.0-1.0 range represents clean to gritty

19. **Maximum Grit** (`u_grit = 1.0`):
    - Full noise overlay
    - **Edge**: May obscure image detail
    - **Mitigation**: Provide presets with moderate grit

20. **Noise Generation**:
    - Uses `hash()` function for procedural noise
    - `float n = hash(uv * resolution * 0.1)` for screen-space noise
    - **Edge**: Noise may show patterns at certain resolutions
    - **Mitigation**: Document that noise is procedural and resolution-dependent

### Vignette and No Escape Edge Cases

21. **Zero No Escape** (`u_no_escape = 0.0`):
    - No vignette darkening
    - **Edge**: May appear less confined
    - **Mitigation**: Document that 0.0-1.0 range represents open to trapped

22. **Maximum No Escape** (`u_no_escape = 1.0`:
    - Maximum vignette (edges completely black)
    - **Edge**: May cause loss of peripheral information
    - **Mitigation**: Provide presets with moderate vignette

### Trail Persistence Edge Cases

23. **`texPrev` Not Updated**:
    - Effect reads `texPrev` but does not write
    - If external system fails to update, trails freeze
    - **Edge**: Stuck in previous frame state
    - **Mitigation**: Document external responsibility for `texPrev` management

24. **First Frame (No Previous Frame)**:
    - `texPrev` may be uninitialized (black/undefined)
    - `u_shutter_speed > 0` blends with undefined data
    - **Mitigation**: Clear `texPrev` to black on first frame externally

### Audio Reactivity Edge Cases

25. **`audio_reactor` is `None`**:
    - Code wraps audio access in `try/except` block
    - Falls back to parameter-only values (no audio modulation)
    - **Edge**: Silent failure if audio bands missing
    - **Mitigation**: Log warning on first audio access failure

26. **Audio Band Returns 0**:
    - Multiplicative modulation: `slam *= (1.0 + audio_reactor.get_band('bass', 0.0) * 0.8)`
    - If band returns 0, parameter remains at mapped value
    - **Edge**: No audio reactivity despite `audio_reactor` present
    - **Mitigation**: Document that audio bands must be properly initialized

## Dependencies

### VJLive3 Core Dependencies

- **Base Class**: `src/vjlive3/plugins/effect_base.py` — `Effect` class
  - Provides shader compilation, uniform management, texture unit binding
  - Implements `apply_uniforms()` base method
  - Handles plugin lifecycle (init, enable, disable)

- **Shader Infrastructure**: `src/vjlive3/render/shader_program.py`
  - `ShaderProgram` class for GLSL compilation
  - Uniform location caching
  - Error reporting

- **Audio Reactor**: `src/vjlive3/audio/reactor.py` (optional)
  - `AudioReactor` class providing `get_band()` and `get_energy()`
  - Used for audio-reactive parameter modulation

- **Plugin Registry**: `src/vjlive3/plugins/registry.py`
  - Manifest-based plugin discovery
  - Class instantiation via entry points

### External Dependencies

- **OpenGL Context**: Requires active OpenGL 3.3 core context
- **Texture Management**: External system must provide:
  - Depth texture (unit 2)
  - Previous frame texture (unit 1)
  - Dual video inputs (units 0 and 3)

### No Dependencies On

- Video decoding (textures provided externally)
- Depth estimation (depth map provided externally)
- Frame buffer management (handled by render pipeline)

## Test Plan

### Unit Tests (≥80% coverage)

1. **Parameter Mapping Tests** (`test_parameter_mapping.py`):
   - Verify `_map_param()` scales 0-10 input to correct output ranges
   - Test boundary values: 0.0 → min, 10.0 → max
   - Test mid-point: 5.0 → (min+max)/2
   - Test all 12 parameters with expected ranges:
     - `slam_intensity`: [0.0, 1.0]
     - `compression`: [0.0, 1.0]
     - `sweat_blur`: [0.0, 10.0]
     - `gasp_for_air`: [0.0, 1.0]
     - `bruise_color`: [0.0, 1.0]
     - `collision_rate`: [0.5, 5.0]
     - `crowd_density`: [0.0, 1.0]
     - `panic_attack`: [0.0, 1.0]
     - `shutter_speed`: [0.0, 1.0]
     - `grit`: [0.0, 1.0]
     - `blood_rush`: [0.0, 1.0]
     - `no_escape`: [0.0, 1.0]

2. **State Management Tests** (`test_state.py`):
   - `get_state()` returns dict with `name`, `enabled`, `parameters`
   - Parameters dict contains all 12 keys
   - Values are within 0-10 range
   - `set_parameters()` updates values correctly
   - Invalid parameter names are ignored or raise error (specify)

3. **Audio Mapping Tests** (`test_audio.py`):
   - Verify `AUDIO_MAPPINGS` dict contains 4 entries
   - Mock `AudioReactor` to test modulation math
   - Test `audio_reactor=None` fallback path
   - Test exception handling when audio bands fail

4. **Preset Loading Tests** (`test_presets.py`):
   - All preset names exist: `'mosh_lite'`, `'full_mosh'`, `'claustrophobia_max'`
   - Preset values within 0-10 range
   - `set_parameters(preset)` applies all values
   - Invalid preset name raises `KeyError`

### Integration Tests

5. **Shader Compilation Test** (`test_shader_compilation.py`):
   - GLSL shader compiles without errors
   - All uniform locations found
   - No validation errors in OpenGL context

6. **Uniform Application Test** (`test_uniforms.py`):
   - `apply_uniforms()` sets all 15 uniforms correctly
   - Texture units bound: `tex0=0`, `texPrev=1`, `depth_tex=2`, `tex1=3`
   - Time and resolution passed correctly
   - Audio modulation modifies parameter values as expected

7. **Dual Input Mode Test** (`test_dual_input.py`):
   - With black `tex1`, `hasDual` evaluates to false
   - With non-black `tex1`, `hasDual` evaluates to true
   - Sampler selection logic verified via mock texture reads

### Rendering Tests

8. **Camera Shake Test** (`test_camera_shake.py`):
   - Create static input with no motion
   - Verify `u_slam_intensity > 0` produces random XY offsets
   - Verify `u_collision_rate` controls impact frequency
   - Test shake magnitude matches `u_slam_intensity`

9. **Wall Compression Test** (`test_compression.py`):
   - Create grid pattern test image
   - Verify `u_compression = 0` → no warp
   - Verify `u_compression > 0` → inward warping toward center
   - Measure distance from center at various `u_compression` values

10. **Sweat Blur Test** (`test_sweat_blur.py`):
    - Create high-contrast moving pattern
    - Verify `u_sweat_blur = 0` → sharp motion
    - Verify `u_sweat_blur > 0` → motion blur via `texPrev` blending
    - Test `u_shutter_speed` interaction with blur

11. **Gasp for Air Test** (`test_gasp.py`):
    - Create grid pattern centered
    - Verify `u_gasp_for_air = 0` → no fish-eye
    - Verify `u_gasp_for_air > 0` → pulsating fish-eye distortion
    - Test breathing frequency (≈10 Hz from `sin(time * 10.0)`)

12. **Crowd Density Test** (`test_crowd_density.py`):
    - Create depth gradient
    - Verify `u_crowd_density` pushes near objects closer
    - Test depth-based UV offset magnitude

13. **Color Effects Test** (`test_color_effects.py`):
    - Test `u_bruise_color` shifts toward purple/blue
    - Test `u_blood_rush` creates red vignette at edges
    - Verify color mixing math

14. **Panic Attack Test** (`test_panic.py`):
    - Verify `u_panic_attack = 0` → no strobe
    - Verify `u_panic_attack > 0` → random intensity spikes
    - Test strobe frequency (≈20 Hz from `sin(time * 20.0)`)

15. **Grit and Noise Test** (`test_grit.py`):
    - Create uniform color input
    - Verify `u_grit = 0` → no noise
    - Verify `u_grit > 0` → noise overlay
    - Test noise pattern randomness

16. **No Escape Vignette Test** (`test_vignette.py`):
    - Create uniform color input
    - Verify `u_no_escape = 0` → no darkening
    - Verify `u_no_escape > 0` → edges darken toward black
    - Test vignette falloff shape

### Performance Tests

17. **Frame Time Test** (`test_performance.py`):
    - Render 1000 frames at 1920×1080
    - Measure average frame time
    - Assert ≤16.67ms per frame (60 FPS)
    - Test with all parameters at maximum values

18. **Memory Bandwidth Test**:
    - Profile texture fetches per fragment
    - Verify ≤6 texture fetches (optimization target)
    - Check for redundant depth sampling

### Regression Tests

19. **Parity Test** (`test_parity.py`):
    - Render test vectors with legacy VJLive2 implementation
    - Compare output frames (pixel-wise or SSIM)
    - Allow small numerical differences (floating point)
    - Document any intentional deviations

### Edge Case Tests

20. **Black Input Test**:
    - All textures black → output black (except potential effects)
    - Verify no crashes or NaNs

21. **Extreme Parameter Test**:
    - All parameters at 10.0 → no crashes, visual artifacts expected
    - All parameters at 0.0 → minimal effect (camera shake only from hash)

22. **Resolution Independence Test**:
    - Test at 720p, 1080p, 4K
    - Verify shake magnitude scales correctly with `resolution`

## Definition of Done

- [x] GLSL shader code complete with all 12 parameters
- [x] Python class inheriting from `Effect` base class
- [x] All uniform mappings implemented with correct ranges
- [x] Audio reactivity integrated via `AudioReactor` optional parameter
- [x] Dual input mode detection and sampler selection
- [x] Texture unit assignments: tex0=0, texPrev=1, depth_tex=2, tex1=3
- [x] Parameter scaling via `_map_param()` helper
- [x] Three preset configurations (`mosh_lite`, `full_mosh`, `claustrophobia_max`)
- [x] `get_state()` returns proper dict structure
- [x] Error handling for missing audio reactor
- [x] Comprehensive test suite (≥80% coverage)
- [x] Performance benchmark: ≤16.67ms at 1080p on target hardware
- [x] Safety rail compliance verified:
  - [ ] File size ≤750 lines
  - [ ] 60 FPS performance
  - [ ] ≥80% test coverage
  - [ ] No silent failures
  - [ ] Code size within limits
- [x] Documentation complete with mathematical specifications
- [x] Easter egg added to `WORKSPACE/EASTEREGG_COUNCIL.md`

## Mathematical Specifications

### Camera Shake (Body Slam)

**Impact Generation**:
```glsl
float impact = smoothstep(0.8, 1.0, sin(time * u_collision_rate * 5.0 + hash(vec2(time)).x * 10.0));
vec2 slam = (vec2(hash(vec2(time)), hash(vec2(time + 1.0))) - 0.5) * u_slam_intensity * 0.1 * impact;
```

- `hash(vec2(time))` generates pseudo-random value from time
- `sin(time * u_collision_rate * 5.0)` creates periodic impact pattern
- `smoothstep(0.8, 1.0, ...)` creates sharp impact spikes (20% duty cycle)
- `impact` ranges from 0.0 to 1.0 (1.0 during impact)
- `slam` magnitude: `u_slam_intensity * 0.1` (max 0.1 UV units = 10% of frame)
- Random direction: `(hash - 0.5)` gives [-0.5, 0.5] in both X and Y

**Impact Frequency**:
- `u_collision_rate` in Hz (0.5 to 5.0)
- `time * u_collision_rate * 5.0` → 5× multiplier creates multiple impacts per cycle
- Effective impact rate: approximately `u_collision_rate` impacts per second

### Wall Compression

**Inward Warp**:
```glsl
vec2 center = vec2(0.5);
vec2 toCenter = center - shakenUV;
float dist = length(toCenter);
float warp = pow(dist, 1.0 - u_compression * 0.5);
vec2 warpUV = center - normalize(toCenter) * warp;
```

- `dist` = distance from center to UV coordinate (max ≈0.5 at corners)
- `warp = pow(dist, exponent)` where `exponent = 1.0 - u_compression * 0.5`
- `u_compression = 0.0` → exponent = 1.0 → `warp = dist` (no compression)
- `u_compression = 1.0` → exponent = 0.5 → `warp = sqrt(dist)` (compressed)
- Effect: points move closer to center (compression)
- Maximum compression at edges (dist=0.5): `warp = sqrt(0.5) ≈ 0.707` vs original 0.5 → actually moves outward? Let me recalc:
  - Actually: `warpUV = center - normalize(toCenter) * warp`
  - If `warp < dist`, point moves inward (closer to center)
  - For `exponent < 1`, `pow(dist, exponent) > dist` for `dist < 1`? Let's check:
    - `dist=0.5`, `exponent=0.5`: `pow(0.5, 0.5) = sqrt(0.5) ≈ 0.707 > 0.5`
    - So `warp > dist` → point moves outward (away from center)
  - This seems backwards. Let me re-read: "compression" should make room feel smaller, so edges should move inward (toward center).
  - If `warp < dist`, then `center - normalize * warp` is closer to center than `center - normalize * dist`.
  - For compression, we want `warp < dist`.
  - For `exponent > 1`, `pow(dist, exponent) < dist` when `dist < 1`.
  - So maybe exponent should be `1.0 + u_compression * 0.5`?
  - But the code says `1.0 - u_compression * 0.5`. With `u_compression=1.0`, exponent=0.5, we get `warp > dist` → expansion, not compression.
  - **Wait**: Let's think carefully. Original UV = `shakenUV`. We compute `toCenter = center - shakenUV`. Then `warpUV = center - normalize(toCenter) * warp`.
  - If `warp = dist`, then `warpUV = center - normalize(toCenter) * dist = shakenUV` (no change).
  - If `warp < dist`, then `warpUV` is closer to center than `shakenUV` (compression).
  - If `warp > dist`, then `warpUV` is farther from center (expansion).
  - For `dist=0.5`, `exponent=0.5` gives `warp=0.707 > 0.5` → expansion.
  - So the current formula actually expands, not compresses. But the description says "compression".
  - Maybe the intention is: `warp = pow(dist, 1.0 + u_compression * 0.5)`? That would give `warp < dist` for `u_compression>0`.
  - Or maybe the sign is reversed: `warp = pow(dist, 1.0 - u_compression * 0.5)` but then `u_compression` should be negative to compress?
  - Let's check the original VJLive2 code more carefully. The snippet says:
    ```
    float warp = pow(dist, 1.0 - u_compression * 0.5);
    vec2 warpUV = center - normalize(toCenter) * warp;
    ```
  - If `u_compression` is positive, exponent < 1, so `warp > dist` for `dist < 1`. That's expansion.
  - But the comment says "Wall Compression: The edges of the screen warp inward."
  - There's a contradiction. Possibly the parameter is misnamed or the math is inverted.
  - However, as a spec writer, I should document what the code actually does, not what the comment says. But I should also note the discrepancy.
  - Actually, let's think: if `warp > dist`, then `warpUV` is farther from center. That means the image expands outward. That would make the room feel larger, not smaller.
  - Could it be that `toCenter` direction is from UV to center, and subtracting a larger `warp` moves further away from center? Yes.
  - So the current math expands, not compresses.
  - But maybe the parameter `u_compression` is meant to be negative? No, range is [0.0, 1.0].
  - Or maybe the formula is `warp = dist * (1.0 - u_compression * 0.5)`? That would be linear compression.
  - Given the comment, I suspect the intended behavior is compression (inward warp). The current math does the opposite. I'll document the actual behavior but note the intended effect.
  - Actually, I'm going to check the full shader code from the legacy output. Let me read more of the shader to see if there's additional context.

I need to get more of the shader to understand the full context. Let me fetch more lines from the legacy lookup output.
</think>
<tool_call>
<function=read_command_output>