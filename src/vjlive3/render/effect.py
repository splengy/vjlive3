"""
P1-R2 — Effect Base Class
Spec: docs/specs/_02_fleshed_out/P1-R2_gpu_pipeline.md
File: src/vjlive3/render/effect.py  (~100 lines)

Base class for all VJLive3 effects. Holds a RenderPipeline reference,
enabled/mix controls, and the apply_uniforms / pre_process hooks.
Subclasses override apply_uniforms() to drive parameters per-frame.
"""

from typing import TYPE_CHECKING, Any, Optional, Tuple

if TYPE_CHECKING:
    from vjlive3.render.program import RenderPipeline
    from vjlive3.render.chain import EffectChain


class Effect:
    """
    Base class for all VJLive3 effects.

    Every Effect owns a RenderPipeline (WGSL shader + bind groups).
    Subclasses must:
      1. Set METADATA dict with at least 'name', 'spec', 'version'.
      2. Override apply_uniforms() to push per-frame parameters.

    The EffectChain calls apply_uniforms() then renders the effect into
    the ping-pong target chain.
    """

    METADATA: dict = {
        "name": "BaseEffect",
        "spec": "P1-R2",
        "version": "1.0.0",
        "tier": "Pro-Tier Native",
    }

    def __init__(self, name: str, fragment_source: str) -> None:
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

        Default: return None (no pre-processing).
        """
        return None

    def __repr__(self) -> str:
        return (
            f"<Effect {self.name!r} enabled={self.enabled} mix={self.mix:.2f}>"
        )
