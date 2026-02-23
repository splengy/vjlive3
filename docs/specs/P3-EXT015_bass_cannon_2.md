# P3-EXT015: BassCanon2

**Task ID:** P3-EXT015  
**Plugin:** BassCanon2 (Bass Canon 2.0)  
**Priority:** P0  
**Status:** ⬜ Todo  
**Source:** vjlive (vdepth/bass_cannon_2.py)  
**Target:** `src/vjlive3/plugins/bass_cannon_2.py`

---

## 📋 Task Overview

Port the **Bass Canon 2.0** effect from VJLive-2 to VJLive3. This is an advanced, high-complexity bass-triggered shockwave weapon effect that goes far beyond simple displacement. It features:

- **6 feedback channels** for neural feedback loops
- **Synesthetic mapping** converting audio features to colors
- **Collective bass** simulating crowd consciousness
- **Depth integration** for 3D displacement effects
- **30+ parameters** with extensive audio reactivity
- **338-line GLSL fragment shader** with modular effect stages

This is one of the most complex datamosh effects in the collection. It requires careful texture management, state tracking, and performance optimization.

---

## 🎯 Core Concept

> "Bass Canon 2.0 - Underground Rave Bass Cannon Experience"

The effect creates an immersive bass cannon experience that:
- Shakes the visual field like a cannon blast triggered by bass hits
- Creates synesthetic shockwaves that map audio to color and displacement
- Generates collective consciousness bass waves that simulate crowd energy
- Produces neural feedback bass loops using 6 ping-pong framebuffers
- Creates intense, hypnotic bass cannon visuals with depth-aware distortion

The effect is designed for peak rave moments where bass hits create explosive visual responses.

---

## 📁 File Structure

```
src/vjlive3/plugins/bass_cannon_2.py
tests/plugins/test_bass_cannon_2.py
```

---

## 1. Class Hierarchy

```python
from core.effects.shader_base import Effect
from core.audio_reactor import AudioReactor
from core.audio_analyzer import AudioFeature

class BassCanon2(Effect):
    """Bass Canon 2.0 - Underground rave bass cannon amplifier."""
    
    def __init__(self):
        # Generate shader
        fragment_shader_source = self._generate_bass_cannon_shader()
        super().__init__("Bass Canon 2.0", fragment_shader_source)
        
        self.description = "Underground rave bass cannon with neural feedback loops"
        self.category = "Bass Cannon"
        
        # Components
        self.audio_reactor = None
        self.depth_source = None
        
        # State dictionary
        self.bass_cannon_state = {
            'intensity': 0.0,
            'bass_wave': 0.0,
            'synesthetic_mapping': 0.0,
            'neural_feedback': 0.0,
            'time_in_rave': 0.0,
            'bass_displacement': 0.0,
            'cannon_charge': 0.0,
            'shockwave_radius': 0.0,
            'collective_bass': 0.0,
            'neural_resonance': 0.0
        }
        
        # Parameters
        self.parameters = self._initialize_bass_cannon_parameters()
        
        # Textures
        self.depth_texture = 0
        self.feedback_textures = [0, 0, 0, 0, 0, 0]  # 6 channels
        self.output_texture = 0
        
        # Timing
        self.start_time = time.time()
        self.last_bass_update = time.time()
        self.cannon_charge_time = 0.0
    
    def _generate_bass_cannon_shader(self) -> str:
        """Generate the 338-line GLSL shader."""
        ...
    
    def _initialize_bass_cannon_parameters(self) -> Dict[str, float]:
        """Initialize all 30+ parameters."""
        ...
    
    def set_audio_reactor(self, audio_reactor: AudioReactor):
        """Set audio reactor for bass cannon effects."""
        ...
    
    def set_depth_source(self, depth_source):
        """Set depth source for 3D displacement."""
        ...
    
    def update_bass_cannon_state(self):
        """Update state based on time and audio."""
        ...
    
    def update_depth_data(self):
        """Update depth frame from source."""
        ...
    
    def _upload_depth_texture(self, depth_frame: np.ndarray):
        """Upload depth texture (GL_RED, normalized 0-1)."""
        ...
    
    def apply_uniforms(self, time_val: float, resolution: tuple, 
                      audio_reactor=None, semantic_layer=None):
        """Apply all uniforms to shader."""
        super().apply_uniforms(time_val, resolution, audio_reactor, semantic_layer)
        self.update_bass_cannon_state()
        self.update_depth_data()
        # Set texture units
        if self.depth_texture != 0:
            self.shader.set_uniform("depth_tex", 2)
        for i in range(6):
            if self.feedback_textures[i] != 0:
                self.shader.set_uniform(f"feedback{i+1}", 3 + i)
        self._apply_bass_cannon_uniforms()
        self._apply_audio_modulation()
    
    def _apply_bass_cannon_uniforms(self):
        """Map parameters to shader uniforms."""
        ...
    
    def _apply_audio_modulation(self):
        """Apply real-time audio modulation."""
        ...
    
    def __del__(self):
        """Cleanup GL resources."""
        ...
```

---

## 2. Parameters (0.0-10.0)

All user-facing parameters are in the 0.0-10.0 range. Internally they are mapped to appropriate shader ranges (0.0-1.0 or raw values).

### Master Controls
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `masterIntensity` | float | 10.0 | Overall effect strength (0-10, mapped to 0-1 in shader) |

### Audio Reactivity (0-10 → 0-1)
| Parameter | Shader Uniform | Default | Audio Feature | Mapping |
|-----------|----------------|---------|---------------|---------|
| `bassPulse` | bassPulse | 10.0 | BASS | /10 |
| `trebleGlow` | trebleGlow | 8.0 | TREBLE | /10 |
| `midRangeHeat` | midRangeHeat | 7.0 | MID | /10 |

### Bass Cannon Effects (0-10 → 0-1)
| Parameter | Shader Uniform | Default |
|-----------|----------------|---------|
| `bassIntensity` | bassIntensity | 10.0 |
| `displacementStrength` | displacementStrength | 9.0 |
| `shockwaveIntensity` | shockwaveIntensity | 8.0 |
| `cannonChargeSpeed` | cannonChargeSpeed | 7.0 |
| `bassWaveFrequency` | bassWaveFrequency | 9.0 |
| `bassWaveAmplitude` | bassWaveAmplitude | 8.0 |
| `bassWaveChaos` | bassWaveChaos | 7.0 |
| `bassWaveModulation` | bassWaveModulation | 8.0 |
| `crowdEnergy` | crowdEnergy | 9.0 |
| `bassVibration` | bassVibration | 10.0 |

### Bass Cannon Specific (raw values)
| Parameter | Shader Uniform | Default | Range |
|-----------|----------------|---------|-------|
| `bassWaveSpeed` | bassWaveSpeed | 1.0 | 0.0-5.0 |
| `bassWaveChaosFactor` | bassWaveChaosFactor | 0.3 | 0.0-1.0 |
| `bassWaveModulationDepth` | bassWaveModulationDepth | 0.2 | 0.0-1.0 |
| `bassWaveModulationSpeed` | bassWaveModulationSpeed | 1.0 | 0.0-5.0 |
| `bassWavePhase` | bassWavePhase | 0.0 | 0.0-2π |

### Neural Effects (0-10 → 0-1)
| Parameter | Shader Uniform | Default |
|-----------|----------------|---------|
| `collectiveBass` | collectiveBass | 9.0 |
| `synestheticMapping` | synestheticMapping | 8.0 |
| `neuralFeedback` | neuralFeedback | 7.0 |

### Neural Parameters (0-10 → 0-1)
| Parameter | Shader Uniform | Default |
|-----------|----------------|---------|
| `neuralSync` | neuralSync | 8.0 |
| `consciousnessFlow` | consciousnessFlow | 7.0 |
| `sensoryOverload` | sensoryOverload | 5.0 |
| `collectiveBeat` | collectiveBeat | 9.0 |
| `synestheticColor` | synestheticColor | 8.0 |
| `neuralResonance` | neuralResonance | 6.0 |

**Total Parameters:** 30+ (exact count: 30)

---

## 3. Texture Unit Layout

| Texture Unit | Sampler | Purpose | Format |
|--------------|---------|---------|--------|
| `GL_TEXTURE0` | `tex0` | Main video source | RGBA |
| `GL_TEXTURE1` | `tex1` | Secondary source (crowd/lights) | RGBA |
| `GL_TEXTURE2` | `texPrev` | Previous frame (feedback) | RGBA |
| `GL_TEXTURE3` | `depth_tex` | Depth map | GL_RED (8-bit) |
| `GL_TEXTURE4` | `feedback1` | Neural feedback channel 1 | RGBA |
| `GL_TEXTURE5` | `feedback2` | Neural feedback channel 2 | RGBA |
| `GL_TEXTURE6` | `feedback3` | Neural feedback channel 3 | RGBA |
| `GL_TEXTURE7` | `feedback4` | Neural feedback channel 4 | RGBA |
| `GL_TEXTURE8` | `feedback5` | Neural feedback channel 5 | RGBA |
| `GL_TEXTURE9` | `feedback6` | Neural feedback channel 6 | RGBA |

**Note:** 10 texture units required. VJLive3 must support at least 16 texture units (check GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS).

---

## 4. GLSL Fragment Shader (338 lines)

The shader is structured in modular functions:

```glsl
#version 330 core
in vec2 uv;
out vec4 fragColor;

// Input textures (10 samplers)
uniform sampler2D tex0;
uniform sampler2D tex1;
uniform sampler2D texPrev;
uniform sampler2D depth_tex;
uniform sampler2D feedback1;
uniform sampler2D feedback2;
uniform sampler2D feedback3;
uniform sampler2D feedback4;
uniform sampler2D feedback5;
uniform sampler2D feedback6;

// Bass cannon state
uniform float time;
uniform vec2 resolution;
uniform float masterIntensity;
uniform float bassPulse;
uniform float trebleGlow;
uniform float midRangeHeat;
uniform float collectiveBass;
uniform float synestheticMapping;
uniform float neuralFeedback;
uniform float timeInRave;
uniform float bassDisplacement;
uniform float cannonCharge;
uniform float shockwaveRadius;
uniform float neuralResonance;

// Neural parameters
uniform float neuralSync;
uniform float consciousnessFlow;
uniform float sensoryOverload;
uniform float collectiveBeat;
uniform float synestheticColor;
uniform float neuralResonance;

// Bass cannon effects
uniform float bassIntensity;
uniform float displacementStrength;
uniform float shockwaveIntensity;
uniform float cannonChargeSpeed;
uniform float bassWaveFrequency;
uniform float bassWaveAmplitude;
uniform float bassWaveChaos;
uniform float bassWaveModulation;
uniform float crowdEnergy;
uniform float bassVibration;

// Bass cannon specific
uniform float bassWavePosition;
uniform float bassWaveSpeed;
uniform float bassWaveChaos;
uniform float bassWaveModulation;
uniform float bassWaveAmplitude;
uniform float bassWaveFrequency;
uniform float bassWavePhase;
uniform float bassWaveChaosFactor;
uniform float bassWaveModulationDepth;
uniform float bassWaveModulationSpeed;

// Helper functions
float hash(vec2 p) { ... }
float luminance(vec4 c) { ... }
vec3 hsv_to_rgb(vec3 c) { ... }
vec3 getSynestheticColor(float audioFeature) { ... }
vec4 sampleFeedback(int channel, vec2 uv) { ... }
vec4 applyNeuralFeedback(vec4 input, vec2 uv, float depth) { ... }
vec4 applySynestheticMapping(vec4 input, vec2 uv, float depth) { ... }
vec4 applyBassCannonEffects(vec4 input, vec2 uv, float depth, float bassPos) { ... }
vec4 applyCollectiveBass(vec4 input, vec2 uv, float depth) { ... }

void main() {
    vec2 uv = uv;
    float depth = texture(depth_tex, uv).r;
    
    // Calculate bass wave position
    float bassPos = bassWavePosition + time * bassWaveSpeed;
    
    // 1. Sample main sources
    vec4 mainSource = texture(tex0, uv);
    vec4 secondarySource = texture(tex1, uv);
    
    // 2. Apply bass cannon effects
    vec4 withBassCannon = applyBassCannonEffects(mainSource, uv, depth, bassPos);
    
    // 3. Apply neural feedback with bass
    vec4 withNeural = applyNeuralFeedback(withBassCannon, uv, depth);
    
    // 4. Apply synesthetic mapping with bass
    vec4 withSynesthesia = applySynestheticMapping(withNeural, uv, depth);
    
    // 5. Apply collective bass
    vec4 final = applyCollectiveBass(withSynesthesia, uv, depth);
    
    // Master intensity
    fragColor = mix(vec4(0.0), final, masterIntensity * 0.1);
    fragColor.a = 1.0;
}
```

**Total Lines:** 338 (including helper functions and main)

---

## 5. Neural Feedback Mathematics

The effect uses **6 feedback channels** arranged in a neural loop:

### Feedback Sampling
```glsl
vec4 sampleFeedback(int channel, vec2 uv) {
    if (channel == 1) return texture(feedback1, uv);
    if (channel == 2) return texture(feedback2, uv);
    // ... up to channel 6
    return vec4(0.0);
}
```

### Neural Feedback Application
```glsl
vec4 applyNeuralFeedback(vec4 input, vec2 uv, float depth) {
    vec4 feedback = vec4(0.0);
    float totalFeedback = 0.0;
    
    // Loop through all 6 channels
    for (int i = 1; i <= 6; i++) {
        vec2 feedbackUV = uv;
        
        // Neural sync distortion
        if (neuralSync > 0.5) {
            float syncFactor = fract(depth * 8.0 + time * 0.2);
            feedbackUV += vec2(
                sin(syncFactor * 3.14159) * 0.03,
                cos(syncFactor * 3.14159) * 0.03
            );
        }
        
        vec4 fbSample = sampleFeedback(i, feedbackUV);
        
        // Collective bass modulation
        if (collectiveBass > 0.5) {
            float collectiveFactor = fract(time * 0.5 + depth * 4.0);
            fbSample.rgb *= mix(0.8, 1.2, collectiveFactor);
        }
        
        feedback += fbSample;
        totalFeedback += 1.0;
    }
    
    // Neural resonance
    if (neuralResonance > 0.5) {
        float resonance = fract(time * 0.1 + depth * 2.0);
        feedback.rgb *= mix(0.9, 1.1, resonance);
    }
    
    return totalFeedback > 0.0 ?
           mix(input, feedback / totalFeedback, neuralFeedback) :
           input;
}
```

---

## 6. Synesthetic Mapping

Audio features are mapped to colors using HSV space:

```glsl
vec3 getSynestheticColor(float audioFeature) {
    float hue = fract(audioFeature * 10.0 + time * 0.1);
    float saturation = 0.8 + sin(time * 2.0) * 0.2;
    float value = 0.6 + sin(time * 3.0) * 0.4;
    return hsv_to_rgb(vec3(hue, saturation, value));
}

vec4 applySynestheticMapping(vec4 input, vec2 uv, float depth) {
    vec4 result = input;
    
    // Bass pulse
    if (bassPulse > 0.5) {
        float pulse = sin(time * 10.0 + depth * 3.0);
        result.rgb *= mix(0.8, 1.3, pulse * 0.5 + 0.5);
    }
    
    // Treble glow
    if (trebleGlow > 0.5) {
        float glow = fract(time * 5.0 + depth * 2.0);
        result.rgb += getSynestheticColor(glow) * 0.3;
    }
    
    // Mid-range heat
    if (midRangeHeat > 0.5) {
        float heat = fract(time * 3.0 + depth * 4.0);
        result.r = mix(result.r, 1.0, heat * 0.5);
    }
    
    return result;
}
```

---

## 7. Bass Cannon Physics

The core bass wave displacement:

```glsl
vec4 applyBassCannonEffects(vec4 input, vec2 uv, float depth, float bassPos) {
    vec4 result = input;
    
    // Bass wave displacement
    float waveDisplacement = sin(bassPos * bassWaveFrequency + bassWavePhase) * bassWaveAmplitude;
    
    // Chaos
    if (bassWaveChaos > 0.5) {
        float chaos = hash(uv + vec2(time * 0.1)) * bassWaveChaosFactor;
        waveDisplacement += chaos * 0.05;
    }
    
    // Modulation
    if (bassWaveModulation > 0.5) {
        float modulation = sin(time * bassWaveModulationSpeed) * bassWaveModulationDepth;
        waveDisplacement *= (1.0 + modulation);
    }
    
    // Apply displacement to UV
    vec2 displacedUV = uv + vec2(waveDisplacement, waveDisplacement * 0.5);
    result = texture(texPrev, displacedUV);
    
    // Bass intensity
    if (bassIntensity > 0.5) {
        float intensity = bassPos * 2.0;
        result.rgb *= mix(0.8, 1.5, intensity);
    }
    
    // Shockwave
    if (shockwaveIntensity > 0.5) {
        float shockwave = sin(bassPos * 20.0) * 0.1;
        result.rgb += vec3(0.5, 0.2, 1.0) * shockwave;
    }
    
    // Cannon charge
    if (cannonCharge > 0.5) {
        float charge = fract(bassPos * 5.0);
        result.rgb *= mix(0.9, 1.3, charge);
    }
    
    return result;
}
```

---

## 8. State Management

The `bass_cannon_state` dictionary tracks runtime values:

```python
self.bass_cannon_state = {
    'intensity': 0.0,           # Time-based intensity ramp
    'bass_wave': 0.0,           # Current bass wave position (0-1)
    'synesthetic_mapping': 0.0, # Time-evolved mapping strength
    'neural_feedback': 0.0,     # Feedback loop intensity
    'time_in_rave': 0.0,        # Seconds since effect start
    'bass_displacement': 0.0,   # Current bass-driven displacement
    'cannon_charge': 0.0,       # Accumulated charge (0-1)
    'shockwave_radius': 0.0,    # Current shockwave size
    'collective_bass': 0.0,     # Crowd energy level
    'neural_resonance': 0.0     # Resonance from feedback
}
```

**Update Logic:**
- `time_in_rave` increases continuously
- `intensity` ramps: 3.0 → 10.0 over first 60s, then 5.0 → 10.0 over 5min
- `collective_bass` ramps: 4.0 → 10.0 over 10min
- `synesthetic_mapping` ramps: 5.0 → 10.0 over 5min
- `neural_feedback` ramps: 3.0 → 10.0 over 2min
- `bass_wave` increments by `bassWaveSpeed * dt` (wrapped to 0-1)
- `bass_displacement` = `audio_reactor.get_feature_level(BASS) * 0.8`
- `cannon_charge` accumulates `bass_intensity * charge_speed * dt` (clamped 0-1)
- `shockwave_radius` = `bass_intensity * 0.5`
- `neural_resonance` = `bass_intensity * 0.8`

---

## 9. Dual Video Support

The effect uses **two video inputs**:

- **Video A (tex0):** Main video source (the performance)
- **Video B (tex1):** Secondary source (crowd shots, lights, visualizer)

Both are sampled in the shader and blended through the effect pipeline. The secondary source provides additional texture for the neural feedback and collective bass effects.

---

## 10. Audio Reactivity Mapping

The effect responds to **three audio features**:

| Parameter | Audio Feature | Mapping |
|------------|---------------|---------|
| `bass_displacement` (state) | BASS | Direct level * 0.8 |
| `cannon_charge` (state) | BASS | Accumulates on bass hits |
| `shockwave_radius` (state) | BASS | Level * 0.5 |
| `neural_resonance` (state) | BASS | Level * 0.8 |
| `bassPulse` (param) | BASS | /10 to 0-1 |
| `bassIntensity` (param) | BASS | /10 to 0-1 |
| `displacementStrength` (param) | BASS | /10 to 0-1 |
| `cannonChargeSpeed` (param) | BASS | /10 to 0-1 |
| `bassWaveAmplitude` (param) | BASS | /10 to 0-1 |
| `trebleGlow` (param) | TREBLE | /10 to 0-1 |
| `midRangeHeat` (param) | MID | /10 to 0-1 |

**Audio Modulation in `_apply_audio_modulation()`:**

```python
def _apply_audio_modulation(self):
    if self.audio_reactor:
        bass_level = self.audio_reactor.get_feature_level(AudioFeature.BASS)
        intensity_mod = 5.0 + bass_level * 5.0
        self.shader.set_uniform("masterIntensity", intensity_mod / 10.0)
        
        treble_level = self.audio_reactor.get_feature_level(AudioFeature.TREBLE)
        light_mod = 5.0 + treble_level * 5.0
        self.shader.set_uniform("lightStreaks", light_mod / 10.0)  # Note: shader uses trebleGlow
        
        mid_level = self.audio_reactor.get_feature_level(AudioFeature.MID)
        heat_mod = 5.0 + mid_level * 5.0
        self.shader.set_uniform("midRangeHeat", heat_mod / 10.0)
        
        charge_speed = bass_level * 0.8
        self.shader.set_uniform("cannonChargeSpeed", charge_speed)
        
        displacement = bass_level * 0.8
        self.shader.set_uniform("displacementStrength", displacement)
        
        wave_amplitude = bass_level * 0.6
        self.shader.set_uniform("bassWaveAmplitude", wave_amplitude)
```

**Note:** The legacy code sets `lightStreaks` uniform but the shader uses `trebleGlow`. This needs to be fixed in the port: use `trebleGlow` consistently.

---

## 11. Presets (5 Minimum)

Create **5 presets** that demonstrate the effect's range:

### 1. `underground_rave` (Legacy)
- **Description:** The original underground rave experience
- **Parameters:**
  - `masterIntensity`: 10.0
  - `bassPulse`: 10.0
  - `trebleGlow`: 8.0
  - `midRangeHeat`: 7.0
  - `bassIntensity`: 10.0
  - `displacementStrength`: 9.0
  - `shockwaveIntensity`: 8.0
  - `cannonChargeSpeed`: 7.0
  - `collectiveBass`: 9.0
  - `synestheticMapping`: 8.0
  - `neuralFeedback`: 7.0
  - All others at default (mid-range)

### 2. `neural_consciousness` (Legacy)
- **Description:** Focus on neural feedback and collective bass
- **Parameters:**
  - `neuralFeedback`: 10.0
  - `collectiveBass`: 10.0
  - `neuralSync`: 10.0
  - `consciousnessFlow`: 10.0
  - `collectiveBeat`: 10.0
  - `masterIntensity`: 8.0
  - `bassPulse`: 5.0 (reduced)
  - All others at 6.0-7.0

### 3. `synesthetic_explosion` (Legacy)
- **Description:** Color-driven synesthetic experience
- **Parameters:**
  - `synestheticMapping`: 10.0
  - `synestheticColor`: 10.0
  - `trebleGlow`: 10.0
  - `midRangeHeat`: 10.0
  - `bassPulse`: 8.0
  - `masterIntensity`: 9.0
  - Neural effects at 4.0-5.0

### 4. `cannon_barrage` (New)
- **Description:** Rapid-fire bass cannon with high chaos
- **Parameters:**
  - `cannonChargeSpeed`: 10.0
  - `bassWaveChaos`: 10.0
  - `bassWaveChaosFactor`: 0.8
  - `shockwaveIntensity`: 10.0
  - `bassVibration`: 10.0
  - `bassIntensity`: 10.0
  - `displacementStrength`: 10.0
  - `masterIntensity`: 10.0
  - Neural/synesthetic at 3.0-4.0

### 5. `collective_rave` (New)
- **Description:** Crowd-synchronized bass experience
- **Parameters:**
  - `collectiveBass`: 10.0
  - `collectiveBeat`: 10.0
  - `consciousnessFlow`: 10.0
  - `neuralResonance`: 10.0
  - `crowdEnergy`: 10.0
  - `bassPulse`: 9.0
  - `masterIntensity`: 9.0
  - `sensoryOverload`: 8.0

---

## 12. Unit Tests (≥ 80% coverage)

**Test File:** `tests/plugins/test_bass_cannon_2.py`

### Critical Tests:

#### Initialization
- [ ] `test_plugin_creates_with_correct_name()`
- [ ] `test_plugin_initializes_all_parameters()`
- [ ] `test_plugin_creates_shader_with_338_lines()`
- [ ] `test_plugin_has_30_parameters()`
- [ ] `test_plugin_initializes_6_feedback_textures_as_zero()`
- [ ] `test_plugin_initializes_depth_texture_as_zero()`
- [ ] `test_plugin_initializes_bass_cannon_state_with_10_keys()`

#### Parameter System
- [ ] `test_set_parameter_valid_range_0_to_10()`
- [ ] `test_set_parameter_rejects_out_of_range()`
- [ ] `test_get_parameter_returns_current_value()`
- [ ] `test_parameters_persist_across_frames()`
- [ ] `test_all_30_parameters_are_settable_and_gettable()`

#### Texture Management
- [ ] `test_depth_texture_upload_normalizes_0_3_to_0_1()`
- [ ] `test_depth_texture_uses_GL_RED_format()`
- [ ] `test_feedback_textures_are_6_in_count()`
- [ ] `test_texture_units_are_correctly_assigned()`

#### State Updates
- [ ] `test_time_in_rave_increases_with_time()`
- [ ] `test_intensity_ramps_over_first_60_seconds()`
- [ ] `test_collective_bass_ramps_over_10_minutes()`
- [ ] `test_bass_wave_position_wraps_at_1_0()`
- [ ] `test_bass_displacement_maps_to_audio_bass()`
- [ ] `test_cannon_charge_accumulates_and_clamps()`
- [ ] `test_shockwave_radius_equals_bass_level_0_5()`

#### Audio Reactivity
- [ ] `test_audio_reactor_set_and_used()`
- [ ] `test_audio_modulation_updates_master_intensity()`
- [ ] `test_audio_modulation_updates_bass_parameters()`
- [ ] `test_audio_modulation_handles_missing_reactor()`
- [ ] `test_bass_level_maps_to_0_8_displacement()`

#### Shader Compilation
- [ ] `test_shader_compiles_without_errors()`
- [ ] `test_shader_has_all_required_uniforms()`
- [ ] `test_shader_has_10_samplers()`
- [ ] `test_shader_uses_correct_texture_units()`

#### Uniform Application
- [ ] `test_apply_uniforms_sets_master_intensity()`
- [ ] `test_apply_uniforms_sets_all_30_parameters()`
- [ ] `test_apply_uniforms_sets_state_values()`
- [ ] `test_apply_uniforms_sets_depth_texture_unit()`
- [ ] `test_apply_uniforms_sets_feedback_texture_units()`
- [ ] `test_apply_uniforms_calls_super()`

#### Depth Integration
- [ ] `test_depth_source_set_and_used()`
- [ ] `test_update_depth_data_calls_source_get_filtered_depth_frame()`
- [ ] `test_depth_texture_upload_with_valid_frame()`
- [ ] `test_depth_texture_upload_with_none_does_nothing()`

#### Cleanup
- [ ] `test_del_cleans_up_depth_texture()`
- [ ] `test_del_cleans_up_feedback_textures()`
- [ ] `test_del_handles_missing_resources_gracefully()`

#### Performance
- [ ] `test_frame_budget_under_2ms()`
- [ ] `test_shader_compile_time_under_100ms()`
- [ ] `test_texture_upload_does_not_leak()`

**Target Coverage:** 85% (44+ tests)

---

## 13. Performance Tests

- **Frame Budget:** ≤ 2.0ms per frame (60 FPS sacred)
- **Shader Compilation:** ≤ 100ms
- **Texture Upload:** ≤ 0.5ms per frame (depth + 6 feedback)
- **Memory:** ≤ 50 MB (6 feedback framebuffers at half-res)
- **GPU:** Test on integrated and discrete GPUs

**Optimization Strategies:**
- Use half-resolution framebuffers for feedback channels
- Batch texture uploads
- Minimize state changes
- Consider reducing feedback channels to 4 on low-end hardware (configurable)

---

## 14. Visual Regression Tests

Capture frames at these critical states:

1. **Idle:** `masterIntensity=0` → black screen
2. **Low Bass:** `bassIntensity=3` → subtle displacement
3. **Medium Bass:** `bassIntensity=6` → moderate shockwaves
4. **Peak Bass:** `bassIntensity=10` → full cannon blast
5. **Neural Mode:** `neuralFeedback=10` → feedback loops visible
6. **Synesthetic Mode:** `synestheticMapping=10` → color explosions
7. **Collective Mode:** `collectiveBass=10` → crowd wave effects
8. **Chaos Mode:** `bassWaveChaos=10` → maximum distortion

Compare against reference images from legacy implementation.

---

## 15. Implementation Phases

### Phase 1: Foundation (Day 1)
- Create `src/vjlive3/plugins/bass_cannon_2.py`
- Implement `__init__` with parameter dictionary and state
- Implement `_generate_bass_cannon_shader()` with full 338-line GLSL
- Implement `_initialize_bass_cannon_parameters()` with all 30 parameters
- Basic texture initialization (depth + 6 feedback)
- Write initial unit tests (10 tests)

**Success:** Shader compiles, plugin loads, all parameters accessible

### Phase 2: Audio & Depth Integration (Day 2)
- Implement `set_audio_reactor()` and `set_depth_source()`
- Implement `_upload_depth_texture()` with normalization
- Implement `update_bass_cannon_state()` with time-based ramps
- Implement `_apply_audio_modulation()` with real-time mapping
- Implement `_apply_bass_cannon_uniforms()` with correct mappings
- Write audio integration tests (10 tests)

**Success:** Audio reactivity works, depth texture uploads, state updates correctly

### Phase 3: Feedback & Rendering (Day 2-3)
- Implement feedback texture management (create/destroy/swap)
- Implement `apply_uniforms()` with full texture unit binding
- Implement `__del__()` cleanup for all GL resources
- Implement framebuffer management (ping-pong between feedback channels)
- Write feedback tests (10 tests)

**Success:** Feedback loops work, no texture leaks, correct framebuffer swapping

### Phase 4: Testing & Validation (Day 3-4)
- Complete unit tests (reach 85% coverage)
- Performance testing (frame budget, memory)
- Visual regression testing
- Preset creation (5 presets)
- Documentation
- Safety Rails compliance verification

**Success:** All tests pass, performance within budget, presets work

---

## 🔒 Safety Rails Compliance

| Rail | Requirement | Compliance Plan |
|------|-------------|-----------------|
| **60 FPS Sacred** | ≤ 16.67ms per frame | Target ≤ 2ms; use half-res feedback; test on low-end |
| **Offline-First** | No cloud dependencies | No network calls in plugin |
| **Plugin Integrity** | METADATA constant | Add `METADATA = {...}` with plugin info |
| **750-Line Limit** | ≤ 750 lines of code | Current estimate: ~400 lines (well under) |
| **Test Coverage** | ≥ 80% coverage | Target 85% with 44+ tests |
| **No Silent Failures** | All errors logged | Use try/except with logging; validate inputs |
| **Resource Leak Prevention** | GL resources cleaned | `__del__` deletes all textures; test with valgrind |
| **Backward Compatibility** | No breaking changes | New plugin, no compatibility concerns |
| **Security** | No exec/eval | No dynamic code execution |

**Special Considerations:**
- **Texture Unit Count:** Uses 10 texture units. Verify `GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS >= 16` in `apply_uniforms()` and log warning if insufficient.
- **Memory:** 6 feedback framebuffers at half resolution: `6 * (w/2 * h/2 * 4) ≈ 6 * 2MB = 12MB` for 1080p. Acceptable.
- **Performance:** The 6-channel feedback loop is expensive. Consider making feedback channel count configurable via parameter (4-6) for low-end systems.

---

## 🔗 Dependencies

```python
# Core
from core.effects.shader_base import Effect
from core.audio_reactor import AudioReactor
from core.audio_analyzer import AudioFeature
from core.framebuffer import Framebuffer  # For feedback channels

# GL
from OpenGL.GL import (glGenTextures, glBindTexture, glTexParameteri,
                      glTexImage2D, glActiveTexture, glDeleteTextures,
                      GL_TEXTURE_2D, GL_LINEAR, GL_CLAMP_TO_EDGE,
                      GL_RED, GL_UNSIGNED_BYTE, GL_RGBA)

# Utils
import numpy as np
import time
import logging
```

**External Dependencies:** None beyond VJLive3 core

---

## 📊 Success Metrics

- ✅ **Shader Compiles:** No GLSL errors on all target GPUs
- ✅ **Tests Pass:** 44/44 unit tests, ≥85% coverage
- ✅ **Performance:** ≤ 2ms/frame average, ≤ 10ms max spike
- ✅ **No Leaks:** All GL textures deleted on plugin destruction
- ✅ **Audio Reactivity:** Bass hits trigger visible cannon blasts
- ✅ **Depth Integration:** Depth map affects displacement correctly
- ✅ **Feedback Loops:** 6 channels create evolving visual patterns
- ✅ **Presets:** 5 presets demonstrate distinct character
- ✅ **Safety Rails:** All 10 rails satisfied

---

## 📝 Notes for Implementation Engineer

### Critical Implementation Details

1. **Texture Unit Management:** The effect uses **10 texture units** (0-9). This is high but within typical desktop GL limits (16+). However, when combined with other effects in a chain, you may exceed the limit. Implement a fallback: if `GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS < 12`, log a warning and reduce feedback channels to 4.

2. **Feedback Framebuffer Lifecycle:** Each feedback channel needs its own Framebuffer object with a texture attachment. Implement a `self.feedback_fbos = []` list to manage them. The feedback loop works by:
   - Rendering current effect to `feedback_textures[i]`
   - Using previous frame's `feedback_textures[i]` as input in next frame
   - Swapping read/write buffers each frame

3. **Depth Texture Format:** The legacy code uses `GL_RED` with `GL_UNSIGNED_BYTE`. Depth is normalized from 0.3-4.0m to 0-1. Ensure your depth source provides meters. If using millimeters, convert: `depth_normalized = np.clip((depth_mm/1000 - 0.3) / (4.0 - 0.3), 0, 1)`.

4. **Audio Modulation Bug Fix:** The legacy code sets uniform `lightStreaks` in `_apply_audio_modulation()` but the shader uses `trebleGlow`. Fix this: replace `self.shader.set_uniform("lightStreaks", ...)` with `self.shader.set_uniform("trebleGlow", ...)`.

5. **State Update Timing:** `update_bass_cannon_state()` should be called **once per frame** before `apply_uniforms()`. The state values are used in `_apply_bass_cannon_uniforms()`. Ensure `self.last_bass_update` is used to compute `dt` for time-based accumulations.

6. **Parameter Ranges:** Some parameters have dual roles:
   - `bassPulse`, `trebleGlow`, `midRangeHeat` are 0-10 user values mapped to 0-1 in shader
   - `bassWaveSpeed`, `bassWaveChaosFactor`, etc. are raw shader values (0-5 or 0-1)
   - Be careful not to divide raw values by 10 in `_apply_bass_cannon_uniforms()`

7. **Shader Uniform Mapping:** The shader has **duplicate uniform names** in some cases (e.g., `bassWaveChaos` appears twice with different meanings). This is a GLSL error! You must rename one set. Suggested:
   - Keep `bassWaveChaos` for the 0-1 parameter (line 358)
   - Rename the second `bassWaveChaos` (line 366) to `bassWaveChaosRaw` or similar
   - Update both the shader and uniform setting code accordingly

8. **Collective Bass Simulation:** The `collective_bass` state ramps over 10 minutes. This is a very long ramp. Consider making it configurable or faster for typical VJ sets (3-5 minutes).

9. **Neural Feedback Loop:** The 6 feedback channels create a recursive system. Ensure you:
   - Create 6 separate textures and FBOs
   - Render to each channel in sequence or use multi-pass
   - Swap textures each frame (ping-pong)
   - This is computationally expensive; monitor performance

10. **Testing Strategy:** Because this effect has many interdependent systems, write **integration tests** that:
    - Set audio_reactor with mock audio data
    - Call `apply_uniforms()` for several frames
    - Read back framebuffer pixels and assert they change over time
    - Use `glReadPixels()` in tests (may need offscreen context)

### Porting Checklist

- [ ] Copy full GLSL shader from legacy (338 lines)
- [ ] Fix duplicate uniform names in shader
- [ ] Implement all 30 parameters in `_initialize_bass_cannon_parameters()`
- [ ] Implement `bass_cannon_state` dictionary with 10 keys
- [ ] Implement `update_bass_cannon_state()` with all ramp logic
- [ ] Implement `_apply_bass_cannon_uniforms()` with correct mappings
- [ ] Fix `lightStreaks` → `trebleGlow` bug in `_apply_audio_modulation()`
- [ ] Implement depth texture upload with normalization
- [ ] Create 6 feedback textures + FBOs
- [ ] Implement feedback texture binding in `apply_uniforms()`
- [ ] Implement `__del__()` cleanup for all GL resources
- [ ] Add `METADATA` constant
- [ ] Write 44+ unit tests
- [ ] Create 5 presets
- [ ] Performance test on target hardware
- [ ] Verify texture unit count at runtime

### Known Issues from Legacy

1. **Duplicate Uniforms:** `bassWaveChaos` defined twice (lines 358 and 366). Must fix.
2. **Uniform Mismatch:** `lightStreaks` set but not used in shader. Fix to `trebleGlow`.
3. **Hard-coded Ramp Times:** 10-minute collective bass ramp may be too long. Consider parameterizing.
4. **No Error Handling:** Legacy code lacks validation. Add checks for `audio_reactor` and `depth_source` being None.
5. **Texture Leak Risk:** `__del__` is incomplete. Ensure all 6 feedback textures + depth texture are deleted.

### Performance Tips

- Use `glTexImage2D` only on first upload; subsequent updates use `glTexSubImage2D`
- For feedback textures, use `GL_RGBA` format (not GL_RED)
- Consider using `GL_HALF_FLOAT` for precision if available
- Batch uniform updates: group related uniforms and set them together
- Use `glFinish()` only for debugging; remove in production

### Debugging

Add debug uniforms to visualize internal state:
```glsl
uniform float debug_bass_level;
uniform float debug_cannon_charge;
// In Python:
self.shader.set_uniform("debug_bass_level", bass_level)
self.shader.set_uniform("debug_cannon_charge", self.bass_cannon_state['cannon_charge'])
```

Then visualize as color overlay in shader:
```glsl
if (debug_bass_level > 0.8) fragColor.rgb = vec3(1.0, 0.0, 0.0); // Red alert
```

---

**Specification Version:** 1.0  
**Last Updated:** 2025-02-23  
**Approved By:** [Awaiting Approval]
