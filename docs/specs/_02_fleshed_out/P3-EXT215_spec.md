# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT215_bad_trip_datamosh.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT215 — BadTripDatamoshEffect

**What This Module Does**

The `BadTripDatamoshEffect` is a psychedelic, horror-themed video effect that simulates a psychological breakdown through aggressive visual distortions. It combines dual video inputs (primary and secondary) with an optional depth map to produce a wide range of unsettling effects: facial distortion into demonic forms, insect-like crawling noise, screen tearing, paranoia strobes, void gaze, breathing walls, and more. The effect is entirely shader-based and runs in real-time, with each effect's intensity controlled by a uniform parameter (0.0–1.0).

The effect is designed to be used as a VJ tool for creating intense, nightmare-inducing visuals. It is self-contained as a fragment shader that samples multiple textures and applies a sequence of transformations.

**What This Module Does NOT Do**

- Does NOT perform audio analysis (it's purely visual)
- Does NOT handle video decoding or texture loading (relies on external texture management)
- Does NOT provide a UI for parameter control (parameters set via set_parameter)
- Does NOT implement 3D rendering (2D full-screen effect)
- Does NOT include fallback for missing depth map (depth is optional but effects degrade gracefully)

---

## Detailed Behavior and Parameter Interactions

### Texture Inputs

The effect uses up to 4 texture units:

- `tex0` (unit 0): Primary video input (Video A). This is the main source.
- `texPrev` (unit 1): Previous frame buffer. Used for feedback/time loop effect.
- `depth_tex` (unit 2): Depth map (optional). Used for facial distortion and shadow people. If not provided, a default depth (e.g., 1.0) can be used.
- `tex1` (unit 3): Secondary video input (Video B). Used for reality tear effect and as an alternative source when dual mode is active.

The effect checks if `tex1` is valid by sampling its center; if all channels sum to near zero, it's considered absent.

### Effect Pipeline (Shader Order)

The fragment shader processes effects in a specific order:

1. **Breathing Walls**: Warps UV coordinates based on radial distance from center, creating a pulsing, organic distortion.
2. **Demon Face**: If depth indicates a nearby face (depth > 0.2), adds high-frequency horizontal warping and hollows out eye regions.
3. **Insect Crawl**: Adds random, tiny UV offsets based on a hash function, simulating bugs crawling under the skin.
4. **Base Color Selection**: After UV modifications, samples either `tex1` (if dual) or `tex0` as the base color, and also samples `texPrev` for feedback.
5. **Time Loop**: Mixes current frame with previous frame: `color = mix(color, prev, u_time_loop * 0.5)`.
6. **Reality Tear**: Randomly replaces portions of the image with the alternate video (or inverted) based on a hash threshold.
7. **Sickness**: Applies a green/purple tint that oscillates with time.
8. **Shadow People**: Darkens areas where depth is low (background) to create shadowy figures.
9. **Psychosis**: Inverts colors based on parameter: `color.rgb = abs(color.rgb - vec3(u_psychosis * 0.5))`.
10. **Void Gaze**: Applies a vignette that darkens edges, with intensity controlled by `u_void_gaze`.
11. **Doom**: Crushes contrast: `color.rgb = (color.rgb - 0.5) * (1.0 + u_doom) + 0.5`.
12. **Paranoia**: Randomly sets color to black with low probability if `u_paranoia > 0`.
13. **Final Mix**: Multiplies by `u_mix` (blend factor) and outputs.

### Parameter Descriptions

| Uniform | Type | Range | Effect |
|---------|------|-------|--------|
| `u_anxiety` | float | 0.0–1.0 | Controls speed/intensity of jitter and breathing walls frequency |
| `u_demon_face` | float | 0.0–1.0 | Amount of facial distortion (warping, eye hollowing) |
| `u_insect_crawl` | float | 0.0–1.0 | Density of bug-like noise; higher = more frequent UV jumps |
| `u_void_gaze` | float | 0.0–1.0 | Vignette strength; darkens periphery, creates "hole" effect |
| `u_reality_tear` | float | 0.0–1.0 | Probability and intensity of screen tearing revealing alternate video |
| `u_sickness` | float | 0.0–1.0 | Tint strength (green/purple) |
| `u_time_loop` | float | 0.0–1.0 | Feedback amount mixing with previous frame (echo) |
| `u_breathing_walls` | float | 0.0–1.0 | UV warping amplitude for organic pulsing |
| `u_paranoia` | float | 0.0–1.0 | Strobe probability; higher = more frequent black frames |
| `u_shadow_people` | float | 0.0–1.0 | Darkening of background (low depth) areas |
| `u_psychosis` | float | 0.0–1.0 | Color inversion/hue shift intensity |
| `u_doom` | float | 0.0–1.0 | Contrast boost/crush |
| `u_mix` | float | 0.0–1.0 | Overall effect blend (0 = original, 1 = full effect) |

All parameters are settable at runtime via `set_parameter(name, value)`.

### Shader Utilities

The shader includes helper functions:
- `hash(vec2 p)`: pseudo-random hash returning [0,1]
- `noise(vec2 p)`: smooth value noise using bilinear interpolation of hash

These are used for procedural effects (insect crawl, reality tear, paranoia).

---

## Integration

### VJLive3 Pipeline Integration

`BadTripDatamoshEffect` is an **Effect** that composites over the input framebuffer. It expects textures to be bound to specific units before rendering. The effect should be added to the effects chain and rendered with the appropriate texture bindings.

**Typical usage**:

```python
# Initialize
effect = BadTripDatamoshEffect(
    texture0="video_a_tex_id",  # or path
    texture1="video_b_tex_id",  # optional
    depth_map="depth_tex_id"    # optional
)

# Each frame:
# 1. Bind textures to units:
glActiveTexture(GL_TEXTURE0); glBindTexture(GL_TEXTURE_2D, tex0_id)
glActiveTexture(GL_TEXTURE1); glBindTexture(GL_TEXTURE_2D, prev_tex_id)  # previous frame
glActiveTexture(GL_TEXTURE2); glBindTexture(GL_TEXTURE_2D, depth_tex_id)  # if available
glActiveTexture(GL_TEXTURE3); glBindTexture(GL_TEXTURE_2D, tex1_id)  # if available

# 2. Set parameters
effect.set_parameter("u_demon_face", 0.8)
effect.set_parameter("u_insect_crawl", 0.3)
# ... etc.

# 3. Render (calls apply_uniforms and draws full-screen quad)
effect.render(time, resolution)
```

The effect requires an OpenGL context and a valid shader program.

### Texture Management

The effect does not own the textures; it expects them to be provided and bound. The `texture0`, `texture1`, `depth_map` arguments can be either OpenGL texture IDs or paths that the texture manager can resolve. The effect should store these IDs and bind them in the correct order during `apply_uniforms`.

The `texPrev` texture is a feedback buffer: after rendering, the current frame should be copied to a texture for use in the next frame. This is managed by the caller.

---

## Performance

### Computational Cost

This effect is **GPU-bound** with a heavy fragment shader:

- The shader performs multiple texture lookups (up to 5 per pixel: tex0, texPrev, depth_tex, tex1, plus noise functions).
- It includes many conditional branches based on uniform values. However, most uniforms are constant across the frame, so the GPU can optimize.
- At 1080p (2M pixels), the shader is moderately expensive but should run at 60 Hz on modern GPUs. The biggest cost is the texture bandwidth: 5 textures × 2M pixels = 10M texels per frame. That's ~160 MB/s at 60 Hz (assuming 16 bytes per texel read), which is fine.

### Memory Usage

- **GPU**: Shader program (< 100 KB). No additional buffers.
- **CPU**: Small parameter storage (< 1 KB).

### Optimization Strategies

- Use lower resolution for the effect if performance is an issue (render to smaller FBO and upscale).
- Ensure texture units are cached and not re-bound unnecessarily.
- Consider merging some conditionals into a single pass to reduce branching, but not critical.

### Platform-Specific Considerations

- **Desktop**: Should run fine on any GPU with OpenGL 3.3+.
- **Embedded**: May struggle with multiple texture fetches; consider simplifying effects or reducing resolution.
- **Mobile**: Use with caution; test on target devices.

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | Effect initializes without crashing if OpenGL context missing (should raise error) |
| `test_basic_rendering` | Effect produces output without errors when all textures are valid |
| `test_missing_tex1` | Effect works correctly when tex1 is not provided (reality tear uses fallback) |
| `test_missing_depth` | Effect works without depth map (depth effects degrade gracefully) |
| `test_parameter_clamping` | All parameters are clamped to [0.0, 1.0] and out-of-range values are corrected |
| `test_breathing_walls_effect` | When u_breathing_walls > 0, UVs are warped radially |
| `test_demon_face_effect` | When depth > 0.2 and u_demon_face > 0, UV warping and eye hollowing occur |
| `test_insect_crawl_effect` | When u_insect_crawl > 0, random UV offsets appear |
| `test_time_loop_feedback` | u_time_loop mixes current frame with previous frame |
| `test_reality_tear_effect` | u_reality_tear causes random patches to show alternate video or inversion |
| `test_sickness_tint` | u_sickness applies green/purple tint |
| `test_shadow_people_darken` | u_shadow_people darkens low-depth areas |
| `test_psychosis_inversion` | u_psychosis inverts colors |
| `test_void_gaze_vignette` | u_void_gaze darkens screen edges |
| `test_doom_contrast` | u_doom increases contrast |
| `test_paranoia_strobe` | u_paranoia occasionally sets frame to black |
| `test_cleanup` | All OpenGL resources (shader, FBOs if any) are released on stop() |

**Minimum coverage**: 80% before task is marked done.

---

## Open Questions and Research Findings

### [NEEDS RESEARCH]: How is `texPrev` managed? It requires a feedback loop where the current frame is saved for the next frame. The effect does not create this texture; the caller must provide it. The spec should clarify that the caller is responsible for maintaining a ping-pong FBO or a texture that holds the previous frame.

**Resolution**: Document that `texPrev` is a texture bound to unit 1 that contains the result of the previous frame's render. The caller should set up a feedback loop: after rendering the effect, copy the output to a texture for the next frame's `texPrev`. The effect itself does not manage this.

### [NEEDS RESEARCH]: The demon face effect uses a simple heuristic `depth > 0.2` and then warps UV based on `sin(uv.y * 50.0 + time * 10.0)`. It also attempts to hollow eyes with a circular mask at the center. This is a crude approximation. Is there a more sophisticated face detection? The legacy code uses this simple approach.

**Resolution**: Keep the simple approach as in legacy. It's performant and gives a glitchy demonic look. The depth map is expected to have face regions with lower depth values (closer to camera). The effect works reasonably if depth map is accurate.

### [NEEDS RESEARCH]: The `hasDual` check samples `tex1` at (0.5) to see if it's valid. This is a hack to detect if the secondary texture is provided. In VJLive3, we might have a more explicit flag. But we can keep the same check: if the texture is bound and has non-zero data, use it.

**Resolution**: Use the same detection: sample center of tex1; if sum of RGB > 0.001, consider dual input present. Alternatively, provide an explicit `has_dual` parameter. We'll stick to legacy behavior.

### [NEEDS RESEARCH]: The `u_mix` uniform is applied at the very end: `color.rgb *= u_mix`? Actually the legacy doesn't show final mix; it likely multiplies alpha or blends with original. The skeleton spec says `u_mix` is blend factor between Video A and Video B, but the shader uses it differently? Let's check: In the legacy, `u_mix` is declared but not used in the snippet. It might be used earlier to mix between tex0 and tex1 before effects? Actually the line `vec4 color = hasDual ? texture(tex1, uv) : texture(tex0, uv);` chooses one or the other, not mixing. So `u_mix` might be used to blend between the effect output and the original? Or maybe it's used in the time loop? Not clear.

**Resolution**: We'll define `u_mix` as the overall effect intensity: after all effects, do `final_color = mix(original_color, processed_color, u_mix)`. The original color is from `tex0` (or maybe the pre-effect color). This matches typical effect blending. The legacy may have used it differently; but we can design it sensibly. The skeleton spec says "Blend factor between Video A and Video B", but that's not what the shader does. Actually the skeleton spec's `u_mix` is listed as "Blend factor between Video A and Video B (0.0–1.0)". But the shader uses a ternary to pick one or the other. Perhaps `u_mix` is used to cross-dissolve between them: `color = mix(texture(tex0, uv), texture(tex1, uv), u_mix)`. That would make sense. However, the legacy code uses `hasDual ? texture(tex1, uv) : texture(tex0, uv)`. So maybe `u_mix` is used elsewhere (like in the time loop or final output). The snippet doesn't show final assignment. We need to infer.

Let's look at the full shader from the snippets: The `main()` function ends with `fragColor = vec4(color, original.a);`? Actually the last snippet shows `fragColor = vec4(color, original.a);`? No, it shows `fragColor = vec4(color, original.a);`? Wait, the last line in snippet 10 is `color.rgb = (color.rgb - 0.5) * (1.0 + u_doom) + 0.5;` and then `if (u_paranoia > 0.0 && hash(vec2(time)) > 0.9) { color.rgb = vec3(0.0); }`. There's no final `fragColor` assignment shown. Probably after that, they set `fragColor = vec4(color, 1.0)` or something. The `u_mix` might be used to blend with `original` (the unmodified tex0). The snippet earlier had `vec4 original = texture(tex0, uv);` but that was inside the loop? Actually that was in the audio particle shader, not this one. In this shader, they don't seem to keep original. So `u_mix` might be used to control the strength of the entire effect: maybe they do `color = mix(original, color, u_mix)` but original not stored. Hmm.

Let's re-read the snippets carefully:

Fragment shader start:
```
uniform sampler2D tex0;
uniform sampler2D texPrev;
uniform sampler2D depth_tex;
uniform sampler2D tex1;
uniform float time;
uniform vec2 resolution;
uniform float u_anxiety; ...
...
void main() {
    vec2 uv = v_uv;
    vec2 texel = 1.0 / resolution;
    bool hasDual = (texture(tex1, vec2(0.5)).r + ...) > 0.001;
    float depth = texture(depth_tex, uv).r;
```
Then they apply breathing walls (modify uv), demon face (modify uv), insect crawl (modify uv). Then:
```
    vec4 color = hasDual ? texture(tex1, uv) : texture(tex0, uv);
    vec4 prev = texture(texPrev, uv);
```
Then time loop: `color = mix(color, prev, u_time_loop * 0.5);`
Then reality tear modifies `color`.
Then sickness modifies `color.rgb`.
Then shadow people: `color.rgb *= (1.0 - u_shadow_people * 0.8);` if depth < 0.3.
Then psychosis: `color.rgb = abs(color.rgb - vec3(u_psychosis * 0.5));`
Then void gaze: `color.rgb *= smoothstep(0.8, 0.2, d * (1.0 + u_void_gaze));`
Then doom: `color.rgb = (color.rgb - 0.5) * (1.0 + u_doom) + 0.5;`
Then paranoia: `if (u_paranoia > 0.0 && hash(vec2(time)) > 0.9) { color.rgb = vec3(0.0); }`
Then presumably `fragColor = vec4(color, 1.0);` or maybe `fragColor = color;` (alpha not used).

Where is `u_mix` used? It's declared but not in the snippets. Possibly it's used to blend between the effect and the original? Or maybe it's used in the time loop? Actually time loop uses `u_time_loop`. So `u_mix` might be used at the very end to blend with the original unmodified frame. But original is not stored because uv was modified. They could have stored `vec4 original = texture(tex0, v_uv);` before modifying uv. The snippet doesn't show that. Maybe they intended to use `u_mix` to blend between the processed color and the original `tex0` sample at the original uv. That would be a common pattern: `final = mix(original, processed, u_mix)`. The skeleton spec says `u_mix` is "Blend factor between Video A and Video B". That's different. Could be a mis-match.

Given the skeleton spec's description: "u_mix: Blend factor between Video A and Video B (0.0–1.0)". That suggests that instead of the ternary `hasDual ? tex1 : tex0`, they might use `mix(tex0, tex1, u_mix)` when dual is present. But the legacy uses ternary. Perhaps `u_mix` is used to cross-disside between the two videos before applying effects? That would make sense: the effect could blend the two sources, then apply distortions. However, the legacy code's ternary is a hard switch. But maybe they later changed? The snippet might be incomplete.

Given the ambiguity, we should follow the skeleton spec's definition: `u_mix` blends between Video A and Video B. So we can define that the base color is `mix(texture(tex0, uv), texture(tex1, uv), u_mix)` if dual is available, else just tex0. That is a reasonable design. And then all effects apply to that mixed color. This also allows smooth crossfading between videos.

Thus, we'll incorporate that: `vec4 base_color = hasDual ? mix(texture(tex0, uv), texture(tex1, uv), u_mix) : texture(tex0, uv);` Actually if hasDual, we use mix; if not, just tex0. But the skeleton says u_mix is blend factor between A and B, so if no B, u_mix irrelevant.

We'll adopt that in the spec.

### [NEEDS RESEARCH]: The `u_paranoia` effect: `if (u_paranoia > 0.0 && hash(vec2(time)) > 0.9) { color.rgb = vec3(0.0); }`. This sets entire frame to black randomly. That's a harsh strobe. Might be too aggressive. But it's the legacy behavior.

**Resolution**: Keep as is. It's a psychological horror effect.

### [NEEDS RESEARCH]: The `u_psychosis` effect: `color.rgb = abs(color.rgb - vec3(u_psychosis * 0.5));`. This subtracts a constant and takes absolute value, causing inversion and color shifts. Works.

**Resolution**: Keep.

### [NEEDS RESEARCH]: The `u_doom` contrast: `(color - 0.5) * (1.0 + u_doom) + 0.5`. This increases contrast; values >1 push colors to extremes.

**Resolution**: Keep.

---

## Configuration Schema

```python
METADATA = {
  "params": [
    {"id": "u_anxiety", "name": "Anxiety", "default": 0.0, "min": 0.0, "max": 1.0, "type": "float"},
    {"id": "u_demon_face", "name": "Demon Face", "default": 0.0, "min": 0.0, "max": 1.0, "type": "float"},
    {"id": "u_insect_crawl", "name": "Insect Crawl", "default": 0.0, "min": 0.0, "max": 1.0, "type": "float"},
    {"id": "u_void_gaze", "name": "Void Gaze", "default": 0.0, "min": 0.0, "max": 1.0, "type": "float"},
    {"id": "u_reality_tear", "name": "Reality Tear", "default": 0.0, "min": 0.0, "max": 1.0, "type": "float"},
    {"id": "u_sickness", "name": "Sickness", "default": 0.0, "min": 0.0, "max": 1.0, "type": "float"},
    {"id": "u_time_loop", "name": "Time Loop", "default": 0.0, "min": 0.0, "max": 1.0, "type": "float"},
    {"id": "u_breathing_walls", "name": "Breathing Walls", "default": 0.0, "min": 0.0, "max": 1.0, "type": "float"},
    {"id": "u_paranoia", "name": "Paranoia", "default": 0.0, "min": 0.0, "max": 1.0, "type": "float"},
    {"id": "u_shadow_people", "name": "Shadow People", "default": 0.0, "min": 0.0, "max": 1.0, "type": "float"},
    {"id": "u_psychosis", "name": "Psychosis", "default": 0.0, "min": 0.0, "max": 1.0, "type": "float"},
    {"id": "u_doom", "name": "Doom", "default": 0.0, "min": 0.0, "max": 1.0, "type": "float"},
    {"id": "u_mix", "name": "Mix", "default": 1.0, "min": 0.0, "max": 1.0, "type": "float", "description": "Blend factor between Video A and Video B (if dual) or effect strength"}
  ]
}
```

Note: `u_mix` serves double duty: if dual input, it blends between the two videos before effects; if not, it can blend the effect output with the original (though not used that way in legacy). We'll define it as: if `hasDual`, `base_color = mix(tex0, tex1, u_mix)`, else `base_color = tex0`. Then all effects apply. Finally, the result is output directly (no further mix). This matches the skeleton's description.

---

## State Management

- **Per-frame state**: None beyond uniform updates.
- **Persistent state**: All parameter values (the u_* floats). These can be changed at runtime.
- **Init-once state**: Shader program, uniform locations, texture unit bindings.
- **Thread safety**: Not thread-safe; must be used from the rendering thread with OpenGL context.

---

## GPU Resources

- **Fragment shader**: The main effect shader (see full code in LEGACY CODE REFERENCES).
- **Uniforms**: 13 float uniforms + 4 sampler2D uniforms.
- **No VBO/VAO** needed (full-screen quad handled by base Effect).
- **Textures**: Up to 4 input textures (provided by caller).

---

## Public Interface

```python
class BadTripDatamoshEffect(Effect):
    def __init__(self, texture0: str, texture1: str = None, depth_map: str = None) -> None:
        """
        Initialize the effect.
        
        Args:
            texture0: Identifier for primary video texture (Video A). Can be an OpenGL texture ID or a path that the texture manager can resolve.
            texture1: Identifier for secondary video texture (Video B). Optional.
            depth_map: Identifier for depth texture. Optional.
        """
    
    def set_parameter(self, name: str, value: float) -> None:
        """
        Set an effect parameter.
        
        Args:
            name: Parameter name (e.g., "u_demon_face", "u_insect_crawl")
            value: Float between 0.0 and 1.0
        
        Raises:
            ValueError: If name is not a recognized parameter or value out of range.
        """
    
    def get_parameter(self, name: str) -> float:
        """
        Get current parameter value.
        
        Args:
            name: Parameter name
            
        Returns:
            Current float value.
        
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
| `texture1` | `str` or `int` | Secondary video texture identifier | Optional; if None, dual effects disabled |
| `depth_map` | `str` or `int` | Depth texture identifier | Optional; if None, depth effects use constant 1.0 |
| `time` | `float` | Current time in seconds | ≥ 0.0 |
| `resolution` | `Tuple[int, int]` | Screen dimensions | width, height > 0 |
| `dt` | `float` | Time delta for updates | ≥ 0.0 |
| All `u_*` parameters | `float` | Effect intensities | [0.0, 1.0] |

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
| `test_missing_tex1` | When texture1 is None, effect uses only tex0 and reality tear falls back to inversion |
| `test_missing_depth` | When depth_map is None, depth effects (demon_face, shadow_people) are disabled or use default depth=1.0 |
| `test_parameter_clamping` | Setting parameters outside [0,1] clamps to range; get_parameter returns clamped value |
| `test_breathing_walls_effect` | With u_breathing_walls > 0, UV coordinates are warped (check by rendering to known pattern) |
| `test_demon_face_effect` | With depth map containing a face region (depth > 0.2) and u_demon_face > 0, UV warping occurs |
| `test_insect_crawl_effect` | With u_insect_crawl > 0, UVs exhibit random offsets (check over time) |
| `test_time_loop_feedback` | With u_time_loop > 0, previous frame influences current (check persistence) |
| `test_reality_tear_effect` | With u_reality_tear > 0, random horizontal/vertical tears appear showing alternate video or inversion |
| `test_sickness_tint` | With u_sickness > 0, color shifts toward green/purple |
| `test_shadow_people_darken` | With u_shadow_people > 0 and depth < 0.3, those areas are darkened |
| `test_psychosis_inversion` | With u_psychosis > 0, colors are inverted/abs-subtracted |
| `test_void_gaze_vignette` | With u_void_gaze > 0, screen edges are darkened with radial falloff |
| `test_doom_contrast` | With u_doom > 0, contrast is increased (dark darker, bright brighter) |
| `test_paranoia_strobe` | With u_paranoia > 0, occasional frames turn completely black (check over multiple frames) |
| `test_cleanup` | After stop(), shader and any FBOs are deleted, no GL errors |

**Minimum coverage**: 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-X] P3-EXT215: bad_trip_datamosh effect implementation` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES

### vjlive1/plugins/vdatamosh/bad_trip_datamosh.py (L1-20)
```python
"""
Bad Trip Datamosh — The Nightmare Flip

DUAL VIDEO INPUT: tex0 = Video A, tex1 = Video B

"IT WON'T STOP."

This effect simulates a psychedelic crisis. The visuals are aggressive,
hostile, and unsettling. It uses depth to identify the subject and
turn them into a monster. The environment breathes with a sickly
pulse. Spiders crawl under the pixels.

Features:
- Demon Face: Distorts facial depth to look skeletal or demonic.
- Insect Crawl: High-frequency noise that moves like bugs.
- Paranoia Strobe: Random, anxiety-inducing flashes.
- Void Gaze: The center of the screen stares back at you.
- Reality Tear: Screen tearing that reveals the "other side" (Video B).

Metadata:
- Tags: horror, nightmare, bad-trip, paranoia, demons, glitch
- Mood: terrifying, anxious, sick, dark, overwhelming
- Visual Style: psychological-horror, deep-fried, cursed-image, void

Texture unit layout:
  Unit 0: tex0 (Video A)
  Unit 1: texPrev (previous frame)
  Unit 2: depth_tex (depth map)
  Unit 3: tex1 (Video B)
"""

from core.effects.shader_base import Effect
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)
```

### vjlive1/plugins/vdatamosh/bad_trip_datamosh.py (L17-36)
```python
from core.effects.shader_base import Effect
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

FRAGMENT = """
#version 330 core
in vec2 v_uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform sampler2D texPrev;
uniform sampler2D depth_tex;
uniform sampler2D tex1;
uniform float time;
uniform vec2 resolution;

uniform float u_anxiety;           // Speed/Jitter intensity
uniform float u_demon_face;        // Facial distortion amount
uniform float u_insect_crawl;      // Bug-like noise
uniform float u_void_gaze;         // Dark vignette/hole
uniform float u_reality_tear;      // Glitch tearing
uniform float u_sickness;          // Green/Purple tinting
uniform float u_time_loop;         // Feedback delay echo
uniform float u_breathing_walls;   // UV warping
uniform float u_paranoia;          // Random strobe/cuts
uniform float u_shadow_people;     // Dark depth artifacts
uniform float u_psychosis;         // Color inversion/hue shift
uniform float u_doom;              // Contrast crush

uniform float u_mix;

float hash(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f*f*(3.0-2.0*f);
    return mix(mix(hash(i + vec2(0.0,0.0)), hash(i + vec2(1.0,0.0)), f.x),
               mix(hash(i + vec2(0.0,1.0)), hash(i + vec2(1.0,1.0)), f.x), f.y);
}

void main() {
    vec2 uv = v_uv;
    vec2 texel = 1.0 / resolution;
    bool hasDual = (texture(tex1, vec2(0.5)).r + texture(tex1, vec2(0.5)).g + texture(tex1, vec2(0.5)).b) > 0.001;
    float depth = texture(depth_tex, uv).r;

    // BREATHING WALLS
    if (u_breathing_walls > 0.0) {
        vec2 center = vec2(0.5);
        vec2 d = uv - center;
        float r = length(d);
        float a = atan(d.y, d.x);
        float breath = sin(time * u_anxiety + r * 10.0) * u_breathing_walls * 0.05;
        uv += d * breath;
    }

    // DEMON FACE (Depth Distortion)
    // If depth is near (face), warp it aggressively
    if (depth > 0.2 && u_demon_face > 0.0) {
        float faceWarp = sin(uv.y * 50.0 + time * 10.0) * u_demon_face * 0.02;
        uv.x += faceWarp * smoothstep(0.2, 0.5, depth);
        
        // Hollow eyes effect
        vec2 eyeUV = (uv - 0.5) * vec2(1.0, 2.0); // Rough approximation
        if (length(eyeUV) < 0.1) {
            uv -= (uv - 0.5) * u_demon_face * 0.5;
        }
    }
    
    // INSECT CRAWL
    if (u_insect_crawl > 0.0) {
        float bugs = hash(uv * 100.0 + vec2(time * 10.0, sin(time)));
        if (bugs > 0.95 - u_insect_crawl * 0.05) {
            uv += (vec2(hash(uv), hash(uv+1.0)) - 0.5) * 0.02;
        }
    }

    vec4 color = hasDual ? texture(tex1, uv) : texture(tex0, uv);
    vec4 prev = texture(texPrev, uv);

    // TIME LOOP (Feedback)
    color = mix(color, prev, u_time_loop * 0.5);

    // REALITY TEAR (Glitch)
    if (u_reality_tear > 0.0) {
        float tear = step(0.98 - u_reality_tear * 0.1, hash(vec2(uv.y * 10.0, time)));
        if (tear > 0.5) {
            // Sample the "Other Side" or just invert
            vec4 other = hasDual ? texture(tex0, uv) : vec4(1.0) - color;
            color = mix(color, other, 0.8);
        }
    }

    // SICKNESS (Tint)
    if (u_sickness > 0.0) {
        vec3 sickGreen = vec3(0.2, 0.5, 0.1);
        vec3 sickPurple = vec3(0.4, 0.0, 0.4);
        float sickMix = sin(time * 0.5) * 0.5 + 0.5;
        vec3 sickColor = mix(sickGreen, sickPurple, sickMix);
        color.rgb = mix(color.rgb, color.rgb * sickColor * 2.0, u_sickness * 0.5);
    }
    
    // SHADOW PEOPLE
    if (u_shadow_people > 0.0 && depth < 0.3) {
        // Darken background figures
        color.rgb *= (1.0 - u_shadow_people * 0.8);
    }
    
    // PSYCHOSIS (Hue Shift/Inversion)
    if (u_psychosis > 0.0) {
        color.rgb = abs(color.rgb - vec3(u_psychosis * 0.5));
    }

    // VOID GAZE (Vignette)
    if (u_void_gaze > 0.0) {
        float d = length(v_uv - 0.5);
        color.rgb *= smoothstep(0.8, 0.2, d * (1.0 + u_void_gaze));
    }
    
    // DOOM (Contrast)
    color.rgb = (color.rgb - 0.5) * (1.0 + u_doom) + 0.5;
    
    // PARANOIA (Strobe)
    if (u_paranoia > 0.0 && hash(vec2(time)) > 0.9) {
        color.rgb = vec3(0.0);
    }
    
    fragColor = color;
}
"""
```

[NEEDS RESEARCH]: The final `fragColor` assignment is simply `color` (no alpha modification). The `u_mix` uniform is declared but not used in the shader body as shown. This is likely an oversight in the snippet; the intended use is to blend between the original (pre-effect) and the processed color, or to blend between Video A and Video B. We'll incorporate `u_mix` as described in the Integration section: base color = `hasDual ? mix(tex0, tex1, u_mix) : tex0`. This uses `u_mix` meaningfully. Additionally, we could also use `u_mix` to blend the final effect with the original: `final = mix(original_tex0, color, u_mix)`. But that would conflict. We'll choose the former: `u_mix` controls the A/B blend before effects. That aligns with the skeleton's description and gives a useful control.

To maintain backward compatibility, if `u_mix` is not used elsewhere, it's fine.

The spec should include the complete, corrected shader code as a reference, with `u_mix` properly used. However, the spec should not paste the entire shader (to keep under 750 lines). We can include a summarized version and note the full shader is in legacy. But the rule says the spec file must exist and be reviewed before code. It's okay to include the full shader as a string in the spec? That would be long. Better to reference the legacy file and describe the behavior. The spec can include key snippets but not the entire 200-line shader. We'll keep it concise.

Given the spec is already long, we'll include the full shader in an appendix or as a code block? The spec might exceed 750 lines if we include full shader. But we can summarize and refer to legacy. The instructions: "Keep specs under 500 lines." So we need to be concise. We'll describe the shader logic in prose and not include the full code. The LEGACY CODE REFERENCES section already contains the full shader from the snippets. That's sufficient.

Thus, the enriched spec should have a clear description of each effect, the parameter list, integration steps, and test plan. We'll avoid pasting the entire shader again.

Now I'll write the enriched spec.
</think>
Let me get the full shader code from the legacy to include as a reference. I'll read the last part of the snippets to see the complete main() function.<tool_call>
<function=execute_command>