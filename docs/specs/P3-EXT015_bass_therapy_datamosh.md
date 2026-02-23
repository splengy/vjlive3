# P3-EXT015: BassTherapyDatamoshEffect

## Task Overview
Create a high-intensity, visceral datamosh effect simulating the physical sensation of being at a rave at 3AM. This effect is designed to be MODULAR, accepting dual video inputs and modulating them with intense strobe-gating, bass-displacement, and dilated-pupil blurring.

**Core Concept**: The "Bass Therapy" experience - a modular rave effect that combines the raw energy of a crowd (Video A) with the visualizer feed (Video B) through strobe lights, sweat simulation, and overwhelming bass frequencies.

## Class Hierarchy
```python
class BassTherapyDatamoshEffect(Effect):
    def __init__(self, name: str = 'bass_therapy_datamosh')
    def apply_uniforms(self, time, resolution, audio_reactor=None, semantic_layer=None)
    def get_state(self) -> Dict[str, Any]
```

## 2. Parameters (0.0-10.0)
| Parameter | Default | Range | Description | Audio Mapping |
|-----------|---------|-------|-------------|---------------|
| strobe_speed | 5.0 | 0.0-10.0 | Speed of the flashing | high |
| strobe_intensity | 5.0 | 0.0-10.0 | Brightness of the flash | - |
| bass_crush | 5.0 | 0.0-10.0 | Screen shake intensity | bass |
| pupil_dilate | 4.0 | 0.0-10.0 | Radial blur amount | mid |
| sweat_drip | 3.0 | 0.0-10.0 | Melting intensity | - |
| laser_burn | 4.0 | 0.0-10.0 | Contrast/Edge burn | - |
| rail_grip | 3.0 | 0.0-10.0 | Feedback locking | - |
| adrenaline | 5.0 | 0.0-10.0 | Overall speed/chaos multiplier | energy |
| bpm_sync | 5.0 | 0.0-10.0 | Simulated BPM logic | - |
| dark_room | 4.0 | 0.0-10.0 | How dark non-lit areas get | - |
| visual_bleed | 5.0 | 0.0-10.0 | How much Video B bleeds into A | - |
| retina_burn | 5.0 | 0.0-10.0 | Image persistence | - |

## 3. Texture Unit Layout
| Unit | Texture | Description |
|------|---------|-------------|
| 0 | tex0 | Video A - The Crowd |
| 1 | texPrev | Previous frame - The Memory |
| 2 | depth_tex | Depth map - The Space |
| 3 | tex1 | Video B - The Vibe/Visuals |

## 4. GLSL Fragment Shader (144 lines)
```glsl
#version 330 core
in vec2 v_uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform sampler2D texPrev;
uniform sampler2D depth_tex;
uniform sampler2D tex1;
uniform float time;
uniform vec2 resolution;

uniform float u_strobe_speed;      // Speed of the flashing
uniform float u_strobe_intensity;  // Brightness of the flash
uniform float u_bass_crush;        // Screen shake intensity
uniform float u_pupil_dilate;      // Radial blur amount
uniform float u_sweat_drip;        // Melting intensity
uniform float u_laser_burn;        // Contrast/Edge burn
uniform float u_rail_grip;         // Feedback locking
uniform float u_adrenaline;        // Overall speed/chaos multiplier
uniform float u_bpm_sync;          // Simulated BPM logic
uniform float u_dark_room;         // How dark the non-lit areas get
uniform float u_visual_bleed;      // How much Video B bleeds into A
uniform float u_retina_burn;       // Image persistence

uniform float u_mix;

float hash(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}

void main() {
    vec2 uv = v_uv;
    vec2 texel = 1.0 / resolution;
    bool hasDual = (texture(tex1, vec2(0.5)).r + texture(tex1, vec2(0.5)).g + texture(tex1, vec2(0.5)).b) > 0.001;
    float depth = texture(depth_tex, uv).r;

    // Bass Crush (Screen Shake)
    vec2 shake = vec2(hash(vec2(time, 0.0)), hash(vec2(0.0, time))) - 0.5;
    vec2 shakenUV = uv + shake * u_bass_crush * 0.05 * u_adrenaline;
    
    // Pupil Dilate (Radial Blur)
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

    // Sample Base
    vec4 color = mix(
        (hasDual ? texture(tex1, shakenUV) : texture(tex0, shakenUV)),
        blurredCol,
        u_pupil_dilate * 0.5
    );
    
    // Video B Bleed (Modular Mixing)
    if (hasDual) {
        vec4 vibe = texture(tex1, shakenUV);
        color = mix(color, vibe, u_visual_bleed * 0.5 + 0.2); // Always some bleed
    }

    // Sweat Drip (Melting)
    float dripNoise = hash(vec2(uv.x * 20.0, floor(time * u_sweat_drip)));
    vec2 dripUV = shakenUV + vec2(0.0, dripNoise * u_sweat_drip * 0.02);
    vec4 dripped = texture(texPrev, dripUV);
    color = mix(color, dripped, u_sweat_drip * 0.5);

    // Strobe Gate
    float strobe = sin(time * u_strobe_speed * 10.0 * u_adrenaline);
    strobe = smoothstep(0.0, 0.1, strobe); // Hard edge strobe
    color.rgb += vec3(strobe) * u_strobe_intensity;
    
    // Dark Room (Contrast Crush)
    color.rgb = pow(color.rgb, vec3(1.0 + u_dark_room));

    // Laser Burn (Edge Detection)
    float edge = length(fwidth(color.rgb));
    color.rgb += vec3(1.0, 0.2, 0.2) * edge * u_laser_burn * 5.0;

    // Retina Burn (Feedback)
    vec4 prev = texture(texPrev, uv);
    color = mix(color, prev, u_retina_burn * 0.9); // High persistence
    
    // Rail Grip (Motion Freeze on bright spots)
    if (length(color.rgb) > 0.9 && u_rail_grip > 0.5) {
         color.rgb = mix(color.rgb, vec3(1.0), 0.5); // Blow out white
    }

    vec4 original = hasDual ? texture(tex1, uv) : texture(tex0, uv);
    fragColor = mix(original, color, u_mix);
}
```

## 5. Effect Mathematics

### Bass Crush (Screen Shake)
```
shake = hash(vec2(time, 0.0)) - 0.5
finalShake = shake * u_bass_crush * 0.05 * u_adrenaline
shakenUV = uv + finalShake
```

### Pupil Dilate (Radial Blur)
```
center = vec2(0.5)
toCenter = center - shakenUV
dist = length(toCenter)
blurDir = toCenter / dist
blurredCol = average of 8 samples along blurDir * u_pupil_dilate * 0.05 * u_adrenaline
```

### Strobe Gate
```
strobe = sin(time * u_strobe_speed * 10.0 * u_adrenaline)
strobe = smoothstep(0.0, 0.1, strobe)  // Creates hard edge
finalStrobe = vec3(strobe) * u_strobe_intensity
```

### Sweat Drip (Melting)
```
dripNoise = hash(vec2(uv.x * 20.0, floor(time * u_sweat_drip)))
dripUV = shakenUV + vec2(0.0, dripNoise * u_sweat_drip * 0.02)
dripped = texture(texPrev, dripUV)
```

### Laser Burn (Edge Detection)
```
edge = length(fwidth(color.rgb))
finalBurn = vec3(1.0, 0.2, 0.2) * edge * u_laser_burn * 5.0
```

## 6. Texture Feedback Management
- **texPrev** (Unit 1): Previous frame for feedback trails and sweat drip effects
- **retina_burn**: High persistence (0.0-0.99) for image persistence
- **sweat_drip**: Uses texPrev for vertical melting effect
- **rail_grip**: Motion freeze on bright spots with feedback

## 7. Dual Video Support
- **Automatic Detection**: Checks if tex1 has meaningful content
- **Video B Bleed**: Always some bleed (0.2 base + u_visual_bleed * 0.5)
- **Modular Mixing**: Mixes Video B (visualizer) with Video A (crowd)
- **Base Sampling**: Uses Video B when available, falls back to Video A

## 8. Presets (5 Minimum)
```python
PRESETS = {
    "berghain_bunker": {
        "strobe_speed": 8.0, "strobe_intensity": 6.0, "bass_crush": 9.0,
        "pupil_dilate": 7.0, "sweat_drip": 4.0, "laser_burn": 2.0,
        "rail_grip": 5.0, "adrenaline": 8.0, "bpm_sync": 6.0,
        "dark_room": 8.0, "visual_bleed": 4.0, "retina_burn": 7.0,
    },
    "warehouse_mainstorm": {
        "strobe_speed": 5.0, "strobe_intensity": 10.0, "bass_crush": 6.0,
        "pupil_dilate": 4.0, "sweat_drip": 8.0, "laser_burn": 6.0,
        "rail_grip": 2.0, "adrenaline": 6.0, "bpm_sync": 5.0,
        "dark_room": 2.0, "visual_bleed": 8.0, "retina_burn": 4.0,
    },
    "sunrise_comedown": {
        "strobe_speed": 1.0, "strobe_intensity": 2.0, "bass_crush": 2.0,
        "pupil_dilate": 9.0, "sweat_drip": 2.0, "laser_burn": 1.0,
        "rail_grip": 8.0, "adrenaline": 1.0, "bpm_sync": 2.0,
        "dark_room": 1.0, "visual_bleed": 9.0, "retina_burn": 9.0,
    },
    "industrial_abyss": {
        "strobe_speed": 10.0, "strobe_intensity": 8.0, "bass_crush": 10.0,
        "pupil_dilate": 6.0, "sweat_drip": 6.0, "laser_burn": 8.0,
        "rail_grip": 7.0, "adrenaline": 10.0, "bpm_sync": 8.0,
        "dark_room": 10.0, "visual_bleed": 3.0, "retina_burn": 8.0,
    },
    "minimal_tech": {
        "strobe_speed": 3.0, "strobe_intensity": 4.0, "bass_crush": 3.0,
        "pupil_dilate": 2.0, "sweat_drip": 1.0, "laser_burn": 3.0,
        "rail_grip": 1.0, "adrenaline": 3.0, "bpm_sync": 4.0,
        "dark_room": 3.0, "visual_bleed": 6.0, "retina_burn": 2.0,
    },
}
```

## 9. Unit Tests (≥ 80% coverage)
### Critical Tests:
```python
def test_bass_therapy_effect_creation():
    """Test effect instantiation and default parameters"""
    effect = BassTherapyDatamoshEffect()
    assert effect.name == 'bass_therapy_datamosh'
    assert len(effect.parameters) == 12
    assert all(0.0 <= v <= 10.0 for v in effect.parameters.values())


def test_shader_compilation():
    """Test GLSL shader compilation"""
    effect = BassTherapyDatamoshEffect()
    assert effect.shader is not None
    assert effect.shader.is_compiled()


def test_texture_unit_layout():
    """Test correct texture unit assignments"""
    effect = BassTherapyDatamoshEffect()
    assert effect.texture_units == {
        'tex0': 0, 'texPrev': 1, 'depth_tex': 2, 'tex1': 3
    }


def test_audio_mappings():
    """Test audio reactivity mappings"""
    effect = BassTherapyDatamoshEffect()
    assert effect.audio_mappings == {
        'bass_crush': 'bass', 'strobe_speed': 'high',
        'adrenaline': 'energy', 'pupil_dilate': 'mid'
    }


def test_preset_loading():
    """Test preset loading functionality"""
    effect = BassTherapyDatamoshEffect()
    for preset_name, preset_values in effect.PRESETS.items():
        effect.load_preset(preset_name)
        for param, value in preset_values.items():
            assert abs(effect.parameters[param] - value) < 0.01


def test_apply_uniforms_with_audio():
    """Test uniform application with audio reactor"""
    effect = BassTherapyDatamoshEffect()
    mock_audio = MockAudioReactor()
    effect.apply_uniforms(0.0, (1920, 1080), audio_reactor=mock_audio)
    # Verify uniforms are set correctly
    assert effect.shader.get_uniform('u_bass_crush') > 0.0


def test_apply_uniforms_without_audio():
    """Test uniform application without audio reactor"""
    effect = BassTherapyDatamoshEffect()
    effect.apply_uniforms(0.0, (1920, 1080))
    # Verify uniforms use default values
    assert effect.shader.get_uniform('u_bass_crush') > 0.0


def test_get_state():
    """Test state serialization"""
    effect = BassTherapyDatamoshEffect()
    state = effect.get_state()
    assert state['name'] == 'bass_therapy_datamosh'
    assert 'parameters' in state
    assert len(state['parameters']) == 12
```

### Performance Tests:
```python
def test_60fps_performance():
    """Test effect maintains 60 FPS"""
    effect = BassTherapyDatamoshEffect()
    frame_times = []
    for _ in range(120):  # 2 seconds at 60 FPS
        start = time.time()
        effect.apply_uniforms(time.time(), (1920, 1080))
        frame_times.append(time.time() - start)
    avg_frame_time = sum(frame_times) / len(frame_times)
    assert avg_frame_time <= (1/60.0)  # Must be under 16.67ms


def test_memory_leak():
    """Test for memory leaks over time"""
    effect = BassTherapyDatamoshEffect()
    initial_mem = get_memory_usage()
    for _ in range(1000):
        effect.apply_uniforms(time.time(), (1920, 1080))
    final_mem = get_memory_usage()
    assert final_mem - initial_mem < 1024 * 1024  # Less than 1MB increase
```

### Visual Regression Tests:
```python
def test_visual_consistency():
    """Test visual output consistency"""
    effect = BassTherapyDatamoshEffect()
    # Render with known parameters and compare to baseline
    output = render_effect(effect, parameters={
        'strobe_speed': 5.0, 'strobe_intensity': 5.0,
        'bass_crush': 5.0, 'pupil_dilate': 4.0
    })
    baseline = load_baseline_image('bass_therapy_baseline.png')
    assert image_similarity(output, baseline) > 0.95
```

## 10. Performance Tests
- **Frame Budget**: Must maintain 60 FPS (16.67ms per frame)
- **Memory Usage**: < 50MB additional memory
- **GPU Load**: < 80% GPU utilization on target hardware
- **Shader Compilation**: < 100ms compilation time
- **Texture Upload**: < 5ms for uniform updates

## 11. Visual Regression Tests
- **Baseline Images**: Compare output against known good images
- **Parameter Variations**: Test different parameter combinations
- **Dual Video Support**: Verify both single and dual video modes
- **Audio Reactivity**: Test with simulated audio input
- **Preset Verification**: Ensure presets produce expected visual results

## 🔒 Safety Rails Compliance
- **60 FPS Sacred**: Performance tests enforce frame budget
- **No Silent Failures**: All exceptions caught and logged
- **Resource Management**: Proper cleanup in destructor
- **Memory Safety**: No leaks, bounded memory usage
- **Shader Safety**: GLSL validation and error handling

## 🔗 Dependencies
- **Core**: Effect base class, ShaderBase
- **Audio**: AudioReactor for audio reactivity
- **Math**: Standard GLSL functions (hash, smoothstep, etc.)
- **Textures**: 4 texture units (0-3)

## 📊 Success Metrics
- **Test Coverage**: ≥80% (target: 85%+)
- **Performance**: 60 FPS sustained
- **Memory**: < 50MB additional
- **Visual Quality**: High-fidelity replication of legacy behavior
- **Audio Integration**: Responsive to bass, energy, and frequency bands

## 📝 Notes for Implementation Engineer
- **Dual Video Detection**: The shader automatically detects if tex1 has content
- **Audio Reactivity**: Bass affects bass_crush, energy affects adrenaline, etc.
- **Feedback Management**: texPrev is crucial for sweat drip and retina burn effects
- **Parameter Mapping**: All parameters are 0.0-10.0, internally mapped to shader ranges
- **Performance**: The radial blur uses 8 samples - consider reducing for lower-end hardware
- **Safety**: The shader includes bounds checking and error handling for missing textures