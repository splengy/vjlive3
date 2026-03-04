# P3-EXT096_LUTGradingEffect.md

## Task: P3-EXT096 — LUTGradingEffect

## Detailed Behavior and Parameter Interactions

### Core Architecture
```python
class LUTGradingEffect(Effect):
    """LUT-based color grading with .cube file support and built-in presets.
    
    Features:
    - Load .cube LUT files (1D and 3D)
    - Built-in procedural presets (teal_orange, film_noir, vintage, cinematic)
    - Lift/Gamma/Gain color correction
    - Temperature (warm/cool) adjustment
    - Adjustable LUT intensity mix
    """
```

### Parameter System
```python
# Available built-in presets
PRESETS = ["identity", "teal_orange", "film_noir", "vintage", "cinematic"]

def __init__(self):
    super().__init__("lut_grading", LUT_GRADING_FRAGMENT)
    self.parameters = {
        "lut_intensity": 10.0,   # Full LUT (10 = 100%)
        "lift": 5.0,             # Neutral (5 = no lift)
        "gamma": 5.0,            # Neutral gamma (~1.0)
        "gain": 5.0,             # Neutral gain (1.0)
        "temperature": 5.0,      # Neutral temperature
    }
```

### Shader Implementation
```glsl
#version 330 core
in vec2 uv;
out vec4 fragColor;
uniform sampler2D tex0;
uniform sampler3D lut_texture;
uniform float time;
uniform vec2 resolution;
uniform float u_mix;

uniform float lut_intensity;    // 0-10 → 0-1 LUT blend
uniform float lift;             // 0-10 → -0.2 to 0.2 shadow lift
uniform float gamma;            // 0-10 → 0.2 to 3.0 gamma
uniform float gain;             // 0-10 → 0.5 to 2.0 gain
uniform float temperature;      // 0-10 → -0.3 to 0.3 warm/cool shift

void main() {
    vec4 input_color = texture(tex0, uv);
    
    // Remap parameters
    float intensity = lut_intensity / 10.0;
    float lift_val = (lift / 10.0 - 0.5) * 0.4;
    float gamma_val = mix(0.2, 3.0, gamma / 10.0);
    float gain_val = mix(0.5, 2.0, gain / 10.0);
    float temp = (temperature / 10.0 - 0.5) * 0.6;
    
    // Apply lift/gamma/gain BEFORE LUT
    vec3 color = input_color.rgb;
    
    // Lift (shadows)
    color = color + vec3(lift_val);
    
    // Gain (highlights)
    color = color * gain_val;
    
    // Gamma (midtones)
    color = pow(max(color, vec3(0.0)), vec3(1.0 / gamma_val));
    
    // Clamp for LUT lookup
    color = clamp(color, 0.0, 1.0);
    
    // 3D LUT lookup
    // Offset by half texel for proper sampling at boundaries
    float lut_size = float(textureSize(lut_texture, 0).x);
    float scale = (lut_size - 1.0) / lut_size;
    float offset = 0.5 / lut_size;
    vec3 lut_coord = color * scale + offset;
    
    vec3 graded = texture(lut_texture, lut_coord).rgb;
    
    // Blend LUT result with original
    color = mix(color, graded, intensity);
    
    // Temperature shift (post-LUT)
    color.r += temp * 0.5;
    color.b -= temp * 0.5;
    color = clamp(color, 0.0, 1.0);
    
    fragColor = mix(input_color, vec4(color, input_color.a), u_mix);
}
```

### .cube LUT File Parser
```python
def parse_cube_lut(filepath: str) -> Tuple[Optional[np.ndarray], int, bool]:
    """Parse a .cube LUT file.
    
    Returns:
        (data, size, is_3d) — data is float32 array, size is LUT dimension, is_3d indicates 3D vs 1D
    """
    try:
        if not os.path.exists(filepath):
            logger.error(f"LUT file not found: {filepath}")
            return None, 0, False
        
        size_1d = 0
        size_3d = 0
        data = []
        domain_min = [0.0, 0.0, 0.0]
        domain_max = [1.0, 1.0, 1.0]
        
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # Parse header
                if line.startswith('TITLE'):
                    continue
                elif line.startswith('LUT_1D_SIZE'):
                    size_1d = int(line.split()[-1])
                elif line.startswith('LUT_3D_SIZE'):
                    size_3d = int(line.split()[-1])
                elif line.startswith('DOMAIN_MIN'):
                    parts = line.split()[1:]
                    domain_min = [float(x) for x in parts[:3]]
                elif line.startswith('DOMAIN_MAX'):
                    parts = line.split()[1:]
                    domain_max = [float(x) for x in parts[:3]]
                else:
                    # Try to parse as color data
                    try:
                        parts = line.split()
                        if len(parts) >= 3:
                            r, g, b = float(parts[0]), float(parts[1]), float(parts[2])
                            # Normalize to domain
                            r = (r - domain_min[0]) / max(domain_max[0] - domain_min[0], 1e-6)
                            g = (g - domain_min[1]) / max(domain_max[1] - domain_min[1], 1e-6)
                            b = (b - domain_min[2]) / max(domain_max[2] - domain_min[2], 1e-6)
                            data.append([r, g, b])
                    except ValueError:
                        continue
        
        if not data:
            logger.error(f"No LUT data found in {filepath}")
            return None, 0, False
        
        data_array = np.array(data, dtype=np.float32)
        
        if size_3d > 0:
            # 3D LUT: reshape to (size, size, size, 3)
            expected = size_3d ** 3
            if len(data) != expected:
                logger.warning(f"3D LUT size mismatch: got {len(data)}, expected {expected}")
                size_3d = int(round(len(data) ** (1.0/3.0)))
            data_array = data_array.reshape(size_3d, size_3d, size_3d, 3)
            return data_array, size_3d, True
        elif size_1d > 0:
            # 1D LUT: shape is (size, 3)
            return data_array[:size_1d], size_1d, False
        else:
            # Auto-detect: try 3D first
            n = len(data)
            cube_root = round(n ** (1.0/3.0))
            if cube_root ** 3 == n:
                data_array = data_array.reshape(cube_root, cube_root, cube_root, 3)
                return data_array, cube_root, True
            else:
                return data_array, n, False
        
    except Exception as e:
        logger.error(f"Failed to parse LUT file {filepath}: {e}")
        return None, 0, False
```

### Procedural LUT Generator
```python
def generate_procedural_lut(preset: str, size: int = 32) -> np.ndarray:
    """Generate a procedural 3D LUT for built-in presets.
    
    Returns: float32 array of shape (size, size, size, 3)
    """
    lut = np.zeros((size, size, size, 3), dtype=np.float32)
    
    for b in range(size):
        for g in range(size):
            for r in range(size):
                # Normalized input
                ri = r / (size - 1)
                gi = g / (size - 1)
                bi = b / (size - 1)
                
                if preset == "teal_orange":
                    # Teal shadows, orange highlights
                    luma = 0.299 * ri + 0.587 * gi + 0.114 * bi
                    # Shadows → teal
                    shadow_r = ri * 0.7
                    shadow_g = gi * 0.9 + 0.05
                    shadow_b = bi * 1.1 + 0.08
                    # Highlights → warm orange
                    high_r = ri * 1.15 + 0.05
                    high_g = gi * 0.95
                    high_b = bi * 0.75
                    # Blend based on luminance
                    ro = shadow_r * (1 - luma) + high_r * luma
                    go = shadow_g * (1 - luma) + high_g * luma
                    bo = shadow_b * (1 - luma) + high_b * luma
                    
                elif preset == "film_noir":
                    # High contrast, desaturated, slight sepia
                    luma = 0.299 * ri + 0.587 * gi + 0.114 * bi
                    # S-curve contrast
                    luma = luma * luma * (3.0 - 2.0 * luma)
                    # Slight sepia
                    ro = luma * 1.05
                    go = luma * 0.95
                    bo = luma * 0.82
                    
                elif preset == "vintage":
                    # Faded blacks, warm mids, slight cross-process
                    ro = ri * 0.85 + 0.08  # Lifted blacks, reduced highlights
                    go = gi * 0.80 + 0.06
                    bo = bi * 0.70 + 0.12  # Bluer shadows
                    # Add slight green to mids
                    mid = (1.0 - abs(gi - 0.5) * 2.0)
                    go += mid * 0.03
                    
                elif preset == "cinematic":
                    # Crushed blacks, blue shadows, warm highlights
                    luma = 0.299 * ri + 0.587 * gi + 0.114 * bi
                    # Crush blacks
                    ro = max(ri * 0.95, 0.02)
                    go = max(gi * 0.92, 0.02)
                    bo = max(bi * 0.88, 0.04)
                    # Blue lift in shadows
                    shadow = max(0, 1.0 - luma * 3.0)
                    bo += shadow * 0.06
                    # Warm highlights
                    highlight = max(0, luma * 2.0 - 1.0)
                    ro += highlight * 0.04
                    go += highlight * 0.01
                    
                else:
                    # Identity
                    ro, go, bo = ri, gi, bi
                
                lut[b, g, r] = [
                    max(0.0, min(1.0, ro)),
                    max(0.0, min(1.0, go)),
                    max(0.0, min(1.0, bo))
                ]
    
    return lut
```

## Public Interface

### Parameter Controls
- **`lut_intensity`** (0-10 → 0-1): LUT blend intensity (10 = 100%)
- **`lift`** (0-10 → -0.2 to 0.2): Shadow lift adjustment
- **`gamma`** (0-10 → 0.2 to 3.0): Gamma correction for midtones
- **`gain`** (0-10 → 0.5 to 2.0): Highlight gain adjustment
- **`temperature`** (0-10 → -0.3 to 0.3): Warm/cool color temperature shift

### LUT Loading Methods
- **`load_lut(filepath: str) -> bool`**: Load .cube LUT file from disk
- **`load_preset(preset_name: str) -> bool`**: Load built-in procedural preset
- **`get_lut_info() -> Dict`**: Get current LUT status and metadata

### Built-in Presets
- **`identity`**: No color change (reference)
- **`teal_orange`**: Teal shadows, orange highlights (cinematic)
- **`film_noir`**: High contrast, desaturated, sepia tone
- **`vintage`**: Faded blacks, warm mids, cross-process effect
- **`cinematic`**: Crushed blacks, blue shadows, warm highlights

## Inputs and Outputs

### Input Sources
- **Texture 0**: Source video frame (sampler2D)
- **Texture 1**: 3D LUT texture (sampler3D, bound by apply_uniforms)
- **Parameters**: 5 color grading parameters (0-10 UI range)
- **LUT files**: .cube format files (1D or 3D)

### Output Destinations
- **Fragment color**: Processed video frame with color grading
- **3D texture**: OpenGL texture containing LUT data
- **UI state**: Current LUT configuration and metadata

## Edge Cases and Error Handling

### LUT File Parsing
- **File not found**: Returns None, logs error, keeps previous LUT
- **Invalid format**: Returns None, logs error, keeps previous LUT
- **Size mismatch**: Auto-detects correct size, logs warning
- **Empty data**: Returns None, logs error, keeps previous LUT
- **Domain normalization**: Handles custom DOMAIN_MIN/MAX values

### Parameter Ranges
- **Out of range**: Clamped to valid range (0-10)
- **Invalid values**: Default to neutral (5.0)
- **NaN/Inf**: Treated as neutral, logs warning

### Texture Management
- **Memory leaks**: Old textures deleted before new ones created
- **OpenGL errors**: Caught and logged, texture binding skipped
- **Invalid texture IDs**: Checked before binding, recreated if needed

### Preset Loading
- **Unknown preset**: Returns False, logs error, keeps previous preset
- **Invalid preset name**: Returns False, logs error
- **Memory errors**: Caught and logged, keeps previous state

## Mathematical Formulations

### Parameter Remapping
```
intensity = lut_intensity / 10.0
lift_val = (lift / 10.0 - 0.5) * 0.4
gamma_val = mix(0.2, 3.0, gamma / 10.0)
gain_val = mix(0.5, 2.0, gain / 10.0)
temp = (temperature / 10.0 - 0.5) * 0.6
```

### Color Correction Pipeline
```
// Lift (shadows)
color = color + vec3(lift_val)

// Gain (highlights)
color = color * gain_val

// Gamma (midtones)
color = pow(max(color, vec3(0.0)), vec3(1.0 / gamma_val))

// 3D LUT lookup with boundary offset
lut_coord = color * scale + offset

// Blend LUT result
color = mix(color, graded, intensity)

// Temperature shift (post-LUT)
color.r += temp * 0.5
color.b -= temp * 0.5
```

### 3D LUT Coordinate Calculation
```
// Offset by half texel for proper sampling at boundaries
float lut_size = float(textureSize(lut_texture, 0).x);
float scale = (lut_size - 1.0) / lut_size;
float offset = 0.5 / lut_size;
vec3 lut_coord = color * scale + offset;
```

### Procedural LUT Formulas

**Teal/Orange Preset:**
```
luma = 0.299 * ri + 0.587 * gi + 0.114 * bi
ro = shadow_r * (1 - luma) + high_r * luma
go = shadow_g * (1 - luma) + high_g * luma
bo = shadow_b * (1 - luma) + high_b * luma
```

**Film Noir Preset:**
```
luma = 0.299 * ri + 0.587 * gi + 0.114 * bi
luma = luma * luma * (3.0 - 2.0 * luma)  // S-curve
ro = luma * 1.05
go = luma * 0.95
bo = luma * 0.82
```

**Vintage Preset:**
```
ro = ri * 0.85 + 0.08
go = gi * 0.80 + 0.06
bo = bi * 0.70 + 0.12
mid = (1.0 - abs(gi - 0.5) * 2.0)
go += mid * 0.03
```

**Cinematic Preset:**
```
luma = 0.299 * ri + 0.587 * gi + 0.114 * bi
ro = max(ri * 0.95, 0.02)
go = max(gi * 0.92, 0.02)
bo = max(bi * 0.88, 0.04)
shadow = max(0, 1.0 - luma * 3.0)
bo += shadow * 0.06
highlight = max(0, luma * 2.0 - 1.0)
ro += highlight * 0.04
go += highlight * 0.01
```

## Performance Characteristics

### Computational Complexity
- **Per-pixel operations**: ~50 FLOPs (excluding LUT lookup)
- **LUT lookup**: 1 3D texture fetch (constant time)
- **Parameter remapping**: 5 simple arithmetic operations
- **Color correction**: 3 sequential operations (lift, gain, gamma)

### Memory Requirements
- **LUT texture**: 32x32x32x3 = 98,304 floats = ~384 KB
- **Parameter storage**: 5 floats + metadata
- **Texture binding**: 1 additional texture unit

### Bottlenecks
- **3D texture fetch**: Main bottleneck, but hardware accelerated
- **Gamma calculation**: pow() function, but optimized in GLSL
- **Memory bandwidth**: 1 texture fetch per pixel

### Optimization Opportunities
- **LUT size**: Can reduce from 32³ to 16³ for lower quality
- **Parameter caching**: Pre-calculate remapped values
- **SIMD operations**: GLSL automatically vectorizes operations

### Real-time Suitability
- **720p**: ~1.5M pixels × 50 FLOPs = ~75 MFLOPs (easily real-time)
- **1080p**: ~2M pixels × 50 FLOPs = ~100 MFLOPs (real-time on modern GPUs)
- **4K**: ~8M pixels × 50 FLOPs = ~400 MFLOPs (requires powerful GPU)

## Test Plan

### Unit Tests (95% coverage target)
1. **LUT File Parser Tests**
   - Test valid .cube files (1D and 3D)
   - Test invalid files (missing, corrupted, wrong format)
   - Test domain normalization (custom DOMAIN_MIN/MAX)
   - Test size auto-detection
   - Test 1D → 3D conversion

2. **Procedural LUT Tests**
   - Test all 5 presets generate correct LUTs
   - Test LUT size variations (16, 32, 64)
   - Test identity LUT correctness
   - Test boundary conditions (0, 1)

3. **Parameter Remapping Tests**
   - Test all parameter ranges (0-10)
   - Test edge cases (0, 5, 10)
   - Test invalid values (NaN, Inf, negative)
   - Test parameter interactions

4. **Shader Tests**
   - Test shader compilation
   - Test uniform binding
   - Test texture binding
   - Test parameter effects

### Integration Tests
1. **Full Pipeline Tests**
   - Test complete color grading workflow
   - Test LUT loading + parameter adjustment
   - Test preset switching
   - Test file loading + preset switching

2. **Performance Tests**
   - Test 720p real-time performance
   - Test 1080p real-time performance
   - Test memory usage
   - Test texture binding performance

3. **Visual Regression Tests**
   - Test teal_orange preset output
   - Test film_noir preset output
   - Test vintage preset output
   - Test cinematic preset output
   - Test identity preset (no change)

### Edge Case Tests
1. **File System Tests**
   - Test missing LUT files
   - Test read-only files
   - Test large files
   - Test concurrent access

2. **Parameter Edge Cases**
   - Test extreme parameter values
   - Test rapid parameter changes
   - Test parameter combinations
   - Test invalid parameter types

3. **OpenGL Edge Cases**
   - Test texture binding failures
   - Test shader compilation failures
   - Test memory allocation failures
   - Test context loss

### Load Tests
1. **File Loading Tests**
   - Test loading multiple LUT files
   - Test loading large LUT files
   - Test loading corrupted files
   - Test loading during playback

2. **Memory Tests**
   - Test memory usage with multiple LUTs
   - Test memory leaks
   - Test texture memory limits
   - Test cleanup on destruction

## Definition of Done

### Technical Requirements
- [ ] All 5 parameters implemented with correct remapping
- [ ] .cube file parser handles 1D and 3D LUTs
- [ ] Built-in procedural presets implemented
- [ ] Lift/Gamma/Gain color correction pipeline working
- [ ] Temperature adjustment implemented
- [ ] 3D LUT texture binding working
- [ ] Error handling for all edge cases
- [ ] Performance meets real-time requirements
- [ ] 95% unit test coverage achieved
- [ ] Integration tests pass
- [ ] Visual regression tests pass

### Documentation Requirements
- [ ] Complete technical specification with all sections filled
- [ ] Mathematical formulations for all algorithms
- [ ] Performance analysis with complexity calculations
- [ ] Test plan with comprehensive coverage strategy
- [ ] Edge case documentation with error handling
- [ ] Public interface documentation

### Quality Requirements
- [ ] Code follows project style guidelines
- [ ] All tests pass and maintain 95% coverage
- [ ] No regressions in existing functionality
- [ ] Documentation is accurate and complete
- [ ] Performance meets real-time requirements
- [ ] Memory usage is efficient

---

*Last Updated: 2026-03-03*  
*Spec Author: desktop-roo*  
*Task ID: P3-EXT096*