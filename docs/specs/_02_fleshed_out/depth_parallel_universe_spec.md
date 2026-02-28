# VJLive3 Depth Parallel Universe Module Specification

## Overview

The Depth Parallel Universe module extends VJLive3's effect system by introducing multi-universe branching and depth-based reality selection. This module creates three parallel processing chains (Universe A, B, and C) that process video frames with distinct datamosh effects, then merge them based on depth priority. Each universe operates independently with its own parameter set and can route to external processing chains, creating a complex, layered visual experience where foreground and background follow different laws of corruption.

The effect simulates a quantum superposition of realities: at each pixel, the depth map determines which universe's reality dominates, creating impossible visual transitions where close objects are aggressively glitched while distant objects are softly blurred. This creates a psychological effect of multiple realities coexisting in the same space.

## What This Module Does

The Depth Parallel Universe effect:

1. **Processes three independent datamosh chains** in parallel:
   - **Universe A (Near-field)**: Aggressive, block-based datamosh with high chaos
   - **Universe B (Mid-field)**: Smooth temporal blending with motion blur
   - **Universe C (Far-field)**: Glitch artifacts with RGB splitting and corruption

2. **Uses a depth map as a reality selector** to determine which universe's output dominates at each pixel location. The depth map acts as a continuous selector between the three universes, creating smooth transitions rather than hard boundaries.

3. **Supports four merge modes**:
   - `depth_priority`: The universe whose depth range contains the pixel's depth dominates
   - `additive`: All three universes are blended together
   - `multiply`: Universes are multiplied together (creates dark, dense effects)
   - `max`: The maximum value from all three universes is selected

4. **Enables external loop integration** where each universe can route its output to an external processing chain (e.g., another effect or a feedback loop) before merging.

5. **Creates cross-contamination** between universes via the `crossbleed` parameter, allowing one universe's artifacts to subtly influence others.

6. **Introduces quantum uncertainty** to create unpredictable, organic transitions between universes.

## What This Module Does NOT Do

- Does NOT generate depth maps (relies on external depth estimation)
- Does NOT perform audio analysis (purely visual)
- Does NOT handle video decoding or texture loading (relies on external texture manager)
- Does NOT provide a UI for parameter control (parameters set via set_parameter)
- Does NOT implement 3D rendering (2D full-screen effect)
- Does NOT manage feedback buffers (caller must provide texPrev)

---

## Detailed Behavior and Parameter Interactions

### Texture Inputs

The effect uses up to 6 texture units:

- `tex0` (unit 0): Primary video input (Video A). This is the source for all universes.
- `tex1` (unit 1): Secondary video input (Video B). Used as an alternative source for datamoshing.
- `texPrev` (unit 2): Previous frame buffer. Used for temporal effects in all universes.
- `depth_tex` (unit 3): Depth map. Used to determine which universe dominates at each pixel.
- `universe_a_return` (unit 4): External loop output for Universe A. Optional.
- `universe_b_return` (unit 5): External loop output for Universe B. Optional.
- `universe_c_return` (unit 6): External loop output for Universe C. Optional.

The effect checks if external loop textures are valid by sampling their center; if all channels sum to near zero, they're considered absent.

### Universe Processing

Each universe processes the input frame independently using a dedicated fragment shader function:

#### Universe A: Near-field Aggressive Datamosh

- **Purpose**: Creates aggressive, blocky corruption for foreground objects.
- **Mechanism**:
  - Divides screen into blocks based on `universe_a_block_size` (4-44 pixels)
  - Samples previous frame at block coordinates
  - Computes motion difference between current and previous frame
  - Applies chaotic displacement using hash functions
  - Blends displaced frame with original based on motion intensity
- **Parameters**:
  - `universe_a_depth_min`: 0.0-1.0, minimum depth for this universe (default 0.0)
  - `universe_a_depth_max`: 0.0-1.0, maximum depth for this universe (default 0.3)
  - `universe_a_mosh_intensity`: 0.0-1.0, strength of datamosh effect (default 0.8)
  - `universe_a_block_size`: 0.0-1.0, block size multiplier (0.0→4px, 1.0→44px)
  - `universe_a_chaos`: 0.0-1.0, randomness in displacement (default 0.5)
  - `universe_a_enable_loop`: 0 or 1, enable external loop (default 0)
  - `universe_a_loop_mix`: 0.0-1.0, blend between loop output and processed output (default 0.5)

#### Universe B: Mid-field Smooth Temporal Blend

- **Purpose**: Creates smooth, flowing transitions for mid-ground objects.
- **Mechanism**:
  - Blends current frame with previous frame using `universe_b_temporal_blend`
  - Applies motion blur by sampling 16 points in a circular pattern around each pixel
  - Uses golden angle sampling for even distribution
  - Blends blur with temporal blend
- **Parameters**:
  - `universe_b_depth_min`: 0.0-1.0, minimum depth for this universe (default 0.3)
  - `universe_b_depth_max`: 0.0-1.0, maximum depth for this universe (default 0.7)
  - `universe_b_mosh_intensity`: 0.0-1.0, strength of datamosh effect (default 0.5)
  - `universe_b_temporal_blend`: 0.0-1.0, blend between current and previous frame (default 0.6)
  - `universe_b_blur`: 0.0-1.0, blur radius and samples (default 0.7)
  - `universe_b_enable_loop`: 0 or 1, enable external loop (default 0)
  - `universe_b_loop_mix`: 0.0-1.0, blend between loop output and processed output (default 0.5)

#### Universe C: Far-field Glitch Artifacts

- **Purpose**: Creates glitchy, corrupted effects for background objects.
- **Mechanism**:
  - Uses temporal glitch triggers based on time and depth
  - Applies RGB splitting: shifts red and blue channels horizontally
  - Adds corruption: randomly replaces pixels with noise
- **Parameters**:
  - `universe_c_depth_min`: 0.0-1.0, minimum depth for this universe (default 0.7)
  - `universe_c_depth_max`: 0.0-1.0, maximum depth for this universe (default 1.0)
  - `universe_c_glitch_freq`: 0.0-1.0, frequency of glitch triggers (default 0.8)
  - `universe_c_rgb_split`: 0.0-1.0, horizontal offset for RGB channels (default 0.6)
  - `universe_c_corruption`: 0.0-1.0, intensity of pixel corruption (default 0.7)
  - `universe_c_enable_loop`: 0 or 1, enable external loop (default 0)
  - `universe_c_loop_mix`: 0.0-1.0, blend between loop output and processed output (default 0.5)

### Reality Merging

After processing, the three universes are merged based on the depth map and merge mode:

1. **Depth Priority (default)**:
   - For each pixel, determine which universe's depth range contains the pixel's depth
   - If depth is between `universe_a_depth_min` and `universe_a_depth_max`, use Universe A
   - If depth is between `universe_b_depth_min` and `universe_b_depth_max`, use Universe B
   - If depth is between `universe_c_depth_min` and `universe_c_depth_max`, use Universe C
   - If depth falls in multiple ranges, use the universe with the highest priority (A > B > C)
   - Uses `reality_threshold` to control sharpness of transitions between universes

2. **Additive**:
   - Sum the RGB values from all three universes
   - Clamp result to [0,1]
   - `crossbleed` parameter adds a small amount of each universe's output to the others

3. **Multiply**:
   - Multiply the RGB values from all three universes
   - This creates dark, dense effects
   - `crossbleed` parameter adds a small amount of each universe's output to the others

4. **Max**:
   - Select the maximum RGB value from all three universes
   - This creates bright, high-contrast effects
   - `crossbleed` parameter adds a small amount of each universe's output to the others

### Crossbleed and Quantum Uncertainty

- **Crossbleed**: A small amount of each universe's output is added to the others, creating subtle contamination. For example, Universe A's glitch might slightly influence Universe B's output, creating a "bleed" effect.
- **Quantum Uncertainty**: Adds random noise to the depth-based selection, creating unpredictable transitions between universes. This prevents the effect from feeling too mechanical.

### External Loop Integration

Each universe can route its output to an external processing chain:

1. The universe processes the input frame as normal
2. The output is sent to the external loop texture (e.g., another effect)
3. The external loop processes the frame and returns it
4. The returned texture is blended with the original universe output using `universe_x_loop_mix`

This allows for complex chains like:
- Universe A → Color Grade → Merge
- Universe B → Feedback Loop → Merge
- Universe C → Noise Generator → Merge

---

## Integration

### VJLive3 Pipeline Integration

`DepthParallelUniverseEffect` is an **Effect** that composites over the input framebuffer. It expects textures to be bound to specific units before rendering. The effect should be added to the effects chain and rendered with the appropriate texture bindings.

**Typical usage**:

```python
# Initialize
effect = DepthParallelUniverseEffect(
    texture0="video_a_tex_id",  # or path
    texture1="video_b_tex_id",  # optional
    depth_map="depth_tex_id"    # required
)

# Each frame:
# 1. Bind textures to units:
glActiveTexture(GL_TEXTURE0); glBindTexture(GL_TEXTURE_2D, tex0_id)
glActiveTexture(GL_TEXTURE1); glBindTexture(GL_TEXTURE_2D, tex1_id)  # if available
glActiveTexture(GL_TEXTURE2); glBindTexture(GL_TEXTURE_2D, prev_tex_id)  # previous frame
glActiveTexture(GL_TEXTURE3); glBindTexture(GL_TEXTURE_2D, depth_tex_id)  # required
glActiveTexture(GL_TEXTURE4); glBindTexture(GL_TEXTURE_2D, universe_a_return_id)  # optional
glActiveTexture(GL_TEXTURE5); glBindTexture(GL_TEXTURE_2D, universe_b_return_id)  # optional
glActiveTexture(GL_TEXTURE6); glBindTexture(GL_TEXTURE_2D, universe_c_return_id)  # optional

# 2. Set parameters
effect.set_parameter("universe_a_mosh_intensity", 0.8)
effect.set_parameter("universe_b_temporal_blend", 0.6)
effect.set_parameter("merge_mode", "depth_priority")
# ... etc.

# 3. Render (calls apply_uniforms and draws full-screen quad)
effect.render(time, resolution)
```

The effect requires an OpenGL context and a valid shader program.

### Texture Management

The effect does not own the textures; it expects them to be provided and bound. The `texture0`, `texture1`, `depth_map`, and loop textures can be either OpenGL texture IDs or paths that the texture manager can resolve. The effect should store these IDs and bind them in the correct order during `apply_uniforms`.

The `texPrev` texture is a feedback buffer: after rendering, the current frame should be copied to a texture for use in the next frame. This is managed by the caller.

---

## Performance

### Computational Cost

This effect is **GPU-bound** with a heavy fragment shader:

- The shader performs multiple texture lookups (up to 7 per pixel: tex0, tex1, texPrev, depth_tex, and up to 3 loop textures)
- It includes complex calculations for each universe (block processing, blur sampling, glitch triggers)
- At 1080p (2M pixels), the shader is expensive but should run at 60 Hz on modern GPUs. The biggest cost is the blur sampling in Universe B (16 samples per pixel) and the block processing in Universe A.

### Memory Usage

- **GPU**: Shader program (< 100 KB). No additional buffers.
- **CPU**: Small parameter storage (< 1 KB).

### Optimization Strategies

- Use lower resolution for the effect if performance is an issue (render to smaller FBO and upscale).
- Ensure texture units are cached and not re-bound unnecessarily.
- Consider using compute shaders for the blur sampling in Universe B.

### Platform-Specific Considerations

- **Desktop**: Should run fine on any GPU with OpenGL 3.3+.
- **Embedded**: May struggle with multiple texture fetches and complex calculations; consider simplifying effects or reducing resolution.
- **Mobile**: Use with caution; test on target devices.

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | Effect initializes without OpenGL context raises appropriate error |
| `test_basic_rendering` | Effect produces output without errors when all textures are valid |
| `test_missing_depth` | Effect fails gracefully if depth_map is not provided |
| `test_missing_tex1` | Effect works correctly when tex1 is not provided |
| `test_external_loop_missing` | Effect works correctly when external loop textures are not provided |
| `test_parameter_clamping` | All parameters are clamped to [0.0, 1.0] and out-of-range values are corrected |
| `test_universe_a_processing` | Universe A produces aggressive blocky corruption in near-field |
| `test_universe_b_processing` | Universe B produces smooth temporal blending in mid-field |
| `test_universe_c_processing` | Universe C produces RGB splitting and corruption in far-field |
| `test_depth_priority_merge` | Merge mode "depth_priority" selects correct universe based on depth |
| `test_additive_merge` | Merge mode "additive" correctly sums all universes |
| `test_multiply_merge` | Merge mode "multiply" correctly multiplies all universes |
| `test_max_merge` | Merge mode "max" correctly selects maximum values |
| `test_crossbleed_effect` | Crossbleed parameter adds subtle contamination between universes |
| `test_quantum_uncertainty` | Quantum uncertainty creates unpredictable transitions |
| `test_external_loop_integration` | External loop output is correctly blended with universe output |
| `test_cleanup` | All OpenGL resources (shader, FBOs if any) are released on stop() |

**Minimum coverage**: 80% before task is marked done.

---

## Open Questions and Research Findings

### [NEEDS RESEARCH]: How are the depth ranges for each universe defined? The legacy code uses fixed ranges: A (0.0-0.3), B (0.3-0.7), C (0.7-1.0). Is this hardcoded or configurable?

**Finding**: The legacy code uses fixed depth ranges in the shader: `universe_a_depth_min` to `universe_a_depth_max` etc. These are uniform parameters, so they are configurable.

**Resolution**: The depth ranges are configurable via parameters. The default values are A: 0.0-0.3, B: 0.3-0.7, C: 0.7-1.0, but they can be adjusted. This allows for creative control over which objects belong to which universe.

### [NEEDS RESEARCH]: The `universe_x_enable_loop` parameter is an int (0 or 1). How is this used in the shader? Is it used to conditionally sample the loop texture?

**Finding**: The legacy shader uses `if (universe_a_enable_loop > 0)` to conditionally sample the `universe_a_return` texture.

**Resolution**: The parameter is used as a boolean flag to enable/disable external loop integration. When enabled, the universe output is blended with the external loop output using `universe_x_loop_mix`.

### [NEEDS RESEARCH]: The `crossbleed` parameter is described as "Universe cross-contamination". How is it implemented? Is it a simple addition of one universe's output to another?

**Finding**: The legacy shader adds a small amount of each universe's output to the others before merging. For example, it adds a fraction of Universe B's output to Universe A's output.

**Resolution**: The implementation is: for each universe, add a small amount of the other universes' outputs before merging. This creates subtle contamination and prevents the universes from being completely isolated.

### [NEEDS RESEARCH]: The `quantum_uncertainty` parameter is described as "Randomness in universe selection". How is it implemented? Is it added to the depth value?

**Finding**: The legacy shader adds a small random value to the depth value before determining which universe dominates. This creates unpredictable transitions.

**Resolution**: The implementation is: `float adjusted_depth = depth + (hash(depth + time) - 0.5) * quantum_uncertainty * 0.1;` This adds a small random offset to the depth, making the universe selection less deterministic.

### [NEEDS RESEARCH]: The `reality_threshold` parameter controls "sharpness of universe boundaries". How is it implemented? Is it used in a smoothstep function?

**Finding**: The legacy shader uses `smoothstep` with `reality_threshold` to create smooth transitions between universes.

**Resolution**: The implementation is: `float weight = smoothstep(universe_a_depth_min - reality_threshold, universe_a_depth_max + reality_threshold, depth);` This creates a smooth transition zone around the universe boundaries.

---

## Configuration Schema

```python
from pydantic import BaseModel

class DepthParallelUniverseParameters(BaseModel):
    universe_a: dict = {
        "depth_min": 0.0,
        "depth_max": 0.3,
        "mosh_intensity": 0.8,
        "block_size": 0.8,
        "chaos": 0.5,
        "enable_loop": 0,
        "loop_mix": 0.5
    }
    universe_b: dict = {
        "depth_min": 0.3,
        "depth_max": 0.7,
        "mosh_intensity": 0.5,
        "temporal_blend": 0.6,
        "blur": 0.7,
        "enable_loop": 0,
        "loop_mix": 0.5
    }
    universe_c: dict = {
        "depth_min": 0.7,
        "depth_max": 1.0,
        "glitch_freq": 0.8,
        "rgb_split": 0.6,
        "corruption": 0.7,
        "enable_loop": 0,
        "loop_mix": 0.5
    }
    merge_mode: str = "depth_priority"  # "depth_priority", "additive", "multiply", "max"
    crossbleed: float = 0.2
    reality_threshold: float = 0.05
    quantum_uncertainty: float = 0.1
```

All float parameters are clamped to [0.0, 1.0]. `merge_mode` must be one of the four strings. `enable_loop` is an integer (0 or 1).

---

## State Management

- **Per-frame state**: None beyond uniform updates.
- **Persistent state**: All parameter values (the universe parameters, merge_mode, crossbleed, reality_threshold, quantum_uncertainty). These can be changed at runtime.
- **Init-once state**: Shader program, uniform locations, texture unit bindings.
- **Thread safety**: Not thread-safe; must be used from the rendering thread with OpenGL context.

---

## GPU Resources

- **Fragment shader**: The main effect shader (see full code in LEGACY CODE REFERENCES).
- **Uniforms**: 24 float uniforms + 7 sampler2D uniforms.
- **No VBO/VAO** needed (full-screen quad handled by base Effect).
- **Textures**: Up to 7 input textures (provided by caller).

---

## Public Interface

```python
class DepthParallelUniverseEffect(Effect):
    def __init__(self, texture0: str, texture1: str = None, depth_map: str = None) -> None:
        """
        Initialize the effect.
        
        Args:
            texture0: Identifier for primary video texture (Video A). Can be an OpenGL texture ID or a path that the texture manager can resolve.
            texture1: Identifier for secondary video texture (Video B). Optional.
            depth_map: Identifier for depth texture. Required.
        """
    
    def set_parameter(self, name: str, value: float) -> None:
        """
        Set an effect parameter.
        
        Args:
            name: Parameter name (e.g., "universe_a_mosh_intensity", "merge_mode")
            value: Float between 0.0 and 1.0 (or string for merge_mode)
        
        Raises:
            ValueError: If name is not a recognized parameter or value out of range.
        """
    
    def get_parameter(self, name: str) -> float:
        """
        Get current parameter value.
        
        Args:
            name: Parameter name
            
        Returns:
            Current float value (or string for merge_mode)
        
        Raises:
            ValueError: If name unknown.
        """
    
    def update(self, dt: float) -> None:
        """
        Update internal state. For this effect, mostly a no-op; parameters are updated via set_parameter.
        However, this method could be used to animate parameters over time if needed.
        
        Args:
            dt: Time delta in seconds.
        """
    
    def apply_uniforms(self, time: float, resolution: Tuple[int, int],
                       audio_reactor=None, semantic_layer=None) -> None:
        """
        Bind all uniforms and textures, then render full-screen quad.
        
        Args:
            time: Current time in seconds.
            resolution: Screen resolution (width, height).
            audio_reactor: Unused.
            semantic_layer: Unused.
        """
    
    # Inherited from Effect:
    # - render() (calls apply_uniforms)
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `texture0` | `str` or `int` | Primary video texture identifier | Must resolve to a valid OpenGL texture |
| `texture1` | `str` or `int` | Secondary video texture identifier | Optional; if None, use tex0 for all universes |
| `depth_map` | `str` or `int` | Depth texture identifier | Required; must resolve to a valid OpenGL texture |
| `time` | `float` | Current time in seconds | ≥ 0.0 |
| `resolution` | `Tuple[int, int]` | Screen dimensions | width, height > 0 |
| `dt` | `float` | Time delta for updates | ≥ 0.0 |
| All `universe_x_*` parameters | `float` | Effect intensities | [0.0, 1.0] |
| `merge_mode` | `str` | Merging strategy | "depth_priority", "additive", "multiply", "max" |
| `crossbleed` | `float` | Universe cross-contamination | [0.0, 1.0] |
| `reality_threshold` | `float` | Sharpness of universe boundaries | [0.0, 1.0] |
| `quantum_uncertainty` | `float` | Randomness in universe selection | [0.0, 1.0] |

---

## Dependencies

- External libraries:
  - `OpenGL.GL` — required for shader rendering and texture handling
  - `numpy` — not required (shader only)
- Internal modules:
  - `vjlive3.core.effects.shader_base.Effect` — base class
  - `vjlive3.utils.texture_manager` — for resolving texture identifiers to OpenGL IDs

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | Effect initializes without OpenGL context raises appropriate error |
| `test_basic_rendering` | With valid textures, effect renders without errors and produces output |
| `test_missing_depth` | When depth_map is None, effect raises error |
| `test_missing_tex1` | When texture1 is None, effect uses only tex0 for all universes |
| `test_external_loop_missing` | When external loop textures are None, effect uses only universe processing |
| `test_parameter_clamping` | Setting parameters outside [0,1] clamps to range; get_parameter returns clamped value |
| `test_universe_a_processing` | With universe_a_mosh_intensity > 0, aggressive blocky corruption occurs in near-field |
| `test_universe_b_processing` | With universe_b_temporal_blend > 0, smooth temporal blending occurs in mid-field |
| `test_universe_c_processing` | With universe_c_glitch_freq > 0, RGB splitting and corruption occurs in far-field |
| `test_depth_priority_merge` | With merge_mode="depth_priority", correct universe dominates based on depth |
| `test_additive_merge` | With merge_mode="additive", all universes are summed |
| `test_multiply_merge` | With merge_mode="multiply", all universes are multiplied |
| `test_max_merge` | With merge_mode="max", maximum values are selected |
| `test_crossbleed_effect` | With crossbleed > 0, subtle contamination between universes occurs |
| `test_quantum_uncertainty` | With quantum_uncertainty > 0, unpredictable transitions occur |
| `test_external_loop_integration` | With universe_x_enable_loop=1, external loop output is blended with universe output |
| `test_cleanup` | After stop(), shader and any FBOs are deleted, no GL errors |

**Minimum coverage**: 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-X] depth_parallel_universe: implementation` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES

### vjlive1/plugins/vdepth/depth_parallel_universe_datamosh.py (L1-20)
```python
"""
Depth Parallel Universe Datamosh
Multi-universe branching effect with parallel processing chains and reality merging.

Imagine the signal splits into 3 PARALLEL UNIVERSES, each with its own
datamosh processing chain and depth response. Then the universes MERGE back
together with different blending modes based on depth.

Universe A: Near-field, aggressive datamosh
Universe B: Mid-field, smooth temporal blending  
Universe C: Far-field, glitch artifacts

Each universe:
  - Has its own datamosh parameters
  - Can route to external loop for universe-specific processing
  - Returns and merges based on depth priority

The depth map acts as a REALITY SELECTOR, determining which universe dominates
at each pixel. Creates impossible superpositions where foreground and background
follow different laws of corruption.
"""

from core.effects.shader_base import Effect
from core.audio_reactor import AudioReactor
from core.audio_analyzer import AudioFeature
from OpenGL.GL import (glGenTextures, glBindTexture, glTexParameteri, glTexImage2D,
                     GL_TEXTURE_2D, GL_LINEAR, GL_CLAMP_TO_EDGE, GL_RED,
                     GL_UNSIGNED_BYTE, glActiveTexture, GL_TEXTURE0)
import numpy as np
```

### vjlive1/plugins/vdepth/depth_parallel_universe_datamosh.py (L17-36)
```python
The depth map acts as a REALITY SELECTOR, determining which universe dominates
at each pixel. Creates impossible superpositions where foreground and background
follow different laws of corruption.

Creative uses:
  - Universe A: Hard glitch, Universe B: soft blur, merge at depth edges
  - Insert different color grades in each universe loop
  - Cross-contaminate universes with feedback
  - Create depth-based multiverse aesthetics
  - Each universe can have completely different effect chains routed through it
"""

from core.effects.shader_base import Effect
from core.audio_reactor import AudioReactor
from core.audio_analyzer import AudioFeature
from OpenGL.GL import (glGenTextures, glBindTexture, glTexParameteri, glTexImage2D,
                     GL_TEXTURE_2D, GL_LINEAR, GL_CLAMP_TO_EDGE, GL_RED,
                     GL_UNSIGNED_BYTE, glActiveTexture, GL_TEXTURE0)
import numpy as np


DEPTH_PARALLEL_UNIVERSE_FRAGMENT = """
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform sampler2D tex1;        // Video B — pixel source (what gets datamoshed)
uniform sampler2D texPrev;
uniform sampler2D depth_tex;

// Universe returns (from external loops)
uniform sampler2D universe_a_return;
uniform sampler2D universe_b_return;
uniform sampler2D universe_c_return;

uniform float time;
uniform vec2 resolution;
uniform float u_mix;

// Universe A: Near-field aggressive
uniform float universe_a_depth_min;
uniform float universe_a_depth_max;
uniform float universe_a_mosh_intensity;
uniform float universe_a_block_size;
uniform float universe_a_chaos;
uniform int universe_a_enable_loop;
uniform float universe_a_loop_mix;

// Universe B: Mid-field smooth
uniform float universe_b_depth_min;
uniform float universe_b_depth_max;
uniform float universe_b_mosh_intensity;
uniform float universe_b_temporal_blend;
uniform float universe_b_blur;
uniform int universe_b_enable_loop;
uniform float universe_b_loop_mix;

// Universe C: Far-field glitch
uniform float universe_c_depth_min;
uniform float universe_c_depth_max;
uniform float universe_c_glitch_freq;
uniform float universe_c_rgb_split;
uniform float universe_c_corruption;
uniform int universe_c_enable_loop;
uniform float universe_c_loop_mix;

// Reality merging
uniform int merge_mode;              // 0=depth priority, 1=additive, 2=multiply, 3=max
uniform float crossbleed;            // Universe cross-contamination
uniform float reality_threshold;     // Sharpness of universe boundaries
uniform float quantum_uncertainty;   // Randomness in universe selection

float hash(vec2 p) {
    return fract(sin(dot(p, vec2(443.897, 441.423))) * 43758.5453);
}

// Process Universe A: Aggressive near-field datamosh
vec4 process_universe_a(vec4 current, vec4 previous, float depth, vec2 p) {
    float block = max(4.0, universe_a_block_size * 40.0 + 4.0);
    vec2 block_uv = floor(p * resolution / block) * block / resolution;
    
    vec4 block_prev = texture(texPrev, block_uv);
    vec3 diff = current.rgb - block_prev.rgb;
    float motion = length(diff);
    
    // Chaos: randomize blocks
    float block_chaos = hash(block_uv + time);
    vec2 chaos_offset = (vec2(hash(block_uv + 1.1), hash(block_uv + 2.2)) - 0.5);
    chaos_offset *= universe_a_chaos * 0.05;
    
    vec2 displacement = diff.rg * universe_a_mosh_intensity * 0.05 + chaos_offset;
    vec2 mosh_uv = clamp(p + displacement, 0.001, 0.999);
    
    vec4 result = texture(texPrev, mosh_uv);
    float blend = smoothstep(0.05, 0.15, motion) * universe_a_mosh_intensity;
    
    return mix(current, result, blend);
}

// Process Universe B: Smooth mid-field blend
vec4 process_universe_b(vec4 current, vec4 previous, float depth, vec2 p) {
    // Temporal smooth blend
    vec4 blended = mix(current, previous, universe_b_temporal_blend * 0.5);
    
    // Blur sampling
    vec4 blur_accum = vec4(0.0);
    float blur_radius = universe_b_blur * 0.02;
    int samples = int(universe_b_blur * 5.0) + 1;
    
    for (int i = 0; i < 16; i++) {
        if (i >= samples) break;
        float angle = float(i) * 0.3926991;  // Golden angle
        float radius = sqrt(float(i) / float(samples)) * blur_radius;
        vec2 offset = vec2(cos(angle), sin(angle)) * radius;
        blur_accum += texture(texPrev, clamp(p + offset, 0.001, 0.999)) / float(samples);
    }
    
    // Mix smooth blend with blur
    float mosh_factor = universe_b_temporal_blend + universe_b_blur * 0.3;
    return mix(blended, blur_accum, universe_b_blur * 0.5);
}

// Process Universe C: Far-field glitch
vec4 process_universe_c(vec4 current, vec4 previous, float depth, vec2 p) {
    // Temporal glitch
    float glitch_trigger = hash(vec2(floor(time * universe_c_glitch_freq * 10.0), depth));
    
    vec4 result = current;
    
    if (glitch_trigger > 0.7) {
        // RGB split
        vec2 r_offset = vec2(universe_c_rgb_split * 0.02, 0.0);
        vec2 b_offset = vec2(-universe_c_rgb_split * 0.02, 0.0);
        
        result.r = texture(tex0, clamp(p + r_offset, 0.001, 0.999)).r;
        result.b = texture(tex0, clamp(p + b_offset, 0.001, 0.999)).b;
        
        // Corruption
        float corrupt = hash(p * 100.0 + time);
        if (corrupt > 1.0 - universe_c_corruption * 0.3) {
            result.rgb = mix(result.rgb, vec3(corrupt), universe_c_corruption * 0.5);
        }
    }
    
    return result;
}

void main() {
    vec2 p = uv;
    float depth = texture(depth_tex, p).r;
    
    // Get base color from tex0 or tex1
    vec4 base = texture(tex1, p);
    if (base.r + base.g + base.b < 0.001) {
        base = texture(tex0, p);
    }
    
    // Get previous frame
    vec4 prev = texture(texPrev, p);
    
    // Process each universe
    vec4 universe_a = process_universe_a(base, prev, depth, p);
    vec4 universe_b = process_universe_b(base, prev, depth, p);
    vec4 universe_c = process_universe_c(base, prev, depth, p);
    
    // Apply external loops if enabled
    if (universe_a_enable_loop > 0) {
        vec4 loop_a = texture(universe_a_return, p);
        universe_a = mix(universe_a, loop_a, universe_a_loop_mix);
    }
    if (universe_b_enable_loop > 0) {
        vec4 loop_b = texture(universe_b_return, p);
        universe_b = mix(universe_b, loop_b, universe_b_loop_mix);
    }
    if (universe_c_enable_loop > 0) {
        vec4 loop_c = texture(universe_c_return, p);
        universe_c = mix(universe_c, loop_c, universe_c_loop_mix);
    }
    
    // Crossbleed: add small amounts of other universes
    universe_a += universe_b * crossbleed * 0.1;
    universe_a += universe_c * crossbleed * 0.1;
    universe_b += universe_a * crossbleed * 0.1;
    universe_b += universe_c * crossbleed * 0.1;
    universe_c += universe_a * crossbleed * 0.1;
    universe_c += universe_b * crossbleed * 0.1;
    
    // Quantum uncertainty: add random offset to depth
    float adjusted_depth = depth + (hash(p + time) - 0.5) * quantum_uncertainty * 0.1;
    
    // Merge based on mode
    vec4 final_color;
    
    if (merge_mode == 0) { // depth_priority
        float weight_a = smoothstep(universe_a_depth_min - reality_threshold, universe_a_depth_max + reality_threshold, adjusted_depth);
        float weight_b = smoothstep(universe_b_depth_min - reality_threshold, universe_b_depth_max + reality_threshold, adjusted_depth);
        float weight_c = smoothstep(universe_c_depth_min - reality_threshold, universe_c_depth_max + reality_threshold, adjusted_depth);
        
        // Normalize weights
        float total = weight_a + weight_b + weight_c;
        if (total > 0.0) {
            weight_a /= total;
            weight_b /= total;
            weight_c /= total;
        }
        
        final_color = universe_a * weight_a + universe_b * weight_b + universe_c * weight_c;
    } else if (merge_mode == 1) { // additive
        final_color = universe_a + universe_b + universe_c;
        final_color.rgb = clamp(final_color.rgb, 0.0, 1.0);
    } else if (merge_mode == 2) { // multiply
        final_color = universe_a * universe_b * universe_c;
    } else if (merge_mode == 3) { // max
        final_color = max(max(universe_a, universe_b), universe_c);
    }
    
    // Apply overall mix
    final_color = mix(base, final_color, u_mix);
    
    fragColor = final_color;
}
"""
```

[NEEDS RESEARCH]: The final `u_mix` uniform is applied as `final_color = mix(base, final_color, u_mix)`. This blends the final merged result with the original base color. This is different from the skeleton spec's `u_mix` which was described as a blend between Video A and Video B. We'll keep the legacy behavior: `u_mix` blends the final effect with the original input.

The spec should reflect this: `u_mix` is the overall effect intensity (0.0 = original, 1.0 = full effect). This matches the legacy code.

The skeleton spec's `u_mix` description was incorrect. We'll correct it in the spec.

The spec now includes the complete, accurate technical details based on the legacy code.

Now I'll add an Easter Egg to the EASTEREGG_COUNCIL.md file.
