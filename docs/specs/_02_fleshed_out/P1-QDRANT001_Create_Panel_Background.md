# Task: P1-QDRANT001 — Create_Panel_Background

**Phase:** Phase 1 / P1-QDRANT001
**Assigned To:** desktop-roo
**Spec Written By:** desktop-roo
**Date:** 2026-03-01

---

## What This Module Does

The `PanelBackgroundCreator` module generates programmatic backgrounds for VJLive3 UI panels and overlays. It creates visually distinct, resolution-independent background textures using mathematical patterns, gradients, and procedural generation. The module supports multiple background styles (solid, gradient, radial, grid, scanlines, noise) with configurable color palettes, opacity, and blending modes. Backgrounds are rendered as RGBA textures using Pillow and numpy, then cached for reuse across panel instances. The module operates as a utility service within the UI layer, providing on-demand background generation with deterministic output for consistent theming.

The module draws inspiration from legacy UI systems in vjlive v1 and VJlive-2, which used hardcoded gradients and static images for panel backgrounds. The new implementation provides a flexible, parameterized approach that allows runtime customization without requiring pre-rendered assets.

---

## What It Does NOT Do

- Handle video processing or real-time video effects (that is the domain of effect plugins)
- Provide 3D rendering or WebGL-based backgrounds (uses CPU-based Pillow/numpy)
- Store persistent state across application sessions (stateless utility)
- Manage panel lifecycle or layout (delegates to UI framework)
- Perform I/O operations beyond optional PNG export (does not read/write files by default)
- Support animated backgrounds (static only; animation would be handled by panel compositor)
- Include advanced texture synthesis (no Perlin noise, Simplex noise, or procedural textures beyond basic patterns)
- Provide direct OpenGL texture management (returns numpy arrays; caller uploads to GPU if needed)

---

## Detailed Behavior

The module processes background generation requests through a well-defined pipeline:

1. **Input Validation**: Verify `panel_id` format, `dimensions` range, and `style` support
2. **Cache Lookup**: Check if identical background already exists in memory cache
3. **Styling Rule Application**: Map style string to concrete parameters (colors, patterns, gradients)
4. **Canvas Allocation**: Create numpy array of shape `(height, width, 4)` with dtype `uint8`
5. **Pattern Rendering**: Fill canvas according to selected style using mathematical formulas
6. **Post-Processing**: Apply opacity, blur, or noise if specified
7. **Caching**: Store result in LRU cache for future reuse
8. **Return**: Output as RGBA numpy array (0-255)

### Supported Styles

The `style` parameter accepts predefined style names or custom color specifications:

- `"solid"`: Single uniform color
- `"gradient_horizontal"`: Linear gradient left-to-right
- `"gradient_vertical"`: Linear gradient top-to-bottom
- `"gradient_radial"`: Radial gradient from center outward
- `"grid"`: Grid lines with configurable spacing
- `"scanlines"`: Horizontal scanlines (CRT effect)
- `"noise"`: Perlin-like random noise (using numpy random)
- `"checkerboard"`: Alternating color squares

### Color Specification

Colors can be specified as:
- Hex string: `"#1a2b3c"` or `"#RRGGBBAA"`
- RGB tuple: `(r, g, b)` or `(r, g, b, a)` with values 0-255
- Named color: `"black"`, `"white"`, `"red"`, etc. (uses Pillow's ImageColor)

### Parameter Mapping

Style-specific parameters are derived from the `style` string or defaults:

**Gradient styles**:
- `color_start`: Color at one end (default: dark blue `#0a0a2a`)
- `color_end`: Color at other end (default: dark purple `#2a0a2a`)
- `angle`: For linear gradients, angle in degrees (0=horizontal, 90=vertical)

**Grid/Scanlines**:
- `line_width`: Width of lines in pixels (default: 1)
- `spacing`: Space between lines (default: 20)
- `line_color`: Color of grid lines (default: semi-transparent white)

**Noise**:
- `noise_scale`: Scale factor for noise pattern (default: 1.0)
- `noise_seed`: Random seed for deterministic output (default: None → random)

**Checkerboard**:
- `square_size`: Size of each square (default: 16)
- `color1`, `color2`: Alternating colors (default: black/white)

### Mathematical Formulas

**Linear Gradient** (horizontal):
```
For each pixel (x, y):
    t = x / width
    color = color_start * (1 - t) + color_end * t
```

**Radial Gradient**:
```
center = (width/2, height/2)
max_radius = sqrt((width/2)^2 + (height/2)^2)
For each pixel (x, y):
    d = sqrt((x - center_x)^2 + (y - center_y)^2)
    t = clamp(d / max_radius, 0, 1)
    color = color_start * (1 - t) + color_end * t
```

**Grid Pattern**:
```
For each pixel (x, y):
    if (x % spacing < line_width) or (y % spacing < line_width):
        color = line_color
    else:
        color = background_color
```

**Scanlines**:
```
For each pixel (x, y):
    intensity = 0.8 + 0.2 * sin(2π * y / scan_period)
    color = background_color * intensity
```

**Checkerboard**:
```
For each pixel (x, y):
    parity = (floor(x / square_size) + floor(y / square_size)) % 2
    color = color1 if parity == 0 else color2
```

### Caching Strategy

- **Cache Key**: `(panel_id, dimensions, style, style_params)` tuple hashed
- **Cache Size**: Maximum 100 unique backgrounds (LRU eviction)
- **Memory Estimate**: 1920×1080×4 ≈ 8 MB per background; 100 max ≈ 800 MB
- **Cache Invalidation**: Manual via `clear_cache()` or automatic on process exit

---

## Public Interface

```python
from typing import Dict, Tuple, Any, Optional, Union
import numpy as np

class PanelBackgroundCreator:
    """
    Utility for generating panel backgrounds with various styles.
    
    Provides deterministic, cached background generation for UI panels.
    All methods are thread-safe for concurrent panel creation.
    """
    
    def __init__(
        self,
        cache_size: int = 100,
        default_style: str = "gradient_horizontal",
        default_colors: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Initialize background creator.
        
        Args:
            cache_size: Maximum number of backgrounds to cache (LRU)
            default_style: Default style when none specified
            default_colors: Default color palette for gradients
            
        Raises:
            ValueError: If cache_size < 1
        """
        pass
    
    def create_background(
        self,
        panel_id: str,
        dimensions: Dict[str, int],
        style: str,
        style_params: Optional[Dict[str, Any]] = None,
        opacity: float = 1.0
    ) -> np.ndarray:
        """
        Generate background texture for a panel.
        
        Args:
            panel_id: Unique identifier for the panel (used for caching)
            dimensions: Dict with 'width' and 'height' keys (pixels)
            style: Background style name (e.g., 'gradient_horizontal')
            style_params: Additional style-specific parameters
            opacity: Global opacity multiplier [0.0, 1.0]
            
        Returns:
            numpy.ndarray: RGBA array of shape (height, width, 4), dtype uint8
            
        Raises:
            ValueError: If dimensions invalid, opacity out of range, style unknown
            MemoryError: If allocation fails (dimensions too large)
            
        Note:
            Output is cached; subsequent calls with same parameters return
            the same array object (shared reference). Caller should not
            modify cached arrays.
        """
        pass
    
    def validate_panel_id(self, panel_id: str) -> bool:
        """
        Validate panel identifier format.
        
        Args:
            panel_id: Panel identifier to validate
            
        Returns:
            bool: True if valid (alphanumeric, hyphens, underscores, 1-64 chars)
            
        Valid format:
        - Only contains: a-z, A-Z, 0-9, hyphen (-), underscore (_)
        - Length between 1 and 64 characters
        - Cannot be only digits (must have at least one letter)
        """
        pass
    
    def generate_background_report(self, panel_id: str) -> str:
        """
        Generate human-readable report about a panel's background.
        
        Args:
            panel_id: Panel identifier (must exist in cache)
            
        Returns:
            str: Multi-line report with dimensions, style, cache status
            
        Report format:
        ```
        Panel: <panel_id>
        Status: Cached / Not cached
        Dimensions: <width>×<height>
        Style: <style_name>
        Parameters: <param_list>
        Memory: <size_in_mb> MB
        ```
        
        Raises:
            KeyError: If panel_id not found in cache
        """
        pass
    
    def apply_styling_rules(
        self,
        style: str,
        canvas_size: Tuple[int, int],
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Resolve style string to concrete rendering parameters.
        
        Args:
            style: Style name or custom specification
            canvas_size: (width, height) in pixels
            params: Override parameters for style
            
        Returns:
            Dict containing resolved parameters:
            - 'type': style category ('solid', 'gradient', 'pattern')
            - 'colors': list of RGB tuples
            - 'geometry': spacing, line_width, etc.
            - 'functions': callable rendering functions (internal)
            
        Raises:
            ValueError: If style unknown or parameters invalid
        """
        pass
    
    def clear_cache(self) -> None:
        """Clear all cached backgrounds to free memory."""
        pass
    
    def cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dict with keys:
            - 'size': current number of cached backgrounds
            - 'max_size': maximum cache size
            - 'hits': number of cache hits
            - 'misses': number of cache misses
            - 'memory_mb': estimated memory usage in MB
        """
        pass
```

---

## Inputs and Outputs

### Inputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `panel_id` | `str` | Unique panel identifier | Regex: `^[a-zA-Z_][a-zA-Z0-9_-]*$`, max 64 chars |
| `dimensions` | `Dict[str, int]` | Canvas size | Must contain `width` and `height`; both ≥ 1, ≤ 16384 |
| `style` | `str` | Background style name | Must be in `SUPPORTED_STYLES` set |
| `style_params` | `Optional[Dict[str, Any]]` | Style-specific overrides | Parameter types validated per style |
| `opacity` | `float` | Global opacity multiplier | Range [0.0, 1.0] inclusive |

### Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `background` | `np.ndarray` | RGBA background texture | Shape `(H, W, 4)`, dtype `uint8`, values 0-255 |
| `report` | `str` | Human-readable status text | Format: multi-line string |

### Memory Layout

The returned numpy array uses standard RGBA byte order:
- Index 0: Height (rows)
- Index 1: Width (columns)
- Index 2: Channels (R, G, B, A)
- Memory contiguous: `array.strides == (width*4, 4, 1)`

For a 1920×1080 background:
- Total pixels: 2,073,600
- Total bytes: 2,073,600 × 4 = 8,294,400 bytes (~7.9 MB)

---

## Edge Cases and Error Handling

### Invalid Panel ID
- **Empty string**: `validate_panel_id("")` returns `False`
- **Only digits**: `validate_panel_id("12345")` returns `False`
- **Invalid characters**: `validate_panel_id("panel@id")` returns `False`
- **Too long**: `validate_panel_id("a"*65)` returns `False`
- **Valid**: `validate_panel_id("main_video_panel")` returns `True`

### Invalid Dimensions
- **Missing keys**: `create_background(..., {"width": 800}, ...)` raises `KeyError` or `ValueError` with message "dimensions must contain 'width' and 'height'"
- **Non-integer values**: `{"width": 800.5, "height": 600}` raises `TypeError`
- **Negative values**: `{"width": -1, "height": 100}` raises `ValueError` ("width must be ≥ 1")
- **Excessive size**: `{"width": 20000, "height": 20000}` raises `ValueError` ("dimensions exceed maximum 16384")
- **Zero dimension**: `{"width": 0, "height": 100}` raises `ValueError`

### Unsupported Style
- **Unknown style**: `create_background(..., style="glitchy_wave", ...)` raises `ValueError` ("Unsupported style: glitchy_wave. Supported: ...")
- **Case sensitivity**: `"Gradient_Horizontal"` (capital G) raises `ValueError`; use lowercase

### Invalid Style Parameters
- **Wrong type**: `{"line_width": "2"}` (string instead of int) raises `TypeError`
- **Out of range**: `{"opacity": 1.5}` raises `ValueError` ("opacity must be in [0.0, 1.0]")
- **Missing required**: `{"square_size": 16}` for checkerboard is OK (has default); missing non-optional param raises `KeyError` during rendering

### Memory Allocation Failure
- **Very large dimensions**: `{"width": 100000, "height": 100000}` may raise `MemoryError` from numpy
- **Mitigation**: Validate dimensions before allocation; raise `ValueError` with clear message

### Cache Saturation
- **Cache full**: When cache reaches `cache_size`, LRU entry is evicted automatically
- **No error raised**: Eviction is silent; caller unaffected
- **Stats update**: `cache_stats()['size']` reflects current count

### Concurrency
- **Thread safety**: All public methods acquire a `threading.RLock` to protect cache and internal state
- **Deadlock prevention**: Lock is reentrant; same thread can call nested methods
- **Performance**: Lock contention minimal (cache lookup fast); acceptable for UI thread + background threads

### Opacity Handling
- **Opacity 0**: Returns fully transparent array (all alpha=0) but still renders pattern
- **Opacity 1**: Full opacity (default)
- **Precision**: Opacity clipped to nearest representable uint8 value: `alpha = uint8(round(opacity * 255))`

### Panel ID Collision
- **Different params, same ID**: If called with same `panel_id` but different `dimensions` or `style`, cache key includes all parameters, so separate entries created
- **Intentional reuse**: Same `panel_id` with identical params returns cached result (shared reference)
- **Mutability warning**: Caller modifying returned array will affect all future callers receiving same cached reference

---

## Dependencies

### External Libraries
- **Pillow (PIL)**: Used for color parsing (`ImageColor.getrgb()`), image format conversion, and optional PNG export. Required. If missing, `ImportError` at module import.
- **numpy**: Used for array operations, gradient computation, and pattern generation. Required. If missing, `ImportError` at module import.
- **threading**: Standard library; used for thread-safe caching.
- **functools**: Standard library; used for `lru_cache` wrapper and `partial`.

### Internal Dependencies
- **`vjlive3.utils.color_parsing`** (hypothetical): If exists, used for advanced color parsing; otherwise falls back to PIL
- **`vjlive3.ui.cache`** (hypothetical): Could use shared cache infrastructure; current design uses local LRU

### Optional Features
- **PNG export**: If `save_png()` method added, requires Pillow's `Image.save()`
- **Advanced noise**: If Perlin/Simplex noise added, would require `noise` library or custom implementation

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_defaults` | Constructor works with default arguments |
| `test_init_custom_cache_size` | Custom cache_size accepted and enforced |
| `test_init_invalid_cache_size` | `cache_size ≤ 0` raises `ValueError` |
| `test_validate_panel_id_valid` | Valid IDs return `True` (various formats) |
| `test_validate_panel_id_invalid` | Invalid IDs (empty, only digits, special chars) return `False` |
| `test_create_background_solid` | Solid style produces uniform color array |
| `test_create_background_gradient_horizontal` | Horizontal gradient varies correctly along X axis |
| `test_create_background_gradient_vertical` | Vertical gradient varies correctly along Y axis |
| `test_create_background_gradient_radial` | Radial gradient varies with distance from center |
| `test_create_background_grid` | Grid pattern has correct line spacing and color |
| `test_create_background_scanlines` | Scanlines produce alternating intensity bands |
| `test_create_background_noise` | Noise generates non-zero variance across pixels |
| `test_create_background_checkerboard` | Checkerboard alternates colors in 2D grid |
| `test_dimensions_validation_missing` | Missing width/height raises `ValueError` |
| `test_dimensions_validation_negative` | Negative dimensions raise `ValueError` |
| `test_dimensions_validation_too_large` | Dimensions > 16384 raise `ValueError` |
| `test_style_unknown` | Unknown style raises `ValueError` with helpful message |
| `test_opacity_clamping` | Opacity < 0 or > 1 raises `ValueError` |
| `test_opacity_application` | Opacity correctly multiplies alpha channel |
| `test_cache_hit_miss` | Same params hit cache; different params miss |
| `test_cache_lru_eviction` | Cache evicts least recently used when full |
| `test_cache_shared_reference` | Cached arrays returned are same object (id equality) |
| `test_clear_cache` | `clear_cache()` empties cache and resets stats |
| `test_cache_stats` | `cache_stats()` returns correct counts and memory estimate |
| `test_concurrent_access` | Multiple threads can safely call `create_background()` |
| `test_generate_report_cached` | Report shows "Cached" for existing panel_id |
| `test_generate_report_uncached` | Report shows "Not cached" for unknown panel_id |
| `test_generate_report_missing` | Unknown panel_id raises `KeyError` |
| `test_apply_styling_rules_solid` | Resolves solid style to correct parameter dict |
| `test_apply_styling_rules_gradient` | Resolves gradient with custom colors |
| `test_apply_styling_rules_invalid` | Invalid style raises `ValueError` |
| `test_color_parsing_hex` | Hex strings `"#RRGGBB"` and `"#RRGGBBAA"` parsed correctly |
| `test_color_parsing_rgb_tuple` | `(r,g,b)` and `(r,g,b,a)` tuples accepted |
| `test_color_parsing_named` | Named colors ("red", "blue") resolved via PIL |
| `test_output_shape` | Output array shape matches `(height, width, 4)` |
| `test_output_dtype` | Output dtype is `np.uint8` |
| `test_output_range` | All pixel values in [0, 255] |
| `test_background_reproducibility` | Same inputs produce identical arrays (deterministic) |
| `test_background_different_panel_ids` | Different panel_ids with same params still hit cache (cache key includes panel_id) |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-1] P1-QDRANT001: panel background creator` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES

Use these to fill in the spec. These are the REAL implementations:

### vjlive1/plugins/vcore/panel_background.py (L1-40)
```python
"""
Panel Background Generator — Create UI panel backdrops.

Generates programmatic backgrounds for VJLive control panels and overlays.
Supports gradients, solid colors, and simple patterns. Backgrounds are
cached and reused across panel instances with identical specifications.
"""
```

### vjlive1/plugins/vcore/panel_background.py (L15-60)
```python
class PanelBackgroundGenerator:
    """Generate cached backgrounds for UI panels."""
    
    def __init__(self):
        self.cache = {}
        self.default_style = "gradient_blue"
    
    def get_background(self, panel_id, width, height, style="default"):
        """Return background texture for panel."""
        cache_key = (panel_id, width, height, style)
        if cache_key not in self.cache:
            self.cache[cache_key] = self._render(panel_id, width, height, style)
        return self.cache[cache_key]
```

### vjlive1/plugins/vcore/panel_background.py (L50-120)
```python
def _render(self, panel_id, width, height, style):
    """Render background based on style."""
    img = Image.new("RGBA", (width, height))
    draw = ImageDraw.Draw(img)
    
    if style == "gradient_blue":
        for y in range(height):
            color = int(10 + (y/height) * 20)
            draw.line([(0,y), (width,y)], fill=(0, color, color*2, 255))
    elif style == "solid_black":
        img.paste((0,0,0,255))
    elif style == "grid":
        self._draw_grid(draw, width, height)
    # ... more styles
    
    return np.array(img)
```

### vjlive1/plugins/vcore/panel_background.py (L100-180)
```python
def _draw_grid(self, draw, width, height, spacing=20, color=(255,255,255,80)):
    """Draw grid lines."""
    for x in range(0, width, spacing):
        draw.line([(x,0), (x,height)], fill=color, width=1)
    for y in range(0, height, spacing):
        draw.line([(0,y), (width,y)], fill=color, width=1)

def _draw_scanlines(self, draw, width, height, period=4):
    """Draw CRT scanlines."""
    for y in range(0, height, period):
        alpha = 200 if y % (period*2) == 0 else 100
        draw.line([(0,y), (width,y)], fill=(0,0,0,alpha), width=1)
```

### VJlive-2/core/ui/background_service.py (L1-50)
```python
"""
Background service for UI panels.

Provides deterministic background generation with LRU caching.
Thread-safe for concurrent access from UI and rendering threads.
"""
import threading

class BackgroundService:
    def __init__(self, max_cached=100):
        self.cache = {}
        self.lock = threading.RLock()
        self.max_cached = max_cached
        self.access_order = []
    
    def get_background(self, key):
        with self.lock:
            if key not in self.cache:
                bg = self._generate(key)
                self.cache[key] = bg
                self._update_access_order(key)
                self._evict_if_needed()
            else:
                self._update_access_order(key)
            return self.cache[key]
    
    def _evict_if_needed(self):
        while len(self.cache) > self.max_cached:
            lru_key = self.access_order.pop(0)
            del self.cache[lru_key]
```

### VJlive-2/core/ui/background_service.py (L80-140)
```python
def _generate(self, key):
    """Generate background from key specification."""
    spec = BackgroundSpec.from_key(key)
    
    # Use numpy for fast array operations
    arr = np.zeros((spec.height, spec.width, 4), dtype=np.uint8)
    
    if spec.style == "gradient":
        self._gradient(arr, spec.colors, spec.angle)
    elif spec.style == "radial":
        self._radial(arr, spec.colors)
    elif spec.style == "pattern":
        self._pattern(arr, spec.pattern_type, spec.params)
    
    # Apply global opacity
    if spec.opacity < 1.0:
        arr[:, :, 3] = (arr[:, :, 3] * spec.opacity).astype(np.uint8)
    
    return arr

def _gradient(self, arr, colors, angle):
    """Linear gradient using numpy broadcasting."""
    h, w = arr.shape[:2]
    if angle in (0, 180):
        t = np.linspace(0, 1, w)
        for i in range(3):
            arr[:, :, i] = np.outer(np.ones(h), colors[0][i] * (1-t) + colors[1][i] * t)
    # ... handle vertical and diagonal
```

---

## Implementation Notes

### Performance Considerations
- **Rendering speed**: For 1920×1080, solid color: <1 ms; gradient: 2-5 ms; grid: 5-10 ms; noise: 10-20 ms (on modern CPU)
- **Cache hit**: O(1) dict lookup; negligible
- **Memory**: Each cached background: width × height × 4 bytes. 100 full-HD backgrounds ≈ 800 MB. Consider reducing `cache_size` on memory-constrained systems.
- **Threading**: Use `threading.RLock` to allow reentrant calls from same thread (e.g., `create_background()` calling `apply_styling_rules()`)

### Color Parsing Strategy
1. Try `ImageColor.getrgb(color_spec)` for hex/named colors
2. If tuple, validate length (3 or 4) and value ranges (0-255)
3. Raise `ValueError` on failure with descriptive message

### Gradient Computation
Use numpy vectorization for performance:
```python
# Horizontal gradient
t = np.linspace(0, 1, width)
color_row = (start_color * (1-t) + end_color * t).astype(np.uint8)
arr[:, :, :3] = color_row  # broadcast across rows
```

### Grid Rendering
Use numpy slicing for efficiency:
```python
# Vertical lines
arr[:, x_start::spacing, :] = line_color
# Horizontal lines
arr[y_start::spacing, :, :] = line_color
```

### Scanline Rendering
```python
period = 4  # pixels between scanlines
y_indices = np.arange(height)
alpha = np.where(y_indices % (period*2) < period, 200, 100)
arr[:, :, 3] = alpha  # broadcast
```

### Noise Generation
Use `np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)` for simple RGB noise. For Perlin-like noise, implement value noise or use `noise` library if available.

### Cache Key Design
```python
cache_key = (
    panel_id,
    dimensions['width'],
    dimensions['height'],
    style,
    frozenset(style_params.items()) if style_params else None,
    opacity
)
```
Use `frozenset` to make params hashable and order-independent.

---

## Safety Rails

1. **Dimension limits**: Hard limit 16384 on width/height to prevent OOM
2. **Cache size limit**: Enforced LRU; cannot exceed `cache_size`
3. **Panel ID validation**: Reject potentially malicious IDs (path traversal, SQL injection patterns) even though not used for file I/O
4. **Opacity clamping**: Strict [0,1] range; no silent clamping
5. **Thread safety**: All cache operations protected by RLock
6. **Memory cleanup**: `clear_cache()` explicitly deletes arrays to free memory; also rely on Python GC
7. **No file I/O by default**: Backgrounds exist only in memory; optional PNG export must be explicitly implemented and validated

---
-

## References

- **Pillow ImageColor**: https://pillow.readthedocs.io/en/stable/reference/ImageColor.html
- **numpy broadcasting**: https://numpy.org/doc/stable/user/basics.broadcasting.html
- **LRU cache pattern**: https://docs.python.org/3/library/functools.html#functools.lru_cache
- **Thread safety in Python**: https://docs.python.org/3/library/threading.html#rlock-objects
