# P3-EXT167: SimulatedColorDepth Effect

## Specification Status
- **Phase**: Pass 1 (Skeleton)
- **Target Phase**: Pass 2 (Detailed Technical Spec)
- **Priority**: P0
- **Module**: `simulated_color_depth` plugin
- **Implementation Path**: `src/vjlive3/plugins/simulated_color_depth.py`
- **Effect Type**: Depth Simulation/Generation

## Executive Summary

SimulatedColorDepth generates plausible 3D depth maps from RGB video input using color-to-depth heuristics. It creates synthetic depth data for depth-processing effects when actual depth sensors (Kinect, RealSense) are unavailable, enabling depth-based visual effects on standard camera feeds.

## Problem Statement

Many VJLive3 effects require depth data (segmentation, 3D positioning, particle sources). However:
- Not all venues have depth camera hardware
- Depth sensors add cost, complexity, and calibration burden
- Software-only effects have larger audience

SimulatedColorDepth bridges this by using intelligent color analysis to infer plausible depth, allowing depth effects to work with standard RGB input.

## Solution Overview

The effect uses multiple heuristics to estimate depth:
1. **Color saturation**: Higher saturation → objects closer (perceptual heuristic)
2. **Hue distribution**: Certain hues associate with depth (red closer, blue further)
3. **Luminance gradient**: Luminance discontinuities often mark depth boundaries
4. **Temporal consistency**: Optical flow indicates relative depth movement
5. **Contrast analysis**: High local contrast suggests closer objects

These signals are weighted and combined into a synthetic depth map that serves as 16-bit grayscale output.

## Detailed Behavior

### Phase 1: Color Analysis
Decompose input to HSL/LAB color spaces

### Phase 2: Heuristic Evaluation
Calculate depth scores from saturation, hue, gradient, contrast

### Phase 3: Temporal Filtering
Apply optical flow for temporal consistency

### Phase 4: Depth Map Generation
Combine heuristics into unified depth image

### Phase 5: Refinement
Apply bilateral filtering and edge preservation

### Phase 6: Output
Generate 16-bit depth frame buffer

## Public Interface

```python
from enum import Enum
from dataclasses import dataclass
from typing import Tuple, Optional
import numpy as np

class DepthHeuristic(Enum):
    """Available depth estimation heuristic."""
    SATURATION = "saturation"
    HUE = "hue"
    LUMINANCE = "luminance"
    OPTICAL_FLOW = "optical_flow"
    CONTRAST = "contrast"
    EDGE_BASED = "edge_based"

@dataclass
class HeuristicWeights:
    """Weights for combining depth heuristics."""
    saturation: float = 0.25
    hue: float = 0.20
    luminance: float = 0.20
    optical_flow: float = 0.15
    contrast: float = 0.15
    edge_based: float = 0.05

class SimulatedColorDepthEffect:
    """Generate synthetic depth from RGB color input."""
    
    def __init__(self, width: int, height: int):
        """Initialize depth generator."""
    
    def update(self, rgb_frame: np.ndarray, dt: float) -> None:
        """Update with new RGB frame."""
        # Analyze color properties
        # Compute heuristic scores
        # Apply temporal filtering
    
    def render(self) -> np.ndarray:
        """Output 16-bit depth frame."""
        # Combine heuristics
        # Apply refinement
        # Return depth buffer
    
    def get_heuristic_layers(self) -> dict:
        """Return individual heuristic outputs for debugging."""
    
    # Parameters
    @property
    def weights(self) -> HeuristicWeights:
        """Get/set heuristic combination weights."""
    
    @weights.setter
    def weights(self, w: HeuristicWeights) -> None:
        """Update heuristic weights (must sum to ~1.0)."""
    
    @property
    def temporal_smoothing(self) -> float:
        """Temporal filter strength (0-1)."""
    
    @temporal_smoothing.setter
    def temporal_smoothing(self, value: float) -> None:
        """Set temporal smoothing."""
    
    @property
    def depth_scale(self) -> float:
        """Scale factor for depth range (1-10)."""
    
    @property
    def invert_depth(self) -> bool:
        """Whether to invert depth (close=white vs close=black)."""
    
    @invert_depth.setter
    def invert_depth(self, value: bool) -> None:
        """Toggle depth polarity."""
    
    @property
    def focus_distance(self) -> float:
        """Distance of focus plane (0-100)."""
    
    @property
    def blur_radius(self) -> int:
        """Bilateral filter radius (1-15 pixels)."""
```

## Mathematical Formulations

### Saturation-based Depth
$$d_s = \text{saturation}(RGB) \quad \in [0, 1]$$

### Hue-based Depth
$$d_h = \frac{|H - H_{\text{ref}}|}{180°} \quad \text{(normalized hue distance)}$$

### Luminance Gradient Depth
$$d_l = \|\nabla L\|_2 \quad \text{(Sobel gradient magnitude)}$$

### Optical Flow Depth (Temporal)
$$d_f(t) = \alpha \cdot d_f(t-1) + (1-\alpha) \cdot \|OF(t)\|_2$$
where OF is optical flow and $\alpha \in [0.7, 0.9]$ is temporal weight.

### Combined Depth
$$D(x,y) = \sum_{i} w_i \cdot d_i(x,y) \quad \text{where } \sum w_i = 1$$

### Boundary Preservation (Bilateral Filter)
$$D_{\text{refined}}(x) = \frac{\sum_y G(x,y) \cdot R(D(x)-D(y)) \cdot D(y)}{\sum_y G(x,y) \cdot R(D(x)-D(y))}$$

## Performance Characteristics

- **Frame rate**: 30-60 FPS @ 1080p (depends on optical flow)
- **CPU cost**: 40-60% single core for full processing
- **Memory**: ~100MB per resolution (buffers + temporal history)
- **Latency**: 50-100ms (includes optical flow computation)

## Test Plan

1. **Heuristic Accuracy**
   - Saturation produces reasonable depth
   - Hue mapping sensible for color space
   - Luminance gradient detects edges

2. **Temporal Consistency**
   - Optical flow computed correctly
   - Temporal smoothing parameter effective
   - No flickering artifacts

3. **Depth Range**
   - Output 16-bit range properly used
   - Scale parameter functional
   - Inversion toggle works

4. **Edge Preservation**
   - Bilateral filter preserves edges
   - Depth discontinuities intact
   - No over-smoothing

5. **Parameter Responsiveness**
   - Weight changes smooth
   - Scale changes take effect
   - Temporal parameter effective

6. **Performance**
   - Frame rate target achieved
   - Memory bounded
   - No leaks

7. **Integration**
   - Output compatible with depth effects
   - Provides heuristic layer access
   - Plays nicely with depth pipeline

## Definition of Done

- [ ] All 6 heuristics implemented
- [ ] Heuristic weight system working
- [ ] Temporal filtering functional
- [ ] Bilateral refinement correct
- [ ] 16-bit output generation
- [ ] All parameters exposed
- [ ] 15+ test cases passing
- [ ] Heuristic layer export working
- [ ] Performance benchmarked
- [ ] No memory leaks
- [ ] No stubs or TODOs
- [ ] Complete docstrings
- [ ] Parameter bounds checking
- [ ] Smooth transitions
- [ ] Invert toggle working
- [ ] Integration with depth pipeline
- [ ] ≤900 lines of code

## Dependencies

- NumPy (color space conversions)
- OpenCV (optical flow, bilateral filter)
- SciPy (Sobel gradient)
- VJLive3 Effect base class

## Related Specs

- P3-DEPTH-MUX: Depth data multiplexing (consumer)
- P3-DEPTH-VIZ: Depth visualization effects (consumer)
- P3-OPTICAL-FLOW: Optical flow computation
- P3-COLOR-SPACE: Color space conversions

---

**Notes for Pass 2 Implementation:**
- Decide between Lucas-Kanade and Farnebäck for optical flow
- Define exact hue zones for depth mapping
- Confirm depth output bit depth (16-bit vs 32-bit float)
- Test on diverse footage (portraits, landscapes, motion)
