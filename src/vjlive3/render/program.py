"""
P1-R2 — RenderPipeline (WGSL Shader Pipeline)
Spec: docs/specs/_02_fleshed_out/P1-R2_gpu_pipeline.md
File: src/vjlive3/render/program.py  (~200 lines)

Compiles a combined WGSL shader module (vertex + fragment in one source)
and exposes use(encoder) + set_uniform(name, value) for per-frame updates.
Device is obtained from the active RenderContext.
"""

import logging
import struct
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Re-export base WGSL constants from P1-R6 so callers can import from here.
from vjlive3.render.shaders import (  # noqa: E402 — intentional re-export
    BASE_VERTEX_WGSL as BASE_VERTEX_SHADER,
    PASSTHROUGH_FRAGMENT_WGSL as PASSTHROUGH_FRAGMENT,
    OVERLAY_FRAGMENT_WGSL as OVERLAY_FRAGMENT,
    WARP_VERTEX_WGSL as WARP_VERTEX_SHADER,
    WARP_BLEND_FRAGMENT_WGSL as WARP_BLEND_FRAGMENT,
)


class RenderPipeline:
    """
    Compiled WGSL shader pipeline with cached bind group layout.

    Accepts a combined WGSL source string containing both @vertex and
    @fragment entry points (vs_main / fs_main by convention).

    Uniforms are pushed via set_uniform(name, value) which writes into a
    mapped uniform buffer. Type dispatch: int → u32, float → f32,
    list/tuple → packed f32 array.

    Device is obtained from the active RenderContext via get_current_device().
    Safe to delete() multiple times (idempotent).
    """

    METADATA: dict = {
        "spec": "P1-R2",
        "tier": "Pro-Tier Native",
        "module": "vjlive3.render.program",
    }

    def __init__(self, shader_source: str, name: str = "unnamed") -> None:
        """
        Compile and link the WGSL shader module.

        Args:
            shader_source:  WGSL source with @vertex + @fragment entry points.
            name:           Debug label used in logging and GPU object labels.

        Raises:
            RuntimeError: If the device is unavailable or compilation fails.
        """
        import wgpu  # lazy — allows mocking in tests
        from vjlive3.render.render_context import get_current_device  # lazy

        self._name = name
        self._deleted = False
        self._shader_module = None
        self._pipeline = None
        self._uniform_buf = None
        self.uniforms: Dict[str, Any] = {}

        device = get_current_device()
        try:
            self._shader_module = device.create_shader_module(
                label=name,
                code=shader_source,
            )
        except Exception as exc:
            raise RuntimeError(
                f"RenderPipeline '{name}': shader compilation failed: {exc}"
            ) from exc

        # Build a minimal render pipeline for a fullscreen quad.
        # layout="auto" instructs wgpu to introspect the WGSL shader and
        # auto-derive the bind group layout — no manual entry list needed.
        # This is the correct pattern when the shader declares its own bindings.
        try:
            self._pipeline = device.create_render_pipeline(
                label=name,
                layout="auto",
                vertex={
                    "module": self._shader_module,
                    "entry_point": "vs_main",
                },
                fragment={
                    "module": self._shader_module,
                    "entry_point": "fs_main",
                    "targets": [{"format": wgpu.TextureFormat.rgba8unorm}],
                },
                primitive={"topology": wgpu.PrimitiveTopology.triangle_strip},
                depth_stencil=None,
                multisample=None,
            )
        except Exception as exc:
            raise RuntimeError(
                f"RenderPipeline '{name}': pipeline creation failed: {exc}"
            ) from exc

        logger.debug("RenderPipeline: compiled '%s'", name)

    def use(self, encoder: Any) -> None:
        """
        Set this pipeline on the provided wgpu render pass encoder.

        Args:
            encoder: A wgpu.GPURenderPassEncoder (active render pass).
        """
        if self._pipeline is not None:
            encoder.set_pipeline(self._pipeline)

    def set_uniform(self, name: str, value: Any) -> None:
        """
        Store a uniform value by name.

        Values are cached in self.uniforms dict. They are written to the
        GPU uniform buffer on the next draw call via the bind group.
        Silently ignores unknown names per spec Edge Cases table.

        Type dispatch:
            int   → stored as int (for u32/i32 uniforms)
            float → stored as float (for f32 uniforms)
            list/tuple → stored as-is (for vec2/vec4 uniforms)
        """
        # Cache locally; the bind group update happens in EffectChain.render()
        self.uniforms[name] = value

    def delete(self) -> None:
        """Release all pipeline GPU resources. Safe to call multiple times."""
        if self._deleted:
            return
        self._deleted = True
        for attr in ("_uniform_buf", "_pipeline", "_shader_module"):
            obj = getattr(self, attr, None)
            if obj is not None:
                destroy = getattr(obj, "destroy", None)
                if destroy is not None:
                    try:
                        destroy()
                    except Exception:
                        pass
                setattr(self, attr, None)
        logger.debug("RenderPipeline: deleted '%s'", self._name)

    def __del__(self) -> None:
        self.delete()

    # ---- Properties ---------------------------------------------------------

    @property
    def name(self) -> str:
        return self._name

    @property
    def pipeline(self) -> Any:
        """The raw wgpu.GPURenderPipeline handle."""
        return self._pipeline
