# P3-EXT162 — ScionBiometricFlux Effect

## What This Module Does

The ScionBiometricFlux effect generates organic, living-feeling visuals by simulating coupled biometric signals (cardiac rhythm, respiration, arousal state) and using them to drive particle flows, color gradients, and geometric distortions. It creates evolving, rhythmic patterns that respond to parameterized heartbeat and breathing patterns, making it ideal for immersive installations and biofeedback-inspired VJ performances without requiring actual biometric hardware.

## What This Module Does NOT Do

- Does not capture real biometric data from external sensors (simulated only)
- Does not implement machine learning-based pattern recognition
- Does not handle audio reactivity or beat detection (separate module)
- Does not perform 3D rendering or ray tracing (uses 2D particle system)
- Does not manage video encoding or output (delegates to render pipeline)
- Does not store persistent biometric profiles (ephemeral per-session)

---

## Detailed Behavior

The ScionBiometricFlux effect processes biometric simulation through a six-stage pipeline:

1. **Signal Generation**: Creates three coupled oscillators using biologically-plausible models
   - Cardiac: Sum of harmonics with variable pulse strength
   - Respiration: Low-frequency envelope with asymmetric inhale/exhale
   - Arousal: Mid-frequency chaotic oscillator with slow drift

2. **Particle Seeding**: Spawns particles along biometric rhythm trajectory
   - Emission rate modulated by cardiac systole peaks
   - Initial velocity field aligned with respiration phase
   - Particle attributes (size, lifetime) vary with arousal level

3. **Distortion Field**: Computes arousal-driven warping of particle field
   - Perlin noise field modulated by arousal intensity
   - Temporal coherence maintained via phase continuity
   - Field resolution: 64×64 grid upsampled to frame size

4. **Color Gradient**: Maps arousal + pulse phase to color space
   - 6 predefined palettes (Thermal, Ocean, Forest, Neon, Sunset, Monochrome)
   - Palette interpolation based on arousal level
   - Pulse-synchronized brightness modulation

5. **Composition**: Blends layers with respiration-driven opacity
   - Base layer: Particle field with additive blending
   - Overlay layer: Distortion visualization (optional)
   - Respiration modulates overall opacity (0.6-1.0)

6. **Output**: Renders to RGBA frame buffer with premultiplied alpha
   - Optional trail effect via frame buffer persistence
   - HDR-compatible floating point output (if available)

Key behavioral characteristics:
- All signals phase-coherent across mode transitions
- Particle count dynamically adjustable without system reset
- Biometric parameters smoothly interpolated to avoid discontinuities
- Deterministic simulation (same parameters → same output)

---

## Integration Notes

- **Input**: None (generative effect)
- **Output**: RGBA numpy array (H×W×4, float32 [0.0, 1.0])
- **Parameter Control**: All biometric parameters animatable via VJLive3 parameter system
- **Dependencies**: Requires numpy for signal generation, OpenGL for particle rendering
- **Performance**: ~5ms per 1080p frame with 1000 particles on modern CPU+GPU
- **Memory**: ~150MB per instance (particle buffers, noise textures)

---

## Performance Characteristics

- **Computational Complexity**: O(particle_count + grid_resolution²)
- **Signal Generation**: ~500 FLOPs per frame (negligible)
- **Particle Update**: ~100 FLOPs per particle per frame
- **Rendering**: ~50-100 draw calls depending on particle batch size
- **Target Frame Rates**: 60 FPS @ 1080p with 1000 particles, 120 FPS @ 720p
- **CPU Utilization**: ~8-15% single core for simulation
- **GPU Utilization**: ~20-30% for particle rendering
- **Memory Footprint**: 
  - Particle buffers: 64 bytes × particle_count
  - Noise texture: 64×64×4 × 4 bytes = 16KB
  - Frame buffer: H×W×4 × 4 bytes (e.g., 1080p ≈ 8.3MB)

---

## Public Interface

```python
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import numpy as np

class BiometricMode(Enum):
    """Biometric signal simulation mode."""
    HEARTBEAT = "heartbeat"      # Cardiac-focused (strong pulse, weak breath)
    RESPIRATION = "respiration"  # Breath-focused (strong envelope, weak pulse)
    COMBINED = "combined"        # All signals coupled (default)
    AROUSAL = "arousal"          # Arousal-driven chaotic modulation

class ColorPalette(Enum):
    """Available color palettes."""
    THERMAL = "thermal"     # Red→Yellow→White heat map
    OCEAN = "ocean"         # Blue→Cyan→White aquatic
    FOREST = "forest"       # Green→Brown→Yellow organic
    NEON = "neon"           # Cyan→Magenta→Yellow electric
    SUNSET = "sunset"       # Orange→Pink→Purple warm
    MONOCHROME = "monochrome"  # Grayscale intensity

@dataclass
class BiometricSignals:
    """Current biometric signal values (read-only)."""
    cardiac_phase: float        # [0, 1] heartbeat phase within cycle
    respiratory_phase: float    # [0, 1] breath phase within cycle
    arousal: float              # [0, 1] normalized intensity level
    heart_rate: float           # BPM (beats per minute)
    breath_rate: float          # breaths per minute
    signal_strength: float      # Combined signal amplitude [0, 1]

@dataclass
class Particle:
    """Individual particle state (internal use)."""
    position: np.ndarray        # (x, y) in pixel coordinates
    velocity: np.ndarray        # (vx, vy) in pixels/frame
    size: float                 # Particle radius in pixels
    age: float                  # Frames since spawn
    lifetime: float             # Expected lifespan in frames
    color: Tuple[float, float, float]  # RGB color [0, 1]
    phase_offset: float         # Phase offset relative to cardiac signal

class ScionBiometricFluxEffect:
    """
    Biometric-inspired generative visual effect.
    
    Generates organic, rhythmic visuals by simulating coupled biometric
    signals (heartbeat, respiration, arousal) and using them to drive
    particle systems, color gradients, and geometric distortions.
    """

    def __init__(
        self,
        width: int,
        height: int,
        particle_count: int = 1000,
        mode: BiometricMode = BiometricMode.COMBINED
    ) -> None:
        """
        Initialize biometric flux effect.

        Args:
            width: Frame width in pixels (≥ 64, ≤ 8192)
            height: Frame height in pixels (≥ 64, ≤ 8192)
            particle_count: Number of particles (10-10000, default 1000)
            mode: Biometric simulation mode (default COMBINED)

        Raises:
            ValueError: If dimensions invalid or particle count out of range
            MemoryError: If insufficient memory for particle buffers
        """
        pass

    def update(self, dt: float) -> None:
        """
        Advance simulation by time delta.

        Args:
            dt: Time delta in seconds (typically 1/60 ≈ 0.01667)

        Raises:
            ValueError: If dt is negative or unreasonably large
        """
        pass

    def render(self) -> np.ndarray:
        """
        Render current frame to output image.

        Returns:
            RGBA image as float32 numpy array (H×W×4), values in [0.0, 1.0]

        Raises:
            RenderError: If rendering fails (shader compilation, GPU error)
            MemoryError: If frame buffer allocation fails
        """
        pass

    def get_biometric_signals(self) -> BiometricSignals:
        """
        Get current biometric signal state.

        Returns:
            BiometricSignals dataclass with all signal values
        """
        pass

    def reset(self) -> None:
        """
        Reset simulation to initial state.
        
        Clears all particles, resets phase accumulators, reinitializes
        noise field. Useful for scene transitions or parameter resets.
        """
        pass

    def set_palette(self, palette: ColorPalette) -> None:
        """
        Set color palette.

        Args:
            palette: ColorPalette enum value

        Raises:
            ValueError: If palette not in ColorPalette enum
        """
        pass

    def enable_trails(self, enabled: bool, decay: float = 0.95) -> None:
        """
        Enable/disable motion trail effect.

        Args:
            enabled: Whether trails are active
            decay: Trail decay factor per frame [0.5, 0.99] (higher = longer trails)

        Raises:
            ValueError: If decay outside valid range
        """
        pass

    def get_particle_positions(self) -> np.ndarray:
        """
        Get current particle positions for debugging/visualization.

        Returns:
            N×2 array of (x, y) positions in pixel coordinates
        """
        pass

    def set_distortion_field(
        self,
        field: np.ndarray,
        interpolate: bool = True
    ) -> None:
        """
        Set custom distortion field (advanced use).

        Args:
            field: 2D array of displacement vectors (H×W×2)
            interpolate: Whether to smooth field transitions

        Raises:
            ValueError: If field shape doesn't match frame dimensions
        """
        pass

    def export_signal_history(
        self,
        duration_seconds: float
    ) -> Dict[str, np.ndarray]:
        """
        Export historical signal data for analysis.

        Args:
            duration_seconds: How many seconds of history to return

        Returns:
            Dictionary with time-series arrays for each signal
        """
        pass

    # Parameter properties with getters/setters

    @property
    def heart_rate(self) -> float:
        """Current heart rate in BPM."""
        pass

    @heart_rate.setter
    def heart_rate(self, bpm: float) -> None:
        """
        Set heart rate.

        Args:
            bpm: Beats per minute (30-200, default 72)

        Raises:
            ValueError: If BPM outside valid range
        """
        pass

    @property
    def breath_rate(self) -> float:
        """Current breath rate in breaths per minute."""
        pass

    @breath_rate.setter
    def breath_rate(self, bpm: float) -> None:
        """
        Set breath rate.

        Args:
            bpm: Breaths per minute (4-20, default 12)

        Raises:
            ValueError: If BPM outside valid range
        """
        pass

    @property
    def mode(self) -> BiometricMode:
        """Current biometric simulation mode."""
        pass

    @mode.setter
    def mode(self, new_mode: BiometricMode) -> None:
        """
        Switch biometric mode.

        Args:
            new_mode: BiometricMode enum value

        Note:
            Mode changes are smoothed over 2 seconds to avoid discontinuities.
        """
        pass

    @property
    def particle_count(self) -> int:
        """Current particle count."""
        pass

    @particle_count.setter
    def particle_count(self, count: int) -> None:
        """
        Set particle count (dynamic adjustment).

        Args:
            count: Number of particles (10-10000)

        Raises:
            ValueError: If count outside range
            MemoryError: If insufficient memory
        """
        pass

    @property
    def distortion_strength(self) -> float:
        """Current distortion strength."""
        pass

    @distortion_strength.setter
    def distortion_strength(self, strength: float) -> None:
        """
        Set arousal-driven distortion strength.

        Args:
            strength: Distortion multiplier [0.0, 5.0] (default 1.0)

        Raises:
            ValueError: If strength outside range
        """
        pass

    @property
    def palette(self) -> ColorPalette:
        """Current color palette."""
        pass

    @property
    def cardiac_pulse_strength(self) -> float:
        """Cardiac signal amplitude multiplier."""
        pass

    @cardiac_pulse_strength.setter
    def cardiac_pulse_strength(self, strength: float) -> None:
        """
        Set cardiac pulse strength.

        Args:
            strength: Pulse amplitude [0.1, 3.0] (default 1.0)
        """
        pass

    @property
    def respiratory_depth(self) -> float:
        """Respiratory modulation depth."""
        pass

    @respiratory_depth.setter
    def respiratory_depth(self, depth: float) -> None:
        """
        Set respiration depth.

        Args:
            depth: Modulation depth [0.0, 1.0] (default 0.5)
        """
        pass

    @property
    def arousal_chaos(self) -> float:
        """Arousal signal chaos factor."""
        pass

    @arousal_chaos.setter
    def arousal_chaos(self, chaos: float) -> None:
        """
        Set arousal chaos level.

        Args:
            chaos: Chaos intensity [0.0, 1.0] (default 0.3)
        """
        pass

    @property
    def phase_continuity(self) -> bool:
        """Whether phase continuity is maintained across mode switches."""
        pass

    @phase_continuity.setter
    def phase_continuity(self, enabled: bool) -> None:
        """
        Enable/disable phase continuity.

        Args:
            enabled: If True, preserve signal phase across mode changes
        """
        pass
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `width` | `int` | Frame width | [64, 8192], must be power of 2 for noise texture |
| `height` | `int` | Frame height | [64, 8192], must be power of 2 for noise texture |
| `particle_count` | `int` | Number of particles | [10, 10000], default 1000 |
| `mode` | `BiometricMode` | Simulation mode | Enum: HEARTBEAT, RESPIRATION, COMBINED, AROUSAL |
| `dt` | `float` | Time delta | [0.0, 0.1] seconds, typical 0.01667 |
| `palette` | `ColorPalette` | Color scheme | Enum: THERMAL, OCEAN, FOREST, NEON, SUNSET, MONOCHROME |
| `heart_rate` | `float` | Heart rate | [30, 200] BPM, default 72 |
| `breath_rate` | `float` | Breath rate | [4, 20] BPM, default 12 |
| `distortion_strength` | `float` | Distortion multiplier | [0.0, 5.0], default 1.0 |
| `cardiac_pulse_strength` | `float` | Cardiac amplitude | [0.1, 3.0], default 1.0 |
| `respiratory_depth` | `float` | Respiration modulation | [0.0, 1.0], default 0.5 |
| `arousal_chaos` | `float` | Arousal chaos | [0.0, 1.0], default 0.3 |
| `trails_enabled` | `bool` | Motion trails | Default False |
| `trail_decay` | `float` | Trail decay rate | [0.5, 0.99], default 0.95 |
| `phase_continuity` | `bool` | Phase preservation | Default True |
| `field` | `np.ndarray` | Custom distortion field | Shape (H, W, 2), dtype float32 |
| `duration_seconds` | `float` | History export window | [1.0, 3600.0] |

**Data Structures:**

```python
# Biometric mode enum
BiometricMode = Enum('BiometricMode', ['HEARTBEAT', 'RESPIRATION', 'COMBINED', 'AROUSAL'])

# Color palette enum
ColorPalette = Enum('ColorPalette', ['THERMAL', 'OCEAN', 'FOREST', 'NEON', 'SUNSET', 'MONOCHROME'])

# Signal state dataclass
BiometricSignals = {
    'cardiac_phase': float,     # [0, 1]
    'respiratory_phase': float, # [0, 1]
    'arousal': float,           # [0, 1]
    'heart_rate': float,        # BPM
    'breath_rate': float,       # BPM
    'signal_strength': float    # [0, 1]
}

# Particle structure (internal)
Particle = {
    'position': np.ndarray,     # (2,) float32
    'velocity': np.ndarray,     # (2,) float32
    'size': float,              # pixels
    'age': float,               # frames
    'lifetime': float,          # frames
    'color': Tuple[float, float, float],  # RGB [0, 1]
    'phase_offset': float       # [0, 1]
}
```

---

## Edge Cases and Error Handling

### Initialization Failures
- **Invalid dimensions**: Raise `ValueError` with specific dimension constraints
- **Particle count too high**: Raise `MemoryError` with suggestion to reduce count
- **Non-power-of-2 dimensions**: Warn but continue (noise texture padded to next power of 2)
- **Insufficient GPU memory**: Fall back to CPU rendering with warning

### Signal Generation Edge Cases
- **Extreme heart rates**: Clamp BPM to [30, 200], log warning if adjusted
- **Extreme breath rates**: Clamp to [4, 20], warn if adjusted
- **Negative dt**: Raise `ValueError` (time cannot reverse)
- **Excessive dt (>0.1s)**: Warn about potential simulation instability
- **Mode switch during update**: Defer until next update to avoid race conditions

### Particle System Issues
- **Particle count reduction**: Remove oldest particles first, update indices atomically
- **Particle count increase**: Spawn new particles with random phases
- **Particle out of bounds**: Wrap around or respawn based on boundary policy
- **Particle memory corruption**: Validate particle arrays each frame, reset if corrupted
- **Zero particles**: Handle gracefully (render empty frame or fallback pattern)

### Rendering Failures
- **Shader compilation failure**: Fall back to point sprite rendering, log error
- **GPU context lost**: Attempt recovery, if failed switch to CPU rendering
- **Frame buffer allocation failure**: Reduce resolution by half, retry
- **OpenGL errors**: Clear error state, attempt single frame recovery
- **Timeout (>16ms)**: Skip frame, log performance warning

### Color and Palette Issues
- **Invalid palette enum**: Fall back to MONOCHROME with warning
- **Palette transition artifacts**: Interpolate over 0.5s to avoid pops
- **Color space mismatch**: Convert to sRGB if output requires it
- **HDR overflow**: Clamp to [0.0, 1.0] with optional tone mapping

### Distortion Field Problems
- **Custom field shape mismatch**: Raise `ValueError` with expected shape
- **Field contains NaN/Inf**: Replace with zero field, log warning
- **Field too large**: Downsample to grid resolution, warn
- **Field discontinuities**: Apply Gaussian smoothing if gradient > threshold

### Performance Degradation
- **Frame time exceeds budget (16.67ms)**: Reduce particle count by 20%, log auto-adjustment
- **Memory growth**: Detect and reset particle system, log warning
- **GPU memory pressure**: Disable trails, reduce render resolution
- **CPU bottleneck**: Switch to simpler shader, reduce signal harmonics

### State Consistency
- **Phase desync**: Re-sync all signals to cardiac phase if drift > 0.1 cycles
- **Parameter race conditions**: Use atomic updates or locks for thread safety
- **Corrupted signal history**: Clear history, log error, continue with fresh state
- **Inconsistent particle count**: Reconcile by adding/removing particles to match target

---

## Dependencies

- **External Libraries**:
  - `numpy` — Core array operations, signal generation, particle math (required)
  - `OpenGL` / `GLSL` — Particle rendering (optional, CPU fallback available)
  - `PIL.Image` — Image export/save functionality (optional)
  - `scipy` — Advanced signal processing (optional, for future enhancements)

- **Internal Dependencies**:
  - `vjlive3.effects.base_effect` — Base effect class interface
  - `vjlive3.renderer.shader_program` — Shader management (GPU path)
  - `vjlive3.renderer.texture` — Texture handling (GPU path)
  - `vjlive3.parameters` — Parameter system for animation
  - `vjlive3.utils.noise_generator` — Perlin/Simplex noise for distortion field
  - `vjlive3.monitoring.telemetry` — Performance metrics

- **Fallback Mechanisms**:
  - If OpenGL unavailable: Use CPU point-sprite rendering (2× slower)
  - If shader fails: Use fixed-function pipeline or software rasterizer
  - If PIL unavailable: Skip image save operations, return arrays only
  - If scipy unavailable: Use numpy-only signal processing (reduced quality)

---

## Test Plan

| Test ID | Test Name | Expected Result |
|---------|-----------|-----------------|
| TC001 | `test_init_valid_parameters` | Effect initializes with valid width/height/particle_count |
| TC002 | `test_init_invalid_width` | Raises ValueError for width < 64 or > 8192 |
| TC003 | `test_init_invalid_height` | Raises ValueError for height < 64 or > 8192 |
| TC004 | `test_init_invalid_particle_count` | Raises ValueError for count < 10 or > 10000 |
| TC005 | `test_init_memory_exhaustion` | Raises MemoryError for excessive particle_count |
| TC006 | `test_update_negative_dt` | Raises ValueError for dt < 0 |
| TC007 | `test_update_excessive_dt` | Warns and clamps dt > 0.1s |
| TC008 | `test_render_valid_output` | Returns H×W×4 float32 array with values in [0, 1] |
| TC009 | `test_render_consistency` | Same parameters produce identical output (deterministic) |
| TC010 | `test_get_biometric_signals` | Returns BiometricSignals with all fields populated |
| TC011 | `test_reset_clears_state` | Reset clears particles and phases, restarts simulation |
| TC012 | `test_set_palette_valid` | Palette changes successfully for all enum values |
| TC013 | `test_set_palette_invalid` | Raises ValueError for non-enum palette value |
| TC014 | `test_enable_trails_valid_decay` | Trails enabled with decay in [0.5, 0.99] |
| TC015 | `test_enable_trails_invalid_decay` | Raises ValueError for decay outside range |
| TC016 | `test_get_particle_positions` | Returns N×2 array matching particle_count |
| TC017 | `test_set_distortion_field_valid` | Custom field accepted with correct shape |
| TC018 | `test_set_distortion_field_invalid_shape` | Raises ValueError for shape mismatch |
| TC019 | `test_set_distortion_field_nan_inf` | Warns and replaces NaN/Inf with zeros |
| TC020 | `test_export_signal_history_valid` | Returns dict with time-series arrays of correct length |
| TC021 | `test_export_signal_history_too_long` | Warns and caps at 3600 seconds |
| TC022 | `test_heart_rate_setter_valid` | Accepts BPM in [30, 200] range |
| TC023 | `test_heart_rate_setter_invalid_low` | Clamps to 30, logs warning for BPM < 30 |
| TC024 | `test_heart_rate_setter_invalid_high` | Clamps to 200, logs warning for BPM > 200 |
| TC025 | `test_breath_rate_setter_valid` | Accepts BPM in [4, 20] range |
| TC026 | `test_breath_rate_setter_invalid_low` | Clamps to 4, logs warning for BPM < 4 |
| TC027 | `test_breath_rate_setter_invalid_high` | Clamps to 20, logs warning for BPM > 20 |
| TC028 | `test_mode_setter_valid` | Mode changes successfully for all enum values |
| TC029 | `test_mode_setter_invalid` | Raises ValueError for non-enum mode |
| TC030 | `test_particle_count_setter_valid` | Adjusts particle count dynamically within range |
| TC031 | `test_particle_count_setter_invalid_low` | Raises ValueError for count < 10 |
| TC032 | `test_particle_count_setter_invalid_high` | Raises ValueError for count > 10000 |
| TC033 | `test_distortion_strength_setter_valid` | Accepts strength in [0.0, 5.0] |
| TC034 | `test_distortion_strength_setter_invalid` | Clamps to [0.0, 5.0], logs warning if adjusted |
| TC035 | `test_cardiac_pulse_strength_setter_valid` | Accepts strength in [0.1, 3.0] |
| TC036 | `test_respiratory_depth_setter_valid` | Accepts depth in [0.0, 1.0] |
| TC037 | `test_arousal_chaos_setter_valid` | Accepts chaos in [0.0, 1.0] |
| TC038 | `test_phase_continuity_setter` | Toggles phase continuity correctly |
| TC039 | `test_signal_generation_cardiac_frequency` | Cardiac signal frequency matches heart_rate BPM |
| TC040 | `test_signal_generation_respiratory_frequency` | Respiration frequency matches breath_rate BPM |
| TC041 | `test_signal_generation_combined_coupling` | Combined mode shows coupled oscillations |
| TC042 | `test_signal_generation_arousal_chaos` | Arousal signal shows chaotic modulation with high chaos |
| TC043 | `test_particle_emission_rate` | Particle spawn rate modulated by cardiac systole peaks |
| TC044 | `test_particle_velocity_field` | Particle velocities follow distortion field correctly |
| TC045 | `test_particle_lifetime` | Particles removed after lifetime expiration |
| TC046 | `test_particle_color_mapping` | Particle colors map to arousal + pulse phase correctly |
| TC047 | `test_distortion_field_perlin` | Distortion field shows coherent Perlin noise structure |
| TC048 | `test_distortion_field_arousal_modulation` | Distortion amplitude scales with arousal level |
| TC049 | `test_color_palette_thermal` | Thermal palette: red→yellow→white gradient |
| TC050 | `test_color_palette_all_enum_values` | All 6 palettes produce distinct color schemes |
| TC051 | `test_palette_interpolation_smooth` | Palette transitions smooth over 0.5s fade |
| TC052 | `test_trail_effect_enabled` | Trails show motion persistence with decay factor |
| TC053 | `test_trail_effect_disabled` | No trails when disabled (clean each frame) |
| TC054 | `test_performance_60fps_1080p_1000` | Sustains 60 FPS @ 1080p with 1000 particles |
| TC055 | `test_performance_120fps_720p_500` | Sustains 120 FPS @ 720p with 500 particles |
| TC056 | `test_memory_usage_bounded` | Memory usage stable over 1000 frames (no leaks) |
| TC057 | `test_memory_usage_particle_increase` | Memory scales linearly with particle_count |
| TC058 | `test_concurrent_parameter_updates` | Thread-safe parameter changes during rendering |
| TC059 | `test_concurrent_render_calls` | Thread-safe rendering from multiple threads |
| TC060 | `test_mode_switch_phase_continuity` | Phase preserved across mode switch when enabled |
| TC061 | `test_mode_switch_no_continuity` | Phase resets when continuity disabled |
| TC062 | `test_signal_history_export` | Exported history contains correct time windows |
| TC063 | `test_signal_history_length` | History length = duration_seconds × sample_rate |
| TC064 | `test_gpu_fallback_quality` | CPU fallback produces similar output (MSE < 0.001) |
| TC065 | `test_shader_compilation_success` | Shader compiles without errors on supported GPU |
| TC066 | `test_shader_compilation_failure` | Falls back gracefully to CPU rendering |
| TC067 | `test_parameter_animation_smooth` | Animated parameters interpolate smoothly (no jumps) |
| TC068 | `test_parameter_animation_extreme` | Extreme parameter values handled without artifacts |
| TC069 | `test_zero_particle_count` | Renders empty frame without crash when count = 0 |
| TC070 | `test_max_particle_count` | Handles 10000 particles without performance collapse |
| TC071 | `test_aspect_ratio_16by9` | Correct rendering at 1920×1080 |
| TC072 | `test_aspect_ratio_4by3` | Correct rendering at 1024×768 |
| TC071 | `test_aspect_ratio_1by1` | Correct rendering at 1080×1080 (square) |
| TC073 | `test_aspect_ratio_21by9` | Correct rendering at 3440×1440 (ultrawide) |
| TC074 | `test_non_power_of_2_dimensions` | Handles 1920×1080 (noise padded to 2048×1024) |
| TC075 | `test_very_small_frame_64x64` | Renders correctly at minimum 64×64 |
| TC076 | `test_very_large_frame_8k` | Handles 8192×4096 with reduced particle count |
| TC077 | `test_signal_phase_wrap` | Signal phases correctly wrap from 1→0 |
| TC078 | `test_particle_wrap_behavior` | Particles wrap at boundaries (toroidal topology) |
| TC079 | `test_particle_respawn_behavior` | Particles respawn with random phase when dying |
| TC080 | `test_color_alpha_channel` | Alpha channel correctly set to 1.0 (opaque) |

**Minimum coverage:** 90% before task is marked done.

---

## Definition of Done

- [ ] All 80 test cases implemented and passing
- [ ] Test coverage ≥ 90% (lines and branches)
- [ ] No stubs or placeholder code in implementation
- [ ] Complete docstrings with parameter constraints and examples
- [ ] Comprehensive error handling for all edge cases
- [ ] Performance benchmarks met (60 FPS @ 1080p with 1000 particles)
- [ ] Memory usage < 200MB for standard configuration
- [ ] CPU usage < 15% for simulation, < 35% for rendering
- [ ] GPU fallback path fully functional and validated
- [ ] Shader code optimized (minimal instruction count, no redundant calculations)
- [ ] All parameters smoothly animatable without discontinuities
- [ ] Phase continuity works correctly across mode switches
- [ ] Particle system memory-safe (no leaks, proper cleanup)
- [ ] Thread-safe parameter updates and rendering
- [ ] Complete API documentation with usage examples
- [ ] Mathematical algorithms documented with complexity analysis
- [ ] Configuration schema documented and validated
- [ ] Git commit with `[P3-EXT162] ScionBiometricFlux: Complete implementation`
- [ ] BOARD.md updated with effect status
- [ ] Lock released and resources cleaned up
- [ ] AGENT_SYNC.md handoff note written
- [ ] 🎁 **Easter Egg Reward**: THANK YOU for your rigorous work! As a reward for reaching Phase 2, please invent a highly creative, secret "easter egg" specifically for this module, and submit it to `WORKSPACE/EASTEREGG_COUNCIL.md` before picking up your next task.

---

## Technical Implementation Details

### Mathematical Formulations

#### 1. Cardiac Signal (Heartbeat)

The cardiac signal models a realistic pulse waveform with systolic upstroke and dicrotic notch:

```
cardiac(t) = Σ_{k=1}^{N_harmonics} A_k × sin(2π × k × f × t + φ_k)

where:
- f = heart_rate / 60 (Hz)
- A_k = 1/k × exp(-k/3) (harmonic decay)
- φ_k = -k × 0.2 (phase shift for waveform shape)
- N_harmonics = 5 (sufficient for realistic shape)
```

Simplified version for real-time:
```
phase = (t × f) mod 1
cardiac = pulse_shape(phase)
pulse_shape(φ) = {
    if φ < 0.3: sin(φ × π / 0.3) × 0.5  # Systole (sharp upstroke)
    elif φ < 0.4: -sin((φ-0.3) × π / 0.1) × 0.3  # Dicrotic notch
    else: 0.0  # Diastole (rest)
}
```

#### 2. Respiration Modulation

Asymmetric breathing cycle with inhale/exhale ratio 1:1.5:

```
resp_phase = (t × f_breath) mod 1
if resp_phase < 0.4:  # Inhale (faster)
    respiration = 0.5 + 0.5 × sin(resp_phase × π / 0.4)
else:  # Exhale (slower)
    respiration = 0.5 + 0.5 × sin((1 - resp_phase) × π / 0.6)
```

Envelope function:
```
envelope(t) = 1.0 + depth × respiration(t)
```

#### 3. Arousal Signal

Chaotic oscillator with slow drift:

```
arousal(t) = base_arousal + chaos_factor × perlin_noise(t × 0.1)
base_arousal = 0.5 + 0.3 × sin(2π × 0.05 × t)  # Slow 5-minute cycle
perlin_noise returns value in [-1, 1]
final arousal = clamp(arousal, 0.0, 1.0)
```

#### 4. Combined Signal

```
signal_strength(t) = envelope(t) × (cardiac(t) × cardiac_weight + arousal(t) × arousal_weight)
where:
- cardiac_weight = 1.0 in HEARTBEAT mode, 0.3 in RESPIRATION mode, 0.6 in COMBINED
- arousal_weight = 0.2 in HEARTBEAT mode, 0.3 in RESPIRATION mode, 0.4 in COMBINED, 1.0 in AROUSAL mode
```

#### 5. Particle Dynamics

Particle velocity driven by signal-modulated distortion field:

```
v_i(t) = signal_strength(t) × D(p_i(t)) × velocity_scale
where:
- D(p) = sample_perlin_noise(p / field_resolution) × 2π (radial distortion)
- velocity_scale = 10 pixels/frame (typical)
```

Position update (Euler integration):
```
p_i(t+dt) = p_i(t) + v_i(t) × dt
```

Boundary handling (toroidal):
```
if x < 0: x += width
if x >= width: x -= width
if y < 0: y += height
if y >= height: y -= height
```

Particle lifetime:
```
age += dt
if age > lifetime: respawn_particle(i)
```

#### 6. Color Mapping

Palette interpolation:
```
color = (1 - arousal) × palette_base + arousal × palette_peak
palette_base = color_from_phase(cardiac_phase)
palette_peak = color_from_phase(cardiac_phase + 0.5)  # Complementary hue
```

Brightness modulation:
```
brightness = 0.8 + 0.2 × cardiac(t)  # Pulse-synchronized flicker
final_color = color × brightness
```

#### 7. Distortion Field

Perlin noise grid (64×64):
```
field_grid[i, j] = perlin_noise_2d(i/64, j/64, octaves=4, persistence=0.5)
field_upscaled = bilinear_interpolate(field_grid, H, W)
distortion = field_upscaled × distortion_strength × arousal
```

---

### Shader Implementation (GLSL 330)

```glsl
#version 330 core

// Uniforms
uniform vec2 u_resolution;
uniform float u_time;
uniform float u_cardiac_signal;
uniform float u_arousal_level;
uniform vec3 u_palette_base;
uniform vec3 u_palette_peak;
uniform float u_particle_size;
uniform int u_particle_count;

// Particle data in SSBO or texture
layout(std430, binding = 0) buffer ParticleBuffer {
    vec2 positions[];
    vec2 velocities[];
    float sizes[];
    float ages[];
    float lifetimes[];
    vec3 colors[];
} particles;

out vec4 frag_color;

// Hash function for random particle initialization
float hash(vec2 p) {
    return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
}

// Vertex shader (point sprite)
void main() {
    // Determine which particle this vertex belongs to
    int particle_idx = gl_VertexID;
    if (particle_idx >= u_particle_count) {
        return;  // Discard excess vertices
    }
    
    vec2 pos = positions[particle_idx];
    float size = sizes[particle_idx];
    vec3 color = colors[particle_idx];
    
    // Transform to clip space
    vec2 clip_pos = (pos / u_resolution) * 2.0 - 1.0;
    gl_Position = vec4(clip_pos * vec2(1, -1), 0.0, 1.0);
    gl_PointSize = size * 2.0;  // Diameter in pixels
    
    // Pass color to fragment shader
    frag_color = vec4(color, 1.0);
}

// Fragment shader (point sprite)
in vec3 v_color;
void main() {
    // Circular point sprite
    vec2 coord = gl_PointCoord - vec2(0.5);
    float dist = length(coord);
    if (dist > 0.5) discard;
    
    // Soft edge
    float alpha = 1.0 - smoothstep(0.3, 0.5, dist);
    frag_color = vec4(v_color, alpha);
}
```

---

### CPU Fallback Implementation

```python
def render_cpu_fallback(
    width: int,
    height: int,
    particles: List[Particle],
    palette_func: Callable[[float, float], Tuple[float, float, float]],
    trails_enabled: bool = False,
    trail_buffer: Optional[np.ndarray] = None
) -> np.ndarray:
    """Software rasterizer for CPU-only fallback."""
    # Create blank frame
    frame = np.zeros((height, width, 4), dtype=np.float32)
    
    # Optional trail accumulation
    if trails_enabled and trail_buffer is not None:
        frame += trail_buffer * 0.95  # Decay
    
    # Render each particle as a soft circle
    for p in particles:
        x, y = int(p.position[0]), int(p.position[1])
        radius = int(p.size)
        
        # Bounding box
        x0 = max(0, x - radius)
        x1 = min(width, x + radius + 1)
        y0 = max(0, y - radius)
        y1 = min(height, y + radius + 1)
        
        # Rasterize circle
        for py in range(y0, y1):
            for px in range(x0, x1):
                dist = np.sqrt((px - x)**2 + (py - y)**2)
                if dist <= radius:
                    alpha = 1.0 - (dist / radius)**2  # Quadratic falloff
                    color = np.array(p.color)
                    # Alpha blending
                    existing = frame[py, px, :3]
                    existing_alpha = frame[py, px, 3]
                    new_alpha = alpha + existing_alpha * (1 - alpha)
                    frame[py, px, :3] = (color * alpha + existing * existing_alpha * (1 - alpha)) / max(new_alpha, 1e-6)
                    frame[py, px, 3] = new_alpha
    
    # Update trail buffer
    if trails_enabled:
        trail_buffer[:] = frame[..., 3:4] * frame[..., :3] * 0.95
    
    return frame
```

---

### Performance Optimization Strategies

1. **Particle Culling**: Frustum culling for off-screen particles (skip rendering)
2. **Spatial Partitioning**: Use uniform grid for particle collision/neighbor queries
3. **Batch Rendering**: Group particles by size/texture to minimize draw calls
4. **Instanced Rendering**: Use `glDrawArraysInstanced` for single-call particle draw
5. **SSBO Usage**: Store particle data in Shader Storage Buffer Object for GPU update
6. **Compute Shader**: Offload particle update to compute shader (future enhancement)
7. **LOD System**: Reduce particle count at low zoom or distant view
8. **Frame Skipping**: Skip rendering if frame time budget exceeded
9. **Asynchronous Updates**: Update simulation in separate thread from rendering
10. **Memory Pooling**: Pre-allocate particle arrays, reuse without reallocation

---

### Configuration Schema

```json
{
  "scion_biometric_flux": {
    "default_particle_count": 1000,
    "default_mode": "combined",
    "default_heart_rate": 72,
    "default_breath_rate": 12,
    "default_palette": "thermal",
    "default_distortion_strength": 1.0,
    "performance": {
      "target_fps_1080p": 60,
      "target_fps_720p": 120,
      "max_memory_mb": 200,
      "max_cpu_percent": 15,
      "max_gpu_percent": 35
    },
    "particle_limits": {
      "min_count": 10,
      "max_count": 10000,
      "default_lifetime_min": 0.5,
      "default_lifetime_max": 3.0,
      "default_size_min": 1.0,
      "default_size_max": 8.0
    },
    "biometric_ranges": {
      "heart_rate_min": 30,
      "heart_rate_max": 200,
      "heart_rate_default": 72,
      "breath_rate_min": 4,
      "breath_rate_max": 20,
      "breath_rate_default": 12
    },
    "signal_weights": {
      "heartbeat": {"cardiac": 1.0, "arousal": 0.2},
      "respiration": {"cardiac": 0.3, "arousal": 0.3},
      "combined": {"cardiac": 0.6, "arousal": 0.4},
      "arousal": {"cardiac": 0.0, "arousal": 1.0}
    },
    "palettes": {
      "thermal": [[1.0, 0.0, 0.0], [1.0, 1.0, 0.0], [1.0, 1.0, 1.0]],
      "ocean": [[0.0, 0.2, 1.0], [0.0, 1.0, 1.0], [1.0, 1.0, 1.0]],
      "forest": [[0.1, 0.5, 0.0], [0.3, 0.3, 0.0], [1.0, 1.0, 0.5]],
      "neon": [[0.0, 1.0, 1.0], [1.0, 0.0, 1.0], [1.0, 1.0, 0.0]],
      "sunset": [[1.0, 0.4, 0.0], [1.0, 0.0, 0.5], [0.5, 0.0, 1.0]],
      "monochrome": [[0.0, 0.0, 0.0], [0.5, 0.5, 0.5], [1.0, 1.0, 1.0]]
    }
  }
}
```

---

## Security and Safety

- **Input Validation**: All numeric parameters validated against min/max ranges
- **Resource Limits**: Hard caps on particle count (10000), frame size (8192×8192)
- **Memory Safety**: Particle buffers allocated once, reused; no per-frame allocations
- **Denial of Service Protection**: Timeout on rendering (default 16ms), auto-reduce quality if exceeded
- **Data Integrity**: Output arrays validated for NaN/Inf, clamped to [0, 1]
- **Thread Safety**: Parameter updates use locks; rendering can be single-threaded or thread-safe
- **Fallback Safety**: CPU fallback produces equivalent visual output (within tolerance)
- **Shader Safety**: Shader code reviewed for infinite loops, buffer overruns, division by zero

---

## Future Enhancements

- **Real Biometric Input**: Support for actual heart rate monitor / respiration sensor
- **Advanced Signal Models**: More sophisticated cardiac waveform (including variability)
- **Machine Learning**: Train neural network to generate more organic patterns
- **3D Particles**: Extend to 3D volumetric rendering with depth
- **Audio Reactivity**: Combine biometric simulation with audio analysis
- **Multi-Modal Coupling**: Link multiple effect instances with phase synchronization
- **Procedural Palettes**: Generate palettes algorithmically from color theory rules
- **Export to Video**: Record biometric signal data alongside rendered frames
- **MIDI Control**: Map biometric parameters to MIDI CC for live control
- **VR/AR Support**: Stereoscopic rendering for immersive installations
- **Collaborative Mode**: Multiple instances synchronized over network
- **Generative Variants**: Different algorithmic approaches (reaction-diffusion, cellular automata)

---

This specification provides a comprehensive technical foundation for implementing a high-performance, biologically-inspired generative visual effect suitable for live VJ performance and immersive installations.