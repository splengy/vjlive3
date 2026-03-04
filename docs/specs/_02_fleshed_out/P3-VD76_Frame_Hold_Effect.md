# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-VD76_Frame_Hold_Effect.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD76 — FrameHoldEffect

## Description

The Frame Hold Effect implements a sophisticated temporal freeze/hold mechanism that captures input frames and maintains them for a configurable duration, enabling creative "bullet-time," temporal stretching, and frame blending effects. This effect is essential for music video production, glitch art, and temporal manipulation in real-time performance contexts.

The effect operates by maintaining a circular buffer of historical frames, allowing selective temporal freezing where certain frames are held and decayed rather than replaced. Multiple hold modes support different artistic outcomes: pure frame freeze (image persistence), temporal stretching (smooth playback of held frames at variable speeds), and exponential decay (ghosting effects). The effect integrates directly with the VJLive3 effect pipeline and supports audio-driven triggering for synchronized temporal manipulation.

## What This Module Does

- Captures and holds input frames for configurable durations (0-10 seconds)
- Supports multiple hold modes: freeze (temporal stasis), stretch (time-remapping), decay (ghosting)
- Maintains a circular frame history buffer (up to 120 frames at 60 FPS = 2 seconds)
- Provides temporal decay rates to fade held frames over time
- Implements audio-reactive hold triggering based on beats and energy thresholds
- Applies smooth transitions between held and live frames using blending
- Supports GPU-accelerated texture composition for real-time 60 FPS performance
- Manages GPU framebuffer lifecycle with automatic reallocation on resolution changes
- Provides configurable hold onset/release envelopes for musical synchronization

## What This Module Does NOT Do

- Does NOT generate depth maps (holds entire frames, not depth-aware)
- Does NOT perform motion compensation or optical flow
- Does NOT resize the input video (output matches input resolution)
- Does NOT implement advanced temporal filtering (use TimeStretch or MotionBlur for that)
- Does NOT support multi-head frame splitting
- Does NOT handle audio analysis directly (relies on `AudioReactor` wrapper)
- Does NOT persist frame history across sessions
- Does NOT provide CPU fallback (requires GPU with texture operations)

---

## Detailed Behavior

### Hold Mechanism

The effect maintains a circular buffer of frames:

```
Frame index:  0(oldest) 1  2  3  4(newest)
              ├─────────────────────────┤
              Circular buffer (size = max hold frames)
              Current write position → 4(newest)
```

When hold is triggered:
1. A frame is captured and marked with a "hold timestamp"
2. Subsequent frame writes continue but don't overwrite the held frame
3. Held frame is blended with live input based on `hold_duration` and `decay_rate`
4. After hold duration expires, frame returns to normal live passthrough

### Hold Modes

| Mode | Behavior | Use Case |
|------|----------|----------|
| `freeze` | Held frame displays unchanged until hold duration expires | Bullet-time effects, dramatic pauses |
| `stretch` | Held frames playback at variable speed (time-remapping) | Temporal acceleration/deceleration |
| `decay` | Held frame exponentially fades over hold duration | Ghosting, afterimage trails |
| `composite` | Held frame blends with live frames based on blend factor | Smooth transitions, motion echoes |

### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `hold_mode` | enum | 0 (freeze) | 0-3 | Select hold mode (0=freeze, 1=stretch, 2=decay, 3=composite) |
| `hold_duration` | float | 2.0 | 0.0 - 10.0 | How long to hold the frame (seconds) |
| `decay_rate` | float | 5.0 | 0.0 - 10.0 | Exponential decay speed for held frame (higher=faster fade) |
| `trigger_threshold` | float | 5.0 | 0.0 - 10.0 | Audio threshold for auto-triggering hold (0=always off, 10=very easy) |
| `hold_offset` | float | 0.0 | 0.0 - 10.0 | Time offset before hold begins (delay in seconds) |
| `release_envelope` | float | 3.0 | 0.0 - 10.0 | Smoothness of hold release (0=instant, 10=very smooth) |
| `temporal_scale` | float | 5.0 | 1.0 - 10.0 | Playback speed for stretch mode (5.0=1x, <5=slower, >5=faster) |
| `blend_factor` | float | 5.0 | 0.0 - 10.0 | Blend between held frame and live input (5.0=50/50) |
| `jitter_amount` | float | 0.0 | 0.0 - 10.0 | Frame index jitter for glitch effects (0=disabled) |
| `buffer_size` | int | 120 | 30 - 300 | Number of frames to buffer (seconds = buffer_size / 60) |

### Parameter Mapping

- `hold_mode`: Integer 0-3 (no scaling, direct enum)
- `hold_duration`: 0-10 → 0-10.0 seconds (divide by 1, clamp to buffer capacity)
- `decay_rate`: 0-10 → 0.01-1.0 inverse time constant (divide by 10)
- `trigger_threshold`: 0-10 → 0.0-1.0 (divide by 10)
- `hold_offset`: 0-10 → 0-1.0 seconds (divide by 10)
- `release_envelope`: 0-10 → 0.0-1.0 second smoothness window (divide by 10)
- `temporal_scale`: 1-10 → 0.5-2.0x playback speed
- `blend_factor`: 0-10 → 0.0-1.0 blend ratio (divide by 10)
- `jitter_amount`: 0-10 → 0.0-1.0 jitter (divide by 10)
- `buffer_size`: Integer frame count (no scaling)

### State Machine

```
State: IDLE
  └─ Trigger received (audio or manual) or trigger_threshold exceeded
     └─ State: HOLDING
        ├─ Capture current frame (frame_index_start)
        ├─ Start hold timer
        ├─ Store hold_duration seconds worth of frame indices
        └─ For each frame until hold expires:
           ├─ Sample held frame(s) from buffer based on hold_mode
           ├─ Blend with live input using time-dependent blend curve
           └─ Apply decay if applicable
        └─ After hold_duration expires
           └─ State: RELEASING (if release_envelope > 0)
              ├─ Smoothly interpolate blend_factor from held→live
              ├─ Duration: release_envelope seconds
              └─ After release is complete
                 └─ State: IDLE
```

### Audio Reactivity

When `trigger_threshold > 0.01`:
- Monitor `BEAT_INTENSITY` from connected `AudioReactor`
- Trigger hold when `BEAT_INTENSITY > trigger_threshold`
- Can also trigger on `ENERGY` threshold or manual parameter set

### Temporal Stretching (Stretch Mode)

In stretch mode, held frames are played back at variable speeds:
- `temporal_scale = 5.0` → playback at 1x (normal speed through held frame history)
- `temporal_scale < 5.0` → slower playback (slow-motion through history)
- `temporal_scale > 5.0` → faster playback (fast-forward through history)

During stretch, the frame index advances as:
```
index = start_index + (elapsed_time * temporal_scale) % buffer_size
```

### Exponential Decay

In decay mode, the held frame's alpha decreases exponentially:
```
alpha(t) = exp(-decay_rate * t / 10.0)
fade_color = held_frame * alpha(t) + live_frame * (1 - alpha(t))
```

---

## Public Interface

```python
class FrameHoldEffect(Effect):
    def __init__(self) -> None: ...
    def set_audio_analyzer(self, audio_analyzer) -> None: ...
    def trigger_hold(self, hold_duration: Optional[float] = None) -> None: ...
    def cancel_hold(self) -> None: ...
    def is_holding(self) -> bool: ...
    def get_hold_progress(self) -> float: ...
    def set_parameter(self, name: str, value: float) -> None: ...
    def get_parameter(self, name: str) -> float: ...
    def process_frame(self, frame: np.ndarray) -> np.ndarray: ...
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `frame` | `np.ndarray` | Input video frame (HWC, 3 or 4 channels) | dtype: uint8 or float32, shape (H, W, C) |
| `audio_analyzer` | `Optional[AudioAnalyzer]` | Optional audio feature source | Provides BEAT_INTENSITY, ENERGY |

**Output**: `np.ndarray` — Video frame with hold effect applied (same shape/dtype as input)

---

## State Management

**Persistent State:**
- `parameters: dict` — Current effect parameters
- `_frame_buffer: List[int]` — Circular buffer of GL texture IDs (up to 300 textures)
- `_frame_fbos: List[int]` — Framebuffer objects for rendering
- `_buffer_index: int` — Current write position in circular buffer
- `_hold_start_time: Optional[float]` — Timestamp when hold was triggered (wall clock)
- `_hold_start_frame_index: int` — Which frame in buffer was captured when hold started
- `_hold_active: bool` — Whether hold is currently active
- `_release_phase: bool` — Whether in release envelope phase
- `_release_start_time: Optional[float]` — When release phase began
- `_frame_width: int` — Current framebuffer width
- `_frame_height: int` — Current framebuffer height
- `_shader: ShaderProgram` — Compiled blend/composition shader
- `_audio_reactor: Optional[AudioReactor]` — Audio feature source
- `_last_beat_time: float` — Timestamp of last detected beat (for debouncing)

**Per-Frame State:**
- `_current_frame_time: float` — Current wall clock time
- `_hold_elapsed: float` — Seconds elapsed since hold started
- `_current_blend_factor: float` — Time-interpolated blend value

**Initialization:**
- Frame buffer textures created on first `set_frame_size()` call
- Number of textures = `buffer_size` (e.g., 120)
- Framebuffers created to match
- Shader compiled in `__init__()`
- `_buffer_index = 0`
- `_hold_active = False`

**Cleanup:**
- Delete all frame textures (`glDeleteTextures` for all in buffer)
- Delete all framebuffers (`glDeleteFramebuffers`)
- Delete shader program

---

## GPU Resources

| Resource | Type | Format | Dimensions | Lifecycle |
|----------|------|--------|------------|-----------|
| Frame buffer textures | GL_TEXTURE_2D | RGBA8 or RGB8 | frame size × buffer_size | Created in `set_frame_size()`, recreated if resolution changes |
| Frame FBOs | Framebuffer | RGBA8 | frame size | Created in `set_frame_size()` |
| Blend shader | GLSL program | vertex + fragment | N/A | Compiled in `__init__()` |
| Composition FBO | Framebuffer | RGBA8 | frame size | Created for intermediate rendering |

**Memory Budget (1080p with 120-frame buffer):**
- Frame textures: 1920 × 1080 × 4 bytes × 120 = ~995 MB (RGBA8)
- - Can reduce to RGB8 to save ~25%: 1920 × 1080 × 3 bytes × 120 = ~746 MB
- Framebuffers: minimal overhead (~1 MB)
- **Total: ~750-1000 MB VRAM depending on texture format**

**Optimization notes:**
- Use `GL_RGB8` instead of `RGBA8` to save 25% VRAM
- For lower-end GPUs, reduce `buffer_size` to 60 (1 second @ 60 FPS)
- Consider using compressed textures (BC1/DXT1) for 4:1 compression

---

## Error Cases

| Error Condition | Response | Recovery |
|-----------------|----------|----------|
| Buffer size = 0 | `ValueError("buffer_size must be > 0")` | Set valid buffer_size in params |
| Hold duration > buffer capacity | Clamp to buffer capacity | Log warning, hold for max available duration |
| Frame size changes | Reallocate all textures/FBOs | Automatic in `set_frame_size()` |
| GPU out of memory | `RuntimeError("Failed to allocate texture")` | Reduce buffer_size or resolution |
| Shader compilation failure | Log error, effect becomes no-op | Check shader syntax |
| Invalid hold_mode | Clamp to 0-3 range | Log warning |
| Audio analyzer not set but audio reactive enabled | Gracefully disable audio triggering | Log info message |
| Negative parameters | Clamp to valid range | Log warning |

---

## Thread Safety

The effect is **not thread-safe**. All GPU operations must occur on the thread owning the OpenGL context. Multiple instances can run on different threads with separate contexts. The frame buffer and state variables are mutable and updated each frame, so concurrent `process_frame()` calls will cause race conditions.

---

## Performance

**Expected Frame Time (1080p, 120-frame buffer):**
- Texture upload (frame copy to buffer slot): ~0.5-1.0 ms
- Blend composite (held + live frames): ~1-2 ms
- Decay exponential calculation: ~0.1 ms
- Total per-frame: ~2-3 ms on discrete GPU

**Optimization strategies:**
- Use `GL_RGB8` instead of `RGBA8` (-25% memory and bandwidth)
- Pre-compute decay curve as lookup texture instead of per-pixel calculation
- Use persistent mapped buffers for frame upload (ARB_buffer_storage)
- For stretch mode, use sampler state to interpolate between buffer positions
- Disable audio analysis if not using trigger_threshold

**Scalability:**
- 720p @ 30 FPS, 60-frame buffer: ~185 MB VRAM, ~1.5 ms per frame
- 1080p @ 60 FPS, 120-frame buffer: ~1000 MB VRAM, ~3 ms per frame
- 4K @ 30 FPS, 60-frame buffer: ~745 MB VRAM, ~3-4 ms per frame

---

## Integration Checklist

- [ ] Frame buffer textures allocated via `set_frame_size()` before processing
- [ ] Shader compiles successfully on all target platforms
- [ ] Parameters validated and clamped to valid ranges
- [ ] `cleanup()` called when effect destroyed to release GPU resources
- [ ] Audio analyzer connected if audio triggering enabled
- [ ] Hold triggering works (manual `trigger_hold()` and audio-based)
- [ ] Hold duration correctly limited by buffer capacity
- [ ] Release envelope smoothing works correctly
- [ ] Memory usage acceptable for target hardware

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init` | Effect initializes with default parameters |
| `test_set_parameter` | All parameters can be set and clamped |
| `test_frame_buffering` | Frames are correctly stored in circular buffer |
| `test_trigger_hold` | Manual hold triggering works |
| `test_cancel_hold` | Hold can be cancelled early |
| `test_is_holding` | Status check returns correct value |
| `test_hold_progress` | Progress tracking matches elapsed time |
| `test_hold_duration_limit` | Hold duration clamped to buffer capacity |
| `test_mode_freeze` | Freeze mode holds frame unchanged |
| `test_mode_stretch` | Stretch mode playback at variable speeds |
| `test_mode_decay` | Decay mode exponentially fades frame |
| `test_mode_composite` | Composite mode blends held + live frames |
| `test_release_envelope` | Smooth release transition works |
| `test_blend_factor` | Held frame blend amount applied correctly |
| `test_jitter` | Jitter amount adds randomness to frame index |
| `test_audio_triggering` | Hold triggered by audio threshold |
| `test_audio_smoothing` | Audio triggers debounced correctly |
| `test_cleanup` | All GPU resources released |
| `test_resolution_change` | Textures reallocated on resolution change |
| `test_edge_case_zero_decay` | Decay rate = 0 holds indefinitely (with blend) |
| `test_edge_case_instant_release` | Release envelope = 0 snaps to live |
| `test_rapid_trigger` | Multiple triggers handled correctly |

**Minimum coverage:** 85%

---

## Definition of Done

- [ ] Spec reviewed and approved
- [ ] All tests pass with 85%+ coverage
- [ ] No file over 800 lines
- [ ] No stub functions in code
- [ ] Performance validated (< 5 ms per frame at 1080p/60fps)
- [ ] Memory profiling complete (VRAM usage tracked)
- [ ] Verification checkpoint passed
- [ ] Git commit with `[Phase-3] P3-VD76: frame_hold_effect` message
- [ ] BOARD.md updated with task completion
- [ ] Lock released in task tracking system
- [ ] AGENT_SYNC.md handoff note written

---

## Legacy Code Mapping

Key references from golden_example_vimana.py and bullet_time_datamosh spec:
- `freeze` parameter (0-10 scale, binary freeze behavior)
- Frame history management using circular textures
- Hold duration parameter (in seconds or frame count)
- Decay mechanism for temporal ghosting effects
- `is_frozen` status variable tracking

Design decisions inherited:
- Effect name: `frame_hold`
- Inherits from base `Effect` class
- Uses circular frame buffer with texture array
- Parameters: `hold_mode`, `hold_duration`, `decay_rate`, `trigger_threshold`, `blend_factor`, `buffer_size`
- GPU resources: frame textures (circular), framebuffers, blend shader
- Audio reactivity via `AudioReactor` wrapper (optional)

---

## Notes for Implementers

1. **Circular Buffer Management**: Use modulo arithmetic to manage write index:
   ```python
   frame_index = (self._buffer_index + offset) % self.buffer_size
   ```

2. **Decay Curve**: Pre-compute decay curve as 1D lookup texture instead of per-pixel calculation:
   ```python
   # At init time, create decay LUT
   decay_lut = np.array([exp(-decay_rate * t / 10.0) for t in linspace(0, 1, 256)])
   # In shader, sample: alpha = texture(decay_lut, t).r
   ```

3. **Temporal Interpolation**: For smooth playback in stretch mode, use sampler linear interpolation:
   ```glsl
   float t = fract(frame_index);  // Fractional part
   vec4 frame0 = texture(frame_buffer[int(frame_index)], uv);
   vec4 frame1 = texture(frame_buffer[int(frame_index) + 1], uv);
   color = mix(frame0, frame1, t);  // Hardware lerp
   ```

4. **Audio Debouncing**: Avoid rapid re-triggering from beat detection noise:
   ```python
   BEAT_DEBOUNCE_TIME = 0.5  # seconds
   if beat_detected and (time.time() - self._last_beat_time) > BEAT_DEBOUNCE_TIME:
       self.trigger_hold()
       self._last_beat_time = time.time()
   ```

5. **Blend Envelope**: Use S-curve interpolation for smooth hold release:
   ```python
   # Smoothstep function for release
   release_progress = release_time / release_envelope
   blend = 0.5 - 0.5 * cos(π * release_progress)  # S-curve
   ```

6. **Memory Optimization**: For limited VRAM, dynamically adjust buffer size:
   ```python
   if available_vram < 500:  # MB
       buffer_size = min(buffer_size, 60)  # 1 second @ 60 FPS
   ```

7. **Jitter Implementation**: Add pseudo-random frame index variation:
   ```glsl
   float jitter = jitter_amount * sin(time * 10.0 + gl_FragCoord.x);  // Smooth jitter
   int jittered_index = int(float(frame_index) + jitter);
   ```

8. **Performance Profiling**: Use OpenGL timer queries:
   ```python
   # At init: glGenQueries(1, &query)
   # Before: glBeginQuery(GL_TIME_ELAPSED, query)
   # After: glEndQuery(GL_TIME_ELAPSED)
   # Result: glGetQueryObjectuiv(query, GL_QUERY_RESULT, &time_ns)
   ```

---

## Presets

```python
PRESETS = {
    "bullet_time": {
        "hold_mode": 0.0,           # freeze
        "hold_duration": 2.0,
        "decay_rate": 2.0,
        "trigger_threshold": 6.0,
        "hold_offset": 0.0,
        "release_envelope": 1.0,
        "temporal_scale": 5.0,
        "blend_factor": 10.0,       # 100% held frame
        "jitter_amount": 0.0,
    },
    "ghosting": {
        "hold_mode": 2.0,           # decay
        "hold_duration": 1.5,
        "decay_rate": 7.0,
        "trigger_threshold": 0.0,
        "hold_offset": 0.0,
        "release_envelope": 0.5,
        "temporal_scale": 5.0,
        "blend_factor": 6.0,        # 60% blend
        "jitter_amount": 0.0,
    },
    "temporal_stretch": {
        "hold_mode": 1.0,           # stretch
        "hold_duration": 2.0,
        "decay_rate": 3.0,
        "trigger_threshold": 5.0,
        "hold_offset": 0.0,
        "release_envelope": 2.0,
        "temporal_scale": 3.0,      # slow-motion playback
        "blend_factor": 10.0,
        "jitter_amount": 0.0,
    },
    "composite_rhythm": {
        "hold_mode": 3.0,           # composite
        "hold_duration": 1.0,
        "decay_rate": 4.0,
        "trigger_threshold": 7.0,
        "hold_offset": 0.1,
        "release_envelope": 0.3,
        "temporal_scale": 5.0,
        "blend_factor": 5.0,        # 50/50 blend
        "jitter_amount": 2.0,       # glitch effect
    },
    "glitch_stutter": {
        "hold_mode": 0.0,           # freeze
        "hold_duration": 0.3,
        "decay_rate": 1.0,
        "trigger_threshold": 8.0,
        "hold_offset": 0.0,
        "release_envelope": 0.1,
        "temporal_scale": 5.0,
        "blend_factor": 10.0,
        "jitter_amount": 8.0,       # heavy jitter
    },
}
```

---
-

## References

- Temporal effects literature: "Real-Time 3D Graphics with WebGL 2.0" by Tony Parisi (Ch. 12: Motion Blur & Temporal Effects)
- Frame buffering patterns: https://www.khronos.org/opengl/wiki/Texture#Texture_Objects
- Decay curves in graphics: https://www.desmos.com/calculator (exponential decay visualization)
- Audio beat detection: Beat tracking algorithms (OpenBCI, Essentia lib)
- Smoothstep/S-curves: https://en.wikipedia.org/wiki/Smoothstep

---

## Additional Notes for Implementation

### Shader Fragment Skeleton

```glsl
#version 330 core

in vec2 uv;
out vec4 fragColor;

uniform sampler2D current_tex;
uniform sampler2DArray frame_buffer;      // Array of held frames
uniform sampler1D decay_lut;              // Exponential decay lookup
uniform int hold_frame_index;
uniform float blend_factor;
uniform float hold_progress;              // 0.0 (start) to 1.0 (end) of hold
uniform int hold_mode;

void main() {
    vec4 live = texture(current_tex, uv);
    
    // Sample held frame from circular buffer
    int frame_idx = hold_frame_index % 120;  // GLSL doesn't have dynamic indexing easily
    vec4 held = texture(frame_buffer, vec3(uv, float(frame_idx)));
    
    if (hold_mode == 0) {  // freeze
        fragColor = mix(live, held, blend_factor);
    } else if (hold_mode == 2) {  // decay
        float alpha = texture(decay_lut, hold_progress).r;
        fragColor = mix(live, held * alpha, blend_factor);
    } else {
        fragColor = live;  // Other modes handled in Python
    }
}
```

### Python Main Loop Skeleton

```python
class FrameHoldEffect(Effect):
    def process_frame(self, frame):
        now = time.time()
        
        # Update hold state
        if self._hold_active:
            self._hold_elapsed = now - self._hold_start_time
            
            if self._hold_elapsed >= self.parameters['hold_duration']:
                self._hold_active = False
                self._release_phase = True
                self._release_start_time = now
        
        # Write current frame to buffer
        self._write_frame_to_buffer(frame)
        
        # Render output
        if self._release_phase:
            # Interpolate from held to live
            release_progress = (now - self._release_start_time) / self.parameters['release_envelope']
            if release_progress >= 1.0:
                self._release_phase = False
                return self._render_live(frame)
            else:
                return self._render_composite(frame, 1.0 - release_progress)
        elif self._hold_active:
            return self._render_composite(frame, self.parameters['blend_factor'])
        else:
            return frame  # Pass through
```

---
