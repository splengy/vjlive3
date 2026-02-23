# P3-EXT075: ExampleGlitchEffect (Audio-Reactive Glitch Processor)

## Task
**P3-EXT075** — `example_glitch` (ExampleGlitchEffect)

## What This Module Does

ExampleGlitchEffect is an audio-reactive glitch processor that applies real-time digital corruption effects to video streams. It responds to audio intensity (particularly high-frequency transients) and dynamically applies a combination of glitch techniques:

- **Digital corruption**: Random block displacement and data corruption
- **Pixelation**: Resolution reduction and mosaic effects
- **Color channel separation**: RGB shift and chromatic aberration
- **Scan line interference**: Horizontal line artifacts and rolling bands
- **Temporal displacement**: Frame buffering and temporal glitching

The effect is implemented as a CPU-based image processing pipeline with optional GLSL shader acceleration. It maintains an 8-frame circular buffer for temporal effects and maps audio signals to individual glitch parameter intensities.

## What It Does NOT Do

- Does NOT provide GPU-accelerated processing (CPU fallback only)
- Does NOT support 4K resolution at 60 FPS on low-end hardware (performance target: 1080p @ 30 FPS minimum)
- Does NOT include advanced machine learning-based glitch patterns
- Does NOT support HDR or wide color gamut processing (expects 8-bit RGB)
- Does NOT provide non-destructive effect chaining (modifies frame data in-place)
- Does NOT include preset management or parameter automation
- Does NOT support multi-threaded processing (single-threaded CPU operations)

## Public Interface

```python
class ExampleGlitchEffect(BaseEffect):
    """
    Audio-reactive glitch effect processor.
    
    Applies multiple glitch techniques to video frames based on audio intensity.
    """
    
    def __init__(self) -> None:
        """Initialize effect with default parameters and empty frame buffer."""
        self.name: str = "Example Glitch"
        self.shader_path: str  # Path to example_glitch.frag (optional)
        self.is_loaded: bool = False
        
        # Glitch intensity parameters (0.0 - 1.0)
        self.intensity: float = 0.0
        self.corruption_level: float = 0.0
        self.pixelation_level: float = 0.0
        self.color_shift: float = 0.0
        self.scan_lines: float = 0.0
        self.temporal_displacement: float = 0.0
        
        # Internal state
        self.last_intensity: float = 0.0
        self.frame_count: int = 0
        self.buffer_size: int = 8
        self.frame_buffer: List[Optional[np.ndarray]] = [None] * 8
        self.buffer_index: int = 0
    
    def load(self) -> bool:
        """Load the GLSL shader if available. Returns True if loaded successfully."""
        pass
    
    def update(self, signals: Dict[str, Any]) -> None:
        """
        Update effect parameters based on audio analysis.
        
        Args:
            signals: Dictionary containing audio analysis keys:
                   - 'treble' (float): High-frequency energy (0.0-1.0)
                   - 'bass' (float): Low-frequency energy (0.0-1.0)
                   - 'mid' (float): Mid-frequency energy (0.0-1.0)
                   - 'volume' (float): Overall amplitude (0.0-1.0)
        """
        pass
    
    def draw(self) -> Optional[np.ndarray]:
        """
        Apply glitch effects to current frame.
        
        Returns:
            Processed frame as HxWx3 uint8 array, or None if no effect applied.
        """
        pass
    
    def _apply_corruption(self, frame: np.ndarray) -> np.ndarray:
        """Apply random block corruption effect."""
        pass
    
    def _apply_pixelation(self, frame: np.ndarray) -> np.ndarray:
        """Apply pixelation/mosaic effect."""
        pass
    
    def _apply_color_shift(self, frame: np.ndarray) -> np.ndarray:
        """Apply RGB channel separation effect."""
        pass
    
    def _apply_scan_lines(self, frame: np.ndarray) -> np.ndarray:
        """Apply scan line interference effect."""
        pass
    
    def _apply_temporal_displacement(self, frame: np.ndarray) -> np.ndarray:
        """Apply temporal glitch using frame buffer."""
        pass
```

### Parameters

| Parameter | Type | Range | Default | Description |
|-----------|------|-------|---------|-------------|
| `intensity` | float | 0.0 - 1.0 | 0.0 | Master effect intensity (audio-driven) |
| `corruption_level` | float | 0.0 - 1.0 | 0.0 | Digital corruption strength |
| `pixelation_level` | float | 0.0 - 1.0 | 0.0 | Pixelation block size multiplier |
| `color_shift` | float | 0.0 - 1.0 | 0.0 | RGB channel separation offset |
| `scan_lines` | float | 0.0 - 1.0 | 0.0 | Scan line opacity and density |
| `temporal_displacement` | float | 0.0 - 1.0 | 0.0 | Frame buffer mix ratio |

### Inputs

- **Audio Signals** (`signals` dict):
  - `treble` (float): High-frequency energy, maps to corruption and pixelation
  - `mid` (float): Mid-frequency energy, maps to color shift
  - `bass` (float): Low-frequency energy, maps to scan lines
  - `volume` (float): Overall amplitude, scales all effects

- **Video Frame** (implicit):
  - Expected as `np.ndarray` with shape (H, W, 3)
  - Format: 8-bit RGB (0-255)
  - Resolution: Any (performance scales with pixel count)

### Outputs

- **Processed Frame** (`np.ndarray`):
  - Same shape and dtype as input
  - Applied effects are non-destructive to original buffer
  - Returns `None` if `intensity <= 0.1` (no effect applied)

### Missing Dependencies

- **OpenCV** (`cv2`): Required for advanced image processing operations
- **NumPy** (`numpy`): Required for array manipulations
- **GLSL Shader** (`example_glitch.frag`): Optional for GPU acceleration

If `cv2` is unavailable, the effect falls back to basic NumPy operations (reduced quality). If shader is unavailable, CPU path is used exclusively.

### Invalid Parameters

- `intensity < 0.0` or `intensity > 1.0`: Clamped to [0.0, 1.0]
- `corruption_level`, `pixelation_level`, `color_shift`, `scan_lines`, `temporal_displacement` outside [0.0, 1.0]: Clamped
- `frame` with wrong shape: Raises `ValueError` (expected HxWx3)
- `frame` with wrong dtype: Raises `ValueError` (expected uint8)
- `signals` missing required keys: Treated as 0.0 (no error)

### Resource Limits

- **Memory**: 8-frame buffer at full resolution (e.g., 8 × 1920×1080×3 ≈ 48 MB for 1080p)
- **CPU**: ~15-25 ms per 1080p frame on modern CPU (single-threaded)
- **GPU**: Optional shader acceleration reduces CPU load to ~5-10 ms
- **Maximum Resolution**: 4K (3840×2160) supported but may drop frames at 60 FPS
- **Frame Buffer**: Fixed at 8 frames; cannot be resized at runtime

### State Corruption

- **Frame buffer integrity**: Buffer may contain `None` entries if not fully populated; `_apply_temporal_displacement` handles this by returning original frame
- **Parameter drift**: Audio signal spikes can cause instantaneous parameter jumps; effect clamps values but does not smooth
- **Thread safety**: Not thread-safe; must be called from main rendering thread only
- **Memory leaks**: Frame buffer holds references to large arrays; must be explicitly cleared on shutdown

### Collaboration Session

Not applicable. This is a standalone effect plugin with no network or multi-user features.

### External Libraries

- **NumPy** (`numpy`): Core array operations
- **OpenCV** (`cv2`): Optional, for advanced image processing (warpAffine, resize, etc.)
- **random**: Python standard library for random block placement
- **os**: For shader path resolution

### Internal Modules

- `core.base_effect.BaseEffect`: Parent class providing plugin lifecycle
- `core.shader.ShaderProgram`: Optional GLSL shader wrapper

## Test Plan

### Unit Tests (pytest)

1. **test_initialization**: Verify default parameter values and buffer allocation
2. **test_load_shader_success**: Test shader loading when file exists
3. **test_load_shader_missing**: Test graceful fallback when shader missing
4. **test_update_intensity_mapping**: Verify audio-to-parameter mapping formulas
5. **test_update_clamping**: Ensure parameters clamped to [0.0, 1.0]
6. **test_draw_no_effect**: Verify `draw()` returns `None` when intensity ≤ 0.1
7. **test_apply_corruption**: Test block corruption produces valid output shape
8. **test_apply_pixelation**: Test pixelation reduces effective resolution
9. **test_apply_color_shift**: Test RGB shift creates visible channel offset
10. **test_apply_scan_lines**: Test scan lines add horizontal dark bands
11. **test_apply_temporal_displacement**: Test frame buffer mixing with insufficient buffer
12. **test_frame_buffer_rollover**: Verify buffer index wraps correctly after 8 frames
13. **test_invalid_frame_shape**: Test error handling for wrong frame dimensions
14. **test_invalid_frame_dtype**: Test error handling for non-uint8 frames
15. **test_missing_audio_signals**: Test default 0.0 for missing signal keys
16. **test_performance_1080p**: Benchmark CPU path < 33ms per frame
17. **test_performance_4k**: Benchmark CPU path < 200ms per frame (warning threshold)
18. **test_memory_usage**: Verify buffer holds exactly 8 frames, no leaks

### Integration Tests

1. **test_full_pipeline**: Process 100 frames with synthetic audio, verify no crashes
2. **test_audio_reactivity**: Sweep audio parameters from 0→1, verify monotonic effect increase
3. **test_effect_blending**: Combine multiple glitch types, verify no color overflow
4. **test_real_time_playback**: 60-second real-time simulation at 30 FPS, monitor dropped frames

### Performance Benchmarks

- **Target (1080p)**: ≤ 25 ms/frame (CPU), ≤ 10 ms/frame (GPU shader)
- **Acceptable (1080p)**: ≤ 33 ms/frame (30 FPS sustained)
- **Maximum (4K)**: ≤ 200 ms/frame (5 FPS minimum)

## Definition of Done

### Performance Targets

- [ ] CPU path processes 1080p frames in ≤ 25 ms average (tested on reference hardware)
- [ ] GPU shader path (if implemented) processes 1080p in ≤ 10 ms
- [ ] No memory leaks after 10,000 frame iterations
- [ ] Frame buffer circular wrap operates without index errors

### Quality Standards

- [ ] All 18 unit tests pass (≥ 80% code coverage)
- [ ] Integration tests pass on CI with headless OpenCV
- [ ] Parameter clamping prevents out-of-range values
- [ ] Graceful degradation when OpenCV unavailable
- [ ] Shader loading failure does not crash application
- [ ] Code follows project style guide (black, isort, mypy)
- [ ] No `print()` statements in production code (use logging)
- [ ] All public methods have complete docstrings with type hints

### Legacy References

- **Source Codebase**: `vjlive`
- **Primary Implementation**: `/home/happy/Desktop/claude projects/vjlive/effects/example_glitch.py` (211 lines)
- **Shader Reference**: `/home/happy/Desktop/claude projects/vjlive/effects/example_glitch.frag` (missing in legacy)
- **Plugin Manifest**: `vjlive/core/plugins/examples/example_glitch_effect.json`
- **Core Plugin**: `vjlive/core/core_plugins/examples/example_glitch_effect.py`

### Porting Strategy

1. **Phase 1 - Framework**: Create `ExampleGlitchEffect` class inheriting from `BaseEffect` in VJLive3 architecture
2. **Phase 2 - Parameters**: Define `@dataclass` for configuration with validation
3. **Phase 3 - CPU Pipeline**: Implement 5 effect methods using NumPy/OpenCV
4. **Phase 4 - Frame Buffer**: Implement circular buffer with proper memory management
5. **Phase 5 - Shader (Optional)**: Write GLSL 330 core shader for GPU acceleration
6. **Phase 6 - Audio Mapping**: Connect audio analyzer signals to parameters
7. **Phase 7 - Testing**: Write unit tests for each effect method
8. **Phase 8 - Optimization**: Profile and optimize hot loops (use Numba if needed)
9. **Phase 9 - Integration**: Register plugin manifest, ensure METADATA compliance
10. **Phase 10 - Documentation**: Update API docs and user guide

### Risks

- **Missing Shader Source**: The legacy `.frag` file was not found in the codebase. Must reconstruct GLSL from CPU implementation or omit GPU path.
- **OpenCV Dependency**: Project may not include `cv2`; need to implement pure NumPy fallbacks for all effects.
- **Performance**: CPU image processing at 1080p/60 FPS is challenging; may need to reduce effect complexity or use Numba JIT.
- **Audio Signal Assumptions**: Legacy code expects specific signal keys (`treble`, `mid`, `bass`, `volume`); must ensure audio analyzer provides these.
- **Frame Format Mismatch**: Legacy uses RGB; VJLive3 may use RGBA or different color space; need conversion layer.

## References

- **VJLive3 Architecture**: `ARCHITECTURE.md`
- **Plugin System**: `WORKSPACE/PRIME_DIRECTIVE.md` (Section 4: Plugin System Integrity)
- **Safety Rails**: `WORKSPACE/SAFETY_RAILS.md` (60 FPS sacred, offline-first)
- **Template**: `docs/specs/_TEMPLATE.md`
- **Similar Specs**: `docs/specs/P3-EXT001_ASCIIEffect.md` (CPU-based effect pattern)
