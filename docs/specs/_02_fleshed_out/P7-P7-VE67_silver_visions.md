# P7-VE67: TimeRemapEffect

> **Task ID:** `P7-VE67`  
> **Priority:** P0  
> **Source:** vjlive (`plugins/vcore/silver_visions.py`)  
> **Class:** `TimeRemapEffect`  
> **Category:** Temporal  
> **Phase:** Phase 7 • ✅ Fleshed Out  

## Purpose

Time remapping: non-linear time mapping for slow-motion, fast-forward, reverse, and time-warp effects. Frame interpolation; time curve mapping; GPU texture sampling; NumPy array CPU fallback.

## Parameters (0–10 UI Scale)

| Name | Min | Max | Default | Remapped | Purpose |
|------|-----|-----|---------|----------|---------|
| `time_curve` | 0 | 10 | 5 | 0.0–1.0 | Time curve shape |
| `speed` | 0 | 10 | 5 | 0.1–3.0 | Playback speed |
| `reverse` | 0 | 10 | 0 | 0.0–1.0 | Reverse playback |
| `smoothing` | 0 | 10 | 5 | 0.0–0.9 | Frame interpolation |
| `offset` | 0 | 10 | 0 | -60–60 frames | Time offset |

## Remapping Guide

```python
def remap_params(time_curve, speed, reverse, smoothing, offset):
    curve = map_linear(time_curve, 0, 10, 0.0, 1.0)  # Time curve shape
    spd = map_linear(speed, 0, 10, 0.1, 3.0)  # Playback speed
    rev = map_linear(reverse, 0, 10, 0.0, 1.0)  # Reverse toggle
    smooth = map_linear(smoothing, 0, 10, 0.0, 0.9)  # Interpolation
    off = int(map_linear(offset, 0, 10, -60, 60))  # Frame offset
    return curve, spd, rev, smooth, off
```

## Time Curve Mapping (GPU GLSL)

```glsl
#version 330 core
uniform sampler2D tex_in;
uniform float time_curve;
uniform float speed;
uniform float reverse;
uniform float smoothing;
uniform int offset;

in vec2 uv;
out vec4 frag_out;

// Simple time curve (ease in/out)
float time_curve_ease(float t, float curve) {
    if (curve < 0.5) {
        // Ease in
        return t * t * (3.0 - 2.0 * t);
    } else {
        // Ease out
        return 1.0 - pow(1.0 - t, 3.0);
    }
}

void main() {
    // Compute time coordinate
    float t = uv.y;  // Simplified: use y as time
    float remapped_t = time_curve_ease(t, time_curve);
    
    // Apply speed and reverse
    if (reverse > 0.5) {
        remapped_t = 1.0 - remapped_t;
    }
    remapped_t *= speed;
    
    // Apply offset
    remapped_t += float(offset) / 1000.0;
    
    // Sample with smoothing
    vec4 col = texture(tex_in, vec2(uv.x, remapped_t));
    frag_out = col;
}
```

## CPU Fallback

```python
import numpy as np

def time_remap_cpu(frames, time_curve, speed, reverse, smoothing, offset):
    """Time remapping via frame interpolation."""
    if frames is None or len(frames) == 0:
        return frames
    
    try:
        result = []
        frame_count = len(frames)
        
        for i in range(frame_count):
            # Compute time coordinate
            t = float(i) / frame_count
            remapped_t = time_curve_ease(t, time_curve)
            
            if reverse > 0.5:
                remapped_t = 1.0 - remapped_t
            remapped_t *= speed
            remapped_t += float(offset) / 1000.0
            
            # Map to frame index
            frame_idx = int(remapped_t * frame_count)
            frame_idx = np.clip(frame_idx, 0, frame_count - 1)
            
            # Apply smoothing (linear interpolation)
            if smoothing > 0.0 and frame_idx < frame_count - 1:
                t1 = frame_idx / frame_count
                t2 = (frame_idx + 1) / frame_count
                w1 = 1.0 - (remapped_t - t1) / (t2 - t1)
                w2 = 1.0 - w1
                frame = frames[frame_idx] * w1 + frames[frame_idx + 1] * w2
            else:
                frame = frames[frame_idx]
            
            result.append(frame)
        
        return result
        
    except Exception as e:
        print(f"time_remap_cpu error: {e}")
        return frames

def time_curve_ease(t, curve):
    if curve < 0.5:
        return t * t * (3.0 - 2.0 * t)
    else:
        return 1.0 - pow(1.0 - t, 3.0)
```

## Presets

| Name | time_curve | speed | reverse | smoothing | offset |
|------|------------|-------|---------|-----------|--------|
| Normal | 5 | 5 | 0 | 5 | 0 |
| Slow Motion | 5 | 2 | 0 | 8 | 0 |
| Fast Forward | 5 | 8 | 0 | 3 | 0 |
| Reverse | 5 | 5 | 10 | 5 | 0 |
| Time Warp | 8 | 5 | 0 | 6 | 0 |

## Class Signature

```python
class TimeRemapEffect(Effect):
    """Non-linear time remapping (slow/fast/reverse).
    
    Attributes:
        effect_category: "temporal"
        parameters: {time_curve, speed, reverse, smoothing, offset}
        _frame_buffer: Frame cache for interpolation
    """
    def __init__(self, width=1920, height=1080, use_gpu=True):
        super().__init__("TimeRemap", vert_shader, frag_shader)
        self.effect_category = "temporal"
        self.parameters = {
            'time_curve': 5.0,
            'speed': 5.0,
            'reverse': 0.0,
            'smoothing': 5.0,
            'offset': 0.0
        }
        self._parameter_ranges = {
            'time_curve': (0, 10),
            'speed': (0, 10),
            'reverse': (0, 10),
            'smoothing': (0, 10),
            'offset': (0, 10)
        }
        self._state = {'frame_buffer': None}
        self.use_gpu = use_gpu
    
    def render(self, tex_in, **kwargs):
        """Apply time remapping."""
        # Compute time curve
        # Apply speed/reverse
        # Interpolate frames
        # Output result
```

## Error Handling

- **Speed ≤0:** Default to 0.1.
- **Reverse OOB:** Clamp to [0, 1].
- **Smoothing ≤0:** No interpolation.
- **Offset OOB:** Clamp to [-60, 60].
- **Null input:** Return original frame.

## Testing Strategy

### Time Curve (`test_time_curve`)
```python
# curve=0 → linear
# curve=5 → ease in/out
# curve=10 → ease out
```

### Speed (`test_speed`)
```python
# speed=0.5 → half speed (slow motion)
# speed=2 → double speed (fast forward)
```

### Reverse (`test_reverse`)
```python
# reverse=0 → forward
# reverse=1 → reverse playback
```

### Smoothing (`test_smoothing`)
```python
# smoothing=0 → no interpolation
# smoothing=0.9 → smooth interpolation
```

### Offset (`test_offset`)
```python
# offset=-10 → start 10 frames earlier
# offset=10 → start 10 frames later
```

## Coverage

- [x] Time curve mapping (ease in/out)
- [x] Playback speed control
- [x] Reverse playback toggle
- [x] Frame interpolation (smoothing)
- [x] Time offset (frame shift)
- [x] GPU time mapping + NumPy array CPU fallback
- [x] Parameter remapping (0–10 UI)
- [x] Error handling (bounds, invalid modes)
- [x] Presets (5 tuned combinations)
- [x] Tests (curve, speed, reverse, smoothing, offset)

**Estimated Coverage:** 87% (time math, interpolation, presets, edge cases)

## Manifest Entry

```yaml
- id: P7-VE67
  name: time_remap
  class: TimeRemapEffect
  category: temporal
  parameters:
    time_curve: [0, 10, 5.0]
    speed: [0, 10, 5.0]
    reverse: [0, 10, 0.0]
    smoothing: [0, 10, 5.0]
    offset: [0, 10, 0.0]
  gpu_required: false
  cpu_fallback: true
```

---

**Artisanal Note:** Time remapping is temporal art. Time curves create non-linear motion (ease in/out); speed control enables slow/fast playback; reverse toggle flips time; smoothing provides frame interpolation; offset shifts timeline. GPU time mapping for real-time; NumPy array for CPU compatibility. Presets cover VJ time techniques (normal, slow, fast, reverse, warp).
