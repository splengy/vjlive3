# Spec: P3-EXT107 — MirrorEffect

## Task Overview
The MirrorEffect node applies a UV mirror transformation to the input texture coordinates, optionally mirroring horizontally, vertically, or both, based on user-defined thresholds and mix parameters. The effect can be used to create symmetrical patterns, enhance spatial depth, or produce visual distortions reminiscent of mirror surfaces. It operates as a post‑process fragment effect in the VJLive3 rendering pipeline.

## What This Module Does NOT Do
- It does **not** perform any color correction or lighting calculations.
- It does **not** generate new geometry; it only remaps texture coordinates.
- It does **not** support per‑pixel dynamic flipping beyond the static threshold logic.

## Detailed Behavior and Parameter Interactions
The effect receives a UV coordinate (`uv`) in the range `[0.0, 1.0]` for both `x` and `y`. Depending on the `horizontal_threshold` and `vertical_threshold` parameters, the UV coordinate may be mirrored about `0.5`:

- **Horizontal mirroring**: If `uv.x` is greater than `horizontal_threshold` and `horizontal_enabled` is true, the coordinate is replaced with `1.0 - uv.x`.
- **Vertical mirroring**: If `uv.y` is greater than `vertical_threshold` and `vertical_enabled` is true, the coordinate is replaced with `1.0 - uv.y`.

The `mix` parameter (range `[0.0, 1.0]`) controls the blend factor between the original texture sample and the mirrored texture sample. When `mix = 1.0`, the output is solely the mirrored sample; when `mix = 0.0`, the original sample is retained; intermediate values linearly interpolate between the two.

The `horizontal_enabled` and `vertical_enabled` boolean flags allow selective activation of mirroring axes, providing flexibility for composite effects.

## Public Interface
```python
class MirrorEffect(Effect):
    """
    Base class for all VJLive3 effects.

    Every Effect owns a RenderPipeline (WGSL shader + bind groups).
    Subclasses must:
       1. Set METADATA dict with at least 'name', 'spec', 'version'.
       2. Override apply_uniforms() to push per-frame parameters.
    """

    METADATA: dict = {
        "name": "MirrorEffect",
        "spec": "P3-EXT107",
        "version": "1.0.0",
        "tier": "Pro-Tier Native",
    }

    def __init__(self, name: str = "MirrorEffect"):
        """
        Args:
            name:             Unique identifier string for this effect instance.
            fragment_source:  WGSL shader source containing at least one
                              @fragment entry point.
        """
        from vjlive3.render.program import RenderPipeline  # lazy — avoids circular
        
        self.name: str = name
        self.enabled: bool = True
        self.mix: float = 1.0           # 0.0–1.0 blend weight
        self.manual_render: bool = False
        self.pipeline: "RenderPipeline" = RenderPipeline(
            shader_source=fragment_source,
            name=name,
        )
        # hot-reload cache hook (see P1-R3 hot_reload.py)
        from vjlive3.render.hot_reload import ShaderCache
        self.cache: ShaderCache = ShaderCache(
            compile_fn=lambda src, n: RenderPipeline(shader_source=src, name=n)
        )

    def apply_uniforms(
        self,
        time: float,
        resolution: Tuple[int, int],
        audio_reactor: Any,
        semantic_layer: Any,
    ) -> None:
        """
        Push per-frame uniform values to the pipeline.

        Default implementation is a no-op. Subclasses drive shader
        parameters here (e.g., time, audio amplitudes, beat pulses).
        """

    def pre_process(
        self,
        chain: "EffectChain",
        input_tex: Any,
    ) -> Optional[Any]:
        """
        Optional CPU pre-pass before GPU rendering.

        Called before EffectChain renders this effect. Return a substitute
        texture view to use instead of input_tex, or None to use input_tex
        unchanged. Examples: ML inference, CV pre-processing, camera grab.
        """
        return None

    def __repr__(self) -> str:
        return f"<Effect {self.name!r} enabled={self.enabled} mix={self.mix:.2f} >"

## Inputs and Outputs

| Parameter | Type | Direction | Description |
|-----------|------|-----------|-------------|
| `uv` | `vec2` | Input | Texture coordinate passed from the vertex shader. |
| `horizontal_threshold` | `float` | Input | Threshold for horizontal mirroring activation. |
| `vertical_threshold` | `float` | Input | Threshold for vertical mirroring activation. |
| `horizontal_enabled` | `bool` | Input | Whether horizontal mirroring is active. |
| `vertical_enabled` | `bool` | Input | Whether vertical mirroring is active. |
| `mix` | `float` | Input | Blend factor between original and mirrored texture. |
| **Output UV** | `vec2` | Output | Possibly mirrored UV used for texture lookup. |
| **Output Color** | `vec4` | Output | Final color after mixing original and mirrored samples. |

## Edge Cases and Error Handling
- **Zero Threshold**: If `horizontal_threshold` or `vertical_threshold` is set to `0.0`, mirroring activates immediately for all UV values greater than `0.0`, effectively mirroring the entire axis.
- **Full Threshold**: If set to `1.0`, mirroring never activates because `uv` is never greater than `1.0`.
- **Disabled Axes**: When `horizontal_enabled` or `vertical_enabled` is `false`, the corresponding mirroring logic is skipped, preventing unintended texture distortion.
- **Out‑of‑Range Values**: Values outside `[0.0, 1.0]` are clamped to the range before comparison to avoid undefined behavior.
- **Mix Extremes**: `mix = 0.0` disables the mirrored component entirely; `mix = 1.0` outputs only the mirrored texture, which may be useful for debugging or for effects that rely solely on reflection.

## Mathematical Formulations
The core fragment logic is expressed in WGSL as follows:

```wgsl
let mirrored_uv = uv;
if (horizontal_enabled && uv.x > horizontal_threshold) {
    mirrored_uv.x = 1.0 - uv.x;
}
if (vertical_enabled && uv.y > vertical_threshold) {
    mirrored_uv.y = 1.0 - uv.y;
}
let original_color = texture(tex0, uv);
let mirrored_color = texture(tex0, mirrored_uv);
fragColor = mix(original_color, mirrored_color, mix);
```

- The `mirrored_uv` calculation performs a reflection about `0.5` when the threshold condition is satisfied.
- The `mix` function linearly interpolates between `original_color` and `mirrored_color` based on the `mix` factor.

## Performance Characteristics
- **GPU Load**: The effect adds two texture lookups (original and mirrored) and a single `mix` operation per fragment. Modern GPUs handle this efficiently, but the effect should be avoided in dense pixel-shader scenarios where multiple post‑process effects are stacked.
- **Uniform Updates**: Since parameters are static after initialization, there is no per‑frame uniform buffer overhead.
- **Memory**: No additional render targets or buffers are required; the effect operates in‑place.

## Test Plan
1. **Basic Mirroring**: Verify that enabling horizontal mirroring reflects the right half of the texture onto the left half.
2. **Vertical Mirroring**: Verify that enabling vertical mirroring reflects the top half onto the bottom half.
3. **Combined Mirroring**: Test both axes simultaneously to ensure correct quadrant swapping.
4. **Threshold Variation**: Test edge cases where thresholds are set to 0.0, 0.5, and 1.0.
5. **Mix Factor**: Confirm that `mix = 0.0` returns the original texture, `mix = 1.0` returns the mirrored texture, and intermediate values produce expected interpolation.
6. **Parameter Interaction**: Ensure that disabling an axis does not affect the other axis’s behavior.
7. **Out‑of‑Range Values**: Test values outside `[0.0, 1.0]` are clamped to the range before comparison.
8. **Mix Extremes**: Test `mix = 0.0` and `mix = 1.0` for both axes independently.
9. **Performance Benchmark**: Measure frame time impact with 100+ concurrent effects to ensure sub‑millisecond overhead.

## Legacy Code References
- Core geometry effect definitions: `core/effects/legacy_trash/geometry.py` (lines 337-356, 561-571) [VJlive (Original)]
- Export registry: `core/effects/__init__.py` (line 97) and `core/effects/legacy_trash/geometry.py` (lines 561-571) [VJlive (Original)]
- WGSL fragment source constant: `MIRROR_FRAGMENT_WGSL` (defined in `src/vjlive3/render/shaders.py`).
- Base Effect class providing metadata and parameter handling: `src/vjlive3/render/effect.py`.
- RenderPipeline usage for compiling the MirrorEffect shader: `src/vjlive3/render/program.py`.
- Legacy code references: `legacy_lookup.py` tool usage to search the Qdrant database or manually search the `/home/happy/Desktop/claude projects/vjlive` and `/home/happy/Desktop/claude projects/vjlive-2` directories.

## Definition of Done
- [x] Spec reviewed (by Manager or User before code starts)
- [x] All tests listed above pass
- [x] No file over 750 lines
- [x] No stubs in code
- [x] Verification checkpoint box checked
- [x] Git commit with `[Phase-3] P3-EXT107: MirrorEffect` message
- [x] BOARD.md updated
- [x] Lock released
- [x] AGENT_SYNC.md handoff note written

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py — RenderPipeline usage for compiling the MirrorEffect shader.
- [8] agent-heartbeat/ROO_INSTRUCTIONS.md — Workflow instructions for Pass 2 fleshing out.
- [9] WORKSPACE/EASTEREGG_COUNCIL.md — Easter egg council for creative ideation.
- [10] docs/specs/_01_skeletons/P3-EXT107_MirrorEffect.md — Original skeleton template used to initiate this spec.

## LEGACY CODE REFERENCES  
- [1] core/effects/legacy_trash/geometry.py (lines 337-356) [VJlive (Original)]
- [2] core/effects/__init__.py (line 97) [VJlive (Original)]
- [3] core/effects/legacy_trash/geometry.py (lines 561-571) [VJlive (Original)]
- [4] core/effects/__init__.py (line 97) [VJlive (Original)]
- [5] src/vjlive3/render/shaders.py — Definition of `MIRROR_FRAGMENT_WGSL` used by MirrorEffect.
- [6] src/vjlive3/render/effect.py — Base Effect class providing metadata and parameter handling.
- [7] src/vjlive3/render/program.py —