# VTemPi Duty Cycle Mode (P3-EXT072)

## Overview

The VTemPi Duty Cycle Mode is a depth-driven visual tempo modulation effect that creates rhythmic, depth-aware variations in video. It's part of the VTemPi (Visual Tempo) system, which synchronizes visual patterns with temporal rhythms.

## What It Does

This plugin modulates video brightness, color, and scanline effects based on:

- **Duty Cycle**: The proportion of time a visual element is "on" vs "off"
- **Tempo**: Beats per minute (BPM) that controls the rhythm speed
- **Depth Mapping**: Uses depth buffer to vary duty cycle and tempo across the scene
- **Rhythm Patterns**: Four distinct rhythmic patterns (straight, swing, shuffle, syncopated)

The result is a video effect where different depth regions appear to pulse and rhythm at different rates, creating a hypnotic, depth-aware visual experience.

## Parameters

### Duty Cycle Parameters

- **`duty_cycle_base`** (float, 0.0-1.0, default: 0.5)
  - Base duty cycle (proportion of "on" time)
  - 0.0 = always off, 1.0 = always on

- **`duty_cycle_variation`** (float, 0.0-0.5, default: 0.2)
  - Amount of depth-based variation in duty cycle
  - Higher values create more extreme brightness modulation

- **`depth_duty_mapping`** (str, default: "uniform")
  - How depth affects duty cycle:
    - `near_long`: Near objects have longer duty cycles (brighter)
    - `far_long`: Far objects have longer duty cycles
    - `mid_long`: Mid-depth objects have longest duty cycles
    - `uniform`: No depth variation (uniform duty cycle)

### Tempo Parameters

- **`tempo_base`** (float, 30-180 BPM, default: 60)
  - Base tempo in beats per minute
  - Controls the speed of the rhythmic modulation

- **`tempo_variation`** (float, 0.0-50.0, default: 20.0)
  - Amount of depth-based tempo variation (BPM)
  - Higher values create more pronounced speed differences

- **`depth_tempo_mapping`** (str, default: "uniform")
  - How depth affects tempo:
    - `near_fast`: Near objects pulse faster
    - `far_fast`: Far objects pulse faster
    - `mid_fast`: Mid-depth objects pulse fastest
    - `uniform`: No depth variation (uniform tempo)

### Rhythm Pattern

- **`rhythm_pattern`** (str, default: "straight")
  - The rhythmic pattern to apply:
    - `straight`: Simple on/off square wave
    - `swing`: Alternating long-short pattern (like swing music)
    - `shuffle`: Smooth sinusoidal modulation
    - `syncopated`: Off-beat emphasis pattern

## Inputs

- **`video_in`** (Texture)
  - Input video stream (RGB/RGBA texture)
  - Expected format: 8-bit per channel

- **`depth_in`** (Texture)
  - Depth buffer texture
  - Should be normalized 0-1 (0 = near, 1 = far)
  - Can come from MiDaS, DPT, or other depth estimation models

## Outputs

- **`video_out`** (Texture)
  - Modulated video stream with VTemPi effects applied
  - Same resolution and format as input

## Technical Details

### Architecture

The plugin is built on the `DepthEffect` base class and uses:

- **OpenGL 3.3 Core** shader for GPU-accelerated processing
- **FBO (Framebuffer Object)** for off-screen rendering
- **VAO/VBO** for fullscreen quad geometry
- **Mock mode** fallback when OpenGL is unavailable

### Shader Implementation

The GLSL fragment shader implements:

1. **Depth factor calculation**: Maps normalized depth to modulation factor based on mapping mode
2. **Duty cycle modulation**: `duty = base + (depth_factor - 0.5) * variation`
3. **Tempo conversion**: BPM → frequency (`freq = tempo / 60`)
4. **Rhythm generation**: Pattern-specific functions that output 0-1 modulation values
5. **Visual effects**:
   - Brightness modulation (70-100% range)
   - Depth-based color tinting (blue→red with depth)
   - Scanline effect synchronized to rhythm

### Performance

- **Target**: 60 FPS at 1920×1080 on RTX 4070 Ti Super
- **Memory**: ~2MB additional buffer (same size as input frame)
- **Optimizations**:
  - Single-pass fullscreen quad rendering
  - Minimal texture lookups (2: video + depth)
  - No dynamic allocations during processing

## Usage Examples

### Basic Usage

```python
from vjlive3.plugins.vtempi_duty_cycle_mode import VTemPiDutyCycleModePlugin

plugin = VTemPiDutyCycleModePlugin()
plugin.initialize(context)

# Process frame with default parameters
output = plugin.process_frame(input_texture, {}, context)
```

### Depth-Aware Pulsing

```python
params = {
    "duty_cycle_base": 0.6,
    "duty_cycle_variation": 0.3,
    "depth_duty_mapping": "near_long",  # Near objects brighter
    "tempo_base": 90.0,
    "tempo_variation": 30.0,
    "depth_tempo_mapping": "far_fast",  # Far objects faster
    "rhythm_pattern": "swing"
}

output = plugin.process_frame(input_texture, params, context)
```

### Subtle Modulation

```python
params = {
    "duty_cycle_base": 0.5,
    "duty_cycle_variation": 0.1,  # Subtle variation
    "depth_duty_mapping": "mid_long",
    "tempo_base": 60.0,
    "tempo_variation": 10.0,
    "depth_tempo_mapping": "uniform",  # Same tempo everywhere
    "rhythm_pattern": "shuffle"
}
```

## Integration with VTemPi Engine

This plugin is designed to integrate with the VTemPiEngine from VJlive-2, which provides:

- Advanced rhythm generation
- Audio-reactive tempo detection
- Pattern sequencing
- Multi-layer modulation

When VTemPiEngine is available, the plugin can:

1. Receive BPM updates from audio analysis
2. Sync with other VTemPi-enabled effects
3. Participate in pattern chains
4. Respond to MIDI clock signals

## Troubleshooting

### Mock Mode

If OpenGL is unavailable or shader compilation fails, the plugin automatically falls back to **mock mode**:

- No GPU processing
- Pass-through behavior (input → output unchanged)
- Logged warning in application logs

Check logs for messages about mock mode activation.

### Performance Issues

If you experience low FPS:

1. Reduce input resolution (e.g., 1280×720 instead of 1920×1080)
2. Lower `duty_cycle_variation` and `tempo_variation` (less complex calculations)
3. Use simpler `rhythm_pattern` (straight is fastest)
4. Ensure depth texture is same resolution as video (no scaling)

### Depth Texture Problems

The plugin expects depth in 0-1 normalized range. If your depth source uses different range:

- **0-255 (8-bit)**: Divide by 255.0
- **0-10 meters**: Use `depth_norm = depth_meters / 10.0`
- **Inverted (1=near, 0=far)**: Invert: `depth_norm = 1.0 - depth_value`

## Testing

Run the test suite:

```bash
pytest tests/plugins/test_vtempi_duty_cycle_mode.py -v
```

Run with performance tests:

```bash
RUN_PERFORMANCE_TESTS=1 pytest tests/plugins/test_vtempi_duty_cycle_mode.py -m performance
```

## See Also

- **P3-EXT073**: VTemPi Human Resolution (related VTemPi plugin)
- **P3-VD35**: Depth Effect Plugin (base class)
- **VJlive-2 Documentation**: VTemPiEngine specification

## License

Part of VJLive3 project. See project LICENSE for details.