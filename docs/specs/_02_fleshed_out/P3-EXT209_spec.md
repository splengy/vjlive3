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

