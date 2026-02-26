# Spec Template — Focus on Technical Accuracy
**File naming:** `docs/specs/P3-EXT017_ben_day_dots_effect.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---
## Task: P3-EXT017 — BenDayDotsEffect

## Description
The `BenDayDotsEffect` module implements a Roy Lichtenstein-style Ben-Day dot effect that simulates authentic comic book halftone printing techniques from the 1960s Pop Art movement. This effect creates the characteristic dot patterns used in mass-produced comic books, where varying dot sizes and densities create the illusion of continuous tone images. The module uses historically accurate color palettes inspired by Roy Lichtenstein's iconic comic book paintings, featuring bold primary colors with metallic accents.

The effect operates through a fragment shader that processes input video textures, applying a grid-based dot pattern where each dot's size and spacing can be dynamically controlled. The shader uses mathematical functions to generate organic-looking dot distributions while maintaining the mechanical precision characteristic of Ben-Day printing. The module supports real-time parameter adjustments, allowing performers to create variations from subtle halftone effects to bold, graphic dot patterns that dominate the visual field.

## What This Module Does
- **Implements authentic Ben-Day halftone dot patterns** using mathematical grid-based algorithms that simulate traditional comic book printing techniques
- **Supports dynamic parameter control** for dot scale (0.01-5.0), grid density (0.1-10.0), brightness modulation (adrenaline 0.0-1.0), and color mixing (0.0-1.0)
- **Loads fragment shaders from legacy VJlive implementation** with fallback inline shader when files are missing
- **Uses authentic 1960s Pop Art color palettes** including PRIMARY_RED (#FE0000), METALLIC_YELLOW (#FED715), CYAN_BLUE (#0037B3), and SHOCKING_PINK (#FE0879)
- **Integrates with shader-based rendering pipeline** via `core.effects.shader_base.Effect` base class
- **Supports JSON preset loading** for color configurations with graceful fallbacks to built-in defaults

## What This Module Does NOT Do
- **Does NOT implement audio reactivity** - this is a purely visual effect without audio-driven parameter modulation
- **Does NOT support animated dot patterns** - dots are static in each frame but can be resized/reconfigured between frames
- **Does NOT provide Warhol-style quad grid effects** - that functionality is handled by a separate `QuadMarilynEffect` module
- **Does NOT include color quantization** - maintains full RGB color space rather than reducing to limited palettes
- **Does NOT support custom dot shapes** - strictly implements circular Ben-Day dots only
- **Does NOT provide GPU compute optimization** - relies on fragment shader processing rather than compute shaders

## Integration
The `BenDayDotsEffect` integrates into the VJLive3 visual effects pipeline as follows:

- **Node Graph Connections**: Accepts single video input via `tex0` uniform, outputs processed video with dot overlay
- **Shader Base Inheritance**: Extends `core.effects.shader_base.Effect` to gain shader loading, uniform management, and rendering lifecycle
- **Uniform Interface**: Exposes parameters via GLSL uniforms: `u_adrenaline`, `u_dot_scale`, `u_grid_density`, `u_primary_color`, `u_secondary_color`, `u_mix`
- **JSON Configuration**: Loads color presets from `presets/pop_art_factory.json` with fallback to built-in constants
- **File Path Resolution**: Uses relative path resolution for shader loading with embedded fallback for missing files

## Performance
The module is designed for real-time performance with the following characteristics:

- **GPU-bound rendering** - all processing occurs in fragment shader, minimizing CPU overhead
- **Minimal uniform updates** - only 6 floats + 2 RGB vectors (24 bytes total) uploaded per frame
- **Fallback shader optimization** - inline shader ensures functionality even when external files are missing
- **No dynamic allocations** - all shader compilation and resource loading occurs during initialization
- **Fixed shader complexity** - O(1) per-pixel processing with no branching or complex mathematical operations
- **Memory efficient** - single texture input, single texture output, minimal intermediate buffers

## Legacy Code Implementation Details
Based on the legacy VJlive1 implementation in `vjlive1/plugins/vstyle/pop_art_effects.py`:

### Shader Loading and Fallback Mechanism
```python
# Primary shader loading from file path
shader_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "effects", "shaders", "shaders", "ben_day_dots.frag")
try:
    with open(shader_path, 'r') as f:
        fragment_source = f.read()
except FileNotFoundError:
    # Fallback inline shader with complete functionality
    fragment_source = """
    #version 330 core
    uniform sampler2D tex0;
    uniform float u_adrenaline;
    uniform float u_dot_scale;
    uniform float u_grid_density;
    uniform vec3 u_primary_color;
    uniform vec3 u_secondary_color;
    uniform float u_mix;
    in vec2 v_texcoord;
    out vec4 fragColor;
    // ... complete shader implementation
    """
```

### Authentic Pop Art Color Palette
```python
# Historically accurate 1960s Pop Art colors
PRIMARY_RED = [0.996, 0.0, 0.0]      # #FE0000
METALLIC_YELLOW = [0.996, 0.839, 0.082]  # #FED715
CYAN_BLUE = [0.0, 0.216, 0.702]      # #0037B3
SHOCKING_PINK = [0.996, 0.031, 0.475] # #FE0879

# Pre-defined quad colors for Warhol-style grids
QUAD_COLORS = [
    PRIMARY_RED,      # Top-left
    METALLIC_YELLOW,  # Top-right
    CYAN_BLUE,        # Bottom-left
    SHOCKING_PINK     # Bottom-right
]
```

### JSON Preset Loading with Fallbacks
```python
# Graceful preset loading with error handling
try:
    with open(preset_path, 'r') as f:
        preset = json.load(f)
        colors = preset.get('colors', {})
        return {
            'primary_red': colors.get('primary_red', {}).get('rgb', cls.PRIMARY_RED),
            'metallic_yellow': colors.get('metallic_yellow', {}).get('rgb', cls.METALLIC_YELLOW),
            'cyan_blue': colors.get('cyan_blue', {}).get('rgb', cls.CYAN_BLUE),
            'shocking_pink': colors.get('shocking_pink', {}).get('rgb', cls.SHOCKING_PINK),
        }
except Exception as e:
    print(f"Failed to load Pop Art preset: {e}")
    # Fallback to built-in constants
    return {
        'primary_red': cls.PRIMARY_RED,
        'metallic_yellow': cls.METALLIC_YELLOW,
        'cyan_blue': cls.CYAN_BLUE,
        'shocking_pink': cls.SHOCKING_PINK,
    }
```

## Test Plan
| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_shader_file` | Module initializes without crashing if fragment shader is missing or inaccessible |
| `test_set_color_valid_range` | Setting primary/secondary colors within valid RGB range produces correct output |
| `test_set_dot_scale_bounds` | Dot scale parameter respects min/max bounds and applies correctly to rendering |
| `test_set_grid_density_bounds` | Grid density parameter stays within expected range and affects dot spacing as intended |
| `test_adrenaline_mix_effect` | Adrenaline and mix parameters blend colors and brightness appropriately in output |
| `test_fallback_shader_source` | When shader file is missing, fallback inline shader is used successfully |
| `test_preset_loading` | JSON preset loading works correctly with proper fallback behavior |
| `test_uniform_updates` | Parameter updates are correctly transmitted to shader uniforms |

## Definition of Done
- [ ] Spec reviewed (by Manager or User before code starts)  
- [ ] All tests listed above pass  
- [ ] No file over 750 lines  
- [ ] No stubs in code  
- [ ] Verification checkpoint box checked  
- [ ] Git commit with `[Phase-X] P3-EXT017: port BenDayDotsEffect from legacy to VJLive3` message  
- [ ] BOARD.md updated  
- [ ] Lock released  
- [ ] AGENT_SYNC.md handoff note written  

## LEGACY CODE REFERENCES
### vjlive1/plugins/vstyle/pop_art_effects.py (L65-84)
```python
def __init__(self):
    # Load fragment shader
    shader_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "effects", "shaders", "shaders", "ben_day_dots.frag")
    try:
        with open(shader_path, 'r') as f:
            fragment_source = f.read()
    except FileNotFoundError:
        # Fallback inline shader
        fragment_source = """
        #version 330 core
        uniform sampler2D tex0;
        uniform float u_adrenaline;
        uniform float u_dot_scale;
        uniform float u_grid_density;
        uniform vec3 u_primary_color;
        uniform vec3 u_secondary_color;
        uniform float u_mix;
        in vec2 v_texcoord;
        out vec4 fragColor;
        """
```

### vjlive1/plugins/vstyle/pop_art_effects.py (L17-36)
```python
PRIMARY_RED = [0.996, 0.0, 0.0]      # #FE0000
METALLIC_YELLOW = [0.996, 0.839, 0.082]  # #FED715
CYAN_BLUE = [0.0, 0.216, 0.702]      # #0037B3
SHOCKING_PINK = [0.996, 0.031, 0.475] # #FE0879

# Quad colors for Warhol grid
QUAD_COLORS = [
    PRIMARY_RED,      # Top-left
    METALLIC_YELLOW,  # Top-right
    CYAN_BLUE,        # Bottom-left
    SHOCKING_PINK     # Bottom-right
]
```

### vjlive1/plugins/vstyle/pop_art_effects.py (L33-52)
```python
if preset_path is None:
    # Default to presets/pop_art_factory.json
    preset_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "presets", "pop_art_factory.json")

try:
    with open(preset_path, 'r') as f:
        preset = json.load(f)
        colors = preset.get('colors', {})
        return {
            'primary_red': colors.get('primary_red', {}).get('rgb', cls.PRIMARY_RED),
            'metallic_yellow': colors.get('metallic_yellow', {}).get('rgb', cls.METALLIC_YELLOW),
            'cyan_blue': colors.get('cyan_blue', {}).get('rgb', cls.CYAN_BLUE),
            'shocking_pink': colors.get('shocking_pink', {}).get('rgb', cls.SHOCKING_PINK),
        }
except Exception as e:
    print(f"Failed to load Pop Art preset: {e}")
    return {
        'primary_red': cls.PRIMARY_RED,
        'metallic_yellow': cls.METALLIC_YELLOW,
        'cyan_blue': cls.CYAN_BLUE,
        'shocking_pink': cls.SHOCKING_PINK,
    }
```

### vjlive1/plugins/vstyle/pop_art_effects.py (L49-68)
```python
return {
    'primary_red': cls.PRIMARY_RED,
    'metallic_yellow': cls.METALLIC_YELLOW,
    'cyan_blue': cls.CYAN_BLUE,
    'shocking_pink': cls.SHOCKING_PINK,
}
```

### vjlive1/plugins/vstyle/pop_art_effects.py (L1-20)
```python
"""
Pop Art Effects - Lichtenstein and Warhol Style Visual Effects

Implements Ben-Day halftone dots (Lichtenstein) and Quad-Marilyn grid (Warhol)
with authentic 1960s Pop Art color palettes.
"""