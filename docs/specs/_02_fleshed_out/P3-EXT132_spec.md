# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT132_vtempi.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT132 — vtempi (ProgramPage) - Port from VJlive legacy to VJLive3

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

The module is CPU-based (no GPU required) and runs as a stateful object that updates on each tick of the VJLive3 time manager. It is designed to be embedded within the ProgramPage UI layer, allowing users to configure tempo parameters through a graphical interface.

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
4. Stores the beat position for retrieval via `get_tempo_channels()` or a separate query method

The `get_tempo_channels()` method returns a dictionary mapping channel numbers (1-6) to their current beat position (0.0-1.0) or possibly the derived BPM value. The spec should clarify which.

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

### VJLive3 ProgramPage Integration

The `VTempiPlugin` is a **utility module** that integrates into the ProgramPage UI layer. It does not process video frames directly but provides timing signals that other effects and modules can query to synchronize their behavior.

**Position in architecture**:
- Lives in the `plugins.clock` or `modules.timing` namespace
- Instantiated once at startup and shared across all modules that need timing
- Controlled via the ProgramPage UI where users can adjust tempo, channel settings, and video FPS
- Communicates with the TimeManager to receive `delta_time` updates

**Typical usage**:

```python
# Initialize with config from ProgramPage
vtempi = VTempiPlugin(config={"leading_tempo": 120.0, "video_fps": 30.0})

# In the main loop (called once per frame or at fixed interval)
vtempi.update(delta_time)  # delta_time in seconds

# Other modules can query current channel states
tempos = vtempi.get_tempo_channels()  # returns {1: 120.0, 2: 60.0, ...} BPM values
# or maybe beat positions: {1: 0.25, 2: 0.5, ...}

# A visual effect can use this to trigger on beat:
if tempos[1] < 0.1:  # near start of beat
    effect.flash()
```

**ProgramPage UI binding**:
- The ProgramPage provides sliders/controls for `leading_tempo`, `video_fps`, and per-channel `multiplier`, `divisor`, `phase`, `mute`
- Changes to these controls update the plugin's parameters in real-time
- The UI may also display current BPM or beat phase for each channel

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

- **Minimal**: Stores a few dozen floats and ints (leading_tempo, video_fps, per-channel multiplier/divisor/phase/mute/duty_cycle)
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
| `test_phase_offset` | phase_coarse shifts beat position by correct fraction (0.25 per step) |
| `test_mute_channel` | Muted channel returns beat position 0 or None |
| `test_tap_tempo_ch1` | Tap tempo updates leading_tempo based on tap intervals |
| `test_tap_tempo_smoothing` | Tap tempo applies smoothing to avoid jitter |
| `test_video_fps_alignment` | Frames per beat computed correctly: fps * (60/tempo) |
| `test_error_invalid_channel` | Setting/getting invalid channel (7, 0, -1) raises IndexError |
| `test_error_invalid_multiplier` | Setting multiplier outside 1-32 raises ValueError |
| `test_error_invalid_divisor` | Setting divisor outside 1-32 raises ValueError |
| `test_error_invalid_phase` | Setting phase_coarse outside 0-3 raises ValueError |
| `test_cleanup` | No resource leaks; can be destroyed cleanly |

**Minimum coverage**: 80% before task is marked done.

---

## Open Questions and Research Findings

### [NEEDS RESEARCH]: What exactly does `get_tempo_channels()` return? Beat positions (0-1) or BPM values?

**Finding**: The legacy manifest shows parameters but not the method signature. The skeleton spec says "Return current tempo values for each channel (1–6)" and returns `dict[int, float]`. In modular synths, a "tempo" could mean BPM or phase. Given that the module is called "tempo" and has a `get_tempo_channels()` method, it likely returns the actual BPM for each channel (the derived tempo). However, beat position is also useful for triggering.

**Resolution**: Define `get_tempo_channels()` to return a dict mapping channel number to its **current BPM** (float). For beat phase, provide a separate method `get_beat_phases()` or `get_phases()`. Alternatively, return both in a tuple. To keep it simple, `get_tempo_channels()` returns BPMs; if beat phase is needed, call `get_beat_phase(channel)`.

### [NEEDS RESEARCH]: What is the purpose of `duty_cycle` parameter?

**Finding**: In modular clock modules, duty cycle controls the pulse width of the clock output (e.g., 50% for a square wave, 10% for a short trigger). For video timing, duty cycle might be used to create short "trigger" events rather than continuous signals. However, the skeleton spec doesn't include duty_cycle in the public interface.

**Resolution**: Include `duty_cycle` as a parameter (float 0.0-1.0) that can be set via `set_parameter("duty_cycle", value)`. It may be used by consumers to determine how long a "beat" event lasts. The VTempi module itself may not use it internally; it's just metadata for downstream modules.

### [NEEDS RESEARCH]: How does the module handle video frame alignment at non-integer frames-per-beat?

**Finding**: If video_fps=30 and channel_tempo=120 BPM, then frames_per_beat = 30 * (60/120) = 15 frames exactly. That's clean. But if tempo=125 BPM, frames_per_beat = 30 * (60/125) = 14.4 frames, which is not an integer. The beat position will drift relative to frame boundaries.

**Resolution**: The module should not try to force alignment; it simply computes beat position as a continuous float. Downstream modules that need frame-aligned triggers should round to nearest frame or use a threshold. Alternatively, the module could offer a "snap to frames" mode, but that's likely beyond scope.

---

## Configuration Schema

```python
METADATA = {
  "params": [
    {"id": "leading_tempo", "name": "Leading Tempo", "default": 120.0, "min": 0.0, "max": 500.0, "type": "float", "description": "Master BPM tempo (0-500 BPM)"},
    {"id": "video_fps", "name": "Video FPS", "default": 30.0, "min": 1.0, "max": 120.0, "type": "float", "description": "Video frame rate for alignment (1-120 fps)"},
    {"id": "tap_tempo_ch1", "name": "Tap Tempo (Ch1)", "default": False, "type": "bool", "description": "Use tap tempo for channel 1 instead of leading_tempo"},
    {"id": "multiplier_1", "name": "Ch1 Multiplier", "default": 1, "min": 1, "max": 32, "type": "int", "description": "Channel 1 tempo multiplier"},
    {"id": "divisor_1", "name": "Ch1 Divisor", "default": 1, "min": 1, "max": 32, "type": "int", "description": "Channel 1 tempo divisor"},
    {"id": "phase_coarse_1", "name": "Ch1 Phase", "default": 0, "min": 0, "max": 3, "type": "int", "description": "Channel 1 phase offset (0=0°, 1=90°, 2=180°, 3=270°)"},
    {"id": "channel_mute_1", "name": "Mute Ch1", "default": False, "type": "bool", "description": "Mute channel 1"},
    {"id": "duty_cycle_1", "name": "Ch1 Duty Cycle", "default": 0.5, "min": 0.0, "max": 1.0, "type": "float", "description": "Channel 1 pulse width (0.0-1.0)"},
    # Repeat for channels 2-6 (multiplier_2, divisor_2, etc.)
  ]
}
```

**Presets**: Not applicable; this is a utility module.

---

## State Management

- **Per-update state**: `delta_time`, `elapsed` accumulator, current beat positions for each channel. These are transient and updated every `update()` call.
- **Persistent state**: All configuration parameters (leading_tempo, video_fps, per-channel multiplier/divisor/phase/mute/duty_cycle). These persist for the lifetime of the module instance.
- **Init-once state**: Nothing special; all state is simple data.
- **Thread safety**: The module is **not thread-safe** by default. If `update()` and `get_tempo_channels()` are called from different threads, external synchronization (e.g., a lock) is required. For typical VJLive3 usage, all calls happen on the main thread, so this is not an issue.

---

## GPU Resources

This module is **CPU-only**. It does not use any GPU resources (no shaders, no textures). It can run on any hardware, including headless servers.

---

## Public Interface

```python
class VTempiPlugin:
    def __init__(self, config: dict) -> None:
        """
        Initialize the V-Tempi plugin with configuration.
        
        Args:
            config: Dictionary containing plugin settings like 'leading_tempo' and 'video_fps'
        """
    
    def update(self, delta_time: float) -> None:
        """
        Update internal state based on time delta for tempo generation.
        
        Args:
            delta_time: Time elapsed since last update in seconds
        """
    
    def get_tempo_channels(self) -> dict:
        """
        Return current tempo values per channel (1–6).
        
        Returns:
            Dictionary mapping channel index to BPM value
        """
    
    def set_video_fps(self, fps: float) -> None:
        """
        Set the video frame rate for synchronization.
        
        Args:
            fps: Frame rate in frames per second (e.g., 30.0)
        """
    
    def get_video_fps(self) -> float:
        """
        Get current video FPS setting.
        
        Returns:
            Current video FPS
        """
    
    def set_channel_parameter(self, channel: int, param: str, value: Any) -> None:
        """
        Set a parameter for a specific channel.
        
        Args:
            channel: Channel number (1-6)
            param: Parameter name ('multiplier', 'divisor', 'phase_coarse', 'mute', 'duty_cycle')
            value: New value (type depends on parameter)
        """
    
    def get_channel_parameter(self, channel: int, param: str) -> Any:
        """
        Get a parameter for a specific channel.
        
        Args:
            channel: Channel number (1-6)
            param: Parameter name
            
        Returns:
            Current parameter value
        """
    
    def tap(self, channel: int = 1) -> None:
        """
        Register a tap event for tap tempo (for channel 1).
        
        Args:
            channel: Channel to tap (default 1, only channel 1 supports tap)
        """
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `config` | `dict` | Initial configuration for the plugin | Must contain 'leading_tempo' (float, ≥0) and optional 'video_fps' (float, ≥1.0) |
| `delta_time` | `float` | Time delta in seconds between updates | Must be ≥ 0; typically from VJLive3's time loop |
| `fps` | `float` | Video frame rate to sync with | Range: [1.0, 120.0]; defaults to 30.0 if missing or invalid |
| `channel` | `int` | Channel number (1-6) | Must be in range 1-6 |
| `param` | `str` | Parameter name | Must be one of: 'multiplier', 'divisor', 'phase_coarse', 'mute', 'duty_cycle' |
| `value` | `Any` | Parameter value | Type depends on parameter (int, bool, float) |
| `return_value` (from get_tempo_channels) | `dict[int, float]` | Tempo per channel (index 1–6) in BPM | Each value must be ≥ 0; values derived from leading_tempo and internal state |
| `return_value` (from get_video_fps) | `float` | Current video FPS | ≥ 1.0 |
| `return_value` (from get_channel_parameter) | `Any` | Current channel parameter value | Type depends on parameter |

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `pydub` — used for audio timing reference — fallback: none (no audio dependency; pydub not actually needed)
  - `numpy` — used in internal state calculations — fallback: basic math operations via built-in types (not critical)
- Internal modules this depends on:
  - `vjlive3.core.time_manager.TimeManager` — for accurate delta_time delivery (but VTempi doesn't depend on it directly; it just receives delta_time)
  - `vjlive3.modules.clock.ClockInterface` — to provide tempo channel output format
  - `vjlive3.ui.programpage.ProgramPageBase` — for integration into the ProgramPage UI layer

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_default` | Default initialization sets leading_tempo=120.0, video_fps=30.0 |
| `test_init_custom_config` | Custom config values are applied correctly |
| `test_channel_tempo_derivation` | Channel tempo = leading_tempo * (multiplier/divisor) |
| `test_beat_position_advancement` | Beat position increases monotonically with time |
| `test_beat_position_wrap` | Beat position wraps to 0 after reaching 1.0 |
| `test_phase_offset` | phase_coarse shifts beat position by correct fraction (0.25 per step) |
| `test_mute_channel` | Muted channel returns beat position 0 or None |
| `test_tap_tempo_ch1` | Tap tempo updates leading_tempo based on tap intervals |
| `test_tap_tempo_smoothing` | Tap tempo applies smoothing to avoid jitter |
| `test_video_fps_alignment` | Frames per beat computed correctly: fps * (60/tempo) |
| `test_error_invalid_channel` | Setting/getting invalid channel (7, 0, -1) raises IndexError |
| `test_error_invalid_multiplier` | Setting multiplier outside 1-32 raises ValueError |
| `test_error_invalid_divisor` | Setting divisor outside 1-32 raises ValueError |
| `test_error_invalid_phase` | Setting phase_coarse outside 0-3 raises ValueError |
| `test_cleanup` | No resource leaks; can be destroyed cleanly |

**Minimum coverage**: 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-X] P3-EXT132: port vtempi plugin to VJLive3` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES

### vjlive1/plugins/vtempi/__init__.py (L1-20)
```python
"""
V-Tempi Plugin for VJLive
Faithful recreation of Make Noise TEMPI — 6-channel polyphonic clock module
extended for video synchronization.
"""

from .vtempi import VTempiPlugin

PLUGIN_METADATA = {
    "id": "vtempi",
    "name": "V-Tempi",
    "description": "6-channel tempo engine with state management",
    "category": "clock",
    "version": "1.0.0",
}

DEFAULT_CONFIG = {
    "leading_tempo": 120.0,
    "video_fps": 30.0,
}
```

### vjlive1/plugins/vtempi/manifest.json (L1-20)
```json
{
  "collection": "vtempi",
  "source": "standalone",
  "modules": [
    {
      "id": "vtempi",
      "name": "V-Tempi",
      "description": "6-channel tempo engine with state management",
      "category": "clock",
      "tags": [
        "tempi",
        "clock",
        "tempo",
        "sync",
        "modular"
      ],
      "gpu_tier": "NONE",
      "module_path": "plugins.vtempi.vtempi",
      "class_name": "VTempiPlugin",
      "node_type": "tempi",
```

### vjlive1/plugins/vtempi/manifest.json (L17-36)
```json
      "gpu_tier": "NONE",
      "module_path": "plugins.vtempi.vtempi",
      "class_name": "VTempiPlugin",
      "node_type": "tempi",
      "parameters": [
        {
          "id": "leading_tempo",
          "name": "Leading Tempo",
          "type": "float",
          "min": 0.0,
          "max": 10.0,
          "default": 3.57
        },
        {
          "id": "tap_tempo_ch1",
          "name": "Tap Tempo (Ch1)",
          "type": "bool",
          "default": true
        },
```

### vjlive1/plugins/vtempi/manifest.json (L33-52)
```json
          "type": "bool",
          "default": true
        },
        {
          "id": "multiplier",
          "name": "Multiplier",
          "type": "int",
          "min": 1,
          "max": 32,
          "default": 1
        },
        {
          "id": "divisor",
          "name": "Divisor",
          "type": "int",
          "min": 1,
          "max": 32,
          "default": 1
        },
```

### vjlive1/plugins/vtempi/manifest.json (L49-68)
```json
          "max": 32,
          "default": 1
        },
        {
          "id": "phase_coarse",
          "name": "Phase Coarse",
          "type": "int",
          "min": 0,
          "max": 3,
          "default": 0
        },
        {
          "id": "channel_mute",
          "name": "Channel Mute",
          "type": "bool",
          "default": false
        },
        {
          "id": "duty_cycle",
          "name": "Duty Cycle",
```

[NEEDS RESEARCH]: The actual implementation of the VTempiPlugin class (the vtempi.py file) was not found in the legacy lookup. The spec is based on the manifest metadata, DEFAULT_CONFIG, and knowledge of the Make Noise TEMPI module. The implementation should be verified against any remaining legacy code or the original VJLive1 plugin if available. The core algorithm (tempo derivation, beat phase calculation) is standard for modular clock modules and should be straightforward to implement.
