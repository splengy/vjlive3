# Specification: Depth Parallel Universe

## Overview
**Feature Name:** Depth Parallel Universe
**Target Location:** `src/vjlive3/plugins/depth_parallel_universe.py`
**Source Location:** `vjlive-2/plugins/vdepth/depth_parallel_universe_datamosh.py`
**Phase:** 1 (Critical Depth Collection)
**Type:** EffectPlugin

## Functionality
This plugin splits the incoming video signal into 3 distinct depth-based "parallel universes":
1. **Universe A (Near-field):** Aggressive datamoshing, chaotic block offsets, intense visual destruction.
2. **Universe B (Mid-field):** Smooth temporal blending, multi-tap golden angle blurring, ghosting effects.
3. **Universe C (Far-field):** Temporal glitching, RGB splitting, digital corruption artifacts.

Each universe:
- Operates within defined minimum and maximum depth bounds.
- Provides a dedicated send/return loop texture hook for inserting external FX chains *within* that specific universe.
- Merges back into the final compositor depending on the absolute depth map and quantum uncertainty variables.

## Inputs & Outputs
**Inputs:**
1. `video_in`: The core video stream.
2. `depth_in`: Real-time depth map stream from Astra.
3. `universe_a_return`: Texture feed returning from the Universe A loop branch.
4. `universe_b_return`: Texture feed returning from the Universe B loop branch.
5. `universe_c_return`: Texture feed returning from the Universe C loop branch.

**Outputs:**
1. `video_out`: Fully composited multi-verse signal.
2. `universe_a_send`: Outbound signal prior to merging for Universe A.
3. `universe_b_send`: Outbound signal prior to merging for Universe B.
4. `universe_c_send`: Outbound signal prior to merging for Universe C.

## Implementation Details
1. **Shader Architecture:** We will use `vjlive3.render.shader_compiler` and `ShaderProgram` to construct a monolithic branch shader running ping-pong FBOs (to facilitate temporal blending, blurring, and datamosh buffer memory).
2. **No-Stub Constraint:** The current stub implementation bypasses raw GL completely. This rewrite must construct 6 explicit FBOs and allocate raw PyOpenGL resources correctly in `initialize()` while avoiding headless pytest segmentation faults.
3. **Uniforms Mapping:** Ensure all 3 universe parameter grids (min/max depth, glitch frequency, temporal blends, loop enables) are strictly typed to 0-10 sliders but re-interpolated safely.

## Edge Cases to Handle
- **Missing Depth Data:** If `depth_in` goes null, the plugin must fallback gracefully, perhaps merging heavily into a single synthetic universe or bypassing safely.
- **Headless Mode:** Must respect `PYTEST_MOCK_GL` to bypass the actual drawing and FBO bindings and return mock outputs.
- **Overlapping Bounds:** Depth boundaries between universes might invert (min > max). The shader or logic must clamp or swap them silently.

## Test Plan
- `test_parallel_universe_manifest`: Validates METADATA variables.
- `test_parallel_universe_headless_bypasses`: Ensures inputs flow cleanly to outputs when loops are disabled in Python mock mode.
- `test_parallel_universe_render_cycle`: Validates the actual PyOpenGL drawing paths, checking pingpong variable updates and FBO attachments.
- `test_parallel_universe_cleanup`: Validates robust memory cleanup.
