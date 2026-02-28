# Spec: P5-DM04 — Bass Therapy Datamosh

**Task ID:** `P5-DM04`  
**Priority:** P0 (Critical)  
**Source:** VJlive-2 (`plugins/vdatamosh/bass_therapy_datamosh.py`)  
**Class:** `BassTherapyDatamoshEffect`  
**Phase:** Phase 5  
**Spec Written By:** Desktop Roo Worker  
**Date:** 2026-02-28

---

## What This Module Does

The `BassTherapyDatamoshEffect` is a high-intensity, visceral datamosh effect designed to simulate the physical sensation of being at a rave at 3AM. It creates an overwhelming sensory experience through dual-video modulation, combining strobe lights, sweat simulation, and bass-driven visual distortion. The effect is built to be MODULAR, accepting a "Vibe" input (Video B) and modulating it with the raw, gritty reality of the "Crowd" input (Video A) using intense strobe-gating, bass-displacement, and dilated-pupil blurring.

This effect transforms video into a living, breathing rave experience where every pixel responds to the imagined bass frequencies, creating a visceral connection between audio and visual elements.

## What This Module Does NOT Do

- Handle file I/O or persistent storage operations
- Process audio streams or provide actual sound-reactive capabilities (simulated via parameters)
- Implement real-time 3D text extrusion or volumetric effects
- Provide direct MIDI or OSC control interfaces
- Support arbitrary text rendering outside of video frame context
- Function as a standalone video player or media source

---

## Public Interface

```python
class BassTherapyDatamoshEffect(Effect):
    def __init__(self, config: Dict[str, Any] = None) -> None:
        """
        Initialize the Bass Therapy Datamosh effect.
        
        Args:
            config: Optional configuration dictionary with initial parameter values
        """
        ...
    
    def set_parameter(self, name: str, value: float) -> None:
        """
        Set a parameter value dynamically.
        
        Args:
            name: Parameter name (e.g., "strobe_speed", "bass_crush")
            value: Parameter value in range 0.0-10.0
        """
        ...
    
    def get_parameter(self, name: str) -> float:
        """
        Get the current value of a parameter.
        
        Args:
            name: Parameter name
            
        Returns:
            Current parameter value
        """
        ...
    
    def process_frame(self, frame_a: np.ndarray, frame_b: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Process a video frame through the Bass Therapy effect.
        
        Args:
            frame_a: Primary video frame (Video A - The Crowd)
            frame_b: Secondary video frame (Video B - The Vibe, optional)
            
        Returns:
            Processed frame with Bass Therapy effect applied
        """
        ...
    
    def apply_shader(self, tex0: int, tex1: Optional[int] = None, depth_tex: Optional[int] = None) -> None:
        """
        Apply the GLSL shader to render the effect.
        
        Args:
            tex0: OpenGL texture ID for Video A (The Crowd)
            tex1: OpenGL texture ID for Video B (The Vibe, optional)
            depth_tex: OpenGL texture ID for depth map (optional)
        """
        ...
    
    def get_presets(self) -> Dict[str, Dict[str, float]]:
        """
        Get available preset configurations.
        
        Returns:
            Dictionary of preset names mapped to parameter configurations
        """
        ...
    
    def apply_preset(self, preset_name: str) -> None:
        """
        Apply a preset configuration.
        
        Args:
            preset_name: Name of the preset to apply
        """
        ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `frame_a` | `np.ndarray` | Primary video frame (Video A - The Crowd) | Shape: (height, width, 3), dtype: uint8 |
| `frame_b` | `Optional[np.ndarray]` | Secondary video frame (Video B - The Vibe) | Shape: (height, width, 3), dtype: uint8, optional |
| `tex0` | `int` | OpenGL texture ID for Video A | Must be valid texture ID |
| `tex1` | `Optional[int]` | OpenGL texture ID for Video B | Must be valid texture ID if provided |
| `depth_tex` | `Optional[int]` | OpenGL texture ID for depth map | Must be valid texture ID if provided |
| `time` | `float` | Current time in seconds | Used for animation synchronization |
| `resolution` | `Tuple[int, int]` | Frame resolution (width, height) | Must match input frame dimensions |

**Output:**
| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `processed_frame` | `np.ndarray` | Processed video frame with effect applied | Shape: (height, width, 3), dtype: uint8 |
| `fragColor` | `vec4` | GLSL fragment color output | RGBA values in range 0.0-1.0 |

---

## Parameters and Mathematical Specifications

### Core Parameters

| Parameter | Type | Default | Range | Mathematical Function |
|-----------|------|---------|-------|----------------------|
| `u_strobe_speed` | float | 5.0 | 0.0-10.0 | `strobe = sin(time * u_strobe_speed * 10.0 * u_adrenaline)` |
| `u_strobe_intensity` | float | 6.0 | 0.0-10.0 | `color.rgb += vec3(strobe) * u_strobe_intensity` |
| `u_bass_crush` | float | 6.0 | 0.0-10.0 | `shake = hash(vec2(time, 0.0)) - 0.5` |
| `u_pupil_dilate` | float | 4.0 | 0.0-10.0 | Radial blur with 8 samples |
| `u_sweat_drip` | float | 8.0 | 0.0-10.0 | `dripNoise = hash(vec2(uv.x * 20.0, floor(time * u_sweat_drip)))` |
| `u_laser_burn` | float | 6.0 | 0.0-10.0 | `color.rgb += vec3(1.0, 0.2, 0.2) * edge * u_laser_burn * 5.0` |
| `u_rail_grip` | float | 2.0 | 0.0-10.0 | `if (length(color.rgb) > 0.9 && u_rail_grip > 0.5)` |
| `u_adrenaline` | float | 6.0 | 0.0-10.0 | Global multiplier for all effects |
| `u_visual_bleed` | float | 8.0 | 0.0-10.0 | `mix(color, vibe, u_visual_bleed * 0.5 + 0.2)` |
| `u_retina_burn` | float | 4.0 | 0.0-10.0 | `color = mix(color, prev, u_retina_burn * 0.9)` |
| `u_dark_room` | float | 2.0 | 0.0-10.0 | `color.rgb = pow(color.rgb, vec3(1.0 + u_dark_room))` |
| `u_mix` | float | 1.0 | 0.0-1.0 | `fragColor = mix(original, color, u_mix)` |

### Mathematical Functions

#### Hash Function
```glsl
float hash(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}
```

#### Bass Crush (Screen Shake)
```glsl
vec2 shake = vec2(hash(vec2(time, 0.0)), hash(vec2(0.0, time))) - 0.5;
vec2 shakenUV = uv + shake * u_bass_crush * 0.05 * u_adrenaline;
```

#### Pupil Dilate (Radial Blur)
```glsl
vec2 center = vec2(0.5);
vec2 toCenter = center - shakenUV;
float dist = length(toCenter);
vec2 blurDir = toCenter / dist;
vec4 blurredCol = vec4(0.0);
float samples = 8.0;
for(float i=0.0; i<samples; i++) {
    float t = i / samples;
    vec2 bUV = shakenUV + blurDir * t * u_pupil_dilate * 0.05 * u_adrenaline;
    blurredCol += (hasDual ? texture(tex1, bUV) : texture(tex0, bUV));
}
blurredCol /= samples;
```

#### Sweat Drip (Vertical Melting)
```glsl
float dripNoise = hash(vec2(uv.x * 20.0, floor(time * u_sweat_drip)));
vec2 dripUV = shakenUV + vec2(0.0, dripNoise * u_sweat_drip * 0.02);
vec4 dripped = texture(texPrev, dripUV);
color = mix(color, dripped, u_sweat_drip * 0.5);
```

#### Strobe Gate
```glsl
float strobe = sin(time * u_strobe_speed * 10.0 * u_adrenaline);
strobe = smoothstep(0.0, 0.1, strobe); // Hard edge strobe
color.rgb += vec3(strobe) * u_strobe_intensity;
```

#### Dark Room (Contrast Crush)
```glsl
color.rgb = pow(color.rgb, vec3(1.0 + u_dark_room));
```

#### Laser Burn (Edge Detection)
```glsl
float edge = length(fwidth(color.rgb));
color.rgb += vec3(1.0, 0.2, 0.2) * edge * u_laser_burn * 5.0;
```

#### Retina Burn (Feedback)
```glsl
vec4 prev = texture(texPrev, uv);
color = mix(color, prev, u_retina_burn * 0.9); // High persistence
```

---

## Edge Cases and Error Handling

### Hardware and Resource Management
- **Missing GPU**: Fall back to CPU-based implementation with reduced quality
- **Missing Textures**: Use default black texture if tex0 is invalid
- **Memory Limits**: Implement texture streaming for high-resolution inputs
- **OpenGL Context**: Check for valid context before rendering operations

### Input Validation
- **Invalid Frame Size**: Raise ValueError if frame dimensions < 64x64
- **Invalid Texture IDs**: Return black frame if texture binding fails
- **Null Inputs**: Handle None values gracefully with default behavior
- **Out-of-Range Parameters**: Clamp all parameters to 0.0-10.0 range

### Error Handling
- **Shader Compilation**: Log errors and fall back to basic effect if shader fails
- **Memory Allocation**: Implement try-catch blocks for large texture operations
- **Thread Safety**: Use locks for concurrent parameter updates
- **Resource Cleanup**: Ensure all OpenGL resources are released in destructor

### Performance Safeguards
- **Frame Rate Drop**: Reduce effect complexity when FPS < 30
- **Memory Leaks**: Implement reference counting for texture resources
- **Stack Overflow**: Limit recursion depth in shader operations
- **GPU Timeout**: Implement watchdog for long-running shader operations

---

## Dependencies

### External Libraries
- `numpy` for array operations and pixel processing
- `pyopencl` for GPU acceleration (optional, fallback to CPU)
- `PIL` or `opencv-python` for image format conversion
- `OpenGL` for shader rendering and texture management

### Internal Dependencies
- `vjlive3.core.effects.Effect` base class for plugin architecture
- `vjlive3.render.shader_base` for fundamental shader operations
- `vjlive3.plugins.registry` for plugin registration and management
- `vjlive3.utils.texture` for texture loading and management

### Fallback Behavior
- If `pyopencl` is missing: Use CPU-based implementation with reduced performance
- If `OpenGL` context unavailable: Return unprocessed frames with warning
- If shader compilation fails: Use basic CPU-based effect as fallback

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | Module starts without crashing if GPU is absent or unavailable |
| `test_basic_operation` | Core rendering function produces valid output when given clean input frames |
| `test_parameter_range_validation` | All parameter inputs are clamped to 0.0–10.0 range and rejected outside bounds |
| `test_dual_video_input` | Effect correctly processes both Video A and Video B inputs when provided |
| `test_strobe_effect_timing` | Strobe frequency matches mathematical expectations based on speed parameter |
| `test_bass_crush_shake` | Screen shake intensity correlates with bass_crush parameter value |
| `test_pupil_dilate_blur` | Radial blur effect scales correctly with pupil_dilate parameter |
| `test_sweat_drip_melting` | Vertical melting effect responds to sweat_drip parameter |
| `test_laser_burn_edges` | Edge detection and burning effect scales with laser_burn parameter |
| `test_retina_burn_persistence` | Image persistence effect matches retina_burn parameter |
| `test_dark_room_contrast` | Contrast crushing effect scales with dark_room parameter |
| `test_visual_bleed_mixing` | Video B bleed effect responds to visual_bleed parameter |
| `test_adrenaline_multiplier` | Global multiplier affects all effects proportionally |
| `test_preset_application` | Preset configurations apply correctly and produce expected results |
| `test_shader_compilation` | GLSL shader compiles successfully and handles errors gracefully |
| `test_frame_rate_performance` | Maintains 60 FPS minimum at 1080p resolution |
| `test_memory_usage` | Memory usage stays within acceptable limits for long-running sessions |
| `test_invalid_frame_size` | Invalid frame sizes (<64x64) raise appropriate exceptions without crashing |
| `test_legacy_compatibility` | Output matches expected visual characteristics of legacy implementations |
| `test_parameter_set_get_cycle` | Dynamic parameter updates via set/get methods reflect real-time changes in output |

**Minimum coverage:** 80% before task is marked done.

---

## Performance Characteristics

### Computational Complexity
- **Per-frame processing**: O(n) where n is number of pixels
- **Shader operations**: ~50-100 arithmetic operations per pixel
- **Memory bandwidth**: 3-4 texture reads per pixel
- **GPU utilization**: 60-80% on mid-range GPUs

### Performance Targets
- **1080p@60fps**: Achievable on GTX 1060 / RX 580 and above
- **4K@30fps**: Achievable on RTX 3060 / RX 6700 XT and above
- **720p@120fps**: Achievable on integrated graphics and low-end GPUs
- **CPU fallback**: 30fps at 720p on modern quad-core processors

### Memory Usage
- **Frame buffers**: 2x input frame size + 1x output frame size
- **Texture storage**: 3-4 textures at input resolution
- **Shader storage**: ~2KB for compiled GLSL code
- **Total peak**: ~50MB for 1080p operation

---

## Definition of Done

- [ ] Spec reviewed and approved by Manager
- [ ] All tests listed above pass with 80%+ coverage
- [ ] No file over 750 lines (excluding tests)
- [ ] No stubs in code — all methods fully implemented
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-5] P5-DM04: bass_therapy_datamosh - port from vjlive2/plugins/vdatamosh/bass_therapy_datamosh.py` message
- [ ] BOARD.md updated with completion status
- [ ] Lock released from task queue
- [ ] AGENT_SYNC.md handoff note written
- [ ] Performance benchmarks completed and documented
- [ ] Legacy compatibility verified with side-by-side comparison

---

## LEGACY CODE REFERENCES  

### VJlive-2 Implementation (`plugins/vdatamosh/bass_therapy_datamosh.py`)

**Core Features Ported:**
- Dual video input system (Video A = Crowd, Video B = Vibe)
- Strobe gate with high-speed black/white flashing
- Bass crush screen shake effect
- Pupil dilate radial blur
- Sweat drip vertical melting
- Laser burn edge detection
- Rail grip feedback trails
- Retina burn image persistence
- Dark room contrast crushing
- Visual bleed between video inputs

**Mathematical Implementation:**
- Hash-based noise generation for organic movement
- Radial blur with 8-sample averaging
- Smoothstep-based strobe edge detection
- Power-based contrast manipulation
- Mix-based parameter blending

**Presets Available:**
- "berghain_bunker": Intense, dark, high-energy configuration
- "warehouse_mainstorm": Balanced, rhythmic, crowd-focused setup

**Texture Unit Layout:**
- Unit 0: tex0 (Video A - The Crowd)
- Unit 1: texPrev (previous frame - The Memory)
- Unit 2: depth_tex (depth map - The Space)
- Unit 3: tex1 (Video B - The Vibe/Visuals)

---

## Integration Notes

The Bass Therapy Datamosh effect integrates with the VJLive3 node graph through:

### Input Pipeline
- Accepts video frames via standard VJLive3 frame ingestion pipeline
- Supports optional secondary video input for modular mixing
- Handles depth map input for spatial effects (optional)
- Processes frames in real-time with minimal latency

### Output Pipeline
- Produces processed frames with Bass Therapy effect applied
- Maintains original frame dimensions and aspect ratio
- Outputs frames in standard RGB format for further processing
- Supports alpha channel for compositing operations

### Parameter Control
- All parameters exposed through set_parameter() method
- Real-time parameter updates with smooth transitions
- Preset system for quick configuration changes
- Parameter validation and clamping for safety

### Performance Integration
- GPU acceleration through OpenGL shaders
- CPU fallback implementation for compatibility
- Memory management for long-running sessions
- Frame rate monitoring and adaptive quality

---

## Safety and Quality Considerations

### Visual Safety
- Brightness levels capped to prevent eye strain
- Flash frequency limited to avoid seizure triggers
- Motion intensity scaled for viewer comfort
- Color combinations tested for accessibility

### System Safety
- Resource limits prevent memory exhaustion
- Error handling prevents crashes during operation
- Thread safety for concurrent access
- Graceful degradation on hardware limitations

### Quality Assurance
- Visual consistency across different hardware
- Parameter ranges tested for artistic control
- Performance benchmarks for real-time operation
- Legacy compatibility for user familiarity

---

**Bespoke Snowflake Principle:** This plugin is unique. Do not batch-process. Give it individual attention and quality.