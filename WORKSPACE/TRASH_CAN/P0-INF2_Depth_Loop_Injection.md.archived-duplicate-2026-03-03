# P0-INF2 Phase 1: Depth Loop Injection

## What this module does
The `DepthLoopInjection` plugin is a specialized depth processing effect from the legacy `vjlive` codebase (originally located at `plugins/vdepth/depth_loop_injection_datamosh.py`). It captures an incoming depth buffer and injects a temporal feedback loop into the depth data, creating an echoing, datamoshed, "hall of mirrors" spatial extrusion effect based on 3D depth movement. It uses ModernGL for hardware-accelerated feedback processing.

## Public Interface
- `class DepthLoopInjection(PluginBase)`
- `async def __init__(self, context: PluginContext)`
- `async def process(self, frame: np.ndarray, audio_data: dict) -> np.ndarray` 

## Inputs and Outputs
- **Inputs**: 
  - `frame` (np.ndarray): The incoming 2D depth frame or RGBA matrix.
  - Parameters: `feedback_amount` (0.0 - 1.0, controls the opacity of the feedback trail), `decay_rate` (0.01 - 0.5, controls how quickly the depth extrusion fades into the background).
- **Outputs**: 
  - Returns a modified `np.ndarray` containing the processed depth frame with injected recursive temporal feedback.
- **Edge cases**: If the frame is entirely static, the feedback will slowly normalize based on `decay_rate`. If the resolution dynamically changes, the internal feedback buffer must flush and resize to prevent memory corruption.

## What it does NOT do
This module does not calculate optical flow. It does not perform color-based datamoshing. It operates purely on temporal frame buffering and blending, tailored for depth matrix inputs.

## Test Plan
- `test_depth_loop_injection_initialization`: Verify plugin context and default parameter loading.
- `test_depth_loop_injection_processing`: Verify that passing identical static frames over time results in output normalization via decay.
- `test_depth_loop_injection_resize`: Verify that changing the input resolution midway resets the feedback buffer without raising exceptions.
- `test_performance_60fps`: Ensure processing the frame feedback takes less than `16.6ms`.
