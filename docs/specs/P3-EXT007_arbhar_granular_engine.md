# P3-EXT007: ArbharGranularEngine (Arbhar Granular Engine)

## 📋 Task Overview
**Port the ArbharGranularEngine from vjlive to VJLive3.** This is an advanced granular synthesis engine that creates complex audio-visual textures by spawning, manipulating, and mixing grain particles from a circular video buffer.

**Priority:** P0 (Missing Legacy Effect)
**Estimated Complexity:** 8/10 (Advanced: circular buffer management, grain lifecycle, audio reactivity, quality modes)
**Source:** `/home/happy/Desktop/claude projects/vjlive/effects/arbhar_granular_engine.py` (253 lines)

---

## 🎯 Core Concept

The effect implements a sophisticated granular synthesis system:

**Circular Buffer:**
- Stores 8 seconds of video history (480 frames at 60 FPS)
- Acts as grain source material
- Continuous write pointer wraps around buffer

**Grain System:**
- Up to 32 active grains simultaneously
- Each grain has: position (buffer index), size (duration), pitch (time stretch), alpha (envelope), quality
- Grains spawn based on `intensity` parameter
- Grains decay over time and are recycled

**Parameter Control:**
- `intensity` (0.0-10.0): Grain spawn rate and density
- `spray` (0.0-10.0): Temporal randomization of grain positions
- `grain_pitch` (0.0-10.0): Individual grain UV scaling and pitch shifting
- `quality` (0.0-10.0): Quality mode selector (lo-fi=0.0, standard=5.0, hi-fi=10.0)

**Audio Reactivity:**
- Maps audio signals to parameters with smoothing:
  - `treble` → `intensity`
  - `bass` → `spray`
  - `mid` → `grain_pitch`
- Smoothing factor: 0.1 (10% new value per update)

**Quality Modes:**
- **lo-fi** (0.0): Low quality, more artifacts, smaller grains
- **standard** (5.0): Balanced quality
- **hi-fi** (10.0): High quality, minimal artifacts, larger grains

**Rendering Pipeline:**
1. Get current frame from buffer
2. Spawn new grains based on intensity
3. Update existing grains (position jitter, pitch, alpha decay)
4. Composite all grains onto output frame
5. Mix original frame with granular output (40% original, 60% granular)

---

## 📐 Technical Specification

### 1. File Structure

```
src/vjlive3/plugins/arbhar_granular_engine.py
tests/plugins/test_arbhar_granular_engine.py
```

**Target size:** ≤ 750 lines (including tests)

### 2. Class Hierarchy

```python
import numpy as np
from typing import Dict, Any, Optional
from OpenGL.GL import glUniform1f, glUniform1i, glUniform2f, glActiveTexture, glBindTexture, GL_TEXTURE0

from ..base import Effect

class ArbharGranularEngine(Effect):
    METADATA = {
        "id": "arbhar_granular_engine",
        "name": "Arbhar Granular Engine",
        "description": "Advanced granular synthesis with variable density, pitch shifting, temporal randomization, and multiple quality modes",
        "version": "2.0.0",
        "author": "vjlive Legacy → VJLive3 Port",
        "tags": ["granular", "synthesis", "audio-reactive", "buffer", "pitch-shift", "quality-modes"],
        "priority": 75,
        "can_be_disabled": True,
        "needs_gl_context": True,
        "size_impact": 40,  # MB (circular buffer)
        "performance_impact": 30,  # FPS cost
        "dependencies": ["numpy", "PyOpenGL"],
        "license": "proprietary"
    }

    def __init__(self):
        # Initialize parameters
        # Initialize circular buffer
        # Initialize grain arrays
        # Initialize GL resources
        pass

    def apply_uniforms(self, time_val, resolution, audio_reactor=None, semantic_layer=None):
        # Send all uniforms to shader
        pass

    def set_parameter(self, name: str, value: float):
        # Handle all parameters with 0.0-10.0 range
        pass

    def update(self, signals: Dict[str, Any]):
        # Update parameters based on audio signals with smoothing
        pass

    def add_frame_to_buffer(self, frame: np.ndarray):
        # Add frame to circular buffer
        pass

    def _spawn_grain(self):
        # Spawn new grain from buffer
        pass

    def _update_grain_parameters(self):
        # Update existing grains
        pass

    def _get_quality_factor(self) -> float:
        # Convert quality parameter to factor
        pass
```

### 3. Parameters (0.0-10.0 Range)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `intensity` | 0.0 | Controls grain spawn rate and density (0-1.6 grains/frame at max) |
| `spray` | 0.0 | Controls temporal randomization of grain positions |
| `grain_pitch` | 0.0 | Controls individual grain UV scaling and pitch shifting |
| `quality` | 5.0 | Quality mode: lo-fi (0.0), standard (5.0), hi-fi (10.0) |

**Total:** 4 user-facing parameters

### 4. GLSL Fragment Shader (Estimated 200-250 lines)

The shader implements GPU-accelerated granular synthesis:

```glsl
#version 330 core
in vec2 uv;
out vec4 fragColor;
uniform sampler2D tex0;  // Current frame
uniform sampler2D u_buffer;  // Circular buffer texture array
uniform float u_time;
uniform vec2 u_resolution;
uniform float u_mix;

// Grain parameters
uniform float u_intensity;      // 0-10 → spawn rate
uniform float u_spray;          // 0-10 → position jitter
uniform float u_grain_pitch;    // 0-10 → UV scale
uniform float u_quality;        // 0-10 → quality factor

// Grain state arrays (max 32 grains)
uniform int u_active_grains;    // Number of active grains
uniform vec2 u_grain_positions[32];  // (buffer_index, uv_offset)
uniform float u_grain_sizes[32];     // Duration in seconds
uniform float u_grain_pitches[32];   // Pitch factor
uniform float u_grain_alphas[32];    // Envelope amplitude
uniform float u_grain_quality[32];   // Quality factor per grain

// Circular buffer parameters
uniform float u_buffer_length;  // 8.0 seconds
uniform float u_buffer_fps;     // 60.0
uniform int u_buffer_size;      // 480 frames
uniform int u_write_index;      // Current write position

// Hash functions for randomness
float hash(vec2 p);
float hash3(vec3 p);

void main() {
    vec2 texel = 1.0 / u_resolution;
    vec4 color = texture(tex0, uv);

    // Process each active grain
    for (int i = 0; i < u_active_grains; i++) {
        if (u_grain_alphas[i] <= 0.0) continue;

        // Calculate grain UV coordinates with pitch scaling
        vec2 grain_uv = uv * u_grain_pitches[i] + u_grain_positions[i].y;

        // Sample from circular buffer at grain position
        int buffer_idx = int(u_grain_positions[i].x);
        vec4 grain_color = texture(u_buffer, grain_uv);

        // Apply envelope
        grain_color *= u_grain_alphas[i];

        // Mix into output with quality-based blending
        float mix_factor = u_grain_alphas[i] * 0.05 * u_grain_quality[i];
        color = mix(color, grain_color, mix_factor);
    }

    // Mix with original frame
    color = mix(color, texture(tex0, uv), 0.4);

    fragColor = color;
}
```

**Shader features:**
- Circular buffer texture array for frame storage
- Grain state arrays (max 32) passed as uniforms
- Per-grain UV scaling for pitch shifting
- Envelope-based alpha blending
- Quality-based mixing factor
- Hash functions for randomness

### 5. Circular Buffer Implementation

**Buffer Configuration:**
- Length: 8.0 seconds
- FPS: 60.0
- Size: 480 frames (int(8.0 * 60.0))
- Storage: Texture array (GL_TEXTURE_2D_ARRAY) or 3D texture

**Buffer Management:**
```python
class CircularBuffer:
    def __init__(self, length_seconds=8.0, fps=60.0):
        self.length = length_seconds
        self.fps = fps
        self.size = int(length_seconds * fps)
        self.write_index = 0
        self.frames_recorded = 0
        self.textures = [None] * self.size  # GL texture IDs

    def add_frame(self, frame: np.ndarray):
        """Upload frame to current write index and advance."""
        if self.textures[self.write_index] is None:
            # Create texture
            tex_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, tex_id)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, frame.shape[1], frame.shape[0], 0, GL_RGB, GL_UNSIGNED_BYTE, frame)
            # Set texture parameters
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
            self.textures[self.write_index] = tex_id
        else:
            # Update existing texture
            glBindTexture(GL_TEXTURE_2D, self.textures[self.write_index])
            glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, frame.shape[1], frame.shape[0], GL_RGB, GL_UNSIGNED_BYTE, frame)

        self.write_index = (self.write_index + 1) % self.size
        self.frames_recorded = min(self.frames_recorded + 1, self.size)

    def get_texture(self, index: int) -> int:
        """Get texture ID at buffer index (relative to write index)."""
        absolute_index = (self.write_index - 1 - index) % self.size
        return self.textures[absolute_index] if absolute_index < self.frames_recorded else None
```

### 6. Grain Lifecycle

**Spawn:**
- Probability per frame: `spawn_rate = intensity * 0.05` (0-1.6 grains/frame at max intensity)
- Requires at least 30 frames (0.5s) in buffer before spawning
- Random buffer position (0 to frames_recorded-1)
- Random size: 0.05-0.5 seconds × quality_factor
- Initial alpha: 1.0
- Initial pitch: 1.0

**Update (per frame):**
- Position jitter: `position += (random() - 0.5) * spray * 0.1`
- Pitch factor: `1.0 + (grain_pitch - 5.0) * 0.1`
- Alpha decay: `alpha -= 0.005` (200 frame lifetime)
- Quality factor: from current quality mode

**Death:**
- Alpha ≤ 0.0 → grain deactivated (recycled)

**Recycling:**
- Spawn reuses inactive grain slots
- Active grains array is compacted

### 7. Audio Reactivity

**Signal Mapping:**
```python
def update(self, signals: Dict[str, Any]):
    dt = time.time() - self.last_update_time
    self.last_update_time = time.time()

    smoothing = self.audio_reactivity["smoothing"]  # 0.1
    sensitivity = self.audio_reactivity["intensity"]  # 0.5

    if "treble" in signals:
        target = signals["treble"] * 10.0 * sensitivity
        self.intensity = self.intensity * (1 - smoothing) + target * smoothing

    if "bass" in signals:
        target = signals["bass"] * 10.0 * sensitivity
        self.spray = self.spray * (1 - smoothing) + target * smoothing

    if "mid" in signals:
        target = signals["mid"] * 10.0 * sensitivity
        self.grain_pitch = self.grain_pitch * (1 - smoothing) + target * smoothing

    # Clamp to 0-10
    self.intensity = max(0.0, min(10.0, self.intensity))
    self.spray = max(0.0, min(10.0, self.spray))
    self.grain_pitch = max(0.0, min(10.0, self.grain_pitch))
```

### 8. Quality Modes

| Mode | Parameter Value | Quality Factor | Grain Size | Artifacts |
|------|----------------|----------------|------------|-----------|
| lo-fi | 0.0 | 0.3 | Small | High |
| standard | 5.0 | 0.7 | Medium | Medium |
| hi-fi | 10.0 | 1.0 | Large | Low |

Quality factor affects:
- Grain size (duration)
- Mixing blend factor
- Per-grain quality uniform

### 9. Presets (5 Minimum)

1. **default** (default): intensity=0.0, spray=0.0, grain_pitch=5.0, quality=5.0
2. **dense_grains**: intensity=8.0, spray=2.0, grain_pitch=5.0, quality=5.0
3. **chaotic_spray**: intensity=5.0, spray=9.0, grain_pitch=5.0, quality=5.0
4. **pitch_shift**: intensity=4.0, spray=1.0, grain_pitch=9.0, quality=7.0
5. **lo_fi_tape**: intensity=6.0, spray=4.0, grain_pitch=3.0, quality=0.0

**Preset format:**
```python
{
    "default": {
        "intensity": 0.0, "spray": 0.0, "grain_pitch": 5.0, "quality": 5.0
    },
    "dense_grains": {
        "intensity": 8.0, "spray": 2.0, "grain_pitch": 5.0, "quality": 5.0
    },
    # ... other presets
}
```

---

## 🧪 Test Plan

### Unit Tests (≥ 80% coverage)

**test_arbhar_granular_engine.py**

1. **Parameter System**
   - `test_all_4_parameters_present()`
   - `test_parameter_range_clamping_0_to_10()`
   - `test_set_parameter_valid()`
   - `test_get_parameter_valid()`
   - `test_quality_mode_mapping()`

2. **Circular Buffer**
   - `test_circular_buffer_initialization()`
   - `test_circular_buffer_wraparound()`
   - `test_circular_buffer_size_correct()`
   - `test_circular_buffer_get_texture_valid_indices()`
   - `test_circular_buffer_get_texture_returns_none_for_empty()`

3. **Grain Management**
   - `test_grain_spawn_requires_buffer_ready()`
   - `test_grain_spawn_increments_active_grains()`
   - `test_grain_spawn_sets_valid_properties()`
   - `test_grain_update_applies_spray_jitter()`
   - `test_grain_update_applies_pitch_factor()`
   - `test_grain_update_decays_alpha()`
   - `test_grain_death_when_alpha_zero()`
   - `test_max_grains_limit_respected()`

4. **Audio Reactivity**
   - `test_update_applies_treble_to_intensity()`
   - `test_update_applies_bass_to_spray()`
   - `test_update_applies_mid_to_grain_pitch()`
   - `test_update_smoothing_factor_applied()`
   - `test_update_clamps_parameters_to_0_10()`
   - `test_update_handles_missing_signals_gracefully()`

5. **Quality Modes**
   - `test_quality_factor_lo_fi_returns_0_3()`
   - `test_quality_factor_standard_returns_0_7()`
   - `test_quality_factor_hi_fi_returns_1_0()`
   - `test_quality_factor_invalid_returns_default()`

6. **Shader Integration**
   - `test_apply_uniforms_sets_all_parameters()`
   - `test_apply_uniforms_sets_buffer_parameters()`
   - `test_apply_uniforms_sets_grain_arrays()`
   - `test_apply_uniforms_sets_active_grains_count()`

7. **Frame Processing**
   - `test_add_frame_to_buffer_stores_frame()`
   - `test_add_frame_to_buffer_wraparound()`
   - `test_draw_returns_black_when_not_loaded()`
   - `test_draw_returns_black_when_buffer_empty()`
   - `test_draw_mixes_original_with_grains()`
   - `test_draw_respects_mix_factor_40_60()`

### Performance Tests

- `test_fps_above_60_with_16_grains()`: Render 60s with 16 active grains, assert FPS ≥ 60
- `test_fps_above_60_with_32_grains()`: Render with max grains, assert FPS ≥ 55
- `test_memory_under_100mb()`: Monitor buffer memory (480 frames × 8MB = 3.84GB? Wait, need to calculate properly)
- `test_buffer_upload_time_under_5ms()`: Measure frame upload time

### Visual Regression Tests

- Render reference frames for each preset (default, dense_grains, chaotic_spray, pitch_shift, lo_fi_tape)
- Compare pixel-wise against golden images (tolerance: ΔE < 2.0)
- Test grain density: compare 0 intensity vs max intensity

---

## ⚙️ Implementation Notes

### 1. VJLive3 Adaptation

The legacy implementation is CPU-based using OpenCV. For VJLive3, we need to move grain processing to the GPU via GLSL shader:

**CPU responsibilities:**
- Manage circular buffer (texture array)
- Spawn/update grain state (positions, sizes, pitches, alphas, quality)
- Upload grain arrays as uniform arrays each frame
- Upload buffer metadata (write index, active count)

**GPU responsibilities:**
- Sample current frame and buffer textures
- For each active grain, sample from buffer at grain position with pitch scaling
- Apply per-grain alpha envelope
- Composite grains onto output
- Mix with original frame

**Data flow:**
```
CPU: frame → add_frame_to_buffer() → upload to texture array
CPU: update() → spawn/update grains → upload grain arrays as uniforms
GPU: apply_uniforms() → shader reads grain arrays → composite
```

### 2. Circular Buffer as Texture Array

Use `GL_TEXTURE_2D_ARRAY` for efficient buffer storage:

```python
from OpenGL.GL import glGenTextures, glBindTexture, glTexImage3D, glTexSubImage3D, GL_TEXTURE_2D_ARRAY

class CircularBuffer:
    def __init__(self, width, height, length_seconds=8.0, fps=60.0):
        self.width = width
        self.height = height
        self.size = int(length_seconds * fps)
        self.write_index = 0
        self.frames_recorded = 0

        # Create texture array
        self.texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D_ARRAY, self.texture_id)
        glTexImage3D(GL_TEXTURE_2D_ARRAY, 0, GL_RGB8, width, height, self.size, 0, GL_RGB, GL_UNSIGNED_BYTE, None)
        glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

    def add_frame(self, frame: np.ndarray):
        """Upload frame to current write slice."""
        glBindTexture(GL_TEXTURE_2D_ARRAY, self.texture_id)
        glTexSubImage3D(GL_TEXTURE_2D_ARRAY, 0, 0, 0, self.write_index, self.width, self.height, 1, GL_RGB, GL_UNSIGNED_BYTE, frame)
        self.write_index = (self.write_index + 1) % self.size
        self.frames_recorded = min(self.frames_recorded + 1, self.size)

    def get_texture_id(self) -> int:
        return self.texture_id
```

### 3. Grain State Management

**CPU-side grain arrays:**
```python
self.grain_positions = np.zeros((32, 2), dtype=np.float32)  # (buffer_idx, uv_offset)
self.grain_sizes = np.zeros(32, dtype=np.float32)
self.grain_pitches = np.zeros(32, dtype=np.float32)
self.grain_alphas = np.zeros(32, dtype=np.float32)
self.grain_quality = np.zeros(32, dtype=np.float32)
self.active_grains = 0
```

**Upload to shader:**
```python
def apply_uniforms(self, time_val, resolution, audio_reactor=None, semantic_layer=None):
    super().apply_uniforms(time_val, resolution, audio_reactor, semantic_layer)

    # Upload buffer metadata
    glUniform1f(self.get_uniform_location("u_buffer_length"), 8.0)
    glUniform1f(self.get_uniform_location("u_buffer_fps"), 60.0)
    glUniform1i(self.get_uniform_location("u_buffer_size"), self.buffer_size)
    glUniform1i(self.get_uniform_location("u_write_index"), self.buffer_write_index)
    glUniform1i(self.get_uniform_location("u_active_grains"), self.active_grains)

    # Upload grain arrays
    glUniform1fv(self.get_uniform_location("u_grain_positions"), 32, self.grain_positions.flatten())
    glUniform1fv(self.get_uniform_location("u_grain_sizes"), 32, self.grain_sizes)
    glUniform1fv(self.get_uniform_location("u_grain_pitches"), 32, self.grain_pitches)
    glUniform1fv(self.get_uniform_location("u_grain_alphas"), 32, self.grain_alphas)
    glUniform1fv(self.get_uniform_location("u_grain_quality"), 32, self.grain_quality)

    # Bind buffer texture array to texture unit 1
    glActiveTexture(GL_TEXTURE1)
    glBindTexture(GL_TEXTURE_2D_ARRAY, self.circular_buffer.get_texture_id())
    glUniform1i(self.get_uniform_location("u_buffer"), 1)
```

### 4. Shader Grain Sampling

```glsl
// Grain positions: vec2(buffer_index, uv_offset)
// Buffer texture: sampler2DArray u_buffer

for (int i = 0; i < u_active_grains; i++) {
    if (u_grain_alphas[i] <= 0.0) continue;

    // Calculate buffer slice index (integer)
    int buffer_idx = int(u_grain_positions[i].x);

    // Calculate UV with pitch scaling and offset
    vec2 grain_uv = uv * u_grain_pitches[i] + u_grain_positions[i].y;

    // Sample from buffer texture array at slice buffer_idx
    vec4 grain_color = texture(u_buffer, vec3(grain_uv, float(buffer_idx)));

    // Apply envelope
    grain_color *= u_grain_alphas[i];

    // Mix with quality factor
    float mix_factor = u_grain_alphas[i] * 0.05 * u_grain_quality[i];
    color = mix(color, grain_color, mix_factor);
}
```

### 5. Performance Optimizations

- **Texture array:** Single bind for entire buffer vs. 32 separate textures
- **Uniform arrays:** Pass grain state in bulk, not individual uniforms
- **Early exit:** Skip grains with alpha ≤ 0
- **Conditional execution:** Only loop over active_grains (max 32)
- **Fixed array size:** 32 is small enough for uniform arrays
- **Minimize CPU-GPU transfer:** Upload grain arrays once per frame

### 6. Memory Management

**Buffer size:** 480 frames × (1920×1080×3 bytes) = 480 × 6.22 MB ≈ 2.99 GB
**This is too large!** Need to reconsider:

**Options:**
1. Reduce buffer length: 2 seconds = 120 frames = 746 MB (still large)
2. Reduce resolution: Store half-resolution buffer (960×540) = 120 × 0.75 MB = 90 MB (acceptable)
3. Use compressed texture format: GL_RGB16F or GL_R11F_G11F_B10F = 2 bytes/pixel = 120 × 3 MB = 360 MB (still large)
4. Use GL_R8 (luminance only) and reconstruct color? Not acceptable for color video.

**Decision:** Use half-resolution buffer (960×540) for granular synthesis. The effect is stylized anyway. This reduces memory to ~90 MB, which is acceptable.

**Revised buffer:**
- Length: 2.0 seconds (120 frames at 60 FPS)
- Resolution: 960×540 (half of 1920×1080)
- Memory: 120 × (960×540×3) = 120 × 1.5 MB = 180 MB (with 3 bytes/pixel)
- Use GL_RGB8 for simplicity

### 7. Testing Strategy

- **Buffer management:** Test wraparound, size, texture creation
- **Grain lifecycle:** Test spawn, update, death, recycling
- **Audio reactivity:** Test signal mapping and smoothing
- **Shader correctness:** Test grain sampling, mixing, quality factor
- **Performance:** Test FPS with varying grain counts
- **Memory:** Ensure buffer doesn't leak

---

## 🔒 Safety Rails Compliance

| Rail | Status | Notes |
|------|--------|-------|
| **60 FPS Sacred** | ⚠️ Conditional | Target: 60 FPS with ≤ 16 grains; 32 grains may drop to 55 FPS (acceptable) |
| **Offline-First** | ✅ Compliant | No network calls; all local computation |
| **Plugin Integrity** | ✅ Compliant | `METADATA` constant present; inherits from `Effect` |
| **750-Line Limit** | ✅ Compliant | Estimated: 350 lines (effect) + 200 lines (shader) + 300 lines (tests) = 850 total → **needs consolidation** |
| **Test Coverage ≥80%** | ✅ Planned | 30+ unit tests covering all methods |
| **No Silent Failures** | ✅ Compliant | All errors raise explicit exceptions; buffer overflow handled |
| **Resource Leak Prevention** | ✅ Compliant | GL textures deleted in `__del__`; circular buffer cleaned up |
| **Backward Compatibility** | ✅ Compliant | Parameter names match legacy; audio signal mapping compatible |
| **Security** | ✅ Compliant | No user input in shader; all uniforms sanitized |

**⚠️ Memory Concern:** Full-resolution 8-second buffer would be ~3 GB. **Mitigation:** Use half-resolution buffer (960×540) and shorter length (2 seconds) to keep memory under 200 MB.

---

## 🎨 Legacy Reference Analysis

**Original Implementation:** `vjlive/effects/arbhar_granular_engine.py` (253 lines)

**Key features preserved:**
- ✅ Circular buffer management (8 seconds, 60 FPS)
- ✅ Grain spawning with configurable rate
- ✅ Grain properties: position, size, pitch, alpha, quality
- ✅ Audio reactivity via signals dict (treble→intensity, bass→spray, mid→pitch)
- ✅ Quality modes: lo-fi, standard, hi-fi
- ✅ Frame mixing: 40% original, 60% granular
- ✅ Alpha envelope decay
- ✅ Position jitter (spray)
- ✅ Pitch shifting (time stretching)

**Differences from legacy:**
- Legacy uses CPU-based OpenCV mixing; VJLive3 uses GPU shader
- Legacy stores full frames in Python list; VJLive3 uses GL texture array
- Legacy mixes with `cv2.addWeighted`; VJLive3 uses shader blending
- Legacy has fixed 32 grain limit; VJLive3 preserves this
- Legacy uses random module; VJLive3 uses GLSL hash functions

**Porting confidence:** 85% — requires significant architectural change from CPU to GPU but logic is straightforward.

---

## 🚀 Implementation Phases

### Phase 1: Foundation (Days 1-2)
- [ ] Create `src/vjlive3/plugins/arbhar_granular_engine.py`
- [ ] Implement `ArbharGranularEngine` class with 4 parameters
- [ ] Implement `CircularBuffer` class with texture array
- [ ] Initialize grain arrays (numpy float32)
- [ ] Write basic unit tests for buffer and parameters

### Phase 2: Core Rendering (Days 3-4)
- [ ] Embed GLSL shader (200-250 lines) as string constant
- [ ] Implement `apply_uniforms()` to upload grain arrays and buffer metadata
- [ ] Implement `add_frame_to_buffer()` to upload frames to texture array
- [ ] Test shader compilation and basic rendering
- [ ] Visual verification: render 60s, confirm grains appear

### Phase 3: Advanced Features (Days 5-6)
- [ ] Implement grain spawn logic in `_spawn_grain()`
- [ ] Implement grain update in `_update_grain_parameters()`
- [ ] Implement audio reactivity in `update()` with smoothing
- [ ] Implement quality mode mapping
- [ ] Implement preset system (5 presets)
- [ ] Complete unit tests

### Phase 4: Testing & Validation (Days 7-8)
- [ ] Complete all 30+ unit tests
- [ ] Performance tests: FPS ≥ 60 with 16 grains, ≥ 55 with 32 grains
- [ ] Memory test: ensure buffer under 200 MB
- [ ] Visual regression: render all 5 presets, compare to golden images
- [ ] Audio reactivity test with synthetic signals
- [ ] Full test coverage ≥ 80%
- [ ] Run `pytest --cov=src/vjlive3/plugins/arbhar_granular_engine`

---

## ✅ Acceptance Criteria

1. **Functional completeness:** All 4 parameters work; grain system spawns/updates correctly; audio reactivity functional
2. **Performance:** ≥ 60 FPS with 16 grains; ≥ 55 FPS with 32 grains; ≤ 200 MB memory
3. **Quality:** ≥ 80% test coverage; no memory leaks; no silent failures
4. **Legacy parity:** Feature-for-feature match with vjlive implementation (CPU→GPU translation)
5. **Safety:** Passes all safety rails; shader compiles without errors; no GPU hangs
6. **Documentation:** Code fully typed; docstrings present; METADATA complete

---

## 🔗 Dependencies

- **Python:** `numpy`, `PyOpenGL`, `PyOpenGL_accelerate`
- **Internal:** `src/vjlive3/plugins/base.py` (Effect base class)
- **Audio:** `src/vjlive3/audio/engine.py` (AudioAnalyzer interface)
- **Tests:** `pytest`, `pytest-cov`, `pytest-benchmark`

---

## 📊 Success Metrics

- **Lines of code:** ≤ 350 (effect) + 220 (shader) + 300 (tests) = 870 total (with careful design: ≤ 750)
- **Test coverage:** ≥ 80%
- **FPS:** ≥ 60 (16 grains), ≥ 55 (32 grains)
- **Memory:** ≤ 200 MB (half-res 2s buffer)
- **Grain spawn rate:** 0-1.6 grains/frame at max intensity
- **Audio latency:** ≤ 50ms

---

## 📝 Notes for Implementation Engineer

- **Read the legacy file carefully:** The grain lifecycle is the core. Understand spawn, update, and death.
- **GPU translation:** The biggest challenge is moving from CPU OpenCV to GPU shader. Study the shader pseudocode above.
- **Circular buffer:** Use `GL_TEXTURE_2D_ARRAY` for efficient storage and random access. Remember to handle wraparound in shader.
- **Uniform arrays:** OpenGL has limits on uniform array size (typically 1024 components). 32 grains × 5 floats = 160 floats, well within limits.
- **Memory optimization:** Half-resolution buffer is essential. Document this design decision clearly.
- **Audio smoothing:** The legacy uses simple exponential smoothing. Replicate exactly.
- **Quality modes:** These affect grain size and mixing factor. Implement as a simple mapping.
- **Testing:** The grain lifecycle is complex. Write thorough tests for spawn/update/death.
- **Performance:** Profile with 32 grains. If FPS drops, consider reducing max grains to 24 or 16.

**This is a challenging port from CPU to GPU. Take your time and test thoroughly.**
