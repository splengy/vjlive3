# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT109_vtempi.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT109 — vtempi (ModBehavior)

**What This Module Does**

The `VTempiPlugin` module is a faithful recreation of the Make Noise TEMPI modular synthesizer module, adapted for video synchronization in VJLive3. It provides a 6-channel polyphonic clock engine that generates precise timing signals for coordinating multiple visual elements. Each channel can operate independently with its own tempo, or be synchronized to a leading tempo with optional multiplication/division factors. The module supports video frame rate alignment, allowing visual elements to stay in sync with the video playback while maintaining musical timing.

The core functionality includes:
- **Leading tempo**: A master BPM that all channels can sync to
- **6 independent channels**: Each with its own tempo derived from the leading tempo via multiplier/divisor
- **Video FPS alignment**: Ability to lock channel tempos to video frame rate for perfect audio-visual sync
- **Tap tempo**: Channel 1 can be set to tap tempo mode for live tempo input
- **Phase control**: Coarse phase adjustment (0-3) for each channel to offset timing
- **Mute per channel**: Individual channel muting
- **Duty cycle**: Pulse width modulation for clock signals (though this may be more relevant for audio)

The module is CPU-based (no GPU required) and runs as a stateful object that updates on each tick of the VJLive3 time manager.

**What This Module Does NOT Do**

- Does not generate actual audio clock signals (video timing only)
- Does not provide MIDI or CV (control voltage) output
- Does not implement swing/groove quantization
- Does not include pattern sequencing or step sequencing
- Does not handle external hardware synchronization (e.g., DIN sync, MIDI clock)
- Does not provide visual waveform output or LED indicators
- Does not implement reset/sync inputs for channel start alignment

---

## Detailed Behavior and Parameter Interactions

### Core Architecture

The VTempi module is fundamentally a **tempo derivation engine**. It maintains:
- A `leading_tempo` (master BPM) that all channels reference
- Per-channel state: `multiplier`, `divisor`, `phase_coarse`, `muted`, `duty_cycle`
- A `video_fps` setting that can be used to align tempos to frame boundaries

Each channel's actual output tempo is computed as:

```
channel_tempo = leading_tempo * (multiplier / divisor)
```

For example:
- multiplier=1, divisor=1 → 120 BPM (same as leading)
- multiplier=2, divisor=1 → 240 BPM (double)
- multiplier=1, divisor=2 → 60 BPM (half)
- multiplier=3, divisor=4 → 90 BPM (three-quarter)

The `phase_coarse` (0-3) introduces a phase offset equivalent to 0, 1/4, 1/2, or 3/4 of a beat, allowing channels to be staggered in time.

### Video FPS Alignment

The `video_fps` parameter (default 30.0) is used to calculate the relationship between tempo and frame timing. The module can compute:

- **Frames per beat**: `frames_per_beat = video_fps * (60.0 / channel_tempo)`
- **Beat phase**: The current position within a beat (0.0 to 1.0) based on elapsed time

This allows other modules to query the channel's current beat phase and trigger events on specific beats or subdivisions.

### Tap Tempo (Channel 1)

Channel 1 has a `tap_tempo_ch1` boolean parameter. When enabled, the leading tempo is derived from the interval between successive `update()` calls that signal a tap. The tap detection algorithm typically:
- Records timestamps of the last N taps (usually 4-8)
- Computes the average interval between taps
- Converts interval to BPM: `bpm = 60.0 / average_interval`
- Applies a smoothing filter to avoid jitter

If `tap_tempo_ch1` is false, channel 1 uses the standard multiplier/divisor derivation from leading_tempo.

### Update Cycle

The `update(delta_time)` method is called regularly (ideally every frame or at a fixed time step). It:
1. Accumulates `delta_time` into an internal `elapsed` counter
2. For each non-muted channel, computes the current beat position:
   ```
   beat_position = (elapsed * channel_tempo / 60.0) % 1.0
   ```
3. Applies phase offset: `beat_position = (beat_position + phase_offset) % 1.0`
4. Stores the beat position for retrieval via `get_tempos()` or a separate query method

The `get_tempos()` method returns a dictionary mapping channel numbers (1-6) to their current beat position (0.0-1.0) or possibly the derived BPM value. The spec should clarify which.

### Parameter Constraints

From the manifest:
- `leading_tempo`: float, min 0.0, max 10.0, default 3.57 — **Wait, this is odd**: 3.57 BPM? That seems like the UI might be using a 0-10 scale that maps to a BPM range. Likely: `actual_bpm = leading_tempo * some_factor` or the max should be higher. The DEFAULT_CONFIG says 120.0, so the manifest's max=10.0 is probably a mistake or the parameter is normalized. We need to decide: either use actual BPM (0-500) or normalized 0-10. Given the legacy uses 0-10 sliders, it's likely normalized and maps to a BPM range internally.
- `multiplier`: int, 1-32, default 1
- `divisor`: int, 1-32, default 1
- `phase_coarse`: int, 0-3, default 0
- `channel_mute`: bool, default false
- `duty_cycle`: likely float 0-1 or 0-100, but incomplete in snippet

**Recommendation**: Use actual BPM values for `leading_tempo` (range 0.0-500.0) for clarity. The UI can still use a 0-10 slider that maps to this range internally.

---

## Integration

### VJLive3 Pipeline Integration

The `VTempiPlugin` is a **utility module**, not a frame processor. It does not take video frames or produce visual output directly. Instead, it provides timing signals that other effects and modules can query to synchronize their behavior.

**Typical usage**:

```python
# Initialize
vtempi = VTempiPlugin(config={"leading_tempo": 120.0, "video_fps": 30.0})

# In the main loop (called once per frame or at fixed interval)
vtempi.update(delta_time)  # delta_time in seconds

# Other modules can query current channel states
tempos = vtempi.get_tempos()  # returns {1: 0.25, 2: 0.5, ...} beat positions
# or maybe: {1: 120.0, 2: 60.0, ...} actual BPMs

# A visual effect can use this to trigger on beat:
if tempos[1] < 0.1:  # near start of beat
    effect.flash()
```

**Position in system**: The VTempi module lives in the `plugins.clock` or `modules.timing` namespace. It is instantiated once at startup and shared across all modules that need timing. It does not process video frames.

### Time Management

The module relies on the VJLive3 `TimeManager` to provide accurate `delta_time` values. The `TimeManager` should:
- Use a high-resolution timer
- Account for pauses or frame drops
- Provide consistent time deltas even if frame rate varies

If `delta_time` is inconsistent, the beat position calculation may drift. The module should be resilient to occasional large `delta_time` values (e.g., if the app was paused).

### Video FPS Handling

The `video_fps` should match the actual frame rate of the video output. If the video FPS changes (e.g., switching between 30fps and 60fps projects), the module should be reinitialized or the parameter updated. The `update()` method may need to know the current video frame time to align beats precisely.

---

## Performance

### Computational Cost

The module is **CPU-bound** but extremely lightweight. Each `update()` call performs:
- 6 channel tempo calculations (simple arithmetic)
- 6 beat position updates (modulo operation)
- Optional tap tempo processing (if channel 1 tap mode enabled)

On any modern CPU, this is negligible (< 0.1 ms per call). The module can be updated every frame (60-120 Hz) without impact.

### Memory Usage

- **Minimal**: Stores a few dozen floats and ints (leading_tempo, video_fps, per-channel state)
- **No dynamic allocation** after initialization
- **No GPU resources** required

### Optimization Strategies

None needed. The module is already optimal.

### Platform-Specific Considerations

- **Desktop**: No issues
- **Embedded (Raspberry Pi)**: Still negligible CPU usage
- **Real-time audio contexts**: If used with audio processing, ensure `update()` is called from a real-time thread if needed (but likely not critical)

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_default` | Default initialization sets leading_tempo=120.0, video_fps=30.0 |
| `test_init_custom_config` | Custom config values are applied correctly |
| `test_channel_tempo_derivation` | Channel tempo = leading_tempo * (multiplier/divisor) |
| `test_beat_position_advancement` | Beat position increases monotonically with time |
| `test_beat_position_wrap` | Beat position wraps to 0 after reaching 1.0 |
| `test_phase_offset` | phase_coarse shifts beat position by correct fraction |
| `test_mute_channel` | Muted channel returns beat position 0 or None |
| `test_tap_tempo_ch1` | Tap tempo updates leading_tempo based on tap intervals |
| `test_tap_tempo_smoothing` | Tap tempo applies smoothing to avoid jitter |
| `test_video_fps_alignment` | Frames per beat computed correctly from video_fps and tempo |
| `test_error_invalid_channel` | Setting/getting invalid channel (7, 0, -1) raises IndexError |
| `test_error_invalid_multiplier` | Setting multiplier outside 1-32 raises ValueError |
| `test_error_invalid_divisor` | Setting divisor outside 1-32 raises ValueError |
| `test_error_invalid_phase` | Setting phase_coarse outside 0-3 raises ValueError |
| `test_cleanup` | No resource leaks; can be destroyed cleanly |

**Minimum coverage**: 80% before task is marked done.

---

## Open Questions and Research Findings

