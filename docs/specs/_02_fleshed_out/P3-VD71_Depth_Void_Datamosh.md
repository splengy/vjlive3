# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-VD71_Depth_Void_Datamosh.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD71 — DepthVoidDatamoshEffect

## Description

The DepthVoidDatamoshEffect is "the dark side" — an oppressive, menacing depth-datamosh explicitly designed for industrial, darkwave, and hard techno. The void consumes the scene, dragging everything toward pure black. Near objects emerge as threatening silhouettes. Shadow entities crawl along depth edges. Dark fog rolls through layers. The void breathes, constricts, and crushes.

This effect is ideal for creating dark, atmospheric visuals where depth drives a descent into darkness. It's perfect for VJ performances that want to create a sense of menace, dread, or supernatural darkness. The effect is deeply audio-reactive, with bass driving shadow expansion and darkness physically pushing outward on kick drums.

## What This Module Does

- Drives the scene toward pure black (void consumption)
- Near objects become threatening silhouettes (infrared threat detection)
- Shadow entities crawl along depth edges (edge datamosh)
- Dark fog rolls through depth layers (fog effect)
- Bass-driven shadow expansion (audio-reactive darkness)
- Depth-driven desaturation (color drain)
- Configurable void strength, edge crawling, fog density
- GPU-accelerated with multiple depth-based effects

## What This Module Does NOT Do

- Does NOT provide CPU fallback (GPU required)
- Does NOT store persistent state across sessions
- Does NOT include audio reactivity in base implementation (may be added later)
- Does NOT produce bright or cheerful visuals (inherently dark)
- Does NOT include color restoration (only desaturation)
- Does NOT support multiple void layers (single void effect)

---

## Detailed Behavior

### Void Datamosh Pipeline

1. **Capture depth frame**: `depth_frame` (HxW, normalized 0-1)
2. **Compute void mask**: Where depth is near, apply void effects
3. **Shadow expansion**: Bass-driven expansion of shadows (if audio reactive)
4. **Edge crawling**: Datamosh artifacts along depth edges
5. **Dark fog**: Depth-layered fog that rolls through scene
6. **Silhouette extraction**: Near objects become black silhouettes with edge glow
7. **Desaturation**: Drain color based on depth and void strength
8. **Composite**: Blend void effects with original via `u_mix`

### Void Consumption

The core concept: everything tends toward black. The void strength controls how much the scene is darkened:

```glsl
vec3 color = texture(tex0, uv).rgb;
float void_strength = u_voidStrength;  // 0-1

// Tend toward black
color = mix(color, vec3(0.0), void_strength * 0.1);
```

But it's not uniform — depth modulates the void:

```glsl
float depth = texture(depth_tex, uv).r;
float void_mask = 1.0 - depth;  // Near = more void
color = mix(color, vec3(0.0), void_mask * void_strength * 0.1);
```

### Threatening Silhouettes

Near objects (close to camera) emerge as threatening silhouettes with infrared glow:

```glsl
if (depth < near_threshold) {
    // Near object becomes silhouette
    vec3 silhouette = vec3(0.0);  // Pure black
    
    // Infrared threat glow (red/orange edge)
    float edge = 1.0 - smoothstep(0.0, 0.1, depth);
    vec3 threat_glow = vec3(1.0, 0.2, 0.0) * edge * threatGlow;
    
    color = mix(silhouette, color, 0.3);  // Mostly black
    color += threat_glow;
}
```

### Edge Crawling (Shadow Entities)

At depth boundaries, shadow entities crawl — datamosh artifacts that follow depth edges:

```glsl
float depth_grad = length(vec2(dFdx(depth), dFdy(depth)));
if (depth_grad > edge_threshold) {
    // This pixel is on a depth edge
    vec2 edge_dir = normalize(vec2(dFdx(depth), dFdy(depth)));
    
    // Crawl along edge
    vec2 crawl_offset = edge_dir * crawl_speed * sin(time * 5.0);
    vec3 shadow_entity = texture(tex0, uv + crawl_offset).rgb;
    
    // Darken and desaturate
    shadow_entity = vec3(dot(shadow_entity, vec3(0.299, 0.587, 0.114)));
    shadow_entity *= 0.3;  // Dark
    
    color = mix(color, shadow_entity, crawl_strength);
}
```

### Dark Fog Rolling Through Layers

Fog that varies with depth, creating a sense of layers:

```glsl
float fog_density = fogDensity * 0.1;
float fog_offset = sin(time * 0.5) * 0.2;  // Rolling motion

// Fog is stronger at certain depths
float fog_mask = smoothstep(0.3, 0.7, depth + fog_offset);
vec3 fog_color = vec3(0.05, 0.02, 0.01);  // Very dark brown/black

color = mix(color, fog_color, fog_mask * fog_density);
```

### Bass-Driven Shadow Expansion

If audio reactive, bass frequencies drive shadow expansion:

```glsl
float bass = audio_reactor.get_bass();  // 0-1
float expansion = bass * shadowExpansion * 0.1;

// Expand shadows outward from depth edges
float depth_mask = smoothstep(0.0, 0.3, depth);
color = mix(color, vec3(0.0), depth_mask * expansion);
```

### Desaturation

Drain color based on void strength and depth:

```glsl
float gray = dot(color, vec3(0.299, 0.587, 0.114));
float desat_factor = voidStrength * 0.1 * (1.0 - depth);  // More desat in void
color = mix(color, vec3(gray), desat_factor);
```

### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `voidStrength` | float | 8.0 | 0.0-10.0 | Overall strength of void consumption |
| `edgeCrawl` | float | 6.0 | 0.0-10.0 | Intensity of shadow entities on depth edges |
| `crawlSpeed` | float | 4.0 | 0.0-10.0 | Speed of edge crawling |
| `fogDensity` | float | 5.0 | 0.0-10.0 | Density of dark fog layers |
| `fogScroll` | float | 3.0 | 0.0-10.0 | Speed of fog rolling motion |
| `threatGlow` | float | 7.0 | 0.0-10.0 | Intensity of infrared threat glow on near objects |
| `shadowExpansion` | float | 5.0 | 0.0-10.0 | Bass-driven shadow expansion (audio reactive) |
| `desaturation` | float | 6.0 | 0.0-10.0 | Color drain strength |
| `nearThreshold` | float | 3.0 | 0.0-10.0 | Depth threshold for near object detection |

**Inherited from Effect**: `u_mix`

---

## Public Interface

```python
class DepthVoidDatamoshEffect(Effect):
    def __init__(self) -> None: ...
    def set_depth_source(self, source) -> None: ...
    def update_depth_data(self) -> None: ...
    def set_audio_reactor(self, reactor) -> None: ...  # For bass-driven effects
    def set_parameter(self, name: str, value: float) -> None: ...
    def get_parameter(self, name: str) -> float: ...
    def apply_uniforms(self, time: float, resolution: Tuple[int, int], audio_reactor=None) -> None: ...
    def process_frame(self, frame: np.ndarray) -> np.ndarray: ...
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description |
|------|------|-------------|
| `frame` | `np.ndarray` | Input video frame (HxWxC, RGB) |
| **Output** | `np.ndarray` | Void datamosh output (HxWxC, RGB) |

---

## State Management

**Persistent State:**
- `_depth_source: Optional[DepthSource]` — Connected depth source
- `_depth_frame: Optional[np.ndarray]` — Current depth frame
- `_audio_reactor: Optional[AudioReactor]` — Audio analysis for bass-driven effects
- `_parameters: dict` — Void parameters
- `_shader: ShaderProgram` — Compiled shader
- `_temp_texture: int` — For intermediate rendering

**Per-Frame:**
- Update depth data from source
- Get audio data if available (bass level)
- Render void effect: apply void consumption, edge crawling, fog, silhouettes, desaturation
- Return result

**Initialization:**
- Compile shader
- Create temporary textures
- Default parameters: voidStrength=8.0, edgeCrawl=6.0, crawlSpeed=4.0, fogDensity=5.0, fogScroll=3.0, threatGlow=7.0, shadowExpansion=5.0, desaturation=6.0, nearThreshold=3.0
- Initialize `_audio_reactor = None`

**Cleanup:**
- Delete temporary textures
- Delete shader
- Call `super().cleanup()`

---

## GPU Resources

| Resource | Type | Format | Dimensions | Lifecycle |
|----------|------|--------|------------|-----------|
| Shader program | GLSL | vertex + fragment | N/A | Init once |
| Temporary textures (optional) | GL_TEXTURE_2D | GL_RGBA8 | frame size | For intermediate renders |

**Memory Budget (640×480):**
- Shader: ~30-40 KB
- Temporary textures: ~1.8 MB (if used)
- Total: ~1.9 MB (moderate)

---

## Error Cases

| Error Condition | Response | Recovery |
|-----------------|----------|----------|
| No depth source | Use uniform depth (0.5) | Normal operation |
| Shader compilation fails | `ShaderCompilationError` | Log and abort |
| Invalid parameter | Clamp to range or raise `ValueError` | Document valid ranges |
| Audio reactor not set | Bass-driven effects disabled | Normal operation |

---

## Thread Safety

The effect is **not thread-safe**. All GPU operations, texture updates, and shader operations must occur on the thread with the OpenGL context. The effect updates state each frame; concurrent `process_frame()` calls will cause race conditions and corrupted rendering. Use one instance per thread or protect with a mutex.

---

## Performance

**Expected Frame Time (640×480):**
- Shader execution (void, edge detection, fog, silhouettes): ~5-12 ms
- Total: ~5-12 ms on GPU (moderate to heavy)

**Optimization Strategies:**
- Disable expensive features (edge crawling, fog)
- Use lower resolution for depth processing
- Simplify edge detection (no crawling, just darkening)
- Reduce shader complexity (fewer effects)

---

## Integration Checklist

- [ ] Depth source set and providing depth frames
- [ ] Void parameters configured
- [ ] Audio reactor set (optional, for bass-driven effects)
- [ ] `process_frame()` called each frame
- [ ] `cleanup()` called on shutdown

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init` | Effect initializes with default parameters |
| `test_set_parameter` | All parameters can be set and clamped |
| `test_get_parameter` | All parameters can be retrieved |
| `test_void_consumption` | Scene tends toward black based on void strength |
| `test_depth_modulated_void` | Near depth consumes more, far less |
| `test_edge_crawl` | Shadow entities crawl along depth edges |
| `test_crawl_speed` | Crawl speed affects animation |
| `test_dark_fog` | Fog rolls through depth layers |
| `test_fog_scroll` | Fog scrolls with time |
| `test_threat_glow` | Near objects have infrared edge glow |
| `test_shadow_expansion` | Bass expands shadows (if audio available) |
| `test_desaturation` | Color drain based on void strength |
| `test_near_threshold` | Near object detection threshold |
| `test_cleanup` | All GPU resources released |
| `test_no_memory_leak` | Repeated init/cleanup cycles don't leak |

**Minimum coverage:** 85%

---

## Definition of Done

- [ ] Spec reviewed
- [ ] All tests pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint checked
- [ ] Git commit with `[Phase-3] P3-VD71: depth_void_datamosh_effect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Legacy Code Mapping

Key references:
- `plugins/vdepth/depth_void_datamosh.py` — VJLive Original implementation
- `plugins/core/depth_void_datamosh/__init__.py` — VJLive-2 implementation
- `plugins/core/depth_void_datamosh/plugin.json` — Effect manifest
- `gl_leaks.txt` — Shows `DepthVoidDatamoshEffect` allocates `glGenTextures` and must free them

Design decisions inherited:
- Effect name: `depth_void_datamosh`
- Inherits from `Effect` (not `DepthEffect`)
- Uses depth texture for void mask, edge detection, fog layers
- Parameters: `voidStrength`, `edgeCrawl`, `crawlSpeed`, `fogDensity`, `fogScroll`, `threatGlow`, `shadowExpansion`, `desaturation`, `nearThreshold`
- Allocates GL resources: temporary textures for intermediate rendering
- Shader implements void consumption, edge crawling, fog, silhouettes, desaturation
- Method `_ensure_textures()` creates GPU resources
- Presets: "creeping_dread", "void_rush", "bass_void", "edge_crawlers", "fog_roll"

---

## Notes for Implementers

1. **Core Concept**: This effect creates an oppressive, menacing darkness that consumes the scene. Depth controls where the void is strongest (near objects become silhouettes, edges crawl with shadows, fog rolls through layers). It's designed for dark, industrial, bass-heavy music.

2. **Void Consumption**: The void is a force that pushes colors toward black. The strength is controlled by `voidStrength`. Near depth experiences more void.

3. **Threatening Silhouettes**: Near objects (depth < `nearThreshold`) become black silhouettes with an infrared (red/orange) edge glow. This creates a "threat detection" visual.

4. **Edge Crawling**: At depth boundaries (where depth gradient is high), shadow entities crawl along the edge. The crawling is animated with `sin(time * crawlSpeed)`.

5. **Dark Fog**: A fog effect that varies with depth and scrolls over time. The fog is darkest at certain depth layers, creating a "rolling" effect.

6. **Bass-Driven Shadow Expansion**: If an audio reactor is provided, bass frequencies drive shadow expansion — on kick drums, darkness physically pushes outward.

7. **Desaturation**: The void drains color, making the scene more monochrome. The desaturation is modulated by depth and void strength.

8. **Shader Uniforms**:
   ```glsl
   uniform sampler2D tex0;           // Input video
   uniform sampler2D depth_tex;      // Depth map
   uniform vec2 resolution;
   uniform float u_mix;
   uniform float time;
   uniform float bass;               // 0-1, from audio reactor (optional)
   
   uniform float voidStrength;       // 0-10
   uniform float edgeCrawl;          // 0-10
   uniform float crawlSpeed;         // 0-10
   uniform float fogDensity;         // 0-10
   uniform float fogScroll;          // 0-10
   uniform float threatGlow;         // 0-10
   uniform float shadowExpansion;    // 0-10
   uniform float desaturation;       // 0-10
   uniform float nearThreshold;      // 0-10
   ```

9. **Parameter Mapping** (0-10 → actual):
   - `voidStrength`: 0-10 → 0-1 (divide by 10)
   - `edgeCrawl`: 0-10 → 0-1 (divide by 10)
   - `crawlSpeed`: 0-10 → rad/s (multiply by some factor)
   - `fogDensity`: 0-10 → 0-1 (divide by 10)
   - `fogScroll`: 0-10 → speed (multiply by 0.1)
   - `threatGlow`: 0-10 → 0-1 (divide by 10)
   - `shadowExpansion`: 0-10 → 0-1 (divide by 10)
   - `desaturation`: 0-10 → 0-1 (divide by 10)
   - `nearThreshold`: 0-10 → 0-1 (divide by 10)

10. **PRESETS**:
    ```python
    PRESETS = {
        "creeping_dread": {
            "voidStrength": 6.0, "edgeCrawl": 8.0, "crawlSpeed": 2.0,
            "fogDensity": 4.0, "fogScroll": 1.0, "threatGlow": 5.0,
            "shadowExpansion": 3.0, "desaturation": 7.0, "nearThreshold": 3.0,
        },
        "void_rush": {
            "voidStrength": 10.0, "edgeCrawl": 10.0, "crawlSpeed": 10.0,
            "fogDensity": 10.0, "fogScroll": 10.0, "threatGlow": 10.0,
            "shadowExpansion": 10.0, "desaturation": 10.0, "nearThreshold": 2.0,
        },
        "bass_void": {
            "voidStrength": 9.0, "edgeCrawl": 5.0, "crawlSpeed": 3.0,
            "fogDensity": 6.0, "fogScroll": 2.0, "threatGlow": 8.0,
            "shadowExpansion": 10.0, "desaturation": 8.0, "nearThreshold": 4.0,
        },
        "edge_crawlers": {
            "voidStrength": 5.0, "edgeCrawl": 10.0, "crawlSpeed": 8.0,
            "fogDensity": 2.0, "fogScroll": 1.0, "threatGlow": 3.0,
            "shadowExpansion": 2.0, "desaturation": 6.0, "nearThreshold": 5.0,
        },
        "fog_roll": {
            "voidStrength": 7.0, "edgeCrawl": 3.0, "crawlSpeed": 1.0,
            "fogDensity": 10.0, "fogScroll": 10.0, "threatGlow": 4.0,
            "shadowExpansion": 4.0, "desaturation": 5.0, "nearThreshold": 6.0,
        },
    }
    ```

11. **Testing Strategy**:
    - Test with uniform depth: void should be uniform
    - Test with depth gradient: void should be stronger near
    - Test voidStrength: higher = darker
    - Test edgeCrawl: edges should have crawling shadows
    - Test crawlSpeed: animation speed
    - Test fogDensity: fog opacity
    - Test fogScroll: fog movement
    - Test threatGlow: near objects should glow
    - Test shadowExpansion: bass should expand shadows (if audio)
    - Test desaturation: color drain
    - Test nearThreshold: controls what is "near"

12. **Performance**: Moderate — multiple effects combined (void, edges, fog, silhouettes). Optimize by disabling some effects.

13. **Memory**: Light — no large buffers needed.

14. **Debug Mode**: Visualize void mask, edge detection, fog mask, threat regions.

---
-

## References

- Datamosh: https://en.wikipedia.org/wiki/Datamosh
- Depth buffer: https://en.wikipedia.org/wiki/Depth_buffer
- Fresnel effect: https://en.wikipedia.org/wiki/Fresnel_effect
- VJLive legacy: `plugins/vdepth/depth_void_datamosh.py`

---

## Implementation Tips

1. **Full Shader**:
   ```glsl
   #version 330 core
   in vec2 uv;
   out vec4 fragColor;
   
   uniform sampler2D tex0;
   uniform sampler2D depth_tex;
   uniform vec2 resolution;
   uniform float u_mix;
   uniform float time;
   uniform float bass;  // 0-1, optional
   
   uniform float voidStrength;       // 0-10
   uniform float edgeCrawl;          // 0-10
   uniform float crawlSpeed;         // 0-10
   uniform float fogDensity;         // 0-10
   uniform float fogScroll;          // 0-10
   uniform float threatGlow;         // 0-10
   uniform float shadowExpansion;    // 0-10
   uniform float desaturation;       // 0-10
   uniform float nearThreshold;      // 0-10
   
   // Pseudo-random
   float random(vec2 uv) {
       return fract(sin(dot(uv, vec2(12.9898, 78.233))) * 43758.5453);
   }
   
   void main() {
       vec3 color = texture(tex0, uv).rgb;
       float depth = texture(depth_tex, uv).r;
       
       // 1. Void consumption (tend toward black)
       float void_mask = 1.0 - depth;  // Near = more void
       float void_factor = voidStrength * 0.1 * void_mask;
       color = mix(color, vec3(0.0), void_factor);
       
       // 2. Threatening silhouettes (near objects)
       float near_mask = 1.0 - smoothstep(nearThreshold * 0.1, nearThreshold * 0.1 + 0.1, depth);
       if (near_mask > 0.0) {
           vec3 silhouette = vec3(0.0);
           
           // Infrared threat glow (red/orange edge)
           float edge = 1.0 - smoothstep(0.0, 0.1, depth);
           vec3 threat_glow = vec3(1.0, 0.2, 0.0) * edge * threatGlow * 0.1;
           
           color = mix(silhouette, color, 0.3);  // Mostly black
           color += threat_glow;
       }
       
       // 3. Edge crawling (shadow entities)
       float depth_grad = length(vec2(dFdx(depth), dFdy(depth)));
       float edge_threshold = 0.02;
       if (depth_grad > edge_threshold && edgeCrawl > 0.0) {
           vec2 edge_dir = normalize(vec2(dFdx(depth), dFdy(depth)));
           float crawl_offset = sin(time * crawlSpeed * 2.0) * 0.02;
           vec2 crawl_uv = uv + edge_dir * crawl_offset * edgeCrawl * 0.1;
           
           vec3 shadow_entity = texture(tex0, crawl_uv).rgb;
           // Desaturate and darken
           float gray = dot(shadow_entity, vec3(0.299, 0.587, 0.114));
           shadow_entity = vec3(gray) * 0.3;
           
           color = mix(color, shadow_entity, edgeCrawl * 0.1);
       }
       
       // 4. Dark fog rolling through layers
       if (fogDensity > 0.0) {
           float fog_offset = sin(time * fogScroll * 0.5) * 0.2;
           float fog_mask = smoothstep(0.3, 0.7, depth + fog_offset);
           vec3 fog_color = vec3(0.05, 0.02, 0.01);
           
           color = mix(color, fog_color, fog_mask * fogDensity * 0.1);
       }
       
       // 5. Bass-driven shadow expansion (if bass provided)
       if (shadowExpansion > 0.0 && bass > 0.0) {
           float expansion = bass * shadowExpansion * 0.1;
           float depth_mask = smoothstep(0.0, 0.3, depth);
           color = mix(color, vec3(0.0), depth_mask * expansion);
       }
       
       // 6. Desaturation
       if (desaturation > 0.0) {
           float gray = dot(color, vec3(0.299, 0.587, 0.114));
           float desat_factor = desaturation * 0.1 * void_mask;
           color = mix(color, vec3(gray), desat_factor);
       }
       
       fragColor = mix(texture(tex0, uv), vec4(color, 1.0), u_mix);
   }
   ```

2. **Python Implementation**:
   ```python
   class DepthVoidDatamoshEffect(Effect):
       def __init__(self):
           super().__init__("depth_void_datamosh", VOID_VERTEX, VOID_FRAGMENT)
           
           self.depth_source = None
           self.depth_frame = None
           self.audio_reactor = None
           
           self.parameters = {
               'voidStrength': 8.0,
               'edgeCrawl': 6.0,
               'crawlSpeed': 4.0,
               'fogDensity': 5.0,
               'fogScroll': 3.0,
               'threatGlow': 7.0,
               'shadowExpansion': 5.0,
               'desaturation': 6.0,
               'nearThreshold': 3.0,
           }
           
           self.shader = None
       
       def set_audio_reactor(self, reactor):
           """Set audio reactor for bass-driven effects."""
           self.audio_reactor = reactor
       
       def process_frame(self, frame):
           h, w = frame.shape[:2]
           
           # Update depth
           self._update_depth()
           
           # Get bass level if available
           bass = 0.0
           if self.audio_reactor:
               bass = self.audio_reactor.get_bass()  # 0-1
           
           # Render
           glBindFramebuffer(GL_FRAMEBUFFER, 0)
           
           self.shader.use()
           self._apply_uniforms(time, (w, h))
           
           # Bind textures
           glActiveTexture(GL_TEXTURE0)
           glBindTexture(GL_TEXTURE_2D, self.current_tex)
           glUniform1i(glGetUniformLocation(self.shader.program, "tex0"), 0)
           
           glActiveTexture(GL_TEXTURE1)
           glBindTexture(GL_TEXTURE_2D, self.depth_texture)
           glUniform1i(glGetUniformLocation(self.shader.program, "depth_tex"), 1)
           
           # Set bass uniform
           glUniform1f(glGetUniformLocation(self.shader.program, "bass"), bass)
           
           draw_fullscreen_quad()
           
           result = self._read_pixels()
           return result
   ```

3. **Edge Crawling**: The edge crawling uses the depth gradient to detect edges, then displaces the sample along the edge direction with a sinusoidal animation.

4. **Fog**: The fog uses a `smoothstep` mask that varies with depth and time (scrolling). The fog color is very dark (almost black with a slight brown tint).

5. **Threat Glow**: Near objects get a red/orange glow (infrared) on their edges, creating a "threat detection" visual.

6. **Bass-Driven Expansion**: If audio is available, the bass level expands shadows outward from depth edges, creating a physical response to low frequencies.

7. **Desaturation**: Color is drained based on the void mask (near depth) and void strength.

8. **Performance**: The shader does multiple texture fetches and gradient computations. Should be okay at 1080p but could be heavy on low-end GPUs.

9. **Testing**: Use a depth ramp and moving objects. Verify:
   - Near region is darker
   - Edges have crawling shadows
   - Fog rolls with time
   - Near objects have red glow
   - Bass causes shadow expansion (if audio)

10. **Future Extensions**:
    - Add multiple void layers
    - Add color tinting (void color)
    - Add audio reactivity to more parameters
    - Add motion-based void (void follows movement)

---

## Conclusion

The DepthVoidDatamoshEffect is a menacing, oppressive effect that consumes the scene in darkness. Using depth to drive void consumption, edge crawling, fog, and silhouettes, it creates a sense of supernatural menace perfect for dark, industrial, bass-heavy VJ performances. With audio reactivity, the void literally pulses with the music, making it a powerful tool for creating immersive, dark atmospheres.

---
