# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT209_agent_avatar.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT209 — AgentAvatarEffect

**What This Module Does**

The `AgentAvatarEffect` visualizes an agent's emotional and cognitive state as a reactive geometric entity that moves across multi-node displays. It renders a dynamic avatar (spinning geometric core with glow) that responds to agent state parameters like thinking, confidence, or overwhelm. The avatar's position is managed by a `SyncManager` to coordinate across multiple display nodes, appearing only when within a node's viewport. The effect is implemented as a full-screen fragment shader that composites the avatar over the scene.

The avatar appears as a glowing, rotating geometric shape (hexagon-based) with configurable scale, color, and effects. It can fragment into particles when the agent is overwhelmed, and its spin speed increases when thinking. The effect supports optional audio reactivity and semantic layer integration for contextual awareness.

**What This Module Does NOT Do**

- Does NOT handle agent state computation (state is provided externally via parameters)
- Does NOT manage multi-node synchronization (relies on SyncManager)
- Does NOT perform vision processing itself (optional VisionSource integration is for future use)
- Does NOT render 3D geometry (uses 2D fragment shader)
- Does NOT provide a full UI for parameter editing (parameters set via set_parameter)
- Does NOT implement advanced particle systems (fragmentation is a simple shader effect)

---

## Detailed Behavior and Parameter Interactions

### Avatar State Parameters

The effect uses the following parameters (set via `set_parameter(name, value)`):

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `avatar_x` | float | 0.5 | Horizontal position in screen space (0.0 = left, 1.0 = right) |
| `avatar_y` | float | 0.5 | Vertical position in screen space (0.0 = bottom, 1.0 = top) |
| `avatar_scale` | float | 0.15 | Size of the avatar (relative to screen height) |
| `avatar_alpha` | float | 1.0 | Opacity of the avatar (0.0 = invisible) |
| `spin_speed` | float | 2.0 | Rotation speed of the geometric core (radians per second) |
| `glow_intensity` | float | 1.0 | Intensity of the outer glow (brightness multiplier) |
| `confidence` | float | 0.8 | Confidence level (0.0-1.0); affects color and stability |
| `fragmentation` | float | 0.0 | Fragmentation level (0.0 = solid, >0 = breaking apart) |
| `glow_color` | vec3 | (1.0, 1.0, 1.0) | RGB color of the glow (white by default) |

These parameters are typically updated each frame based on agent state and sync manager data.

### Position and Visibility Management

The `update_from_global_state()` method queries the `SyncManager` for the avatar's position on the current node:

```python
local_pos = sync_manager.get_avatar_position_for_node(self.node_id)
if local_pos >= 0.0:
    self.set_parameter("avatar_x", local_pos)
    self.set_parameter("avatar_y", 0.5)  # fixed vertical center
    self.set_parameter("avatar_alpha", 1.0)
else:
    self.set_parameter("avatar_alpha", 0.0)
```

The `SyncManager` returns a normalized x-coordinate (0.0-1.0) if the avatar is within the node's viewport, or -1.0 if not visible. This ensures the avatar appears to travel across the multi-node display.

### Shader Rendering

The fragment shader renders the avatar as follows:

1. **Coordinate transformation**: Convert pixel UV to avatar-centered space: `p = (uv - avatar_position) / avatar_scale`.
2. **Rotation**: Apply time-based rotation: `p = rotate(p, time * spin_speed)`.
3. **Geometric core**: Draw a central hexagon using signed distance functions (SDF). The hexagon is created by repeating the angle 6 times and computing distance to a triangle.
4. **Glow**: Add a radial glow around the core based on `glow_intensity` and `glow_color`.
5. **Fragmentation**: If `fragmentation > 0`, add noise-based displacement to the core edges, making it look broken.
6. **Confidence**: Modulate color brightness or saturation based on `confidence` (higher confidence = brighter, more stable).
7. **Alpha blending**: Multiply final color by `avatar_alpha` and composite over the background using `u_mix`.

The shader also supports optional features:
- **Shadow Mode**: If `shadow_mode_enabled` and `has_shadow_mask`, apply a shadow effect.
- **Eye Tracking**: If `eye_tracking_enabled`, use `gaze_direction` to shift the avatar's focus.

### Audio and Semantic Integration

The `apply_uniforms` method accepts optional `audio_reactor` and `semantic_layer`. These can influence avatar parameters:

- **AudioReactor**: Could provide emotional state from audio (e.g., excitement → higher spin_speed, lower confidence → more fragmentation). The effect does not directly use audio uniforms in the current shader; instead, the caller may adjust parameters based on audio analysis.
- **SemanticLayer**: Could provide intent or topic data to change glow color or shape. Not used in current shader.

The base `Effect` class handles uniform setting; `AgentAvatarEffect` adds its own uniforms.

---

## Integration

### VJLive3 Pipeline Integration

`AgentAvatarEffect` is a **compositing effect** that draws over the current framebuffer. It should be added to the effects chain and rendered after the main scene to overlay the avatar.

**Typical usage**:

```python
# Initialize with sync manager and node ID
avatar = AgentAvatarEffect(sync_manager=sync, node_id=3)

# Each frame:
avatar.update_from_global_state()  # updates position/alpha from sync manager
avatar.apply_uniforms(
    time=current_time,
    resolution=(1920, 1080),
    audio_reactor=audio,  # optional
    semantic_layer=semantic  # optional
)
# The effect's render() method is called automatically in the chain
```

The effect requires an OpenGL context and a shader program.

### Multi-Node Synchronization

The `SyncManager` (not defined here) provides a global state where the avatar's position is tracked across nodes. Each node queries `get_avatar_position_for_node(node_id)` to get the local x coordinate (0-1) if the avatar is currently on that node's screen, or -1 if not. This creates the illusion of a single avatar traveling across multiple displays.

---

## Performance

### Computational Cost

This effect is **GPU-bound** but very lightweight:

- **CPU**: Minimal work: updating a few parameters, querying sync manager, setting uniforms. Negligible.
- **GPU**: Fragment shader runs per pixel (full-screen). The shader does SDF calculations for a hexagon, rotation, glow, and some conditionals. At 1080p (2M pixels), this is trivial for modern GPums (< 1 ms).

### Memory Usage

- **CPU**: Small parameter storage (< 1 KB)
- **GPU**: Shader program (< 50 KB), uniform data (< 1 KB)
- **No textures** required (unless using shadow mask, which would be a small texture)

### Optimization Strategies

None needed; the effect is already efficient.

### Platform-Specific Considerations

- **Desktop**: No issues; OpenGL 3.3+ required.
- **Embedded**: Full-screen fragment shader at high resolution may be heavy; consider reducing resolution or optimizing shader.
- **Vision source imports**: The legacy code conditionally imports `VisionSource` and `SurfaceIRSource` (Windows only). These are optional and not used in the core effect. They can be stubbed or omitted in VJLive3.

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_sync_manager` | Effect initializes without crashing if sync_manager is None |
| `test_update_from_global_state_with_position` | When sync_manager returns local_pos >= 0, avatar_x, avatar_y, alpha are set correctly |
| `test_update_from_global_state_out_of_viewport` | When sync_manager returns -1, avatar_alpha set to 0.0 |
| `test_apply_uniforms_with_valid_params` | All avatar uniforms are set with current parameter values |
| `test_apply_uniforms_no_audio_semantic` | Effect works when audio_reactor and semantic_layer are None |
| `test_parameter_set_get` | set_parameter and get_parameter work for all avatar parameters |
| `test_invalid_parameter_name` | get_parameter with unknown name raises ValueError |
| `test_shader_compilation` | Fragment shader compiles successfully with all uniforms |
| `test_cleanup` | No OpenGL resource leaks on destruction |

**Minimum coverage**: 80% before task is marked done.

---

## Open Questions and Research Findings

### [NEEDS RESEARCH]: How are emotional states (thinking/confident/overwhelmed) mapped to avatar parameters?

**Finding**: The legacy code does not show automatic mapping from agent state to parameters. The `update_from_global_state` only handles position. The caller likely sets `spin_speed`, `confidence`, `fragmentation` based on agent state. For example:
- Thinking → high `spin_speed`
- Confident → high `confidence`, low `fragmentation`
- Overwhelmed → high `fragmentation`, low `confidence`

**Resolution**: The VJLive3 implementation should provide a method or external mapping to set these state-driven parameters. The spec can include a helper method `set_emotional_state(state: str)` that maps to parameters, but the skeleton spec doesn't have that. We'll note that the effect exposes parameters but does not compute them; the agent system should call `set_parameter` accordingly.

### [NEEDS RESEARCH]: What is the exact shader logic for fragmentation and confidence?

**Finding**: The legacy shader snippet shows `agent_core` function with `fragmentation` parameter but not its use. Likely, fragmentation adds noise to the SDF or displaces vertices. Confidence might affect color or glow intensity.

**Resolution**: In the enriched spec, we can describe expected behavior:
- Fragmentation: When > 0, add a noise-based offset to the position before computing SDF, creating a jagged, broken look.
- Confidence: Multiply `glow_intensity` by confidence, or mix glow color towards red when low.

We'll define these as shader implementations but keep them optional.

### [NEEDS RESEARCH]: How does shadow mode and eye tracking work?

**Finding**: The shader has uniforms for `shadow_mode_enabled`, `has_shadow_mask`, `eye_tracking_enabled`, `gaze_direction`. But the implementation details are not in the snippets. Likely, shadow mode darkens the avatar based on a mask texture; eye tracking shifts the avatar's "face" to look at the gaze direction.

**Resolution**: Since these are advanced features and not core, we can mention them as optional. The base implementation can ignore them or provide simple defaults. The spec should include these uniforms for compatibility but not require full implementation.

### [NEEDS RESEARCH]: What is the `AVATAR_FRAGMENT_SHADER` full code?

**Finding**: Only partial shader code is available. We need the complete shader to understand rendering. The missing parts likely include:
- The rest of `agent_core` function (how hexagon is constructed, how fragmentation is applied)
- The `main()` function that calls `agent_core`, computes glow, and outputs color.

**Resolution**: We'll reconstruct a plausible full shader based on typical SDF techniques. The spec should include a complete shader reference implementation as an appendix or comment. But since we're enriching the spec, we can describe the intended behavior and leave shader details to the implementer, with a note to match legacy output.

---

## Configuration Schema

```python
METADATA = {
  "params": [
    {"id": "avatar_x", "name": "Avatar X", "default": 0.5, "min": 0.0, "max": 1.0, "type": "float"},
    {"id": "avatar_y", "name": "Avatar Y", "default": 0.5, "min": 0.0, "max": 1.0, "type": "float"},
    {"id": "avatar_scale", "name": "Avatar Scale", "default": 0.15, "min": 0.01, "max": 1.0, "type": "float"},
    {"id": "avatar_alpha", "name": "Avatar Alpha", "default": 1.0, "min": 0.0, "max": 1.0, "type": "float"},
    {"id": "spin_speed", "name": "Spin Speed", "default": 2.0, "min": 0.0, "max": 10.0, "type": "float"},
    {"id": "glow_intensity", "name": "Glow Intensity", "default": 1.0, "min": 0.0, "max": 5.0, "type": "float"},
    {"id": "confidence", "name": "Confidence", "default": 0.8, "min": 0.0, "max": 1.0, "type": "float"},
    {"id": "fragmentation", "name": "Fragmentation", "default": 0.0, "min": 0.0, "max": 1.0, "type": "float"},
    {"id": "glow_color", "name": "Glow Color", "default": [1.0, 1.0, 1.0], "type": "vec3"}
  ]
}
```

---

## State Management

- **Per-frame state**: `avatar_x`, `avatar_y`, `avatar_alpha` are updated each frame from sync manager.
- **Persistent state**: All other parameters (`spin_speed`, `glow_intensity`, `confidence`, `fragmentation`, `glow_color`, `avatar_scale`) persist and can be changed at runtime.
- **Init-once state**: Shader program, uniform locations.
- **Thread safety**: Not thread-safe; must be used from the rendering thread with OpenGL context.

---

## GPU Resources

- **Fragment shader**: The main shader that renders the avatar.
- **Uniforms**: Several floats and vec3.
- **No textures** required (unless using shadow mask, which is optional).
- **No VBO/VAO** needed (full-screen quad is handled by base Effect class).

---

## Public Interface

```python
class AgentAvatarEffect(Effect):
    def __init__(self, sync_manager: Optional[SyncManager] = None, node_id: int = 0) -> None:
        """
        Initialize the agent avatar effect.
        
        Args:
            sync_manager: Optional SyncManager for multi-node positioning.
            node_id: Identifier of the current display node (0-based).
        """
    
    def update_from_global_state(self) -> None:
        """
        Update avatar position and visibility based on the sync manager's state.
        This should be called each frame before rendering.
        """
    
    def apply_uniforms(self, time: float, resolution: Tuple[int, int],
                       audio_reactor: Optional[AudioReactor] = None,
                       semantic_layer: Optional[SemanticLayer] = None) -> None:
        """
        Apply shader uniforms for rendering.
        
        Args:
            time: Current time in seconds.
            resolution: Screen resolution (width, height).
            audio_reactor: Optional audio context for emotional inference.
            semantic_layer: Optional semantic data for contextual cues.
        """
    
    def set_parameter(self, name: str, value: Any) -> None:
        """Set an avatar parameter (inherited from Effect)."""
    
    def get_parameter(self, name: str) -> Any:
        """Get an avatar parameter (inherited from Effect)."""
    
    # Inherited from Effect:
    # - render() (calls apply_uniforms internally)
    # - set_uniform(name, value)
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `sync_manager` | `Optional[SyncManager]` | Global state manager for avatar positioning | If None, avatar position must be set manually |
| `node_id` | `int` | Current node identifier | 0 ≤ node_id < max_nodes |
| `time` | `float` | Playback time in seconds | ≥ 0.0 |
| `resolution` | `Tuple[int, int]` | Screen dimensions | width > 0, height > 0 |
| `audio_reactor` | `Optional[AudioReactor]` | Audio context for emotional inference | May be None |
| `semantic_layer` | `Optional[SemanticLayer]` | Semantic data for contextual cues | May be None |
| `avatar_x`, `avatar_y` | `float` | Normalized screen position | [0.0, 1.0] |
| `avatar_scale` | `float` | Avatar size | > 0.0 |
| `avatar_alpha` | `float` | Opacity | [0.0, 1.0] |
| `spin_speed` | `float` | Rotation speed | ≥ 0.0 |
| `glow_intensity` | `float` | Glow brightness | ≥ 0.0 |
| `confidence` | `float` | Confidence level | [0.0, 1.0] |
| `fragmentation` | `float` | Fragmentation amount | [0.0, 1.0] |
| `glow_color` | `Tuple[float, float, float]` | RGB color | components in [0,1] |

---

## Dependencies

- External libraries:
  - `numpy` — for parameter arrays and math
  - `cv2` — optional, for vision source integration (can be skipped)
- Internal modules:
  - `vjlive3.core.effects.shader_base.Effect` — base class
  - `vjlive3.core.sync.SyncManager` — optional, for multi-node positioning
  - `vjlive3.core.audio.AudioReactor` — optional
  - `vjlive3.core.semantic.SemanticLayer` — optional

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_sync_manager` | Effect initializes without sync_manager |
| `test_update_from_global_state_with_position` | Avatar position/alpha set correctly when sync returns >= 0 |
| `test_update_from_global_state_out_of_viewport` | Avatar alpha = 0 when sync returns -1 |
| `test_apply_uniforms_with_valid_params` | All uniforms are set with correct values |
| `test_apply_uniforms_no_audio_semantic` | Works with None for optional args |
| `test_parameter_set_get` | Parameters can be set and retrieved |
| `test_invalid_parameter_name` | get_parameter raises ValueError for unknown name |
| `test_shader_compilation` | Shader compiles without errors |
| `test_cleanup` | No OpenGL resource leaks |

**Minimum coverage**: 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-X] P3-EXT209: agent_avatar effect implementation` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES

### vjlive1/core/effects/agent_avatar.py (L1-20)
```python
"""
Agent Avatar Effect - Geometric entity that visualizes agent state.

Renders a reactive geometric core that responds to agent emotional states:
- Thinking: Rapid spinning
- Confident: Stable bright white glow
- Overwhelmed: Fragments into particles
"""

from typing import Optional, Tuple
import time
import numpy as np
import cv2
from core.effects.shader_base import Effect

# Vision source imports - SurfaceIRSource is optional (Windows only)
try:
    from ..vision_source import VisionSource
except ImportError:
    VisionSource = None
```

### vjlive1/core/effects/agent_avatar.py (L17-36)
```python
try:
    from ..vision_source import VisionSource
except ImportError:
    VisionSource = None

try:
    from drivers.x86_windows.surface_ir_source import SurfaceIRSource
except ImportError:
    SurfaceIRSource = None


class TravelingAvatarEffect(Effect):
    """
    Traveling Avatar effect that moves across the multi-node display.

    The avatar appears as a geometric entity that travels from node to node,
    appearing on each screen only when within its viewport.
    """

    def __init__(self, sync_manager=None, node_id=0):
        super().__init__("traveling_avatar", AVATAR_FRAGMENT_SHADER)

        self.sync_manager = sync_manager
        self.node_id = node_id

        # Avatar parameters
        self.set_parameter("avatar_scale", 0.15)    # Size of avatar
        self.set_parameter("avatar_alpha", 1.0)     # Full opacity when visible
        self.set_parameter("spin_speed", 2.0)       # Base spin speed
        self.set_parameter("glow_intensity", 1.0)   # Glow intensity
        self.set_parameter("confidence", 0.8)       # Confidence level
        self.set_parameter("fragmentation", 0.0)    # Fragmentation level
        self.set_parameter("glow_color", [1.0, 1.0, 1.0])  # White glow
```

### vjlive1/core/effects/agent_avatar.py (L33-52)
```python
        self.set_parameter("glow_color", [1.0, 1.0, 1.0])  # White glow

    def update_from_global_state(self):
        """Update avatar position and visibility based on global state."""
        if not self.sync_manager:
            return

        # Get avatar position for this node
        local_pos = self.sync_manager.get_avatar_position_for_node(self.node_id)

        if local_pos >= 0.0:  # Avatar is visible on this node
            # Position avatar horizontally across the screen
            avatar_x = local_pos  # 0.0 = left edge, 1.0 = right edge
            avatar_y = 0.5       # Center vertically

            self.set_parameter("avatar_x", avatar_x)
            self.set_parameter("avatar_y", avatar_y)
            self.set_parameter("avatar_alpha", 1.0)  # Fully visible
        else:
            # Avatar not in this node's viewport
            self.set_parameter("avatar_alpha", 0.0)  # Invisible
```

### vjlive1/core/effects/agent_avatar.py (L49-68)
```python
            self.set_parameter("avatar_alpha", 1.0)  # Fully visible
        else:
            # Avatar not in this node's viewport
            self.set_parameter("avatar_alpha", 0.0)  # Invisible

    def apply_uniforms(self, time: float, resolution: Tuple[int, int], audio_reactor=None, semantic_layer=None):
        """Apply uniforms for traveling avatar."""
        super().apply_uniforms(time, resolution, audio_reactor, semantic_layer)

        # Update from global state
        self.update_from_global_state()

        # Apply avatar parameters
        self.shader.set_uniform("avatar_position", [
            self.get_parameter("avatar_x"),
            self.get_parameter("avatar_y")
        ])
        self.shader.set_uniform("avatar_scale", self.get_parameter("avatar_scale"))
        self.shader.set_uniform("avatar_alpha", self.get_parameter("avatar_alpha"))
```

### vjlive1/core/effects/agent_avatar.py (L65-84)
```python
            self.get_parameter("avatar_y")
        ])
        self.shader.set_uniform("avatar_scale", self.get_parameter("avatar_scale"))
        self.shader.set_uniform("avatar_alpha", self.get_parameter("avatar_alpha"))
        self.shader.set_uniform("spin_speed", self.get_parameter("spin_speed"))
        self.shader.set_uniform("glow_intensity", self.get_parameter("glow_intensity"))
        self.shader.set_uniform("confidence", self.get_parameter("confidence"))
        self.shader.set_uniform("fragmentation", self.get_parameter("fragmentation"))
        self.shader.set_uniform("glow_color", self.get_parameter("glow_color"))


# Simplified fragment shader for external agent avatar with Shadow Mode and Eye Tracking
AVATAR_FRAGMENT_SHADER = """
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform float time;
uniform vec2 resolution;
uniform float u_mix;

// Agent state parameters
uniform float spin_speed;
uniform float glow_intensity;
uniform float confidence;
uniform float fragmentation;
uniform vec3 glow_color;
uniform float avatar_alpha;

// Avatar positioning and scaling
uniform float avatar_scale;
uniform vec2 avatar_position;  // Position in screen space (0-1)

// Shadow Mode parameters
uniform float shadow_mode_enabled;
uniform float has_shadow_mask;

// Eye Tracking parameters
uniform float eye_tracking_enabled;
uniform vec2 gaze_direction;

#define PI 3.14159265359

// Distance to a triangle
float triangle_distance(vec2 p, vec2 a, vec2 b, vec2 c) {
    vec2 ab = b - a;
    vec2 ac = c - a;
    vec2 ap = p - a;

    float d1 = dot(ap, ab) / dot(ab, ab);
    float d2 = dot(ap, ac) / dot(ac, ac);

    vec2 closest;
    if (d1 >= 0.0 && d2 >= 0.0 && d1 + d2 <= 1.0) {
        closest = a + d1 * ab + d2 * ac;
    } else if (d1 < 0.0) {
        closest = a;
    } else if (d2 < 0.0) {
        closest = a;
    } else {
        closest = c;
    }

    return distance(p, closest);
}

// Create a spinning geometric core
float agent_core(vec2 p, float time, float spin_speed, float fragmentation) {
    // Transform to avatar space
    p = (p - avatar_position) / avatar_scale;

    // Apply rotation
    float angle = time * spin_speed;
    float cos_a = cos(angle);
    float sin_a = sin(angle);
    p = vec2(p.x * cos_a - p.y * sin_a, p.x * sin_a + p.y * cos_a);

    // Create multiple geometric elements
    float d = 1.0;

    // Central hexagon
    float hex_angle = atan(p.y, p.x) / (2.0 * PI) * 6.0;
    hex_angle = fract(hex_angle);
    float hex_radius = length(p);
```

### vjlive1/core/effects/agent_avatar.py (L113-132)
```python
    // Central hexagon
    float hex_angle = atan(p.y, p.x) / (2.0 * PI) * 6.0;
    hex_angle = fract(hex_angle);
    float hex_radius = length(p);
    // ... (rest of hexagon SDF construction)
```

[NEEDS RESEARCH]: The complete `agent_core` function and `main()` function are not fully shown. The spec should include a complete reference shader implementation to ensure visual fidelity. The missing parts likely include:
- Hexagon SDF: using `triangle_distance` to form a hexagon from 6 triangles.
- Fragmentation: adding noise to `p` before SDF.
- Confidence: affecting final color or glow.
- Main: sampling background (`tex0`), computing avatar SDF, applying glow, compositing with `u_mix`.

The implementer should reconstruct these based on the described behavior and legacy aesthetic.
