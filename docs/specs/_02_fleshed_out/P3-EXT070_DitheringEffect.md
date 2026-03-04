# P3-EXT070 DitheringEffect

**File naming:** `docs/specs/P3-EXT070_DitheringEffect.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT070 — DitheringEffect

**What This Module Does**

DitheringEffect transforms smooth gradients into textured, printable, mechanical patterns through structured noise algorithms. It reduces color depth by mapping continuous color values to discrete levels using various dithering techniques:

- **Bayer matrices**: Clean, grid-aligned, retro-digital patterns (2x2, 4x4, 8x8)
- **Halftone**: Print/newspaper feel with configurable dot shapes and angles
- **Blue noise**: Organic, film-like grain with procedural generation
- **Error diffusion**: Chaotic but accurate approximation of Floyd-Steinberg algorithm

With palette control, this effect can map any image to any color set, from 1-bit monochrome to custom palettes, making it essential for retro aesthetics, print simulation, and artistic color reduction.

**What This Module Does NOT Do**

- True Floyd-Steinberg error diffusion (cannot implement in fragment shader due to sequential dependency requirements)
- Real-time palette optimization or color quantization
- Vector-based halftone patterns (uses raster-based approximation)
- Multi-pass dithering for improved quality
- Color space conversion beyond RGB

---

## Detailed Behavior and Parameter Interactions

### Dither Core Parameters

| Parameter | Range | Physical Range | Description |
|-----------|-------|----------------|-------------|
| `dither_mode` | 0-10 | 0=bayer2, 2=bayer4, 4=bayer8, 6=halftone, 8=blue_noise, 10=error_diffuse | Selects dithering algorithm |
| `color_count` | 0-10 | 2 to 32 colors per channel | Number of discrete levels per color channel |
| `pattern_scale` | 0-10 | 0.5 to 8.0 | Scale of dither pattern (higher = larger patterns) |
| `threshold_bias` | 0-10 | -0.3 to 0.3 | Bias threshold for dithering decisions |

### Halftone Parameters

| Parameter | Range | Physical Range | Description |
|-----------|-------|----------------|-------------|
| `dot_shape` | 0-10 | 0=circle, 3=diamond, 5=line, 7=cross, 10=star | Shape of halftone dots |
| `dot_angle` | 0-10 | 0 to 180 degrees | Rotation angle of halftone screen |
| `dot_size_min` | 0-10 | 0 to 0.5 | Minimum dot size (relative to pixel) |
| `dot_size_max` | 0-10 | 0.3 to 1.0 | Maximum dot size (relative to pixel) |
| `cmyk_mode` | 0-10 | 0=grayscale, 5=RGB separate, 10=CMYK separate | Color channel separation for halftone |

### Palette Parameters

| Parameter | Range | Physical Range | Description |
|-----------|-------|----------------|-------------|
| `palette_mode` | 0-10 | 0=gray, 2=1bit, 4=gameboy, 6=cga, 8=custom, 10=rainbow | Palette selection algorithm |
| `palette_hue` | 0-10 | 0-1 hue for custom palette | Base hue for custom palettes |
| `palette_spread` | 0-10 | 0 to 1 | Color spread in custom palette |

### Post-Processing Parameters

| Parameter | Range | Physical Range | Description |
|-----------|-------|----------------|-------------|
| `pixel_grid` | 0-10 | 0 to 1 | Pixel grid overlay visibility |
| `color_bleed` | 0-10 | 0 to 1 | Color bleeding between pixels |
| `brightness` | 0-10 | 0.5 to 2.0 | Output brightness multiplier |
| `contrast_boost` | 0-10 | 0.5 to 3.0 | Contrast enhancement |
| `invert` | 0-10 | 0 to 1 | Invert output colors |

### Animation Parameters

| Parameter | Range | Physical Range | Description |
|-----------|-------|----------------|-------------|
| `animate_pattern` | 0-10 | 0 to 1 | Pattern animation speed |
| `rotate_pattern` | 0-10 | 0 to 1 | Pattern rotation speed |

### Parameter Interactions

- **Dither Mode + Color Count**: Higher color counts reduce the visual impact of dithering patterns. Low color counts (2-4) make patterns more visible and pronounced.
- **Halftone + CMYK Mode**: CMYK separation creates distinct dot patterns for each channel, producing realistic print simulation. RGB separation creates colored dot patterns.
- **Palette Mode + Color Count**: Palette modes override color count for specific aesthetic effects (e.g., Game Boy mode uses fixed 4-color palette regardless of color_count).
- **Pattern Scale + Animation**: Larger pattern scales combined with animation create flowing, organic patterns. Small scales with animation create fine-grained texture.
- **Brightness + Contrast + Invert**: These post-processing parameters affect the final output after dithering, allowing creative control over the final appearance.

---

## Public Interface

### Constructor
```python
DitheringEffect()
```
Initializes the effect with default parameters and loads the DITHERING_FRAGMENT shader.

### Methods

#### `set_parameter(name: str, value: float)`
Sets a parameter value. Parameters are mapped from 0-10 UI range to shader-specific ranges using `_map_param()`.

#### `get_parameter(name: str) -> float`
Returns the current value of a parameter.

#### `apply_uniforms(time: float, resolution: tuple, audio_reactor=None)`
Applies uniforms to the shader, including:
- Time-based animation parameters
- Resolution for pattern scaling
- Audio reactor data (if provided)
- All dithering parameters

#### `update_depth_data()`
Not used by this effect (no depth dependency).

#### `set_depth_source(source)`
Not used by this effect (no depth dependency).

---

## Inputs and Outputs

### Inputs
- **Texture0**: Source image (sampler2D)
- **Time**: Current time (float)
- **Resolution**: Output resolution (vec2)
- **AudioReactor**: Audio analysis data (optional)

### Outputs
- **FragColor**: Dithered output color (vec4)

### Data Flow
```
Source Image → Dithering Effect → Dithered Output
     ↓
  Audio Reactor → Pattern Animation
```

---

## Edge Cases and Error Handling

### Parameter Edge Cases

1. **Dither Mode Extremes**:
   - Mode 0 (Bayer 2x2): Very coarse dithering, may appear blocky
   - Mode 10 (Error Diffusion): Shader approximation may produce artifacts

2. **Color Count Limits**:
   - Count < 2: Invalid, defaults to 2
   - Count > 32: May produce banding instead of smooth dithering

3. **Pattern Scale**:
   - Scale < 0.5: Patterns may be too fine to see
   - Scale > 8.0: Patterns may be too large, causing moiré effects

4. **Halftone Parameters**:
   - Dot Size Min > Max: Invalid configuration, defaults to min < max
   - Dot Shape > 10: Defaults to circle

### Shader Edge Cases

1. **Division by Zero**:
   - `n_colors = pow(2.0, color_count)` → color_count=0 prevents division by zero
   - `scale = pattern_scale / 5.0` → pattern_scale=0 prevents division by zero

2. **Texture Sampling**:
   - UV coordinates outside [0,1] range are clamped by OpenGL
   - Missing texture0 defaults to black

3. **Matrix Indexing**:
   - Bayer matrix indices use `mod(p, N)` to prevent out-of-bounds access

### Performance Edge Cases

1. **High Resolution**:
   - 4K resolution with complex dithering may drop below 60fps
   - Blue noise mode is most computationally expensive

2. **Animation**:
   - High animation speeds with large pattern scales may cause visual artifacts
   - Time-based patterns may desynchronize across multiple instances

### Memory Management

- No dynamic memory allocation in shader
- All patterns are procedurally generated
- No texture uploads required for pattern generation

---

## Mathematical Formulations

### Dither Mode Mapping
```
dither_mode_value = dither_mode / 10.0
```
Maps 0-10 UI range to 0.0-1.0 for shader selection.

### Color Count Calculation
```
n_colors = pow(2.0, color_count)  // 2^color_count
```
Converts UI range to discrete color levels.

### Pattern Scale
```
scale = pattern_scale / 5.0  // 0.5 to 8.0
```
Maps UI range to physical pattern scale.

### Bayer Matrix Values
```
// 2x2 Bayer matrix
float bayer2(vec2 p) {
    vec2 i = floor(mod(p, 2.0));
    float m[4] = float[4](0.0, 2.0, 3.0, 1.0);
    return m[int(i.x + i.y * 2.0)] / 4.0;
}

// 4x4 Bayer matrix
float bayer4(vec2 p) {
    vec2 i = floor(mod(p, 4.0));
    float m[16] = float[16](0.0, 8.0, 2.0, 10.0, 12.0, 4.0, 14.0, 6.0, 3.0, 11.0, 1.0, 9.0, 15.0, 7.0, 13.0, 5.0);
    return m[int(i.x + i.y * 4.0)] / 16.0;
}

// 8x8 Bayer from recursive 4x4
float bayer8(vec2 p) {
    float b4 = bayer4(p);
    float b2 = bayer2(p / 4.0);
    return (b4 + b2 / 4.0);
}
```

### Halftone Dot Shapes
```
// Circle
step(length(p), size)

// Diamond
step(abs(p.x) + abs(p.y), size * 1.4)

// Line
step(abs(p.y), size * 0.5)

// Cross
max(step(abs(p.x), size * 0.3), step(abs(p.y), size * 0.3))

// Star
float angle = atan(p.y, p.x);
float r = length(p);
float star = cos(angle * 5.0) * 0.3 + 0.7;
step(r, size * star)
```

### Palette Color Mapping
```
// Grayscale
vec3(luma)

// 1-bit black & white
vec3(step(0.5, luma))

// Game Boy green (4-color)
float idx = floor(luma * 3.99);
if (idx < 1.0) return vec3(0.06, 0.22, 0.06);
if (idx < 2.0) return vec3(0.19, 0.38, 0.19);
if (idx < 3.0) return vec3(0.55, 0.67, 0.06);
return vec3(0.61, 0.74, 0.06);

// Custom hue palette
float idx = floor(luma * 4.99) / 5.0;
return hsv2rgb(vec3(fract(hue + idx * spread), 0.8 - idx * 0.3, idx + 0.1));
```

### Error Diffusion Approximation
```
// Approximate error diffusion using local neighborhood
float l_err = dot(texture(tex0, uv - vec2(tx.x, 0.0)).rgb, vec3(0.299, 0.587, 0.114));
float u_err = dot(texture(tex0, uv - vec2(0.0, tx.y)).rgb, vec3(0.299, 0.587, 0.114));

float accumulated_err = (l_err - floor(l_err * n_colors) / n_colors) * err_spread * 0.4375
                      + (u_err - floor(u_err * n_colors) / n_colors) * err_spread * 0.1875;

dithered = floor((color + accumulated_err + bias) * n_colors + 0.5) / n_colors;
```

---

## Performance Characteristics

### Computational Complexity
- **Bayer Dithering**: O(1) per pixel (simple matrix lookup)
- **Halftone**: O(1) per pixel (shape calculation)
- **Blue Noise**: O(1) per pixel (hash function)
- **Error Diffusion**: O(1) per pixel (texture sampling + math)

### Memory Bandwidth
- **Texture Reads**: 1-3 per pixel (depending on mode)
- **Texture Writes**: 1 per pixel (output)
- **Total**: ~60 MB/s at 1080p60 (4 bytes per pixel)

### GPU Utilization
- **Fragment Shader**: 100% utilization (pixel-dependent computation)
- **Texture Units**: 1 unit (source texture)
- **Arithmetic Intensity**: High (complex math per pixel)

### Performance Bottlenecks
1. **Blue Noise Mode**: Hash function is computationally expensive
2. **Error Diffusion**: Multiple texture samples per pixel
3. **High Resolution**: 4K resolution may drop below 60fps
4. **Animation**: Time-based patterns add computational overhead

### Optimization Opportunities
- **Bayer Mode**: Pre-compute matrices for faster lookup
- **Halftone**: Reduce shape complexity for performance
- **Blue Noise**: Use lower-quality hash for speed
- **Error Diffusion**: Reduce neighborhood sampling

---

## Test Plan

### Unit Tests (Python)
1. **Parameter Mapping**: Test `_map_param()` with edge values
2. **Shader Compilation**: Verify shader compiles without errors
3. **Parameter Validation**: Test invalid parameter values
4. **Preset Loading**: Test all presets load correctly

### Integration Tests (Python)
1. **Basic Dithering**: Test all dither modes with simple gradients
2. **Palette Modes**: Test all palette modes with color images
3. **Halftone Shapes**: Test all halftone shapes with uniform input
4. **Animation**: Test pattern animation over time

### Visual Regression Tests (Python)
1. **Bayer Comparison**: Compare output with reference Bayer patterns
2. **Halftone Accuracy**: Verify halftone dot placement
3. **Palette Mapping**: Test palette color accuracy
4. **Performance Regression**: Monitor frame rates at different resolutions

### Shader Tests (GLSL)
1. **Matrix Bounds**: Test Bayer matrix indexing with edge coordinates
2. **Division Safety**: Test division by zero protection
3. **Color Clamping**: Verify output stays in [0,1] range
4. **Texture Sampling**: Test UV coordinate handling

### Coverage Requirements
- **Python Code**: 85% line coverage
- **GLSL Shader**: 90% line coverage (manual testing)
- **Integration**: 80% scenario coverage

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-EXT070: DitheringEffect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES  

- **File**: `/home/happy/Desktop/claude projects/vjlive/plugins/vcore/dithering.py`
- **Class**: `DitheringEffect` (lines 337-356)
- **Shader**: `DITHERING_FRAGMENT` (full shader code provided)
- **Presets**: 5 predefined configurations (newspaper, game_boy, cga_retro, ordered_8x8, stipple_art)
- **Dependencies**: `core.effects.shader_base.Effect` base class

---

## Technical Notes

### Shader Architecture
- **Version**: GLSL 330 core
- **Inputs**: `uv`, `time`, `resolution`, `u_mix`
- **Uniforms**: 18 parameters controlling all aspects of dithering
- **Output**: `fragColor` with dithered result

### Parameter System
- All parameters use 0-10 normalized range
- `_map_param()` converts to shader-specific ranges
- Presets provide quick access to common configurations

### Performance Considerations
- Blue noise mode is most expensive due to hash function
- Error diffusion approximation trades accuracy for performance
- Halftone mode with CMYK separation is most complex

### WebGPU Migration Notes
- GLSL to WGSL conversion required
- Bind group layout for 18 parameters
- Uniform buffer for time, resolution, u_mix
- Texture binding for source image

### Known Limitations
- True Floyd-Steinberg not possible in fragment shader
- Error diffusion is approximation using local neighborhood
- Blue noise quality is lower than pre-computed blue noise textures

### Creative Applications
- Retro game aesthetics (Game Boy, CGA palettes)
- Print simulation (newspaper, halftone)
- Artistic color reduction
- Animated texture generation

---
