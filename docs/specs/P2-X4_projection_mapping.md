# Spec Template — P2-X4 Projection Mapping

**File naming:** `docs/specs/P2-X4_projection_mapping.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P2-X4 — Projection Mapping (Warp, Edge-Blend, Mask)

**Phase:** Phase 2
**Assigned To:** (Pending Manager Assignment)
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

This module extends the basic output mapper (P2-X3) into a professional multi-projector projection mapping system. It introduces `EdgeBlend` (smooth gradient falloffs where two projector beams overlap) and `Mask` (polygonal black-out areas to avoid projecting on windows, people, or outside the projection surface). It operates as a post-processing pass on the warped slices before they are sent to physical displays.

---

## What It Does NOT Do

- It does NOT automatically align projectors using cameras (that is a separate auto-calibration task).
- It does NOT handle the raw 2D slicing (that belongs to P2-X3). It strictly adds blending and masking layers to those slices.

---

## Public Interface

```python
import numpy as np
from typing import List, Tuple
from dataclasses import dataclass

@dataclass
class BlendRegion:
    edge: str  # 'left', 'right', 'top', 'bottom'
    width: float  # Normalized 0.0 to 1.0 width of the blend zone
    gamma: float = 1.0  # Curve for the blend falloff
    luminance: float = 0.5  # Center point luminance adjustment

@dataclass
class PolygonMask:
    points: List[Tuple[float, float]]  # Normalized 0.0 to 1.0 coordinates
    inverted: bool = False  # True = mask outside, False = mask inside

class ProjectionMapper:
    """Applies edge blending and masking to a warped slice."""
    def __init__(self, slice_width: int, slice_height: int) -> None: ...
    
    def set_blend(self, region: BlendRegion) -> None: ...
    def clear_blend(self, edge: str) -> None: ...
    
    def add_mask(self, mask: PolygonMask) -> int: ...
    def remove_mask(self, mask_id: int) -> bool: ...
    
    def process_slice(self, texture_id: int) -> int:
        """Applies blending and masks, returning final texture ID."""
        ...
```

---

## Inputs and Outputs

| Feature | Input | Rendering Mechanism |
|---------|-------|---------------------|
| Edge Blend | `BlendRegion` config | Applied via a GLSL fragment shader multiplying the edge gradient by the texture. |
| Mask | `PolygonMask` points | Rendered as black geometry to the FBO or using a stencil buffer. |
| Video | GL Texture ID | Sourced from `OutputMapper` |
| Output | GL Texture ID | Final output ready for Spout/NDI/Display |

---

## Edge Cases and Error Handling

- **Overlapping Blends**: If a user sets a left blend of 0.6 and a right blend of 0.6 (sum > 1.0), the system must clamp them to 0.5 each to prevent mathematical inversion and visual artifacts.
- **Malformed Masks**: If a polygon mask has less than 3 points, it is safely ignored during the render pass.
- **Performance**: Masking and blending must be done entirely on the GPU via GLSL shaders. CPU-based numpy masking will violate the 60 FPS constraint (SAFETY RAIL #1).

---

## Dependencies

- Requires an active OpenGL context (P1-R1).
- Depends heavily on the `OutputMapper` structure from P2-X3.

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_blend_region_clamping` | Adding intersecting blend regions automatically clamps their sizes to prevent overlap conflicts. |
| `test_mask_validation` | Passing a 2-point mask does not crash the system. |
| `test_projection_mapper_pipeline` | `process_slice` runs without raising GL errors and returns a valid texture ID. |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-2] P2-X4: Projection mapping edge-blend and masks` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written
