# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT007_arbhar_granular_engine.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT007 — arbhar_granular_engine (ArbharGranularEngine)

## Description

The `ArbharGranularEngine` module implements an advanced granular synthesis system inspired by granular audio synthesis techniques, adapted for visual generation. It creates complex temporal visual effects by manipulating small "grains" of video frames from a circular buffer, allowing for sophisticated time-based visual transformations that respond dynamically to audio input. The module uses a sophisticated parameter mapping system where audio features (treble, bass, mid) are mapped to visual parameters (intensity, spray, grain pitch) with configurable smoothing to create organic, responsive visual patterns.

## What This Module Does

- Generates audio-reactive visual effects using temporal grain manipulation from a circular video buffer
- Manages up to 32 simultaneous grains with individual position, size, pitch, alpha, and quality properties
- Maps audio frequency bands (treble → intensity, bass → spray, mid → grain pitch) with configurable sensitivity
- Implements parameter smoothing to prevent jarring visual jumps when audio levels change rapidly
- Supports three quality modes (lo-fi, standard, hi-fi) that affect grain rendering fidelity
- Provides real-time grain spawning based on intensity parameter and audio reactivity
- Handles grain lifecycle including temporal randomization, UV scaling, and alpha decay
- Integrates with video buffer manager for frame access and circular buffer management

## What This Module Does NOT Do

- Handle audio input directly (relies on external audio analyzer providing frequency bands)
- Implement GPU-based rendering (uses CPU-side grain management with shader output)
- Support persistent grain configurations or presets
- Handle video file I/O or persistence of frame buffer contents
- Implement advanced audio analysis (only uses pre-processed frequency bands)
- Provide collision detection between grains or complex physics interactions
- Support multi-threading for performance optimization

## Integration

This module integrates with the VJLive3 node graph as a visual effect generator that connects to:

- **Audio Analyzer**: Receives frequency band data (treble, bass, mid) for audio-reactive parameter mapping
- **Video Buffer Manager**: Accesses circular buffer of video frames for grain source material
- **Shader System**: Outputs grain data to fragment shaders for final rendering
- **Parameter System**: Exposes intensity, spray, grain_pitch, audio_reactivity_intensity, and audio_reactivity_smoothing parameters
- **Quality Mode System**: Provides lo-fi, standard, and hi-fi quality presets

The module expects to be called within the main render loop and receives audio signals as a dictionary containing frequency band values. It manages internal grain state and outputs visual data that can be rendered using standard OpenGL shaders with UV mapping and alpha blending.

## Performance

- **Grain Count**: Supports up to 32 simultaneous grains (configurable, default 32)
- **Buffer Size**: 8-second circular buffer at 60fps (480 frames total)
- **CPU Usage**: Grain management and parameter smoothing run on CPU with O(n) complexity
- **Memory Usage**: ~50KB for grain arrays + frame buffer storage (depends on resolution)
- **Frame Rate**: Target 60fps with minimal overhead from grain calculations
- **Audio Processing**: Lightweight parameter mapping with configurable smoothing factor
- **Scalability**: Performance remains constant regardless of grain count (fixed 32 max)
- **Fallback**: Can operate without shader file (grains still calculated but not rendered)

---

## Public Interface

```python
class ArbharGranularEngine:
    def __init__(self) -> None: ...
    def load(self) -> bool: ...
    def update(self, signals: Dict[str, Any]) -> None: ...
    def get_parameters(self) -> Dict[str, float]: ...
    def set_parameter(self, name: str, value: float) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `signals` | `Dict[str, Any]` | Dictionary of input signals including audio levels or control data (e.g., "audio_level", "frame_rate") | Must contain at least `"audio_level"` if audio reactivity is enabled; values must be numeric |
| `name` | `str` | Parameter name to set (e.g. "intensity", "spray", "grain_pitch") | Must be one of: "intensity", "spray", "grain_pitch", "audio_reactivity_intensity", "audio_reactivity_smoothing" |
| `value` | `float` | Value to assign to parameter; range 0.0–10.0 for all parameters | Values must be within [0.0, 10.0] inclusive |
| `return_value` (from `get_parameters`) | `Dict[str, float]` | Current state of all effect parameters | All values in range [0.0, 10.0]; quality mode is string |

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `numpy` — used for array operations on frame buffers and grain data — fallback: built-in lists with reduced performance
  - `os` — used to check shader file existence — fallback: silent failure, no error raised
  - `time` — used for seeding random number generator — fallback: uses system time if available; falls back to monotonic clock
- Internal modules this depends on:
  - `core.base_effect.BaseEffect`
  - `core.video_buffer_manager.get_buffer_manager`, `VideoBufferConfig`

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | Module starts without crashing if hardware or external resources are absent |
| `test_load_shader_success` | `load()` returns True when shader file exists at expected path |
| `test_load_shader_failure` | `load()` returns False when shader file is missing or inaccessible |
| `test_update_with_audio_signal` | `update()` adjusts grain intensity based on audio level input (e.g., 0.5 sensitivity) |
| `test_parameter_set_range_validation` | Setting parameters outside [0.0, 10.0] raises ValueError |
| `test_get_parameters_returns_correct_values` | `get_parameters()` returns current values matching internal state |
| `test_quality_mode_switching` | Switching between "lo-fi", "standard", and "hi-fi" modes changes grain quality settings correctly |
| `test_cleanup_resources` | No memory leaks or open file handles after module shutdown |
| `test_audio_dropout` | Module handles sudden loss of audio input gracefully without crashing |
| `test_extreme_parameter_values` | Setting parameters at boundary values (0.0 and 10.0) behaves correctly |
| `test_concurrent_access` | Multiple threads can safely access module state |
| `test_memory_leak` | No memory leaks detected during prolonged operation |
| `test_shader_compilation_failure` | Module handles shader compilation errors gracefully |
| `test_buffer_overflow` | Circular buffer handles edge cases when full |

**Minimum coverage:** 80% before task is marked done.

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
    
    def update(self, signals: Dict[str, Any]):
```

## Audio-Reactive Parameter Updates

The `update()` method implements sophisticated audio-reactive parameter mapping using exponential smoothing to prevent jarring visual transitions. Audio signals are mapped as follows:

- **Treble signals** (0.0-1.0) are mapped to intensity parameter (0.0-10.0) using: `target_intensity = treble * 10.0 * audio_reactivity["intensity"]`
- **Bass signals** (0.0-1.0) are mapped to spray parameter (0.0-10.0) using: `target_spray = bass * 10.0 * audio_reactivity["intensity"]`
- **Mid signals** (0.0-1.0) are mapped to grain_pitch parameter (0.0-10.0) using: `target_pitch = mid * 10.0 * audio_reactivity["intensity"]`

All parameter updates use exponential smoothing: `current = current * (1.0 - smoothing) + target * smoothing` where smoothing factor is configurable via `audio_reactivity["smoothing"]`.

## Video Buffer Integration

The module integrates with the video buffer manager through a circular buffer implementation that stores the last 8 seconds of video frames at 60fps (480 frames total). Frames are accessed by grain positions to source visual material for grain rendering. The buffer uses a write-pointer approach where new frames overwrite the oldest, maintaining constant memory usage while providing temporal access to recent video history.

## Grain Position and Size Updates

Grain positions and sizes are updated each frame based on multiple factors:

- **Temporal Randomization**: Grain positions are offset by `(random.random() - 0.5) * spray * 0.1` to create organic movement
- **Pitch Scaling**: Grain UV scaling is calculated as `1.0 + (grain_pitch - 5.0) * 0.1` to map pitch parameter to visual scaling
- **Quality-Based Filtering**: Quality factors (0.3 for lo-fi, 0.7 for standard, 1.0 for hi-fi) are applied to grain rendering
- **Alpha Decay**: Grain alpha values decay by 0.005 per frame to create natural fade-out effects

## UV Scaling and Pitch Mapping

UV scaling and pitch mapping from audio input is handled through a multi-stage process:

1. Audio frequency bands (treble, bass, mid) are mapped to main parameters (intensity, spray, grain_pitch) with configurable sensitivity
2. Main parameters are then mapped to grain-specific properties:
   - Grain pitch parameter controls UV scaling: `uv_scale = 1.0 + (grain_pitch - 5.0) * 0.1`
   - This creates a range from 0.5x to 1.5x scaling centered around neutral (5.0 pitch = 1.0x scaling)
3. Quality mode affects the final rendering fidelity, with lo-fi mode introducing more artifacts and hi-fi mode providing clean rendering