````markdown
# P6-QC06: Traveling Avatar Effect

> **Task ID:** `P6-QC06`
> **Priority:** P0 (Critical)
> **Source:** VJlive-2 (`plugins/vagent/agent_avatar.py`)
> **Class:** `TravelingAvatarEffect`
> **Phase:** Phase 6
> **Status:** ✅ Fleshed out

## Mission Context
Provide a complete, unambiguous Pass 2 specification for the `TravelingAvatarEffect`—
a dynamic sprite-based avatar renderer that animates agent personas (or custom sprites)
traveling along motion paths. The effect combines parameterized path generation (linear,
Bézier, sinusoidal), sprite animation (frame sequencing or morphing), and audio-reactive
scaling/color modulation. The objective is to document the exact motion math, animation
lifecycle, parameter remaps, presets, CPU fallback, and comprehensive tests for feature
parity with VJLive-2.

## Technical Requirements
- Implement as a VJLive3 generator plugin (produces visual output)
- Support smooth 60 FPS sprite animation and path following (Safety Rail 1)
- Achieve ≥80% unit/test coverage (Safety Rail 5)
- Keep core implementation <750 lines (Safety Rail 4)
- Graceful fallback to CPU sprite rendering when GPU unavailable (Safety Rail 7)
- No silent failures; emit clear error messages for invalid sprite or path configs

## Implementation Notes / Porting Strategy
1. Decouple sprite asset loading from path logic (fonts, textures, glyphs).
2. Implement motion paths via parametric equations (line, Bézier, sine wave).
3. Support framebuffer-based sprite rendering or quad-per-sprite instancing.
4. Provide deterministic NumPy-based CPU fallback (PIL rasterization).
5. Include audio reactivity hooks (color shift, scale pulse, speed modulation).
6. Profile path computation and sprite batch rendering to ensure 60 FPS.

## Public Interface
```python
class TravelingAvatarEffect(Effect):
    """
    Animated sprite avatar traveling along parameterized motion paths.
    
    Renders a sprite (agent persona, text, or custom glyph) that follows
    configurable motion paths with optional audio reactivity and animation
    frame sequencing.
    """

    def __init__(self, width: int = 1920, height: int = 1080, 
                 avatar_type: str = "agency", use_gpu: bool = True):
        """
        Initialize the traveling avatar effect.
        
        Args:
            width: Output width (pixels).
            height: Output height (pixels).
            avatar_type: Sprite asset set ("agency", "geometric", "abstract", "text").
            use_gpu: If True, use GPU rendering; else CPU rasterization.
        """
        super().__init__("Traveling Avatar", AVATAR_VERTEX_SHADER, 
                         AVATAR_FRAGMENT_SHADER)
        
        # Agent Metadata
        self.effect_category = "generator"
        self.effect_tags = ["avatar", "sprite", "motion", "animation"]
        self.features = ["SPRITE_ANIMATION", "PATH_FOLLOWING", "AUDIO_REACTIVE"]
        self.usage_tags = ["GENERATES_GEOMETRY", "ANIMATED"]
        
        self.avatar_type = avatar_type
        self.use_gpu = use_gpu
        self.sprite_data = None      # Texture atlas or sprite buffer
        self.path_buffer = None      # Precomputed path points
        self.path_length = 0         # Total arc length

        # Parameter ranges (all UI sliders 0.0—10.0)
        self._parameter_ranges = {
            'speed': (0.0, 10.0),              # pixels/frame or path parametrization
            'path_type': (0.0, 10.0),          # line, sine, bezier, spiral
            'amplitude': (0.0, 10.0),          # path oscillation magnitude
            'scale': (0.0, 10.0),              # sprite size
            'rotation': (0.0, 10.0),           # sprite rotation (0—360 degrees)
            'color_r': (0.0, 10.0),            # color channel red modulation
            'color_g': (0.0, 10.0),            # color channel green
            'color_b': (0.0, 10.0),            # color channel blue
            'alpha': (0.0, 10.0),              # sprite opacity
            'animation_speed': (0.0, 10.0),    # frame advance rate
        }

        # Default parameter values
        self.parameters = {
            'speed': 5.0,
            'path_type': 3.0,                  # Bézier (default middle ground)
            'amplitude': 3.0,
            'scale': 5.0,
            'rotation': 0.0,
            'color_r': 10.0,
            'color_g': 10.0,
            'color_b': 10.0,
            'alpha': 10.0,
            'animation_speed': 5.0
        }

        # Parameter descriptions
        self._parameter_descriptions = {
            'speed': "Avatar travel speed along path (0=static, 10=fast sweep)",
            'path_type': "Motion path shape: 0=line, 3=sine, 6=bezier, 10=spiral",
            'amplitude': "Oscillation magnitude (0=straight line, 10=wide wave)",
            'scale': "Sprite size (0=invisible, 5=normal, 10=huge)",
            'rotation': "Sprite rotation: 0=0°, 5=180°, 10=360° (wrap)",
            'color_r': "Red channel (0=off, 10=full)",
            'color_g': "Green channel (0=off, 10=full)",
            'color_b': "Blue channel (0=off, 10=full)",
            'alpha': "Opacity (0=invisible, 10=opaque)",
            'animation_speed': "Frame advance rate (0=frozen, 10=fast cycle)"
        }

        # Sweet spots for presets
        self._sweet_spots = {
            'speed': [2.0, 5.0, 8.0],
            'path_type': [1.0, 3.0, 6.0, 9.0],
            'amplitude': [0.0, 3.0, 6.0]
        }

    def render(self, tex_in: int = None, extra_textures: list = None, 
              chain = None) -> int:
        """
        Render animated avatar sprite to framebuffer.
        
        Args:
            tex_in: Optional background texture (for compositing).
            extra_textures: Optional (e.g., audio_texture for reactivity).
            chain: Rendering chain context.
            
        Returns:
            Framebuffer texture handle.
        """
        # Compute avatar position along path
        # Sample sprite frame from atlas or buffer
        # Apply color/scale/rotation transforms
        # Composite to output
        pass

    def compute_path(self, path_type: int, amplitude: float, 
                    t: float) -> tuple:
        """
        Compute avatar position along parametrized path.
        
        Args:
            path_type: 0=line, 3=sine, 6=bezier, 10=spiral.
            amplitude: Oscillation magnitude.
            t: Time parameter [0, 1].
            
        Returns:
            (x, y) position in normalized screen space.
        """
        # Compute path coordinates based on type
        pass

    def apply_uniforms(self, time: float, resolution: tuple, 
                      audio_reactor = None, semantic_layer = None):
        """
        Apply shader uniforms and update animation frame.
        
        Args:
            time: Current time (seconds).
            resolution: Tuple of (width, height).
            audio_reactor: Optional audio for reactivity.
            semantic_layer: Optional semantic input.
        """
        # Map UI parameters to internal values
        # Compute current path position
        # Update animation frame index
        # Bind uniforms to GPU
        pass
```

### Exposed Parameters, types and remaps (UI slider 0—10)
- `speed` (float, UI 0—10) → internal `S` = map_linear(x, 0,10, 0.0, 2.0)
  - Path traversal speed (cycles per second); 10 = complete path sweep every 0.5s
- `path_type` (float, UI 0—10) → internal `P` = round(x) for path selection:
  - 0: Straight line (left to right)
  - 1: Diagonal line (bottom-left to top-right)
  - 2: Vertical line (bottom to top)
  - 3: Sine wave (horizontal oscillation)
  - 4: Cosine wave (vertical bounce)
  - 5: Circle (orbital path)
  - 6: Bézier curve (configurable control points)
  - 7: Lissajous (complex parametric curve)
  - 8: Spiral (expanding/contracting helical path)
  - 9: Figure-8 (lemniscate shape)
  - 10: Random walk (procedural noise-based path)
- `amplitude` (float, UI 0—10) → internal `A` = map_linear(x, 0,10, 0.0, 0.5)
  - Path wave magnitude (screen-space fraction); 0.5 means ±25% screen width/height
- `scale` (float, UI 0—10) → internal `Z` = map_linear(x, 0,10, 0.1, 3.0)
  - Sprite size multiplier (1.0 = design size, 3.0 = 3x larger)
- `rotation` (float, UI 0—10) → internal `R` = x * 36.0 % 360.0
  - Sprite rotation in degrees (0—360, wrapping)
- `color_r`, `color_g`, `color_b` (float, UI 0—10) → internal RGB:
  - Each maps to 0.0—1.0 intensity; combined into final RGBA modulation
- `alpha` (float, UI 0—10) → internal `α` = map_linear(x, 0,10, 0.0, 1.0)
  - Sprite opacity
- `animation_speed` (float, UI 0—10) → internal `anim_fps` = map_linear(x, 0,10, 0.0, 30.0)
  - Frame advance rate (0 = frozen, 30 = 30 FPS for sprite animation)

Remap functions:
- `map_linear(v,a,b,c,d) = c + (d-c) * ((v-a)/(b-a))`

## Shader uniforms (authoritative names for GPU path)
- `uniform float speed;`              // path traversal speed
- `uniform int path_type;`            // path selection (0—10)
- `uniform float amplitude;`          // oscillation magnitude
- `uniform float scale;`              // sprite size
- `uniform float rotation;`           // rotation in radians
- `uniform vec3 color_modulation;`    // (r, g, b) [0,1]
- `uniform float alpha;`              // opacity
- `uniform int animation_frame;`      // current sprite frame index
- `uniform float time;`               // elapsed time for procedural paths
- `uniform sampler2D sprite_atlas;`   // sprite texture
- `uniform sampler2D audio_texture;`  // optional audio reactivity

## Effect Math (concise, GPU/CPU-consistent)

All math is written to be implementable identically in GLSL and NumPy.

### 1) Path Computation

Create a parametric path `p(t)` where `t ∈ [0, 1]` represents position along the
path (normalized time). The screen position is mapped from `p(t)`.

a) **Line Path** (`P = 0`):
```
p(t) = (t * 2 - 1, 0)      // left to right, centered vertically
```

b) **Sine Wave Path** (`P = 3`):
```
x(t) = t * 2 - 1
y(t) = A * sin(2π * t)     // oscillate vertically
p(t) = (x(t), y(t))
```

c) **Bézier Curve** (`P = 6`):
```
control_points = [(start_x, start_y), (cp1_x, cp1_y), (cp2_x, cp2_y), (end_x, end_y)]
p(t) = cubic_bezier(t, control_points)
// Using De Casteljau's algorithm for smooth interpolation
```

d) **Circle Path** (`P = 5`):
```
angle = t * 2π
center = (0.5, 0.5)
radius = 0.3
p(t) = center + radius * (cos(angle), sin(angle))
```

e) **Spiral Path** (`P = 8`):
```
angle = t * 4π              // 2 full rotations over path length
radius = A * t              // radius grows with t
p(t) = (0.5, 0.5) + radius * (cos(angle), sin(angle))
```

### 2) Speed and Timeline

Current position along path:
```
path_time = fmod(time * speed, 1.0)   // repeat [0,1]
position = p(path_time)               // compute on-path screen coordinates
```

Timeline wraps, so avatar loops continuously (if speed > 0).

### 3) Animation Frame Selection

Sprite atlas contains multiple frames (e.g., 8 frames of avatar animation).
Current frame index:
```
num_frames = 8  // or derived from asset atlas metadata
frame_index = floor(fmod(time * animation_speed, num_frames))
frame_uv = lookup_frame_uv(frame_index, sprite_atlas)  // UV coords for this frame
```

### 4) Color and Opacity

Final color is modulated by parameters:
```
color_out = sprite_color * color_modulation    // (r, g, b) [0,1]
alpha_out = sprite_alpha * alpha               // [0,1]
```

If audio_reactor available:
```
audio_energy = sample_audio_texture()
color_out *= (1.0 + audio_energy * 0.5)       // brighten with bass
alpha_out *= (1.0 - audio_energy * 0.2)       // subtle fade on peaks
```

### 5) Transform Application

In vertex/fragment:
```
// Rotate sprite around its center
rotated_vertex = rotate(vertex, rotation)

// Scale
scaled_vertex = rotated_vertex * scale

// Translate to path position
final_vertex = scaled_vertex + position * resolution

// Apply perspective/projection (standard OpenGL)
```

## Sprite Asset System

Avatar types and presets:
- **agency**: Stylized agent persona (humanoid silhouette)
- **geometric**: Colorful shapes (circles, triangles, stars)
- **abstract**: Neural network–inspired nodes and connections
- **text**: Rendered glyphs (agent name or phrase)

Each asset type has an associated sprite atlas (texture) with multiple animation frames
arranged in a grid (typically 8×1, 4×2, or 2×4 layout).

## CPU Fallback (NumPy sketch)

```python
def render_avatar_cpu(frame, time, speed, path_type, amplitude, scale, 
                      animation_speed, color_mod, alpha, sprite_atlas):
    """Rasterize traveling avatar to output frame."""
    
    # Compute path position
    path_time = (time * speed) % 1.0
    pos_x, pos_y = compute_path(path_type, amplitude, path_time)
    
    # Convert normalized [-1,1] to pixel coordinates
    px = int((pos_x + 1.0) / 2.0 * frame.shape[1])
    py = int((pos_y + 1.0) / 2.0 * frame.shape[0])
    
    # Select animation frame
    num_frames = sprite_atlas.shape[2]  // assume atlas is (H, W, num_frames, 3)
    frame_idx = int((time * animation_speed) % num_frames)
    sprite = sprite_atlas[:, :, frame_idx, :]
    
    # Resize sprite by scale factor
    sprite_h, sprite_w = sprite.shape[:2]
    new_h = int(sprite_h * scale)
    new_w = int(sprite_w * scale)
    sprite_resized = cv2.resize(sprite, (new_w, new_h))
    
    # Composit onto frame at position (px, py)
    # Handle out-of-bounds and alpha blending
    # ...
    
    return frame
```

## Presets (recommended)
- `Steady March`:
  - `speed` 3.0, `path_type` 0 (line), `amplitude` 0.0, `scale` 4.0,
    `rotation` 0.0, `color_r/g/b` 10.0, `alpha` 10.0, `animation_speed` 2.0
- `Dancing Wave`:
  - `speed` 4.0, `path_type` 3 (sine), `amplitude` 5.0, `scale` 5.0,
    `rotation` 5.0, `color_r/g/b` 10.0, `alpha` 10.0, `animation_speed` 6.0
- `Orbital Drift`:
  - `speed` 2.0, `path_type` 5 (circle), `amplitude` 3.0, `scale` 3.0,
    `rotation` 10.0, `color_r` 8.0, `color_g` 6.0, `color_b` 10.0,
    `alpha` 8.0, `animation_speed` 4.0
- `Spiral Ascent`:
  - `speed` 1.5, `path_type` 8 (spiral), `amplitude` 4.0, `scale` 6.0,
    `rotation` 10.0, `color_r` 10.0, `color_g` 5.0, `color_b` 8.0,
    `alpha` 10.0, `animation_speed` 3.0

## Edge Cases and Error Handling
- **Missing sprite atlas**: Fall back to solid-color quad (white rectangle).
  Emit warning in logs.
- **Invalid path_type**: Clamp to valid range [0, 10].
- **Off-screen rendering**: Sprite may travel partially off-screen; allow clipping
  (do not re-center).
- **Animation frame out-of-bounds**: Wrap frame index via modulo.
- **Audio input unavailable**: Render without audio reactivity; skip bass modulation.
- **NaN in position**: Guard against division by zero in Bézier or spiral math.

## Test Plan (minimum ≥80% coverage)
- `test_path_computation_line` — line path produces x ∈ [-1, 1], y = 0
- `test_path_computation_sine` — sine wave oscillates at correct amplitude
- `test_path_computation_circle` — circle path maintains constant radius
- `test_speed_modulation` — speed parameter affects traversal rate
- `test_animation_frame_cycling` — frames advance at correct rate
- `test_color_modulation` — RGB channels independently apply
- `test_scale_bounds` — scale parameter produce valid [0.1, 3.0] multipliers
- `test_rotation_wrapping` — rotation values wrap at 360° boundary
- `test_alpha_blending` — alpha compositing correct at boundaries [0, 1]
- `test_sprite_lookup` — frame UV coordinates map to correct atlas regions
- `test_cpu_vs_gpu_parity` — CPU and GPU output match within tolerance
- `test_missing_sprite_fallback` — render without crashing if atlas unavailable
- `test_preset_renderable` — all presets render without error at 60 FPS

## Verification Checkpoints
- [ ] `TravelingAvatarEffect` class registers with plugin registry
- [ ] All parameters (0—10 UI sliders) bind correctly to path/animation logic
- [ ] Path computation produces valid normalized screen coordinates
- [ ] Sprite atlas loads and frames animate smoothly
- [ ] CPU fallback produces viewable output (headless mode)
- [ ] Presets load and render at intended visual styles
- [ ] Tests pass with ≥80% code coverage
- [ ] 60 FPS sustained at 1080p with concurrent audio reactivity
- [ ] No safety rail violations

## Implementation Handoff Notes
- Sprite atlas structure: Recommend 8-frame horizontal strip (2048×256 texture for
  256×256 sprite).
- Path precomputation: If paths are expensive, cache p(t) for common path types
  at t = [0, 0.01, 0.02, ..., 1.0] (100 samples).
- Audio reactivity: Optional; provide hooks but make them graceful no-ops if
  audio_reactor is None.
- Agent persona customization: Support loading multiple avatar types via asset
  registry (config file or manifest).

## Resources
- Reference (sprite animation): Common VJ conventions (MilkdropWaveform, Resolume avatars)
- Parametric paths: Bézier curve libraries, lemniscate/Lissajous math references
- Performance: Profile sprite batch rendering and path caching via GPU profiler

````
