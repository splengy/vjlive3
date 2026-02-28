# P3-EXT007: Arbhar Granular Engine — Technical Specification

**File naming:** `docs/specs/P3-EXT007_arbhar_granular_engine.md`  
**Priority:** Phase 3 Extension  
**Status:** In Progress  
**Assigned Worker:** desktop-roo  
**Created:** 2026-02-27  
**Last Updated:** 2026-02-27  

---

## IMPORTANT: File Location and Naming

The final implementation **MUST** be placed at:
- `src/vjlive3/core/effects/arbhar_granular_engine.py` (or `plugins/arbhar/arbhar_granular_engine.py`)

This file **must** exist and be reviewed BEFORE writing any code for this task.

---

## Description

The `ArbharGranularEngine` is a sophisticated granular synthesis system that creates audio-reactive visual effects by manipulating video frames as temporal "grains." It maintains a circular buffer of recent video frames (8 seconds at 60fps), then spawns multiple grains that sample from this buffer with variable pitch, timing, and opacity. The engine responds to audio input by modulating grain density, pitch, and temporal randomization, creating dynamic visual patterns that "grain" the video stream in time.

The implementation uses a hybrid CPU/GPU architecture: the CPU manages the circular buffer, spawns and updates grain properties, and performs frame mixing using OpenCV; the GPU runs a fragment shader that implements the granular sampling with grid-based positioning and hash-based randomness. The result is a high-performance, real-time effect suitable for VJ performances.

---

## Core Architecture

The system consists of three main components:

1. **Circular Buffer Manager**: Stores the last N frames (typically 480 frames at 60fps for 8 seconds) in a ring buffer. Frames are added each tick via `add_frame_to_buffer()`.
2. **Grain Manager**: Maintains arrays for up to 32 active grains (`grain_positions`, `grain_sizes`, `grain_pitches`, `grain_alphas`, `grain_quality`). Grains are spawned based on `intensity` and updated each frame with temporal randomization (`spray`) and pitch shifting (`grain_pitch`).
3. **Shader-Based Rendering**: The fragment shader `arbhar_granular_engine.frag` implements a grid-based grain sampling algorithm using a texture array (`sampler2DArray frame_buffer`). The shader determines which frame from the buffer to sample based on hash functions and the current parameters.

The CPU and GPU work together: the CPU prepares the texture array with recent frames, sets shader uniforms (intensity, spray, grain_pitch, buffer_size, current_frame_index), and triggers a full-screen draw. The GPU fragment shader runs per-pixel, computing a grain grid and sampling from the appropriate frame in the array. The output is then mixed with the original frame using OpenCV's `addWeighted`.

---

## Complete Class Structure

```python
import numpy as np
from typing import Dict, Any, Optional
import os
import time
import random
import cv2
from core.base_effect import BaseEffect
from core.video_buffer_manager import get_buffer_manager, VideoBufferConfig

class ArbharGranularEngine(BaseEffect):
    """
    Arbhar Granular Engine - Advanced Granular Synthesis System
    
    Implements a sophisticated granular synthesis engine with:
    - Variable grain density and temporal randomization
    - Pitch shifting and UV scaling
    - Circular buffer management
    - Audio-reactive parameter control
    - Multiple quality modes
    """
    
    def __init__(self):
        """Initialize the granular synthesis engine."""
        super().__init__()
        self.name = "Arbhar Granular Engine"
        self.shader_path = "effects/shaders/shaders/arbhar_granular_engine.frag"
        self.is_loaded = False
        
        # Effect parameters (0.0-10.0 range)
        self.intensity: float = 0.0      # Controls grain spawn rate and density
        self.spray: float = 0.0         # Controls temporal randomization
        self.grain_pitch: float = 0.0    # Controls individual grain UV scaling
        
        # Audio reactivity settings
        self.audio_reactivity = {
            "intensity": 0.5,  # Sensitivity to audio signals
            "smoothing": 0.1   # Smoothing factor for parameter changes
        }
        
        # Quality modes
        self.quality_modes = {
            "lo-fi": 0.0,
            "standard": 5.0,
            "hi-fi": 10.0
        }
        self.current_quality = "standard"
        
        # Buffer configuration
        self.buffer_length = 8.0  # seconds
        self.fps = 60.0
        self.buffer_size = int(self.buffer_length * self.fps)
        
        # Circular buffer for frame storage (managed by buffer manager or locally)
        self.ring_buffer = [None] * self.buffer_size
        self.buffer_write_index = 0
        self.frames_recorded = 0
        
        # Grain management (max 32 active grains)
        self.max_grains = 32
        self.active_grains = 0
        self.grain_positions = [0.0] * self.max_grains
        self.grain_sizes = [0.0] * self.max_grains
        self.grain_pitches = [0.0] * self.max_grains
        self.grain_alphas = [0.0] * self.max_grains
        self.grain_quality = [0.0] * self.max_grains
        
        # Internal state
        self.last_update_time = 0.0
        self.frame_count = 0
        self.seed = int(time.time())
        random.seed(self.seed)
        
        # Shader program (loaded via load())
        self.shader_program = None
    
    def load(self) -> bool:
        """
        Load the associated .frag shader file.
        
        Returns:
            bool: True if shader file exists and loads successfully, False otherwise
        """
        print(f"Loading Arbhar Granular Engine shader from {self.shader_path}")
        if os.path.exists(self.shader_path):
            # Read shader source and compile (actual compilation handled by base class)
            with open(self.shader_path, 'r') as f:
                shader_source = f.read()
            # In VJLive3, shader compilation is typically done via Effect base class
            self.is_loaded = True
            print("Arbhar Granular Engine shader loaded successfully.")
            return True
        else:
            print("Warning: .frag file for Arbhar Granular Engine not found.")
            self.is_loaded = False
            return False
    
    def update(self, signals: Dict[str, Any]) -> None:
        """
        Update effect parameters based on incoming audio signals.
        
        Args:
            signals (Dict[str, Any]): A dictionary of realtime signals 
                                 (e.g., 'bass', 'treble', 'bpm', 'midi_cc_1').
        """
        current_time = time.time()
        dt = current_time - self.last_update_time
        self.last_update_time = current_time
        
        # Map audio signals to effect parameters with smoothing
        if "treble" in signals:
            target_intensity = signals["treble"] * 10.0 * self.audio_reactivity["intensity"]
            self.intensity = (self.intensity * (1.0 - self.audio_reactivity["smoothing"]) + 
                             target_intensity * self.audio_reactivity["smoothing"])
        
        if "bass" in signals:
            target_spray = signals["bass"] * 10.0 * self.audio_reactivity["intensity"]
            self.spray = (self.spray * (1.0 - self.audio_reactivity["smoothing"]) + 
                         target_spray * self.audio_reactivity["smoothing"])
        
        if "mid" in signals:
            target_pitch = signals["mid"] * 10.0 * self.audio_reactivity["intensity"]
            self.grain_pitch = (self.grain_pitch * (1.0 - self.audio_reactivity["smoothing"]) + 
                               target_pitch * self.audio_reactivity["smoothing"])
        
        # Ensure parameters stay within 0-10 range
        self.intensity = max(0.0, min(10.0, self.intensity))
        self.spray = max(0.0, min(10.0, self.spray))
        self.grain_pitch = max(0.0, min(10.0, self.grain_pitch))
        
        # Update grain parameters based on main parameters
        self._update_grain_parameters()
    
    def _update_grain_parameters(self) -> None:
        """Update individual grain parameters based on main effect parameters."""
        # Calculate grain spawn rate based on intensity
        spawn_rate = self.intensity * 0.05  # 0-1.6 grains per frame at max intensity
        
        # Spawn new grains if needed
        if random.random() < spawn_rate:
            self._spawn_grain()
        
        # Update existing grains
        for i in range(self.active_grains):
            # Apply temporal randomization (spray)
            self.grain_positions[i] += (random.random() - 0.5) * self.spray * 0.1
            
            # Apply pitch shifting
            self.grain_pitches[i] = 1.0 + (self.grain_pitch - 5.0) * 0.1
            
            # Apply quality-based processing
            quality_factor = self._get_quality_factor()
            self.grain_quality[i] = quality_factor
            
            # Apply alpha envelope (slow decay)
            self.grain_alphas[i] = max(0.0, self.grain_alphas[i] - 0.005)
    
    def _get_quality_factor(self) -> float:
        """Get quality factor based on current quality mode."""
        if self.current_quality == "lo-fi":
            return 0.3  # Low quality, more artifacts
        elif self.current_quality == "standard":
            return 0.7  # Standard quality
        elif self.current_quality == "hi-fi":
            return 1.0  # High quality, minimal artifacts
        return 0.7
    
    def _spawn_grain(self) -> None:
        """Spawn a new grain from the buffer."""
        if self.frames_recorded < 30:  # Need at least 0.5 seconds of buffer
            return
        
        if self.active_grains < self.max_grains:
            grain_index = self.active_grains
            self.active_grains += 1
            
            # Random position in buffer
            self.grain_positions[grain_index] = random.randint(0, self.frames_recorded - 1)
            
            # Random size (duration)
            self.grain_sizes[grain_index] = random.uniform(0.1, 0.5)
            
            # Initial alpha (opacity)
            self.grain_alphas[grain_index] = random.uniform(0.3, 0.7)
            
            # Pitch is set in _update_grain_parameters
    
    def add_frame_to_buffer(self, frame: np.ndarray) -> None:
        """Add a frame to the circular buffer."""
        # Store frame in ring buffer
        self.ring_buffer[self.buffer_write_index] = frame.copy()
        
        # Update indices
        self.buffer_write_index = (self.buffer_write_index + 1) % self.buffer_size
        self.frames_recorded = min(self.frames_recorded + 1, self.buffer_size)
    
    def get_parameters(self) -> Dict[str, float]:
        """Get current effect parameters."""
        return {
            "intensity": self.intensity,
            "spray": self.spray,
            "grain_pitch": self.grain_pitch,
            "audio_reactivity_intensity": self.audio_reactivity["intensity"],
            "audio_reactivity_smoothing": self.audio_reactivity["smoothing"],
            "quality_mode": self.quality_modes[self.current_quality]
        }
    
    def set_parameter(self, name: str, value: float) -> None:
        """Set effect parameter with validation."""
        if name == "intensity":
            self.intensity = max(0.0, min(10.0, value))
        elif name == "spray":
            self.spray = max(0.0, min(10.0, value))
        elif name == "grain_pitch":
            self.grain_pitch = max(0.0, min(10.0, value))
        elif name == "audio_reactivity_intensity":
            self.audio_reactivity["intensity"] = max(0.0, min(1.0, value))
        elif name == "audio_reactivity_smoothing":
            self.audio_reactivity["smoothing"] = max(0.0, min(1.0, value))
        else:
            raise ValueError(f"Unknown parameter: {name}")
    
    def draw(self, current_frame: np.ndarray) -> np.ndarray:
        """
        Render the granular effect onto the current frame.
        
        Args:
            current_frame: Input frame (numpy array, HxWx3, uint8 or float32)
            
        Returns:
            Processed frame with granular effect applied
        """
        if not self.is_loaded or self.frames_recorded < 30:
            return current_frame
        
        # 1. Prepare texture array with recent frames (GPU side in real impl)
        # In actual implementation, the frame buffer would be uploaded to a 2D texture array
        
        # 2. Render granular effect via shader (simplified Python fallback)
        # The shader would run full-screen and sample from the texture array
        # Here we simulate the result using CPU-based grain blending
        
        output_frame = np.zeros_like(current_frame)
        
        # Start with black background
        output_frame.fill(0)
        
        # Blend each active grain
        for i in range(self.active_grains):
            grain_pos = int(self.grain_positions[i])
            if grain_pos < 0 or grain_pos >= self.frames_recorded:
                continue
            
            source_frame = self.ring_buffer[grain_pos % self.buffer_size]
            if source_frame is None:
                continue
            
            # Apply pitch shifting (time stretching) - simplified as scaling
            pitch_factor = self.grain_pitches[i]
            if pitch_factor != 1.0:
                # Resize source frame according to pitch
                new_w = int(source_frame.shape[1] * pitch_factor)
                new_h = int(source_frame.shape[0] * pitch_factor)
                if new_w > 0 and new_h > 0:
                    source_frame = cv2.resize(source_frame, (new_w, new_h))
            
            # Quality-based blending
            quality_factor = self.grain_quality[i]
            mix_factor = self.grain_alphas[i] * 0.05 * quality_factor
            
            # Blend grain into output
            output_frame = cv2.addWeighted(output_frame, 1.0, source_frame, mix_factor, 0)
        
        # Mix original with granular output (40% original, 60% granular)
        final_frame = cv2.addWeighted(current_frame, 0.4, output_frame, 0.6, 0)
        
        return final_frame
```

---

## Shader Architecture

### Vertex Shader (implicit)
The base `Effect` class provides a vertex shader that renders a full-screen quad with UV coordinates.

### Fragment Shader: `arbhar_granular_engine.frag`

```glsl
#version 330 core

in vec2 uv;
out vec4 fragColor;

// Texture array for storing last N frames
uniform sampler2DArray frame_buffer;
uniform int current_frame_index;
uniform int buffer_size;

// Arbhar parameters (0-10 range)
uniform float intensity;     // Controls grain spawn rate and density
uniform float spray;         // Randomizes temporal position
uniform float grain_pitch;   // Scales individual fragments
uniform float time;
uniform vec2 resolution;

// Hash function for pseudo-random numbers
float hash(float seed) {
    return fract(sin(seed) * 43758.5453);
}

// Hash function for 2D vectors
float hash(vec2 p) {
    return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
}

// Generate pseudo-random 2D vector
vec2 hash2(vec2 p) {
    p = vec2(dot(p, vec2(127.1, 311.7)), dot(p, vec2(269.5, 183.3)));
    return fract(sin(p) * 43758.5453);
}

// Granular effect implementation
vec3 arbhar_granular(vec2 coord) {
    // Normalize parameters to 0-1 range
    float normalized_intensity = intensity / 10.0;
    float normalized_spray = spray / 10.0;
    float normalized_grain_pitch = grain_pitch / 10.0;
    
    // Calculate grain size based on grain_pitch
    float grain_size = max(0.01, 0.1 - normalized_grain_pitch * 0.09);
    
    // Grid-based grain positioning
    vec2 grid_coord = floor(coord / grain_size);
    
    // Add randomness based on spray parameter
    vec2 random_offset = vec2(0.0);
    if (normalized_spray > 0.0) {
        vec2 noise = hash2(grid_coord + time * 0.01);
        random_offset = (noise - 0.5) * normalized_spray * grain_size * 10.0;
    }
    
    // Apply random offset to grid coordinate
    vec2 sample_coord = grid_coord * grain_size + random_offset;
    
    // Ensure coordinates stay within bounds
    sample_coord = clamp(sample_coord, vec2(0.0), vec2(1.0));
    
    // Determine which frame to sample from based on intensity and spray
    float frame_selector = hash(grid_coord.x + grid_coord.y * 1000.0 + time * 0.1);
    
    // Intensity affects how much temporal variation we see
    frame_selector = mix(0.5, frame_selector, normalized_intensity);
    
    // Spray adds more randomness to frame selection
    if (normalized_spray > 0.0) {
        float spray_noise = hash(frame_selector + time * 0.2);
        frame_selector = mix(frame_selector, spray_noise, normalized_spray);
    }
    
    // Map frame selector to buffer index
    int frame_index = int(frame_selector * float(buffer_size - 1));
    
    // Ensure frame_index is within valid range
    frame_index = clamp(frame_index, 0, buffer_size - 1);
    
    // Sample from the selected frame in the texture array
    vec3 color = texture(frame_buffer, vec3(sample_coord, frame_index)).rgb;
    
    // Apply grain pitch effect as a scaling factor
    if (normalized_grain_pitch > 0.0) {
        // Add subtle color variation based on grain position
        vec3 pitch_effect = vec3(
            hash(grid_coord.x * 0.1),
            hash(grid_coord.y * 0.1),
            hash((grid_coord.x + grid_coord.y) * 0.05)
        );
        color = mix(color, color * pitch_effect, normalized_grain_pitch * 0.3);
    }
    
    return color;
}

void main() {
    // Apply the granular effect
    vec3 granular_color = arbhar_granular(uv);
    
    // Output final color
    fragColor = vec4(granular_color, 1.0);
}
```

**Shader Key Points:**
- Uses `sampler2DArray` to access multiple frames from the circular buffer
- Grid-based grain positioning: `grain_size` decreases as `grain_pitch` increases
- Hash functions provide deterministic pseudo-randomness based on grid coordinates and time
- `frame_selector` determines which historical frame to sample; controlled by `intensity` and `spray`
- `normalized_grain_pitch` adds subtle color variation to grains for artistic effect
- The shader runs entirely on GPU; CPU only sets uniforms and manages buffer

---

## Audio Reactivity

The `update(signals)` method maps audio features to effect parameters:

- **Treble** → `intensity` (grain density)
- **Bass** → `spray` (temporal randomization)
- **Mid** → `grain_pitch` (pitch shifting)

Each mapping uses:
```python
target_param = signal_value * 10.0 * self.audio_reactivity["intensity"]
current_param = lerp(current_param, target_param, smoothing)
```

The `audio_reactivity["intensity"]` acts as a global sensitivity multiplier (default 0.5). The `smoothing` parameter (default 0.1) creates exponential smoothing: `new = old * 0.9 + target * 0.1`.

---

## Circular Buffer Management

The circular buffer stores the last `buffer_size = buffer_length * fps` frames. For 8 seconds at 60fps, that's 480 frames.

**Adding a frame:**
```python
def add_frame_to_buffer(self, frame: np.ndarray):
    self.ring_buffer[self.buffer_write_index] = frame.copy()
    self.buffer_write_index = (self.buffer_write_index + 1) % self.buffer_size
    self.frames_recorded = min(self.frames_recorded + 1, self.buffer_size)
```

**Accessing a frame:** Use modulo indexing: `self.ring_buffer[grain_pos % self.buffer_size]`.

The buffer must be filled with at least 30 frames (0.5 seconds) before grains can spawn.

---

## Quality Modes

Quality modes affect the CPU-side blending and potential shader complexity:

| Mode | Value | CPU Factor | Description |
|------|-------|------------|-------------|
| lo-fi | 0.0 | 0.3x | Minimal blending, fewer grains, more artifacts |
| standard | 5.0 | 0.7x | Balanced quality (default) |
| hi-fi | 10.0 | 1.0x | Full blending, all grains, highest fidelity |

In the CPU fallback, `quality_factor` scales the `mix_factor` in `cv2.addWeighted`. In the GPU shader, quality could affect grain size distribution or number of samples.

---

## Grain Lifecycle

1. **Spawn**: When `random.random() < spawn_rate` (spawn_rate = intensity * 0.05), a new grain is created at a random buffer position.
2. **Initialize**: Grain gets random size (0.1-0.5), alpha (0.3-0.7), and initial position.
3. **Update**: Each frame:
   - Position drifts by `(random - 0.5) * spray * 0.1`
   - Pitch is set to `1.0 + (grain_pitch - 5.0) * 0.1`
   - Alpha decays by 0.005 per frame
   - Quality factor is updated from current quality mode
4. **Death**: When alpha reaches 0, the grain is removed (by decrementing `active_grains` and shifting arrays). The legacy code doesn't explicitly show death handling; it likely relies on alpha decay and skipping zero-alpha grains in rendering. A robust implementation would cull dead grains.

---

## Integration

### VJLive3 Pipeline

The effect should be added to the effects chain as a video processor:

```python
# Initialization
arbhar = ArbharGranularEngine()
arbhar.load()  # Load shader
arbhar.set_parameter("intensity", 5.0)
arbhar.set_parameter("spray", 2.0)
arbhar.set_parameter("grain_pitch", 5.0)

# Each frame:
# 1. Add current frame to buffer
arbhar.add_frame_to_buffer(current_frame)

# 2. Update parameters from audio
arbhar.update(signals)  # signals = {"bass": 0.7, "mid": 0.5, "treble": 0.9}

# 3. Render effect (either via shader or CPU fallback)
processed_frame = arbhar.draw(current_frame)  # or arbhar.render() if using GPU
```

The effect expects the base class to manage OpenGL context and shader compilation. The `draw()` method shown above is a CPU fallback; the real implementation should use the GPU shader for performance.

### Audio Integration

Audio analysis is external. The `signals` dictionary should contain normalized values (0.0-1.0) for at least some of: `bass`, `mid`, `treble`. The effect's `audio_reactivity["intensity"]` scales these signals before applying to parameters.

---

## Performance

### Computational Cost

- **CPU (fallback path)**:
  - Buffer management: O(1) per frame (just storing a frame copy)
  - Grain update: O(max_grains) = O(32) per frame - negligible
  - Rendering: O(active_grains * frame_pixels) - very high! Each grain does a full-frame blend via `cv2.addWeighted`. This is why GPU shader is essential.
- **GPU (shader path)**:
  - Fragment shader runs once per pixel (e.g., 2M pixels at 1080p)
  - Per-pixel: hash computations, texture array fetch, color mixing
  - Texture array bandwidth: reading from a 480-frame texture array is heavy but cache-coherent
  - Expected cost: moderate to high, but should be okay on modern GPUs with enough VRAM

### Memory Usage

- **CPU**: Ring buffer stores `buffer_size` frames. At 1080p (1920x1080x3 ≈ 6MB per frame), 480 frames ≈ 2.88 GB. This is **very high**; likely the legacy used a smaller buffer or compressed frames. The spec should note this as a potential issue.
- **GPU**: Texture array of same size: 480 × 6MB ≈ 2.88 GB VRAM. This is unrealistic for embedded systems. The legacy may have used a smaller buffer (e.g., 60 frames = 1 second) or lower resolution.
- **Grain arrays**: 32 elements × 5 arrays ≈ 160 floats ≈ 1.3 KB - negligible

### Optimization Strategies

- Reduce `buffer_size` (shorter history) to lower memory
- Use lower resolution for buffer frames (e.g., half-size)
- Implement the shader path (mandatory for performance)
- Limit `max_grains` on low-end hardware
- Use integer texture formats or compression for the texture array

### Platform-Specific Considerations

- **Desktop**: Should handle 480-frame buffer at 1080p with 4+ GB VRAM
- **Embedded (Orange Pi 5)**: May need to reduce buffer to 60-120 frames and/or use 720p
- **Memory constraints**: The 8-second buffer at full resolution is the biggest risk; consider making buffer size configurable

---

## Error Cases

- **No shader file**: `load()` returns False; effect should fall back to CPU implementation or disable gracefully.
- **Buffer not ready**: If `frames_recorded < 30`, `draw()` returns original frame unchanged.
- **Parameter out of range**: `set_parameter` clamps to [0,10] and raises `ValueError` for unknown names.
- **Audio signals missing**: `update()` simply doesn't adjust those parameters; current values persist.
- **Frame buffer corruption**: If a frame in the ring buffer is None (not yet written), it's skipped during rendering.
- **OpenCV missing**: The CPU fallback uses `cv2.addWeighted`; if `cv2` is unavailable, the effect should fall back to a simple blend or raise an error at initialization.
- **Texture array limits**: OpenGL has limits on texture array layers (typically 256 or 512). 480 layers may exceed some implementations. Should check `GL_MAX_ARRAY_TEXTURE_LAYERS` and reduce buffer if needed.

---

## Configuration Schema

```python
METADATA = {
  "params": [
    {
      "id": "intensity",
      "name": "Grain Intensity",
      "default": 0.0,
      "min": 0.0,
      "max": 10.0,
      "type": "float",
      "description": "Controls grain spawn rate and density; also scales audio reactivity"
    },
    {
      "id": "spray",
      "name": "Temporal Spray",
      "default": 0.0,
      "min": 0.0,
      "max": 10.0,
      "type": "float",
      "description": "Randomizes grain temporal positions; creates more chaotic, scattered grains"
    },
    {
      "id": "grain_pitch",
      "name": "Grain Pitch",
      "default": 0.0,
      "min": 0.0,
      "max": 10.0,
      "type": "float",
      "description": "Scales grain UV sampling; higher values create smaller, more numerous grains with color variation"
    },
    {
      "id": "audio_reactivity_intensity",
      "name": "Audio Reactivity Intensity",
      "default": 0.5,
      "min": 0.0,
      "max": 1.0,
      "type": "float",
      "description": "Sensitivity multiplier for audio-driven parameter modulation"
    },
    {
      "id": "audio_reactivity_smoothing",
      "name": "Audio Reactivity Smoothing",
      "default": 0.1,
      "min": 0.0,
      "max": 1.0,
      "type": "float",
      "description": "Smoothing factor for audio-driven parameter changes (0=instant, 1=very slow)"
    }
  ],
  "quality_modes": {
    "lo-fi": {"value": 0.0, "description": "Minimal processing, lowest CPU cost"},
    "standard": {"value": 5.0, "description": "Balanced quality and performance (default)"},
    "hi-fi": {"value": 10.0, "description": "Maximum quality, highest CPU cost"}
  }
}
```

---

## State Management

- **Per-frame state**: `frame_count`, `last_update_time` (for dt calculation)
- **Persistent state**: Parameters (`intensity`, `spray`, `grain_pitch`), `audio_reactivity` dict, `current_quality`, `ring_buffer`, grain arrays
- **Init-once state**: Shader program, uniform locations, random seed
- **Thread safety**: Not thread-safe; must be called from rendering thread. The circular buffer and grain arrays need protection if accessed from multiple threads.

The effect maintains a large circular buffer in CPU memory; this state persists across frames and must be preserved when the effect is paused/resumed.

---

## GPU Resources

- **Texture array**: `sampler2DArray` containing `buffer_size` layers of 2D frames. This is the largest resource.
- **Shader program**: Fragment shader with hash functions and texture array sampling.
- **Uniforms**: `intensity`, `spray`, `grain_pitch`, `time`, `resolution`, `buffer_size`, `current_frame_index` (if needed)
- **No FBO** required if rendering directly to screen; if effect chain uses FBOs, the effect renders to an intermediate texture.

The texture array must be updated each frame with the latest circular buffer contents. This is a significant bandwidth cost: uploading 480 frames (2.88 GB) per frame is impossible. Therefore, the texture array should be managed as a **ring texture** where only new frames are updated, and the shader samples from the existing array that is continuously refreshed in a circular manner. The `current_frame_index` uniform would indicate the most recent frame, and older frames are at indices modulo `buffer_size`.

---

## OpenGL.GL Fallback

If the GPU shader path is unavailable (driver issues, hardware limitations), the effect can fall back to the CPU implementation using OpenCV. The fallback is much slower and may not achieve real-time performance at high resolutions, but it provides a functional degradation path.

The fallback should be automatically selected if shader compilation fails or if `cv2` is the only available path. The `BaseEffect` class could provide a `use_gpu` flag.

---

## Test Plan (Enhanced)

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init` | All arrays initialized to correct sizes, defaults set |
| `test_load_shader_success` | Shader file loads when present |
| `test_load_shader_failure` | Returns False when shader missing |
| `update_treble_maps_to_intensity` | Treble signal increases intensity |
| `update_bass_maps_to_spray` | Bass signal increases spray |
| `update_mid_maps_to_grain_pitch` | Mid signal increases grain_pitch |
| `test_smoothing_math` | Smoothing interpolation works correctly |
| `test_parameter_clamping` | Values outside [0,10] are clamped |
| `test_spawn_grain` | New grain added when conditions met |
| `test_spawn_limited_to_max` | active_grains never exceeds max_grains |
| `test_grain_alpha_decay` | Alpha decreases each update |
| `test_circular_buffer_wrap` | Write index wraps correctly at buffer_size |
| `test_buffer_grows_until_full` | frames_recorded increases to buffer_size then stops |
| `test_add_frame_to_buffer` | Frame is stored and can be retrieved |
| `test_draw_requires_buffer_ready` | Returns original frame if buffer has <30 frames |
| `test_quality_factor_lo_fi` | _get_quality_factor returns 0.3 for lo-fi |
| `test_quality_factor_standard` | Returns 0.7 for standard |
| `test_quality_factor_hi_fi` | Returns 1.0 for hi-fi |
| `test_mix_weights` | Final blend is 40% original, 60% granular |
| `test_cleanup` | No resource leaks (frames, textures) on deletion |

**Minimum coverage**: 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-X] P3-EXT007: Port ArbharGranularEngine to VJLive3` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES

### vjlive1/effects/arbhar_granular_engine.py (L1-20)
```python
import numpy as np
from typing import Dict, Any
import os
import time
import random
import cv2
from core.base_effect import BaseEffect
from core.video_buffer_manager import get_buffer_manager, VideoBufferConfig

class ArbharGranularEngine(BaseEffect):
    """
    Arbhar Granular Engine - Advanced Granular Synthesis System
    
    Implements a sophisticated granular synthesis engine with:
    - Variable grain density and temporal randomization
    - Pitch shifting and UV scaling
    - Circular buffer management
    - Audio-reactive parameter control
    - Multiple quality modes
    """
```

### vjlive1/effects/arbhar_granular_engine.py (L17-36)
```python
    - Circular buffer management
    - Audio-reactive parameter control
    - Multiple quality modes
    """
    
    def __init__(self):
        super().__init__()
        self.name = "Arbhar Granular Engine"
        self.shader_path = "effects/shaders/shaders/arbhar_granular_engine.frag"
        self.is_loaded = False
        
        # Effect parameters (0.0-10.0 range)
        self.intensity = 0.0      # Controls grain spawn rate and density
        self.spray = 0.0         # Controls temporal randomization
        self.grain_pitch = 0.0    # Controls individual grain UV scaling
        self.is_loaded = False
        
        # Buffer configuration
        self.buffer_length = 8.0  # seconds
        self.fps = 60.0
```

### vjlive1/effects/arbhar_granular_engine.py (L33-52)
```python
        # Buffer configuration
        self.buffer_length = 8.0  # seconds
        self.fps = 60.0
        self.buffer_size = int(self.buffer_length * self.fps)
        
        # Circular buffer for frame storage
        self.ring_buffer = [None] * self.buffer_size
        self.buffer_write_index = 0
        self.frames_recorded = 0
        
        # Grain management
        self.max_grains = 32
        self.active_grains = 0
        self.grain_positions = [0.0] * self.max_grains
        self.grain_sizes = [0.0] * self.max_grains
        self.grain_pitches = [0.0] * self.max_grains
        self.grain_alphas = [0.0] * self.max_grains
        self.grain_quality = [0.0] * self.max_grains
```

### vjlive1/effects/arbhar_granular_engine.py (L49-68)
```python
        self.grain_pitches = [0.0] * self.max_grains
        self.grain_alphas = [0.0] * self.max_grains
        self.grain_quality = [0.0] * self.max_grains
        
        # Audio reactivity settings
        self.audio_reactivity = {
            "intensity": 0.5,  # Sensitivity to audio signals
            "smoothing": 0.1   # Smoothing factor for parameter changes
        }
        
        # Quality modes
        self.quality_modes = {
            "lo-fi": 0.0,
            "standard": 5.0,
            "hi-fi": 10.0
        }
        self.current_quality = "standard"
        
        # Internal state
        self.last_update_time = 0.0
```

### vjlive1/effects/arbhar_granular_engine.py (L65-84)
```python
        self.current_quality = "standard"
        
        # Internal state
        self.last_update_time = 0.0
        self.frame_count = 0
        self.seed = int(time.time())
        random.seed(self.seed)
        
    def load(self):
        """Load the associated .frag shader file."""
        print(f"Loading Arbhar Granular Engine shader from {self.shader_path}")
        if os.path.exists(self.shader_path):
            self.is_loaded = True
            print("Arbhar Granular Engine shader loaded successfully.")
        else:
            print("Warning: .frag file for Arbhar Granular Engine not found.")
            self.is_loaded = False
```

### vjlive1/effects/arbhar_granular_engine.py (L81-100)
```python
            self.is_loaded = False
    
    def update(self, signals: Dict[str, Any]):
        """
        Update effect parameters based on incoming signals.
        
        Args:
            signals (Dict[str, Any]): A dictionary of realtime signals 
                                 (e.g., 'bass', 'treble', 'bpm', 'midi_cc_1').
        """
        current_time = time.time()
        dt = current_time - self.last_update_time
        self.last_update_time = current_time
        
        # Map audio signals to effect parameters with smoothing
        if "treble" in signals:
            target_intensity = signals["treble"] * 10.0 * self.audio_reactivity["intensity"]
            self.intensity = (self.intensity * (1.0 - self.audio_reactivity["smoothing"]) + 
                             target_intensity * self.audio_reactivity["smoothing"])
```

### vjlive1/effects/arbhar_granular_engine.py (L97-116)
```python
            target_intensity = signals["treble"] * 10.0 * self.audio_reactivity["intensity"]
            self.intensity = (self.intensity * (1.0 - self.audio_reactivity["smoothing"]) + 
                             target_intensity * self.audio_reactivity["smoothing"])
        
        if "bass" in signals:
            target_spray = signals["bass"] * 10.0 * self.audio_reactivity["intensity"]
            self.spray = (self.spray * (1.0 - self.audio_reactivity["smoothing"]) + 
                         target_spray * self.audio_reactivity["smoothing"])
        
        if "mid" in signals:
            target_pitch = signals["mid"] * 10.0 * self.audio_reactivity["intensity"]
            self.grain_pitch = (self.grain_pitch * (1.0 - self.audio_reactivity["smoothing"]) + 
                               target_pitch * self.audio_reactivity["smoothing"])
        
        # Ensure parameters stay within 0-10 range
        self.intensity = max(0.0, min(10.0, self.intensity))
        self.spray = max(0.0, min(10.0, self.spray))
        self.grain_pitch = max(0.0, min(10.0, self.grain_pitch))
        
        # Update grain parameters based on main parameters
```

### vjlive1/effects/arbhar_granular_engine.py (L113-132)
```python
        self.spray = max(0.0, min(10.0, self.spray))
        self.grain_pitch = max(0.0, min(10.0, self.grain_pitch))
        
        # Update grain parameters based on main parameters
        self._update_grain_parameters()
    
    def _update_grain_parameters(self):
        """Update individual grain parameters based on main effect parameters."""
        # Calculate grain spawn rate based on intensity
        spawn_rate = self.intensity * 0.05  # 0-1.6 grains per frame at max intensity
        
        # Spawn new grains if needed
        if random.random() < spawn_rate:
            self._spawn_grain()
        
        # Update existing grains
        for i in range(self.active_grains):
            # Apply temporal randomization (spray)
            self.grain_positions[i] += (random.random() - 0.5) * self.spray * 0.1
            
            # Apply pitch shifting
            self.grain_pitches[i] = 1.0 + (self.grain_pitch - 5.0) * 0.1
            
            # Apply quality-based processing
            quality_factor = self._get_quality_factor()
            self.grain_quality[i] = quality_factor
            
            # Apply alpha envelope
            self.grain_alphas[i] = max(0.0, self.grain_alphas[i] - 0.005)  # Slower decay
```

### vjlive1/effects/arbhar_granular_engine.py (L129-148)
```python
        for i in range(self.active_grains):
            # Apply temporal randomization (spray)
            self.grain_positions[i] += (random.random() - 0.5) * self.spray * 0.1
            
            # Apply pitch shifting
            self.grain_pitches[i] = 1.0 + (self.grain_pitch - 5.0) * 0.1
            
            # Apply quality-based processing
            quality_factor = self._get_quality_factor()
            self.grain_quality[i] = quality_factor
            
            # Apply alpha envelope
            self.grain_alphas[i] = max(0.0, self.grain_alphas[i] - 0.005)  # Slower decay
    
    def _get_quality_factor(self) -> float:
        """Get quality factor based on current quality mode."""
        if self.current_quality == "lo-fi":
            return 0.3  # Low quality, more artifacts
        elif self.current_quality == "standard":
            return 0.7  # Standard quality
```

### vjlive1/effects/arbhar_granular_engine.py (L145-164)
```python
        if self.current_quality == "lo-fi":
            return 0.3  # Low quality, more artifacts
        elif self.current_quality == "standard":
            return 0.7  # Standard quality
        elif self.current_quality == "hi-fi":
            return 1.0  # High quality, minimal artifacts
        return 0.7
    
    def _spawn_grain(self):
        """Spawn a new grain from the buffer."""
        if self.frames_recorded < 30:  # Need at least 0.5 seconds of buffer
            return
        
        if self.active_grains < self.max_grains:
            grain_index = self.active_grains
            self.active_grains += 1
            
            # Random position in buffer
            self.grain_positions[grain_index] = random.randint(0, self.frames_recorded - 1)
```

### vjlive1/effects/arbhar_granular_engine.py (L161-180)
```python
            self.grain_positions[grain_index] = random.randint(0, self.frames_recorded - 1)
            
            # Random size (duration)
            self.grain_sizes[grain_index] = random.uniform(0.1, 0.5)
            
            # Initial alpha (opacity)
            self.grain_alphas[grain_index] = random.uniform(0.3, 0.7)
            
            # Pitch is set in _update_grain_parameters
    
    def add_frame_to_buffer(self, frame: np.ndarray):
        """Add a frame to the circular buffer."""
        # Store frame in ring buffer
        self.ring_buffer[self.buffer_write_index] = frame.copy()
        
        # Update indices
        self.buffer_write_index = (self.buffer_write_index + 1) % self.buffer_size
        self.frames_recorded = min(self.frames_recorded + 1, self.buffer_size)
```

### vjlive1/effects/arbhar_granular_engine.py (L177-196)
```python
        # Update indices
        self.buffer_write_index = (self.buffer_write_index + 1) % self.buffer_size
        self.frames_recorded = min(self.frames_recorded + 1, self.buffer_size)
    
    def get_metadata(self) -> Dict[str, Any]:
        """Metadata for the effect."""
        return {
            "name": "Arbhar Granular Engine",
            "description": "Advanced granular synthesis with variable density, pitch shifting, temporal randomization, and multiple quality modes",
            "tags": ["granular", "synthesis", "audio-reactive", "buffer", "pitch-shift", "quality-modes"],
            "parameters": {
                "intensity": "Controls grain spawn rate and density",
                "spray": "Controls temporal randomization of grain positions",
                "grain_pitch": "Controls individual grain UV scaling and pitch shifting",
                "quality": "Selects quality mode: lo-fi (0.0), standard (5.0), hi-fi (10.0)"
            },
            "performance": {
                "complexity": "High",
                "cpu_cost": "High",
                "gpu_cost": "Medium",
                "memory_usage": "High"
            }
        }
```

### effects/shaders/shaders/arbhar_granular_engine.frag (L1-20)
```glsl
#version 330 core

in vec2 uv;
out vec4 fragColor;

// Texture array for storing last 60 frames
uniform sampler2DArray frame_buffer;
uniform int current_frame_index;
uniform int buffer_size;

// Arbhar parameters
uniform float intensity;     // 0-10: Controls seeding density
uniform float spray;         // 0-10: Randomizes temporal position
uniform float grain_pitch;   // 0-10: Scales individual fragments
uniform float time;
uniform vec2 resolution;

// Hash function for pseudo-random numbers
float hash(float seed) {
    return fract(sin(seed) * 43758.5453);
}
```

### effects/shaders/shaders/arbhar_granular_engine.frag (L17-36)
```glsl

// Hash function for pseudo-random numbers
float hash(float seed) {
    return fract(sin(seed) * 43758.5453);
}

// Hash function for 2D vectors
float hash(vec2 p) {
    return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
}

// Generate pseudo-random 2D vector
vec2 hash2(vec2 p) {
    p = vec2(dot(p, vec2(127.1, 311.7)), dot(p, vec2(269.5, 183.3)));
    return fract(sin(p) * 43758.5453);
}

// Granular effect implementation
vec3 arbhar_granular(vec2 coord) {
    // Normalize parameters to 0-1 range
```

### effects/shaders/shaders/arbhar_granular_engine.frag (L33-52)
```glsl

// Granular effect implementation
vec3 arbhar_granular(vec2 coord) {
    // Normalize parameters to 0-1 range
    float normalized_intensity = intensity / 10.0;
    float normalized_spray = spray / 10.0;
    float normalized_grain_pitch = grain_pitch / 10.0;
    
    // Calculate grain size based on grain_pitch
    float grain_size = max(0.01, 0.1 - normalized_grain_pitch * 0.09);
    
    // Grid-based grain positioning
    vec2 grid_coord = floor(coord / grain_size);
    
    // Add randomness based on spray parameter
    vec2 random_offset = vec2(0.0);
    if (normalized_spray > 0.0) {
        vec2 noise = hash2(grid_coord + time * 0.01);
        random_offset = (noise - 0.5) * normalized_spray * grain_size * 10.0;
    }
```

### effects/shaders/shaders/arbhar_granular_engine.frag (L49-68)
```glsl
    if (normalized_spray > 0.0) {
        vec2 noise = hash2(grid_coord + time * 0.01);
        random_offset = (noise - 0.5) * normalized_spray * grain_size * 10.0;
    }
    
    // Apply random offset to grid coordinate
    vec2 sample_coord = grid_coord * grain_size + random_offset;
    
    // Ensure coordinates stay within bounds
    sample_coord = clamp(sample_coord, vec2(0.0), vec2(1.0));
    
    // Determine which frame to sample from based on intensity and spray
    float frame_selector = hash(grid_coord.x + grid_coord.y * 1000.0 + time * 0.1);
    
    // Intensity affects how much temporal variation we sees
    frame_selector = mix(0.5, frame_selector, normalized_intensity);
    
    // Spray adds more randomness to frame selection
    if (normalized_spray > 0.0) {
        float spray_noise = hash(frame_selector + time * 0.2);
```

### effects/shaders/shaders/arbhar_granular_engine.frag (L65-84)
```glsl
    
    // Spray adds more randomness to frame selection
    if (normalized_spray > 0.0) {
        float spray_noise = hash(frame_selector + time * 0.2);
        frame_selector = mix(frame_selector, spray_noise, normalized_spray);
    }
    
    // Map frame selector to buffer index
    int frame_index = int(frame_selector * float(buffer_size - 1));
    
    // Ensure frame_index is within valid range
    frame_index = clamp(frame_index, 0, buffer_size - 1);
    
    // Sample from the selected frame in the texture array
    vec3 color = texture(frame_buffer, vec3(sample_coord, frame_index)).rgb;
    
    // Apply grain pitch effect as a scaling factor
    if (normalized_grain_pitch > 0.0) {
        // Add subtle color variation based on grain position
        vec3 pitch_effect = vec3(
```

### effects/shaders/shaders/arbhar_granular_engine.frag (L81-100)
```glsl
    // Apply grain pitch effect as a scaling factor
    if (normalized_grain_pitch > 0.0) {
        // Add subtle color variation based on grain position
        vec3 pitch_effect = vec3(
            hash(grid_coord.x * 0.1),
            hash(grid_coord.y * 0.1),
            hash((grid_coord.x + grid_coord.y) * 0.05)
        );
        color = mix(color, color * pitch_effect, normalized_grain_pitch * 0.3);
    }
    
    return color;
}

void main() {
    // Apply the granular effect
    vec3 granular_color = arbhar_granular(uv);
    
    // Output final color
    fragColor = vec4(granular_color, 1.0);
}
```

---

## Error Cases

- **No shader file**: `load()` returns False; effect should fall back to CPU implementation or disable gracefully.
- **Buffer not ready**: If `frames_recorded < 30`, `draw()` returns original frame unchanged.
- **Parameter out of range**: `set_parameter` clamps to [0,10] and raises `ValueError` for unknown names.
- **Audio signals missing**: `update()` simply doesn't adjust those parameters; current values persist.
- **Frame buffer corruption**: If a frame in the ring buffer is None (not yet written), it's skipped during rendering.
- **OpenCV missing**: The CPU fallback uses `cv2.addWeighted`; if `cv2` is unavailable, the effect should fall back to a simple blend or raise an error at initialization.
- **Texture array limits**: OpenGL has limits on texture array layers (typically 256 or 512). 480 layers may exceed some implementations. Should check `GL_MAX_ARRAY_TEXTURE_LAYERS` and reduce buffer if needed.

---

## Performance Considerations

The effect is **memory-intensive** due to the circular buffer storing many full-resolution frames. At 1080p (1920x1080x3 ≈ 6MB per frame), an 8-second buffer at 60fps requires 480 × 6MB ≈ 2.88 GB of RAM/VRAM. This is a significant requirement. The VJLive3 architecture may mitigate this by:

- Using a lower resolution for the buffer (e.g., 960x540)
- Using a shorter buffer (e.g., 2 seconds = 120 frames)
- Compressing frames (e.g., JPEG or DXT compression) in the texture array

The spec should make the buffer size configurable or at least note the memory impact.

The GPU shader is efficient per-pixel, but the texture array fetch from 480 layers could be bandwidth-heavy. Modern GPUs with large L2 caches should handle it, but it's a consideration.

---

## OpenGL.GL Fallback

If the GPU shader path is unavailable (driver issues, hardware limitations), the effect can fall back to the CPU implementation using OpenCV. The fallback is much slower and may not achieve real-time performance at high resolutions, but it provides a functional degradation path.

The fallback should be automatically selected if shader compilation fails or if `cv2` is the only available path. The `BaseEffect` class could provide a `use_gpu` flag.

---

## State Management

- **Per-frame state**: `frame_count`, `last_update_time` (for dt calculation)
- **Persistent state**: Parameters (`intensity`, `spray`, `grain_pitch`), `audio_reactivity` dict, `current_quality`, `ring_buffer`, grain arrays
- **Init-once state**: Shader program, uniform locations, random seed
- **Thread safety**: Not thread-safe; must be called from rendering thread. The circular buffer and grain arrays need protection if accessed from multiple threads.

The effect maintains a large circular buffer in CPU memory; this state persists across frames and must be preserved when the effect is paused/resumed.

---

## GPU Resources

- **Texture array**: `sampler2DArray` containing `buffer_size` layers of 2D frames. This is the largest resource.
- **Shader program**: Fragment shader with hash functions and texture array sampling.
- **Uniforms**: `intensity`, `spray`, `grain_pitch`, `time`, `resolution`, `buffer_size`, `current_frame_index` (if needed)
- **No FBO** required if rendering directly to screen; if effect chain uses FBOs, the effect renders to an intermediate texture.

The texture array must be updated each frame with the latest circular buffer contents. This is a significant bandwidth cost: uploading 480 frames (2.88 GB) per frame is impossible. Therefore, the texture array should be managed as a **ring texture** where only new frames are updated, and the shader samples from the existing array that is continuously refreshed in a circular manner. The `current_frame_index` uniform would indicate the most recent frame, and older frames are at indices modulo `buffer_size`.

---

## Configuration Schema

```python
METADATA = {
  "params": [
    {
      "id": "intensity",
      "name": "Grain Intensity",
      "default": 0.0,
      "min": 0.0,
      "max": 10.0,
      "type": "float",
      "description": "Controls grain spawn rate and density; also scales audio reactivity"
    },
    {
      "id": "spray",
      "name": "Temporal Spray",
      "default": 0.0,
      "min": 0.0,
      "max": 10.0,
      "type": "float",
      "description": "Randomizes grain temporal positions; creates more chaotic, scattered grains"
    },
    {
      "id": "grain_pitch",
      "name": "Grain Pitch",
      "default": 0.0,
      "min": 0.0,
      "max": 10.0,
      "type": "float",
      "description": "Scales grain UV sampling; higher values create smaller, more numerous grains with color variation"
    },
    {
      "id": "audio_reactivity_intensity",
      "name": "Audio Reactivity Intensity",
      "default": 0.5,
      "min": 0.0,
      "max": 1.0,
      "type": "float",
      "description": "Sensitivity multiplier for audio-driven parameter modulation"
    },
    {
      "id": "audio_reactivity_smoothing",
      "name": "Audio Reactivity Smoothing",
      "default": 0.1,
      "min": 0.0,
      "max": 1.0,
      "type": "float",
      "description": "Smoothing factor for audio-driven parameter changes (0=instant, 1=very slow)"
    }
  ],
  "quality_modes": {
    "lo-fi": {"value": 0.0, "description": "Minimal processing, lowest CPU cost"},
    "standard": {"value": 5.0, "description": "Balanced quality and performance (default)"},
    "hi-fi": {"value": 10.0, "description": "Maximum quality, highest CPU cost"}
  }
}
```

---

## Test Plan (Enhanced)

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init` | All arrays initialized to correct sizes, defaults set |
| `test_load_shader_success` | Shader file loads when present |
| `test_load_shader_failure` | Returns False when shader missing |
| `update_treble_maps_to_intensity` | Treble signal increases intensity |
| `update_bass_maps_to_spray` | Bass signal increases spray |
| `update_mid_maps_to_grain_pitch` | Mid signal increases grain_pitch |
| `test_smoothing_math` | Smoothing interpolation works correctly |
| `test_parameter_clamping` | Values outside [0,10] are clamped |
| `test_spawn_grain` | New grain added when conditions met |
| `test_spawn_limited_to_max` | active_grains never exceeds max_grains |
| `test_grain_alpha_decay` | Alpha decreases each update |
| `test_circular_buffer_wrap` | Write index wraps correctly at buffer_size |
| `test_buffer_grows_until_full` | frames_recorded increases to buffer_size then stops |
| `test_add_frame_to_buffer` | Frame is stored and can be retrieved |
| `test_draw_requires_buffer_ready` | Returns original frame if buffer has <30 frames |
| `test_quality_factor_lo_fi` | _get_quality_factor returns 0.3 for lo-fi |
| `test_quality_factor_standard` | Returns 0.7 for standard |
| `test_quality_factor_hi_fi` | Returns 1.0 for hi-fi |
| `test_mix_weights` | Final blend is 40% original, 60% granular |
| `test_cleanup` | No resource leaks (frames, textures) on deletion |

**Minimum coverage**: 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-X] P3-EXT007: Port ArbharGranularEngine to VJLive3` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES

### vjlive1/effects/arbhar_granular_engine.py (L1-20)
```python
import numpy as np
from typing import Dict, Any
import os
import time
import random
import cv2
from core.base_effect import BaseEffect
from core.video_buffer_manager import get_buffer_manager, VideoBufferConfig

class ArbharGranularEngine(BaseEffect):
    """
    Arbhar Granular Engine - Advanced Granular Synthesis System
    
    Implements a sophisticated granular synthesis engine with:
    - Variable grain density and temporal randomization
    - Pitch shifting and UV scaling
    - Circular buffer management
    - Audio-reactive parameter control
    - Multiple quality modes
    """
```

### vjlive1/effects/arbhar_granular_engine.py (L17-36)
```python
    - Circular buffer management
    - Audio-reactive parameter control
    - Multiple quality modes
    """
    
    def __init__(self):
        super().__init__()
        self.name = "Arbhar Granular Engine"
        self.shader_path = "effects/shaders/shaders/arbhar_granular_engine.frag"
        self.is_loaded = False
        
        # Effect parameters (0.0-10.0 range)
        self.intensity = 0.0      # Controls grain spawn rate and density
        self.spray = 0.0         # Controls temporal randomization
        self.grain_pitch = 0.0    # Controls individual grain UV scaling
        self.is_loaded = False
        
        # Buffer configuration
        self.buffer_length = 8.0  # seconds
        self.fps = 60.0
```

### vjlive1/effects/arbhar_granular_engine.py (L33-52)
```python
        # Buffer configuration
        self.buffer_length = 8.0  # seconds
        self.fps = 60.0
        self.buffer_size = int(self.buffer_length * self.fps)
        
        # Circular buffer for frame storage
        self.ring_buffer = [None] * self.buffer_size
        self.buffer_write_index = 0
        self.frames_recorded = 0
        
        # Grain management
        self.max_grains = 32
        self.active_grains = 0
        self.grain_positions = [0.0] * self.max_grains
        self.grain_sizes = [0.0] * self.max_grains
        self.grain_pitches = [0.0] * self.max_grains
        self.grain_alphas = [0.0] * self.max_grains
        self.grain_quality = [0.0] * self.max_grains
```

### vjlive1/effects/arbhar_granular_engine.py (L49-68)
```python
        self.grain_pitches = [0.0] * self.max_grains
        self.grain_alphas = [0.0] * self.max_grains
        self.grain_quality = [0.0] * self.max_grains
        
        # Audio reactivity settings
        self.audio_reactivity = {
            "intensity": 0.5,  # Sensitivity to audio signals
            "smoothing": 0.1   # Smoothing factor for parameter changes
        }
        
        # Quality modes
        self.quality_modes = {
            "lo-fi": 0.0,
            "standard": 5.0,
            "hi-fi": 10.0
        }
        self.current_quality = "standard"
        
        # Internal state
        self.last_update_time = 0.0
```

### vjlive1/effects/arbhar_granular_engine.py (L65-84)
```python
        self.current_quality = "standard"
        
        # Internal state
        self.last_update_time = 0.0
        self.frame_count = 0
        self.seed = int(time.time())
        random.seed(self.seed)
        
    def load(self):
        """Load the associated .frag shader file."""
        print(f"Loading Arbhar Granular Engine shader from {self.shader_path}")
        if os.path.exists(self.shader_path):
            self.is_loaded = True
            print("Arbhar Granular Engine shader loaded successfully.")
        else:
            print("Warning: .frag file for Arbhar Granular Engine not found.")
            self.is_loaded = False
```

### vjlive1/effects/arbhar_granular_engine.py (L81-100)
```python
            self.is_loaded = False
    
    def update(self, signals: Dict[str, Any]):
        """
        Update effect parameters based on incoming signals.
        
        Args:
            signals (Dict[str, Any]): A dictionary of realtime signals 
                                 (e.g., 'bass', 'treble', 'bpm', 'midi_cc_1').
        """
        current_time = time.time()
        dt = current_time - self.last_update_time
        self.last_update_time = current_time
        
        # Map audio signals to effect parameters with smoothing
        if "treble" in signals:
            target_intensity = signals["treble"] * 10.0 * self.audio_reactivity["intensity"]
            self.intensity = (self.intensity * (1.0 - self.audio_reactivity["smoothing"]) + 
                             target_intensity * self.audio_reactivity["smoothing"])
```

### vjlive1/effects/arbhar_granular_engine.py (L97-116)
```python
            target_intensity = signals["treble"] * 10.0 * self.audio_reactivity["intensity"]
            self.intensity = (self.intensity * (1.0 - self.audio_reactivity["smoothing"]) + 
                             target_intensity * self.audio_reactivity["smoothing"])
        
        if "bass" in signals:
            target_spray = signals["bass"] * 10.0 * self.audio_reactivity["intensity"]
            self.spray = (self.spray * (1.0 - self.audio_reactivity["smoothing"]) + 
                         target_spray * self.audio_reactivity["smoothing"])
        
        if "mid" in signals:
            target_pitch = signals["mid"] * 10.0 * self.audio_reactivity["intensity"]
            self.grain_pitch = (self.grain_pitch * (1.0 - self.audio_reactivity["smoothing"]) + 
                               target_pitch * self.audio_reactivity["smoothing"])
        
        # Ensure parameters stay within 0-10 range
        self.intensity = max(0.0, min(10.0, self.intensity))
        self.spray = max(0.0, min(10.0, self.spray))
        self.grain_pitch = max(0.0, min(10.0, self.grain_pitch))
        
        # Update grain parameters based on main parameters
```

### vjlive1/effects/arbhar_granular_engine.py (L113-132)
```python
        self.spray = max(0.0, min(10.0, self.spray))
        self.grain_pitch = max(0.0, min(10.0, self.grain_pitch))
        
        # Update grain parameters based on main parameters
        self._update_grain_parameters()
    
    def _update_grain_parameters(self):
        """Update individual grain parameters based on main effect parameters."""
        # Calculate grain spawn rate based on intensity
        spawn_rate = self.intensity * 0.05  # 0-1.6 grains per frame at max intensity
        
        # Spawn new grains if needed
        if random.random() < spawn_rate:
            self._spawn_grain()
        
        # Update existing grains
        for i in range(self.active_grains):
            # Apply temporal randomization (spray)
            self.grain_positions[i] += (random.random() - 0.5) * self.spray * 0.1
            
            # Apply pitch shifting
            self.grain_pitches[i] = 1.0 + (self.grain_pitch - 5.0) * 0.1
            
            # Apply quality-based processing
            quality_factor = self._get_quality_factor()
            self.grain_quality[i] = quality_factor
            
            # Apply alpha envelope
            self.grain_alphas[i] = max(0.0, self.grain_alphas[i] - 0.005)  # Slower decay
```

### vjlive1/effects/arbhar_granular_engine.py (L129-148)
```python
        for i in range(self.active_grains):
            # Apply temporal randomization (spray)
            self.grain_positions[i] += (random.random() - 0.5) * self.spray * 0.1
            
            # Apply pitch shifting
            self.grain_pitches[i] = 1.0 + (self.grain_pitch - 5.0) * 0.1
            
            # Apply quality-based processing
            quality_factor = self._get_quality_factor()
            self.grain_quality[i] = quality_factor
            
            # Apply alpha envelope
            self.grain_alphas[i] = max(0.0, self.grain_alphas[i] - 0.005)  # Slower decay
    
    def _get_quality_factor(self) -> float:
        """Get quality factor based on current quality mode."""
        if self.current_quality == "lo-fi":
            return 0.3  # Low quality, more artifacts
        elif self.current_quality == "standard":
            return 0.7  # Standard quality
```

### vjlive1/effects/arbhar_granular_engine.py (L145-164)
```python
        if self.current_quality == "lo-fi":
            return 0.3  # Low quality, more artifacts
        elif self.current_quality == "standard":
            return 0.7  # Standard quality
        elif self.current_quality == "hi-fi":
            return 1.0  # High quality, minimal artifacts
        return 0.7
    
    def _spawn_grain(self):
        """Spawn a new grain from the buffer."""
        if self.frames_recorded < 30:  # Need at least 0.5 seconds of buffer
            return
        
        if self.active_grains < self.max_grains:
            grain_index = self.active_grains
            self.active_grains += 1
            
            # Random position in buffer
            self.grain_positions[grain_index] = random.randint(0, self.frames_recorded - 1)
```

### vjlive1/effects/arbhar_granular_engine.py (L161-180)
```python
            self.grain_positions[grain_index] = random.randint(0, self.frames_recorded - 1)
            
            # Random size (duration)
            self.grain_sizes[grain_index] = random.uniform(0.1, 0.5)
            
            # Initial alpha (opacity)
            self.grain_alphas[grain_index] = random.uniform(0.3, 0.7)
            
            # Pitch is set in _update_grain_parameters
    
    def add_frame_to_buffer(self, frame: np.ndarray):
        """Add a frame to the circular buffer."""
        # Store frame in ring buffer
        self.ring_buffer[self.buffer_write_index] = frame.copy()
        
        # Update indices
        self.buffer_write_index = (self.buffer_write_index + 1) % self.buffer_size
        self.frames_recorded = min(self.frames_recorded + 1, self.buffer_size)
```

### vjlive1/effects/arbhar_granular_engine.py (L177-196)
```python
        # Update indices
        self.buffer_write_index = (self.buffer_write_index + 1) % self.buffer_size
        self.frames_recorded = min(self.frames_recorded + 1, self.buffer_size)
    
    def get_metadata(self) -> Dict[str, Any]:
        """Metadata for the effect."""
        return {
            "name": "Arbhar Granular Engine",
            "description": "Advanced granular synthesis with variable density, pitch shifting, temporal randomization, and multiple quality modes",
            "tags": ["granular", "synthesis", "audio-reactive", "buffer", "pitch-shift", "quality-modes"],
            "parameters": {
                "intensity": "Controls grain spawn rate and density",
                "spray": "Controls temporal randomization of grain positions",
                "grain_pitch": "Controls individual grain UV scaling and pitch shifting",
                "quality": "Selects quality mode: lo-fi (0.0), standard (5.0), hi-fi (10.0)"
            },
            "performance": {
                "complexity": "High",
                "cpu_cost": "High",
                "gpu_cost": "Medium",
                "memory_usage": "High"
            }
        }