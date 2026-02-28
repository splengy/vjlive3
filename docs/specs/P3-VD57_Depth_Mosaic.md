# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-VD57_Depth_Mosaic.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD57 — DepthMosaicEffect

## Description

The DepthMosaicEffect creates a depth-controlled video tessellation where the size of mosaic tiles varies based on depth. Near objects are rendered with large, bold tiles, while far objects display fine, detailed tiles. This creates a stylized effect that emphasizes depth relationships through varying levels of detail. The effect includes configurable cell size range, gap styling, color quantization, and optional tile rotation based on depth.

This effect is ideal for creating artistic, low-poly, or pixelated looks that respect scene depth. It's perfect for VJ performances that need a distinctive visual style—turning performers into large-tiled foreground elements against finely-tiled backgrounds. The depth-based tile sizing creates natural depth perception even without other depth cues.

## What This Module Does

- Tessellates video into a grid of tiles (mosaic)
- Tile size controlled by depth: near = large, far = small
- Configurable cell size min/max range
- Gap between tiles with customizable color
- Optional tile rotation based on depth
- Optional color quantization (posterization)
- Depth inversion option (swap near/far behavior)
- GPU-accelerated fragment shader

## What This Module Does NOT Do

- Does NOT provide 3D geometry (2D tessellation only)
- Does NOT include animation/tweening between tile sizes
- Does NOT provide CPU fallback (GPU required)
- Does NOT store persistent state across sessions
- Does NOT support non-uniform tile shapes (only squares/rectangles)
- Does NOT include audio reactivity (may be added later)

---

## Detailed Behavior

### Depth-Controlled Tessellation

1. **Sample depth**: Get depth value `d` from depth texture
2. **Normalize depth**: Map depth to 0-1 range based on effect's depth understanding
3. **Compute cell size**: Interpolate between `cellSizeMin` and `cellSizeMax`:
   ```
   cell_size = mix(cellSizeMax, cellSizeMin, d_norm)
   ```
   - Near (d_norm ≈ 0) → `cellSizeMin` (large tiles)
   - Far (d_norm ≈ 1) → `cellSizeMax` (small tiles)
4. **Determine tile coordinates**: Find which tile the current pixel belongs to:
   ```
   tile_x = floor(uv.x * resolution / cell_size)
   tile_y = floor(uv.y * resolution / cell_size)
   tile_center = (tile_x + 0.5, tile_y + 0.5) * cell_size / resolution
   ```
5. **Sample tile color**: Average or sample center of tile:
   ```
   color = texture(tex0, tile_center)
   ```
6. **Apply gaps**: If `gapWidth > 0`, draw gap color at tile edges
7. **Optional rotation**: Rotate tile based on depth (if `rotateByDepth > 0`)
8. **Optional color quantization**: Reduce color depth
9. **Final mix**: Blend with original video

### Tile Sampling Strategies

- **Center sampling**: Use tile center pixel (fast, but may alias)
- **Average sampling**: Average all pixels in tile (expensive, high quality)
- **Random sampling**: Random pixel within tile (cheap, good enough)

The legacy likely uses center sampling for performance.

### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `cellSizeMin` | float | 1.0 | 0.0-10.0 | Minimum cell size (pixels) for far objects |
| `cellSizeMax` | float | 7.0 | 0.0-10.0 | Maximum cell size (pixels) for near objects |
| `tileStyle` | float | 0.0 | 0.0-10.0 | Tile shape/style (0=square, 1=hex, etc.) |
| `depthInvert` | float | 0.0 | 0.0-10.0 | Invert depth mapping (near=small, far=large) |
| `gapWidth` | float | 2.0 | 0.0-10.0 | Gap between tiles (pixels) |
| `gapColor` | float | 0.0 | 0.0-10.0 | Gap color (grayscale 0-10 → 0-1) |
| `colorQuantize` | float | 0.0 | 0.0-10.0 | Color bit depth reduction |
| `rotateByDepth` | float | 0.0 | 0.0-10.0 | Rotate tiles based on depth |

**Inherited from Effect**: `u_mix`, `resolution`

---

## Public Interface

```python
class DepthMosaicEffect(Effect):
    def __init__(self) -> None: ...
    def set_depth_source(self, source) -> None: ...
    def update_depth_data(self) -> None: ...
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
| **Output** | `np.ndarray` | Mosaic output (HxWxC, RGB) |

---

## State Management

**Persistent State:**
- `_depth_source: Optional[DepthSource]` — Connected depth source
- `_depth_frame: Optional[np.ndarray]` — Latest depth frame
- `_depth_texture: int` — GL texture for depth data
- `_parameters: dict` — Mosaic parameters
- `_shader: ShaderProgram` — Compiled shader

**Per-Frame:**
- Update depth data from source
- Upload depth texture
- Set shader uniforms
- Render mosaic effect
- Return result

**Initialization:**
- Create depth texture (lazy)
- Compile shader
- Default parameters: cellSizeMin=1.0, cellSizeMax=7.0, tileStyle=0.0, depthInvert=0.0, gapWidth=2.0, gapColor=0.0, colorQuantize=0.0, rotateByDepth=0.0

**Cleanup:**
- Delete depth texture
- Delete shader
- Call `super().cleanup()`

---

## GPU Resources

| Resource | Type | Format | Dimensions | Lifecycle |
|----------|------|--------|------------|-----------|
| Depth texture | GL_TEXTURE_2D | GL_RED, GL_UNSIGNED_BYTE | depth_frame size | Updated each frame |
| Shader program | GLSL | vertex + fragment | N/A | Init once |

**Memory Budget (640×480):**
- Depth texture: 307,200 bytes
- Shader: ~20-30 KB
- Total: ~0.3 MB

---

## Error Cases

| Error Condition | Response | Recovery |
|-----------------|----------|----------|
| Depth frame missing | Use uniform depth (0.5) | Normal operation |
| Depth texture upload fails | `RuntimeError("GPU error")` | Check GL errors |
| Shader compilation fails | `ShaderCompilationError` | Log and abort |
| Invalid parameter | Clamp to range or raise `ValueError` | Document valid ranges |

---

## Thread Safety

The effect is **not thread-safe**. All GPU operations and texture updates must occur on the thread with the OpenGL context. The depth texture is updated each frame, and the shader is used for rendering, so concurrent `process_frame()` calls will cause race conditions. Use one instance per thread or protect with a mutex.

---

## Performance

**Expected Frame Time (640×480):**
- Depth texture upload: ~0.5-1 ms
- Shader execution (tessellation + gaps + effects): ~2-5 ms
- Total: ~2.5-6 ms on GPU

**Optimization Strategies:**
- Increase `cellSizeMin` (fewer, larger tiles = faster)
- Disable expensive features (gap, rotation, quantization)
- Use simpler tile sampling (center vs average)
- Cache depth texture if depth hasn't changed
- Use compute shader for parallel tile computation

---

## Integration Checklist

- [ ] Depth source set and providing depth frames
- [ ] Mosaic parameters configured (cell sizes, gap, etc.)
- [ ] `process_frame()` called each frame
- [ ] `cleanup()` called on shutdown

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init` | Effect initializes with default parameters |
| `test_set_parameter` | All parameters can be set and clamped |
| `test_get_parameter` | All parameters can be retrieved |
| `test_cell_size_mapping` | Depth maps to correct cell size range |
| `test_depth_invert` | Inverts near/far cell size relationship |
| `test_gap_rendering` | Gaps appear between tiles with correct color |
| `test_color_quantization` | Reduces color depth when enabled |
| `test_rotation_by_depth` | Tiles rotate based on depth |
| `test_tile_style` | Different tile styles render correctly |
| `test_process_frame_no_depth` | Falls back to uniform cell size |
| `test_process_frame_with_depth` | Cell size varies with depth |
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
- [ ] Git commit with `[Phase-3] P3-VD57: depth_mosaic_effect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Legacy Code Mapping

Key references:
- `plugins/vdepth/depth_mosaic.py` — VJLive Original implementation
- `plugins/core/depth_mosaic/__init__.py` — VJLive-2 implementation
- `plugins/core/depth_mosaic/plugin.json` — Effect manifest
- `gl_leaks.txt` — Shows `DepthMosaicEffect` allocates `glGenTextures` and must free them
- `assets/gists/depth_mosaic.json` — Gist documentation

Design decisions inherited:
- Effect name: `depth_mosaic`
- Inherits from `Effect` (not `DepthEffect`)
- Uses depth texture for cell size modulation
- Parameters: `cellSizeMin`, `cellSizeMax`, `tileStyle`, `depthInvert`, `gapWidth`, `gapColor`, `colorQuantize`, `rotateByDepth`
- Allocates GL resources: depth texture
- Shader implements depth-controlled tessellation with gaps and optional effects
- Near objects = large tiles, far objects = small tiles (inverted with `depthInvert`)

---

## Notes for Implementers

1. **Core Concept**: The effect divides the screen into a grid of tiles (cells). The size of each tile is determined by the depth at that location. Near = large tiles (low detail), far = small tiles (high detail). This is the opposite of typical LOD systems where near = high detail.

2. **Cell Size Calculation**:
   ```glsl
   float depth = texture(depth_tex, uv).r;
   float d_norm = depth;  // Already 0-1 or normalize
   if (depthInvert > 0.0) {
       d_norm = 1.0 - d_norm;
   }
   float cell_size = mix(cellSizeMax, cellSizeMin, d_norm);
   ```
   Note: `cellSizeMin` and `cellSizeMax` are in pixel units. They represent the size of the tile in screen space.

3. **Tile Coordinate Computation**:
   ```glsl
   vec2 tile_index = floor(uv * resolution / cell_size);
   vec2 tile_center = (tile_index + 0.5) * cell_size / resolution;
   ```
   This finds which tile the current pixel belongs to, then computes the center of that tile to sample the source image.

4. **Gap Rendering**: If `gapWidth > 0`, draw a gap (border) around each tile:
   ```glsl
   vec2 tile_uv = fract(uv * resolution / cell_size);  // 0-1 within tile
   float edge = step(1.0 - gap_width_frac, tile_uv.x) + step(1.0 - gap_width_frac, tile_uv.y) +
                step(tile_uv.x, gap_width_frac) + step(tile_uv.y, gap_width_frac);
   if (edge > 0.0) {
       color = gap_color;
   }
   ```
   Where `gap_width_frac = gapWidth / cell_size`.

5. **Color Quantization**: Reduce color bit depth:
   ```glsl
   if (colorQuantize > 0.0) {
       float levels = pow(2.0, 8.0 - colorQuantize * 0.5);  // 256 down to 2
       color.rgb = floor(color.rgb * levels) / levels;
   }
   ```

6. **Tile Rotation**: If `rotateByDepth > 0.0`, rotate the tile sampling coordinates based on depth:
   ```glsl
   float angle = depth * rotateByDepth * 6.28;  // 0-2π
   mat2 rot = mat2(cos(angle), -sin(angle), sin(angle), cos(angle));
   vec2 rotated_uv = rot * (uv - tile_center) + tile_center;
   color = texture(tex0, rotated_uv);
   ```

7. **Tile Style**: The `tileStyle` parameter could select between different tile shapes:
   - 0 = square (default)
   - 1 = hexagonal (requires different tiling math)
   - 2 = triangular
   - 3 = random/voronoi
   For simplicity, implement square only unless legacy specifies otherwise.

8. **Shader Uniforms**:
   ```glsl
   uniform sampler2D tex0;        // Input frame
   uniform sampler2D depth_tex;   // Depth texture
   uniform vec2 resolution;
   uniform float u_mix;
   
   uniform float cellSizeMin;      // in pixels
   uniform float cellSizeMax;      // in pixels
   uniform float tileStyle;        // 0=square
   uniform float depthInvert;      // 0 or 1
   uniform float gapWidth;         // in pixels
   uniform vec3 gapColor;          // RGB
   uniform float colorQuantize;    // 0-10
   uniform float rotateByDepth;    // 0-10
   ```

9. **Parameter Mapping**:
   - `cellSizeMin`, `cellSizeMax`: 0-10 → pixel values (maybe scale: 0→1px, 10→20px or similar)
   - `gapWidth`: 0-10 → pixel values (0→0px, 10→10px)
   - `gapColor`: 0-10 → grayscale (0=black, 10=white) or RGB if extended
   - `colorQuantize`: 0-10 → levels reduction
   - `rotateByDepth`: 0-10 → rotation multiplier (radians per depth unit)
   - `tileStyle`: 0-10 → enum (only 0 implemented initially)
   - `depthInvert`: 0-10 → 0 or 1 (threshold >0)

10. **Pixel-Perfect Tiling**: Ensure tiles align to pixel boundaries to avoid subpixel gaps. Use `floor()` to compute tile indices, not `round()`.

11. **Edge Cases**: At screen edges, tiles may be partial. Clamp sampling to edge or extend with border color.

12. **Performance**: The shader is relatively fast. Main cost is texture fetches per pixel (1 for depth, 1 for source). With large tiles, cache locality improves.

13. **PRESETS**:
    ```python
    PRESETS = {
        "clean": {
            "cellSizeMin": 1.0, "cellSizeMax": 1.0,  # Uniform tiny tiles
            "tileStyle": 0.0, "depthInvert": 0.0,
            "gapWidth": 0.0, "gapColor": 0.0,
            "colorQuantize": 0.0, "rotateByDepth": 0.0,
        },
        "mild_mosaic": {
            "cellSizeMin": 3.0, "cellSizeMax": 5.0,
            "tileStyle": 0.0, "depthInvert": 0.0,
            "gapWidth": 1.0, "gapColor": 0.0,
            "colorQuantize": 0.0, "rotateByDepth": 0.0,
        },
        "bold_foreground": {
            "cellSizeMin": 10.0, "cellSizeMax": 2.0,  # Near = large
            "tileStyle": 0.0, "depthInvert": 0.0,
            "gapWidth": 3.0, "gapColor": 0.0,
            "colorQuantize": 2.0, "rotateByDepth": 0.0,
        },
        "inverted": {
            "cellSizeMin": 2.0, "cellSizeMax": 10.0,  # Near = small
            "tileStyle": 0.0, "depthInvert": 1.0,
            "gapWidth": 2.0, "gapColor": 0.5,
            "colorQuantize": 3.0, "rotateByDepth": 0.0,
        },
        "rotating_tiles": {
            "cellSizeMin": 4.0, "cellSizeMax": 6.0,
            "tileStyle": 0.0, "depthInvert": 0.0,
            "gapWidth": 1.0, "gapColor": 0.0,
            "colorQuantize": 0.0, "rotateByDepth": 5.0,
        },
    }
    ```

14. **Testing Strategy**: Create depth ramps and verify:
    - Near region has large tiles
    - Far region has small tiles
    - Inverting swaps the relationship
    - Gaps appear with correct width and color
    - Color quantization reduces colors
    - Rotation spins tiles based on depth

15. **Future Extensions**:
    - Add hexagonal/other tile shapes
    - Add tile color averaging (instead of center sampling)
    - Add animated tile size (pulsing)
    - Add audio reactivity to cell size
    - Add depth-based tile color tinting

---

## Easter Egg Idea

When `cellSizeMin` is set exactly to 6.66, `cellSizeMax` to exactly 6.66, `gapWidth` to exactly 6.66, `colorQuantize` to exactly 6.66, `rotateByDepth` to exactly 6.66, and the depth map contains a perfect torus, the mosaic enters a "tessellation singularity" where all tiles become perfect 6.66×6.66 pixel squares that rotate in synchronized harmony at exactly 6.66 Hz, the gaps glow with a 6.66% transparency revealing a hidden layer beneath, and the color quantization creates exactly 6.66 distinct color levels that form a perfect dithering pattern. VJs report seeing "the matrix of reality" where each tile is a window into a deeper layer of existence.

---

## References

- Tessellation: https://en.wikipedia.org/wiki/Tessellation
- Mosaic: https://en.wikipedia.org/wiki/Mosaic
- Pixelation: https://en.wikipedia.org/wiki/Pixelation
- Depth perception: https://en.wikipedia.org/wiki/Depth_perception
- VJLive legacy: `plugins/vdepth/depth_mosaic.py`

---

## Implementation Tips

1. **Full Shader**:
   ```glsl
   #version 330 core
   in vec2 uv;
   out vec4 fragColor;
   
   uniform sampler2D tex0;        // Input frame
   uniform sampler2D depth_tex;   // Depth texture
   uniform vec2 resolution;
   uniform float u_mix;
   uniform float time;
   
   uniform float cellSizeMin;      // in pixels
   uniform float cellSizeMax;      // in pixels
   uniform float tileStyle;        // 0=square
   uniform float depthInvert;      // 0 or 1
   uniform float gapWidth;         // in pixels
   uniform vec3 gapColor;          // RGB 0-1
   uniform float colorQuantize;    // 0-10
   uniform float rotateByDepth;    // 0-10
   
   void main() {
       vec4 source = texture(tex0, uv);
       float depth = texture(depth_tex, uv).r;
       
       // Invert depth if requested
       if (depthInvert > 0.0) {
           depth = 1.0 - depth;
       }
       
       // Compute cell size for this depth
       float cell_size = mix(cellSizeMax, cellSizeMin, depth);
       cell_size = max(cell_size, 1.0);  // Minimum 1 pixel
       
       // Tile coordinates
       vec2 tile_index = floor(uv * resolution / cell_size);
       vec2 tile_center = (tile_index + 0.5) * cell_size / resolution;
       
       // Optional rotation by depth
       if (rotateByDepth > 0.0) {
           float angle = depth * rotateByDepth * 6.28318;  // 0-2π
           float cos_a = cos(angle);
           float sin_a = sin(angle);
           vec2 offset = uv - tile_center;
           vec2 rotated = vec2(
               offset.x * cos_a - offset.y * sin_a,
               offset.x * sin_a + offset.y * cos_a
           );
           uv = rotated + tile_center;
       } else {
           uv = tile_center;
       }
       
       // Sample source at tile center (or rotated position)
       vec3 color = texture(tex0, uv).rgb;
       
       // Color quantization
       if (colorQuantize > 0.0) {
           float levels = pow(2.0, 8.0 - colorQuantize * 0.5);
           color = floor(color * levels) / levels;
       }
       
       // Gap rendering
       if (gapWidth > 0.0) {
           vec2 tile_uv = fract(uv * resolution / cell_size);
           float gap_frac = gapWidth / cell_size;
           float edge = 0.0;
           edge += step(1.0 - gap_frac, tile_uv.x);
           edge += step(1.0 - gap_frac, tile_uv.y);
           edge += step(gap_frac, tile_uv.x) * step(tile_uv.x, gap_frac);  // Actually need to check if within gap region
           edge += step(gap_frac, tile_uv.y) * step(tile_uv.y, gap_frac);
           // Simpler: check if near any edge
           float margin = gap_frac * 0.5;
           if (tile_uv.x < margin || tile_uv.x > 1.0 - margin ||
               tile_uv.y < margin || tile_uv.y > 1.0 - margin) {
               color = gapColor;
           }
       }
       
       // Final mix
       fragColor = mix(source, vec4(color, 1.0), u_mix);
   }
   ```

2. **Python Implementation**:
   ```python
   class DepthMosaicEffect(Effect):
       def __init__(self, name: str = "Depth Mosaic"):
           super().__init__(name, MOSAIC_FRAGMENT)
           
           self.depth_source = None
           self.depth_frame = None
           self.depth_texture = 0
           
           self.parameters = {
               'cellSizeMin': 1.0,
               'cellSizeMax': 7.0,
               'tileStyle': 0.0,
               'depthInvert': 0.0,
               'gapWidth': 2.0,
               'gapColor': 0.0,
               'colorQuantize': 0.0,
               'rotateByDepth': 0.0,
           }
           
           self.shader = None
       
       def _ensure_resources(self, width, height):
           if self.depth_texture == 0:
               self.depth_texture = glGenTextures(1)
               glBindTexture(GL_TEXTURE_2D, self.depth_texture)
               glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
               glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
               glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
               glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
               
           if self.shader is None:
               self.shader = ShaderProgram(vertex_src, fragment_src)
   ```

3. **Parameter Clamping**:
   ```python
   def set_parameter(self, name, value):
       if name in ('cellSizeMin', 'cellSizeMax', 'gapWidth'):
           self.parameters[name] = max(0.0, min(10.0, value))
       elif name == 'colorQuantize':
           self.parameters[name] = max(0.0, min(10.0, value))
       elif name == 'rotateByDepth':
           self.parameters[name] = max(0.0, min(10.0, value))
       elif name in ('tileStyle', 'depthInvert'):
           self.parameters[name] = max(0.0, min(10.0, value))
   ```

4. **Gap Color**: The legacy uses `gapColor` as a float 0-10. Map to RGB grayscale:
   ```python
   gap_rgb = vec3(gapColor / 10.0)
   ```

5. **Process Frame**:
   ```python
   def process_frame(self, frame):
       h, w = frame.shape[:2]
       self._ensure_resources(w, h)
       
       # Upload depth
       self._upload_depth_texture()
       
       # Render
       glBindFramebuffer(GL_FRAMEBUFFER, 0)
       
       self.shader.use()
       self._apply_uniforms(time, (w, h))
       
       # Bind textures
       glActiveTexture(GL_TEXTURE0)
       glBindTexture(GL_TEXTURE_2D, self._texture_from_array(frame))
       self.shader.set_uniform("tex0", 0)
       
       glActiveTexture(GL_TEXTURE1)
       glBindTexture(GL_TEXTURE_2D, self.depth_texture)
       self.shader.set_uniform("depth_tex", 1)
       
       # Draw fullscreen quad
       draw_fullscreen_quad()
       
       result = glReadPixels(0, 0, w, h, GL_RGBA, GL_UNSIGNED_BYTE)
       
       return result
   ```

6. **Tile Sampling**: The simplest approach is to sample the tile center. For better quality, you could average the tile, but that's expensive. Center sampling is acceptable for mosaic style.

7. **Gap Width Handling**: The gap is drawn in the fragment shader by checking if the current pixel is within `gapWidth` pixels of a tile boundary. Use `fract()` to get position within tile.

8. **Depth Invert**: When `depthInvert > 0`, swap the mapping so near objects get small tiles and far objects get large tiles.

9. **Testing**: Create a depth map with a gradient from 0 to 1. Verify that cell size changes smoothly across the gradient. Test with a depth map containing a circle (near) on background (far) to see distinct tile sizes.

10. **Performance**: The shader does a few divisions and texture lookups. It's relatively fast. The main performance factor is the number of tiles (smaller cells = more tiles = more texture fetches? Actually same fetches per pixel, but more cache misses if tiles are small).

---

## Conclusion

The DepthMosaicEffect creates a stylized, depth-aware tessellation that turns video into a mosaic where tile size encodes depth. Large tiles for near objects and small tiles for far objects create a unique visual that emphasizes depth relationships. With options for gaps, color quantization, and tile rotation, it's a versatile tool for artistic VJ performances.

---
>>>>>>> REPLACE