# P3-EXT214: BackgroundSubtractionEffect

## Specification Status
- **Phase**: Pass 1 (Skeleton)
- **Target Phase**: Pass 2 (Detailed Technical Spec)
- **Priority**: P0
- **Module**: `depth_effects` plugin system
- **Implementation Path**: `src/vjlive3/plugins/depth_effects/background_subtraction.py`
- **Effect Type**: Depth-Based Segmentation

## Executive Summary

BackgroundSubtractionEffect uses depth data to isolate foreground subjects from backgrounds, creating interactive visual effects that respond to human presence and movement. It implements real-time background modeling and subtraction to segment depth video into foreground masks suitable for particle effects, lighting masks, and interactive installations.

## Problem Statement

Interactive VJ performances need to isolate performers or audience members from static backgrounds:
- Standard chroma-key fails in low-light venues
- Depth-based approaches are more robust and don't require specific clothing
- Traditional background subtraction (frame differencing) is noisy
- Depth background modeling is computationally expensive

BackgroundSubtractionEffect bridges this gap by efficiently modeling depth backgrounds and subtracting them to create clean foreground masks.

## Solution Overview

The effect maintains a statistical background model:
1. **Background modeling**: Learn depth distribution per pixel over time
2. **Model update**: Incrementally update background with adaptive learning rate
3. **Foreground detection**: Compare current frame to model
4. **Morphological cleanup**: Remove noise via erosion/dilation
5. **Confidence mapping**: Generate continuous foreground confidence map
6. **Mask generation**: Binary or soft foreground masks

## Detailed Behavior

### Phase 1: Background Model Initialization
Learn background distribution from initial frames (warmup period)

### Phase 2: Frame Input
Receive new depth frame and timestamp

### Phase 3: Foreground Detection
Compare frame to background model, compute difference

### Phase 4: Morphological Processing
Apply erosion/dilation to clean foreground mask

### Phase 5: Confidence Calculation
Generate soft mask with confidence values

### Phase 6: Model Update
Incrementally update background model for adaptation

### Phase 7: Output
Generate foreground mask or segmentation map

## Public Interface

```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Tuple
import numpy as np

class BackgroundModel(Enum):
    """Background modeling strategy."""
    GAUSSIAN = "gaussian"         # Per-pixel Gaussian mixture
    MEDIAN = "median"             # Temporal median background
    ADAPTIVE = "adaptive"          # Adaptive per-pixel mean/variance
    MOG2 = "mog2"                 # Mixture of Gaussians (GMM)

class ForegroundMethod(Enum):
    """Foreground detection method."""
    THRESHOLD = "threshold"       # Simple depth threshold
    MAHALANOBIS = "mahalanobis"   # Mahalanobis distance
    ZSCORE = "zscore"             # Z-score deviation (simple)

@dataclass
class SegmentationResult:
    """Result from background subtraction."""
    foreground_mask: np.ndarray    # Binary or soft mask [0, 1]
    confidence: np.ndarray         # Per-pixel confidence [0, 1]
    num_foreground_pixels: int     # Pixel count in foreground
    foreground_area_ratio: float   # Foreground / total area [0, 1]

class BackgroundSubtractionEffect:
    """Depth-based background subtraction and foreground segmentation."""
    
    def __init__(self, width: int, height: int):
        """Initialize effect."""
    
    def update(self, depth_frame: np.ndarray, dt: float) -> None:
        """Process new depth frame."""
        # Update background model
        # Detect foreground pixels
        # Update internal state
    
    def render(self) -> np.ndarray:
        """Generate foreground mask output."""
        # Apply morphological operations
        # Compute confidence map
        # Return mask
    
    def get_segmentation(self) -> SegmentationResult:
        """Get detailed segmentation result with statistics."""
    
    def reset_background(self) -> None:
        """Clear background model and re-initialize."""
    
    # Parameters
    @property
    def model_type(self) -> BackgroundModel:
        """Get/set background modeling strategy."""
    
    @model_type.setter
    def model_type(self, model: BackgroundModel) -> None:
        """Change background model type."""
    
    @property
    def detection_method(self) -> ForegroundMethod:
        """Get/set foreground detection method."""
    
    @detection_method.setter
    def detection_method(self, method: ForegroundMethod) -> None:
        """Change detection method."""
    
    @property
    def threshold(self) -> float:
        """Depth difference threshold (mm)."""
    
    @threshold.setter
    def threshold(self, value: float) -> None:
        """Set detection threshold (10-200 mm)."""
    
    @property
    def learning_rate(self) -> float:
        """Background model adaptation rate [0.001, 0.1]."""
    
    @learning_rate.setter
    def learning_rate(self, value: float) -> None:
        """Set how quickly model adapts to changes."""
    
    @property
    def morphology_iterations(self) -> int:
        """Number of erosion/dilation passes."""
    
    @morphology_iterations.setter
    def morphology_iterations(self, value: int) -> None:
        """Set morphology iterations (1-5)."""
    
    @property
    def morphology_kernel_size(self) -> int:
        """Size of morphological kernel (pixels)."""
    
    @property
    def min_foreground_area(self) -> int:
        """Minimum foreground pixel count to keep."""
    
    @min_foreground_area.setter
    def min_foreground_area(self, count: int) -> None:
        """Filter out small components."""
    
    @property
    def use_soft_mask(self) -> bool:
        """Whether to output soft mask [0-1] or binary."""
    
    @property
    def warmup_frames(self) -> int:
        """Number of frames for background initialization."""
    
    @property
    def is_initialized(self) -> bool:
        """Check if background model is trained."""
```

## Mathematical Formulations

### Gaussian Background Model (Per-Pixel)
$$\mu_i = \alpha \cdot Z_i + (1 - \alpha) \cdot \mu_{i-1}$$
$$\sigma_i = \sqrt{\alpha (Z_i - \mu_i)^2 + (1 - \alpha) \sigma_{i-1}^2}$$

### Z-Score Detection
$$z = \frac{Z_{\text{current}} - \mu}{\sigma}$$
$$\text{foreground} = |z| > \tau \quad \text{where } \tau \in [2, 3]$$

### Mahalanobis Distance
$$D = \sqrt{(Z - \mu)^T \Sigma^{-1} (Z - \mu)}$$

### Temporal Median Background
$$\text{background} = \text{median}(Z_{t-N}, ..., Z_t)$$

### Morphological Erosion
$$\text{eroded}(x,y) = \min_{(i,j) \in K} \text{mask}(x+i, y+j)$$

### Dilation
$$\text{dilated}(x,y) = \max_{(i,j) \in K} \text{mask}(x+i, y+j)$$

## Performance Characteristics

- **Frame rate**: 30-60 FPS @ 640×480 (depends on method)
- **CPU usage**: 15-40% per frame (morphology heavy)
- **Memory**: ~30MB for model + workspace buffers
- **Latency**: 16-50ms per frame
- **Model overhead**: ~200KB per pixel per model type

## Test Plan

1. **Initialization**
   - Warmup period correct
   - Background model converges
   - State initialized properly

2. **Foreground Detection**
   - Static foreground detected when object present
   - Background unchanged when object absent
   - Threshold parameter affects sensitivity

3. **Morphological Cleaning**
   - Erosion removes noise
   - Dilation fills gaps
   - Iterations parameter controls strength

4. **Model Adaptation**
   - Model updates with new background
   - Learning rate controls speed
   - Sudden changes tracked smoothly

5. **Segmentation Results**
   - Foreground area calculated correctly
   - Confidence values in [0, 1]
   - Soft vs hard mask toggle works

6. **Reset Functionality**
   - Reset clears model
   - Re-initialization after reset works

7. **Performance**
   - Target FPS achieved
   - Memory bounded
   - Latency acceptable

## Definition of Done

- [ ] Background model implemented (≥2 types)
- [ ] Foreground detection algorithm working
- [ ] Morphological operations functional
- [ ] Learning rate adaptation correct
- [ ] Confidence map generation working
- [ ] All parameters exposed and settable
- [ ] 15+ test cases passing
- [ ] Frame rate target met
- [ ] Memory usage bounded
- [ ] Warmup period functioning
- [ ] Reset capability working
- [ ] Soft/hard mask toggle
- [ ] Connected component filtering working
- [ ] No stubs or TODOs
- [ ] Complete docstrings
- [ ] Performance benchmarked
- [ ] ≤900 lines of code

## Dependencies

- NumPy (image operations)
- SciPy (morphological operations)
- OpenCV (optional, for faster morphology)
- VJLive3 Depth effect base class

## Related Specs

- P3-DEPTH-VIZ: Depth visualization
- P3-DEPTH-MUX: Depth data multiplexing
- P3-MORPHOLOGY-OPS: Morphological operations library
- P3-SEGMENTATION: Segmentation/connected components

---

**Notes for Pass 2 Implementation:**
- Recommend GMM (MOG2) as primary model, Gaussian as fallback
- Define typical threshold range (20-100mm typical)
- Confirm learning rate defaults (0.01-0.05 typical)
- Document expected false-positive rate and tuning strategy
- Consider hardware acceleration (GPU morphology) if performance needed
