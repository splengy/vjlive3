# Specification: Depth Portal Composite

## Overview
**Feature Name:** Depth Portal Composite
**Target Location:** `src/vjlive3/plugins/depth_portal_composite.py`
**Source Location:** `vjlive-2/plugins/vdepth/depth_portal_composite.py`
**Phase:** 1 (Critical Depth Collection)
**Type:** EffectPlugin

## Functionality
This plugin performs "green screen without the green screen" by utilizing Astra depth data to isolate a performer (the alpha matte) and composite their silhouette over a secondary video source (the background).

It computes a feathered matte via smooth-stepping the near and far depth bounds, applying optional spill suppression across the edges, and rendering the scaled/offset foreground performer over the background feed.

## Inputs & Outputs
**Inputs:**
1. `video_in`: The secondary video feed acting as the new background replacement.
2. `depth_in`: Real-time depth map stream from Astra (creates the isolation matte).
3. `color_in`: Real-time RGB color stream from Astra (the actual performer's appearance).

**Outputs:**
1. `video_out`: Fully composited frame containing the performer over the background.

## Uniforms & Parameters
All parameters are scaled to the standard `0.0` - `1.0` float signal rail in VJLive3 instead of the `0.0`-`10.0` range found in VJLive-2.

- **sliceNear:** Near depth threshold for isolation.
- **sliceFar:** Far depth threshold for isolation.
- **edgeSoftness:** Feathering of the depth matte edges.
- **spillSuppress:** Suppress background color bleeding at edges.
- **bgOpacity:** Opacity of the replacement background video.
- **fgScale:** Scale multiplier of the foreground performer.
- **fgOffsetX:** Horizontal position of the performer.
- **fgOffsetY:** Vertical position of the performer.

## Implementation Details
1. **Shader Architecture:** Requires 3 discrete texture bindings (`tex0` for background, `tex1` for depth map, `tex2` for foreground RGB). We will use `vjlive3.render.shader_compiler` or `vjlive3.render.program.ShaderProgram` if feasible, but more likely raw PyOpenGL shader compilation matching `Depth Parallel Universe`.
2. **No-Stub Constraint:** The plugin must actually compile the shader, bind the uniforms, map the textures to their respective active units (`GL_TEXTURE0`, `GL_TEXTURE1`, `GL_TEXTURE2`), and draw the quad. 
3. **Headless Mocking:** Respect `PYTEST_MOCK_GL` to bypass the actual drawing logic during the test suite execution.

## Edge Cases to Handle
- **Missing Inputs:** If `depth_in` or `color_in` is missing, the plugin must fail open by just returning the `video_in` texture uninterrupted. 
- **Missing Background:** If `video_in` is missing, composite the performer over a black background.

## Test Plan
- `test_portal_composite_manifest`: Validates METADATA variables.
- `test_portal_composite_headless_bypasses`: Ensures inputs flow cleanly to outputs when loops are disabled in Python mock mode.
- `test_portal_composite_missing_inputs`: Ensures the plugin returns the background unmodified if the depth map/color maps are missing.
- `test_portal_composite_render_cycle`: Validates the actual PyOpenGL drawing paths, checking quad rendering and texture unit bindings.
- `test_portal_composite_cleanup`: Validates robust memory cleanup.
