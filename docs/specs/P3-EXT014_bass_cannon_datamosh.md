# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT014_bass_cannon_datamosh.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

## Task: P3-EXT014 — BassCannonDatamoshEffect

## Description
The BassCannonDatamoshEffect implements a real-time video distortion effect that simulates a sonic weapon called the "Bass Cannon." It takes dual video inputs and a depth map to generate shockwave-based visual distortions triggered by audio bass levels. When bass intensity exceeds a threshold, it emits radial shockwaves that displace pixels, create muzzle flash effects, simulate recoil, and scatter debris across the frame. The effect is designed for aggressive, high-energy visuals with dynamic response to input audio.

## What This Module Does
- Implements a real-time video distortion effect that simulates a sonic weapon called the "Bass Cannon"
- Takes dual video inputs (tex0 and tex1) and a depth map as inputs
- Generates shockwave-based visual distortions triggered by audio bass levels
- Emits radial shockwaves that displace pixels when bass intensity exceeds a threshold
- Creates muzzle flash effects that blind the sensor on impact
- Simulates recoil where the entire frame kicks back
- Scatters debris across the frame as pixels shatter
- Designed for aggressive, high-energy visuals with dynamic response to input audio
- Integrates with the VJLive3 effect system as a core distortion module

## What This Module Does NOT Do
- Does NOT handle audio processing beyond reading audio level input
- Does NOT provide audio output or visualization - purely a visual effect
- Does NOT handle file I/O or persistence - relies on external systems for data storage
- Does NOT provide network communication - operates as a standalone effect module
- Does NOT support real-time parameter modulation beyond what's defined in config
- Does NOT handle user interface elements directly - focuses on visual output

## Integration
The BassCannonDatamoshEffect integrates with the VJLive3 node graph as a core distortion effect. It connects to:
- `vjlive3.core.effect_manager.Effect` for base effect functionality
- `vjlive3.utils.texture_utils` for texture sampling and resolution handling
- Dual video input nodes (tex0 and tex1) for source material
- Depth map input for spatial distortion calculations
- Audio input nodes for bass level detection
- Output nodes for processed frame delivery

## Performance
The BassCannonDatamoshEffect is optimized for real-time performance:
- GPU-accelerated shader implementation with minimal CPU overhead
- O(1) time complexity per frame processing
- Suitable for 60+ FPS operation on modern hardware
- Memory usage: ~2KB per instance (excluding texture data)
- Requires OpenGL 3.3+ or equivalent graphics API support
- Can be used in headless environments without graphics capabilities (though visual output will be minimal)

## Error Cases
The BassCannonDatamoshEffect handles errors gracefully:
- Invalid parameter values (negative thresholds, zero resolution) raise `ValueError` with descriptive messages
- Missing required texture inputs raise `ResourceUnavailableError` with clear guidance
- Shader compilation failures raise `ShaderCompileError` with diagnostic information
- Invalid audio level values (outside [0.0, 1.0]) are clamped to valid range with warning
- Memory allocation failures raise `MemoryError` with system-level diagnostics
- Cleanup operations always succeed and release resources properly

## Configuration Schema
The BassCannonDatamoshEffect uses a detailed configuration schema with all parameters:

| Field | Type | Default | Range | Description |
|-------|------|---------|-------|-------------|
| `u_cannon_power` | `float` | 5.0 | (0.0, 10.0) | Intensity of the shockwave |
| `u_shockwave_speed` | `float` | 5.0 | (0.1, 20.0) | Speed of the blast wavefront |
| `u_recoil` | `float` | 3.0 | (0.0, 10.0) | Screen kickback intensity |
| `u_muzzle_flash` | `float` | 4.0 | (0.0, 10.0) | Whiteout intensity on impact |
| `u_debris_scatter` | `float` | 4.0 | (0.0, 10.0) | Pixel shattering effect strength |
| `u_bass_threshold` | `float` | 3.0 | (0.0, 10.0) | Input level to trigger fire |
| `u_impact_radius` | `float` | 5.0 | (0.1, 20.0) | Size of the cannon blast radius |
| `u_distortion` | `float` | 6.0 | (0.0, 10.0) | UV warping amount for pixel displacement |
| `u_chroma_blast` | `float` | 5.0 | (0.0, 10.0) | Color separation on blast for chromatic aberration |
| `u_thermal_exhaust` | `float` | 3.0 | (0.0, 10.0) | Heat distortion feedback effect |
| `u_depth_penetration` | `float` | 8.0 | (0.1, 50.0) | How far the blast travels into depth space |
| `u_decay` | `float` | 6.0 | (0.1, 20.0) | How fast the blast fades over distance |
| `u_mix` | `float` | 0.7 | (0.0, 1.0) | Blend factor for combining processed and original frames |

## State Management
- **Per-frame state**: The effect processes each frame independently based on current inputs
- **Persistent state**: Configuration parameters remain constant unless explicitly changed
- **Init-once**: Shader programs initialize once during effect startup
- **Thread safety**: Not thread-safe; should be used from a single update thread
- **Reset behavior**: Effect state resets when configuration changes or effect is restarted

## GPU Resources
The BassCannonDatamoshEffect is GPU-accelerated:
- Requires shader compilation with OpenGL 3.3+ or equivalent
- Uses multiple texture units (up to 4 simultaneous texture inputs)
- Requires framebuffer objects for intermediate rendering
- Uses texture sampling with UV coordinate manipulation
- Requires ~1KB of uniform buffer space for parameters
- Can be used in headless environments without graphics capabilities (though visual output will be minimal)

## Public Interface
```python
class BassCannonDatamoshEffect(Effect):
    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        self._setup_shader_parameters()

    def process_frame(self, frame_data: Dict[str, Any], audio_level: float) -> Dict[str, Any]:
        """
        Process a video frame with bass-triggered distortion.
        
        Args:
            frame_data: Dictionary containing texture inputs (tex0, tex1, depth_tex), 
                        and metadata like resolution
            audio_level: Current audio input level (0.0 to 1.0) used to trigger shockwave
        
        Returns:
            Processed frame data with applied distortion effects
        """
        return self._apply_bass_cannon_effect(frame_data, audio_level)

    def _setup_shader_parameters(self):
        """Initialize uniform parameters from config for shader use."""
        pass

    def get_metadata(self) -> Dict[str, Any]:
        """Return metadata describing the effect's visual style and behavior."""
        return {
            "tags": ["bass", "weapon", "shockwave", "aggressive", "impact", "dubstep", "distortion"],
            "mood": ["violent", "powerful", "explosive", "overwhelming", "heavy"],
            "visual_style": ["shockwave-simulation", "sonic-boom", "camera-shake", "impact-frames"]
        }
```

## Inputs and Outputs
| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `config` | `Dict[str, Any]` | Configuration dictionary for effect parameters | Must include all parameters listed in Configuration Schema |
| `frame_data` | `Dict[str, Any]` | Contains texture inputs: tex0 (Video A), tex1 (Video B), depth_tex (depth map) and resolution | Must include all textures; resolution must be valid (width > 0, height > 0) |
| `audio_level` | `float` | Current audio input level between 0.0 and 1.0 | Range: [0.0, 1.0]; below threshold does not trigger effect |
| `output_frame` | `Dict[str, Any]` | Processed frame with applied distortion effects | Must contain updated texture outputs (e.g., distorted tex0) and metadata |

## Dependencies
- **External libraries needed (and what happens if they are missing):**
  - `core.effects.shader_base` — used for shader-based effect rendering — fallback: basic video pass
- **Internal modules this depends on:**
  - `vjlive3.core.effect_manager.Effect` — base class for all effects
  - `vjlive3.utils.texture_utils` — for texture sampling and resolution handling

## Test Plan
| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | Module starts without crashing if hardware inputs (depth, video) are absent or missing |
| `test_basic_operation` | Core effect applies shockwave distortion when audio level exceeds threshold |
| `test_error_handling` | Invalid input values (e.g., negative audio_level, zero resolution) raise appropriate exceptions |
| `test_cleanup` | Effect releases GPU resources and shader uniforms cleanly on stop() call |
| `test_parameter_range_validation` | All uniform parameters are clamped to valid ranges during initialization |

**Minimum coverage:** 80% before task is marked done.

## Definition of Done
- [ ] Spec reviewed (by Manager or User before code starts)  
- [ ] All tests listed above pass  
- [ ] No file over 750 lines  
- [ ] No stubs in code  
- [ ] Verification checkpoint box checked  
- [ ] Git commit with `[Phase-X] P3-EXT014: bass_cannon_datamosh effect implementation` message  
- [ ] BOARD.md updated  
- [ ] Lock released  
- [ ] AGENT_SYNC.md handoff note written  

## LEGACY CODE REFERENCES
### vjlive1/plugins/vdatamosh/bass_cannon_datamosh.py (L1-20)
```python
"""
Bass Cannon Datamosh — Sonic Weapon of Mass Distortion

DUAL VIDEO INPUT: tex0 = Video A, tex1 = Video B

"Fire the Bass Cannon."

This effect turns your depth camera into a sonic weapon. Every bass hit
fires a shockwave through the depth map. The center of the screen is the
cannon muzzle. Shockwaves distort, displace, and shatter pixels as they
travel outward. The harder the bass, the bigger the blast.

Includes "Recoil" simulation where the entire frame kicks back, and
"Muzzle Flash" that blinds the sensor.

Metadata:
- Tags: bass, weapon, shockwave, aggressive, impact, dubstep, distortion
- Mood: violent, powerful, explosive, overwhelming, heavy
- Visual Style: shockwave-simulation, sonic-boom, camera-shake, impact-frames
```

### vjlive1/plugins/vdatamosh/bass_cannon_datamosh.py (L17-36)
```python
Texture unit layout:
  Unit 0: tex0 (Video A)
  Unit 1: texPrev (previous frame)
  Unit 2: depth_tex (depth map)
  Unit 3: tex1 (Video B)
```

### vjlive1/plugins/vdatamosh/bass_cannon_datamosh.py (L33-52)
```python
FRAGMENT = """
#version 330 core
in vec2 v_uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform sampler2D texPrev;
uniform sampler2D depth_tex;
uniform sampler2D tex1;
uniform float time;
uniform vec2 resolution;

uniform float u_cannon_power;      // Intensity of the shockwave
uniform float u_shockwave_speed;   // Speed of the blast
uniform float u_recoil;            // Screen kickback intensity
uniform float u_muzzle_flash;      // Whiteout intensity on impact
uniform float u_debris_scatter;    // Pixel shattering
uniform float u_bass_threshold;    // Input level to trigger fire
uniform float u_impact_radius;     // Size of the cannon
"""
```

### vjlive1/plugins/vdatamosh/bass_cannon_datamosh.py (L49-68)
```python
uniform float u_muzzle_flash;      // Whiteout intensity on impact
uniform float u_debris_scatter;    // Pixel shattering
uniform float u_bass_threshold;    // Input level to trigger fire
uniform float u_impact_radius;     // Size of the cannon
uniform float u_distortion;        // UV warping amount
uniform float u_chroma_blast;      // Color separation on blast
uniform float u_thermal_exhaust;   // Heat distortion after-effect
uniform float u_depth_penetration; // How far the blast travels
uniform float u_decay;             // How fast the blast fades
uniform float u_mix;

float hash(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}
```

### vjlive1/plugins/vdatamosh/bass_cannon_datamosh.py (L65-84)
```python
void main() {
    vec2 uv = v_uv;
    vec2 texel = 1.0 / resolution;
    bool hasDual = (texture(tex1, vec2(0.5)).r + texture(tex1, vec2(0.5)).g + texture(tex1, vec2(0.5)).b) > 0.001;
    float depth = texture(depth_tex, uv).r;

    // Center uv for radial calculations
    vec2 p = uv - 0.5;
    float r = length(p);
    float a = atan(p.y, p.x);

    // BASS CANNON LOGIC
    // We simulate a shockwave based on time and power
    // Since we don't have accumulators in this simple shader pass, 
    // we use a repeating wave function modulated by power.
    
    // Shockwave wavefront
    float wavePhase = time * u_shockwave_speed;
```

[NEEDS RESEARCH] — Shader output handling and blending logic

## Notes
- The legacy implementation used parameters like `cannon_power`, `shockwave_speed`, `recoil`, etc. that map to the current configuration schema
- The shader implementation must maintain numerical stability across parameter ranges
- Metadata must match legacy output format for compatibility with existing systems
- The effect should handle dual video inputs gracefully, with fallback behavior when only one input is available
- The legacy code contains TODO comments about shader output handling that need to be addressed in implementation
