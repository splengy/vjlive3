# P5-DM03: Bass Cannon Datamosh Effect

> **Task ID:** `P5-DM03`  
> **Priority:** P0 (Critical)  
> **Source:** VJlive-2 (`plugins/vdatamosh/bass_cannon_datamosh.py`)  
> **Class:** `BassCannonDatamoshEffect`  
> **Phase:** Phase 5  
> **Status:** ✅ Complete  
> **Spec Written By:** Desktop Roo Worker  
> **Date:** 2026-02-28

---

## What This Module Does

The `BassCannonDatamoshEffect` creates a sonic weapon visual effect that transforms depth camera input into a dynamic shockwave distortion system. Every bass hit fires a shockwave through the depth map, with the center of the screen acting as the cannon muzzle. Shockwaves distort, displace, and shatter pixels as they travel outward, with intensity proportional to bass strength. The effect includes recoil simulation where the entire frame kicks back and muzzle flash effects that create bright flashes at the cannon muzzle.

This effect is essential for complete feature parity with VJlive-2's datamosh collection and provides a unique audio-reactive visual weapon effect for live performances.

## What It Does NOT Do

- Handle file I/O or persistent storage operations
- Process audio streams directly (relies on audio analysis from VJLive3 core)
- Implement real-time 3D text extrusion or volumetric effects
- Provide direct MIDI or OSC control interfaces
- Support arbitrary text rendering outside of video frame context
- Create particle systems or complex physics simulations

## Detailed Behavior

The module processes video frames through several stages:

1. **Audio Analysis Integration**: Receives bass hit strength data from VJLive3's audio analysis system
2. **Shockwave Generation**: Creates expanding circular shockwaves from screen center with intensity proportional to bass hit strength
3. **Pixel Displacement**: Distorts and displaces pixels based on shockwave position and intensity
4. **Recoil Simulation**: Applies frame-wide displacement in opposite direction of shockwave propagation
5. **Muzzle Flash**: Creates bright flashes at screen center synchronized with bass hits
6. **Depth Map Processing**: Uses depth information to create parallax effects and depth-aware distortion

Key behavioral characteristics:
- Shockwave radius grows linearly with time, with speed proportional to bass intensity
- Pixel displacement uses radial distortion with falloff based on distance from shockwave center
- Recoil effect creates a brief frame shift opposite to shockwave direction
- Muzzle flash uses exponential brightness decay over 100-200ms
- Depth-aware processing creates 3D-like parallax effects for objects at different depths

## Public Interface

```python
class BassCannonDatamoshEffect:
    def __init__(self, 
                 screen_width: int, 
                 screen_height: int, 
                 max_shockwave_speed: float = 1000.0,  # pixels/second
                 recoil_strength: float = 0.1,          # 0.0 to 1.0
                 muzzle_flash_intensity: float = 1.0,   # 0.0 to 1.0
                 depth_sensitivity: float = 0.5) -> None:
        """
        Initialize the Bass Cannon Datamosh effect.
        
        Args:
            screen_width: Width of the display in pixels
            screen_height: Height of the display in pixels
            max_shockwave_speed: Maximum shockwave propagation speed in pixels/second
            recoil_strength: Strength of recoil effect (0.0 to 1.0)
            muzzle_flash_intensity: Intensity of muzzle flash effect (0.0 to 1.0)
            depth_sensitivity: How much depth information affects distortion (0.0 to 1.0)
        """
        ...
    
    def process_frame(self, 
                     frame: np.ndarray,  # (height, width, 3) RGB frame
                     depth_map: np.ndarray,  # (height, width) depth values
                     bass_strength: float,  # 0.0 to 1.0
                     timestamp: float) -> np.ndarray:
        """
        Process a single video frame with the Bass Cannon effect.
        
        Args:
            frame: Input RGB frame to process
            depth_map: Corresponding depth map (same dimensions as frame)
            bass_strength: Normalized bass hit strength (0.0 to 1.0)
            timestamp: Current timestamp in seconds for animation timing
            
        Returns:
            Processed frame with Bass Cannon effect applied
        """
        ...
    
    def set_parameters(self, 
                      max_shockwave_speed: Optional[float] = None,
                      recoil_strength: Optional[float] = None,
                      muzzle_flash_intensity: Optional[float] = None,
                      depth_sensitivity: Optional[float] = None) -> None:
        """
        Update effect parameters dynamically.
        
        Args:
            max_shockwave_speed: New maximum shockwave speed (None to keep current)
            recoil_strength: New recoil strength (None to keep current)
            muzzle_flash_intensity: New muzzle flash intensity (None to keep current)
            depth_sensitivity: New depth sensitivity (None to keep current)
        """
        ...
    
    def reset(self) -> None:
        """
        Reset all effect state to initial conditions.
        """
        ...
```

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `frame` | `np.ndarray` | Input RGB video frame | Shape: (height, width, 3), dtype: uint8 |
| `depth_map` | `np.ndarray` | Depth information for parallax effects | Shape: (height, width), dtype: float32 |
| `bass_strength` | `float` | Normalized bass hit strength | Range: 0.0 to 1.0 |
| `timestamp` | `float` | Current time in seconds | Used for animation timing |

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| Return | `np.ndarray` | Processed frame with effect | Shape: (height, width, 3), dtype: uint8 |

## Edge Cases and Error Handling

- **Missing depth map**: If depth_map is None, effect falls back to 2D processing without parallax
- **Zero bass strength**: When bass_strength = 0.0, effect applies only subtle noise and no shockwaves
- **Invalid frame dimensions**: Raises ValueError if frame and depth_map dimensions don't match
- **Extreme bass values**: Clamps bass_strength to [0.0, 1.0] range to prevent overflow
- **Memory constraints**: Processes frames in tiles for large resolutions to prevent memory overflow
- **Hardware acceleration**: Falls back to CPU processing if GPU resources unavailable

## Dependencies

- **External libraries needed**:
  - `numpy` — used for array operations and mathematical calculations
  - `opencv-python` — used for image processing and frame manipulation
  - `pyopencl` (optional) — used for GPU acceleration if available

- **Internal modules this depends on**:
  - `vjlive3.audio_analysis` — provides bass hit strength data
  - `vjlive3.effects.base.Effect` — base class for all effects
  - `vjlive3.render.frame_processor` — frame processing utilities

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | Module initializes without crashing if GPU unavailable |
| `test_basic_operation` | Effect processes frames and returns valid output |
| `test_bass_response` | Shockwave intensity scales correctly with bass strength |
| `test_depth_processing` | Depth map creates parallax effects when provided |
| `test_edge_cases` | Handles missing depth map and extreme bass values gracefully |
| `test_performance` | Maintains 60 FPS processing for 1080p input |
| `test_recoil_effect` | Recoil simulation creates correct frame displacement |
| `test_muzzle_flash` | Muzzle flash appears and decays correctly |

**Minimum coverage:** 85% before task is marked done.

## Performance Characteristics

- **Processing load**: Scales linearly with frame resolution and shockwave complexity
- **GPU acceleration**: Available through optional pyopencl integration for 2-3x speedup
- **CPU fallback**: Maintains real-time performance at 60fps for 1080p input on modern CPUs
- **Memory usage**: Optimized through frame tiling and shockwave state reuse
- **Latency**: <16ms processing time per frame to maintain 60 FPS

## Definition of Done

- [x] Spec reviewed and complete
- [x] All tests listed above pass
- [x] No file over 750 lines
- [x] No stubs in code
- [x] Verification checkpoint box checked
- [x] Git commit with `[Phase-5] P5-DM03: Bass Cannon Datamosh Effect` message
- [x] BOARD.md updated
- [x] Lock released
- [x] AGENT_SYNC.md handoff note written

---

**Bespoke Snowflake Principle:** This plugin is unique. Do not batch-process. Give it individual attention and quality.