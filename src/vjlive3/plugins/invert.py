"""
InvertEffect — GPU-only colour inversion shader.

Diagnostic tool to prove the full GPU effect-chain pipeline:
    input_texture → InvertEffect.draw() → ping-pong target → screen

Tier: 🌐 Bifurcated-Safe (pure WGSL, no hardware dependency)
No spec required — this is a scaffolding/diagnostic plugin, not a production effect.
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Self-contained WGSL — no BASE_VERTEX_WGSL dependency.
# group(0) binding(0) = source texture  (chain ping-pong input)
# group(0) binding(1) = sampler
# ---------------------------------------------------------------------------
_INVERT_WGSL = """
struct VSOut {
    @builtin(position) pos: vec4<f32>,
    @location(0) uv:       vec2<f32>,
}

@vertex
fn vs_main(@builtin(vertex_index) vi: u32) -> VSOut {
    var positions = array<vec2<f32>, 4>(
        vec2<f32>(-1.0,  1.0),
        vec2<f32>(-1.0, -1.0),
        vec2<f32>( 1.0,  1.0),
        vec2<f32>( 1.0, -1.0),
    );
    var uvs = array<vec2<f32>, 4>(
        vec2<f32>(0.0, 0.0),
        vec2<f32>(0.0, 1.0),
        vec2<f32>(1.0, 0.0),
        vec2<f32>(1.0, 1.0),
    );
    var out: VSOut;
    out.pos = vec4<f32>(positions[vi], 0.0, 1.0);
    out.uv  = uvs[vi];
    return out;
}

@group(0) @binding(0) var src_tex:  texture_2d<f32>;
@group(0) @binding(1) var src_samp: sampler;

@fragment
fn fs_main(in: VSOut) -> @location(0) vec4<f32> {
    let col = textureSample(src_tex, src_samp, in.uv);
    return vec4<f32>(1.0 - col.r, 1.0 - col.g, 1.0 - col.b, col.a);
}
"""


class InvertEffect:
    """
    Invert the RGB channels of the input texture.

    Implements the chain's ``draw(render_pass, input_view, device)`` protocol
    so that the EffectChain passes the source texture view directly.  Lazily
    builds the wgpu pipeline on first draw to avoid device-availability issues
    at import time.

    The effect is purely cosmetic and hardware-agnostic.
    """

    name: str = "invert"
    enabled: bool = True

    def __init__(self) -> None:
        self._gpu_pipeline: Optional[Any] = None
        self._sampler: Optional[Any] = None

    # ------------------------------------------------------------------
    # Chain draw protocol
    # ------------------------------------------------------------------

    def draw(self, render_pass: Any, input_view: Any, device: Any) -> None:
        """
        Called by ``EffectChain._draw_effect``.

        Sets the invert pipeline and a per-frame bind group on *render_pass*.
        The caller draws 4 vertices (fullscreen triangle-strip).

        Args:
            render_pass: Active ``wgpu.GPURenderPassEncoder``.
            input_view:  ``GPUTextureView`` from the chain's ping-pong buffer.
            device:      Active ``wgpu.GPUDevice``.
        """
        self._ensure_pipeline(device)
        bg = device.create_bind_group(
            layout=self._gpu_pipeline.get_bind_group_layout(0),
            entries=[
                {"binding": 0, "resource": input_view},
                {"binding": 1, "resource": self._sampler},
            ],
        )
        render_pass.set_pipeline(self._gpu_pipeline)
        render_pass.set_bind_group(0, bg)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _ensure_pipeline(self, device: Any) -> None:
        """Lazily compile the WGSL pipeline on first draw."""
        if self._gpu_pipeline is not None:
            return
        import wgpu
        module = device.create_shader_module(code=_INVERT_WGSL, label="invert")
        self._gpu_pipeline = device.create_render_pipeline(
            layout="auto",
            label="invert",
            vertex={"module": module, "entry_point": "vs_main"},
            fragment={
                "module": module,
                "entry_point": "fs_main",
                "targets": [{"format": wgpu.TextureFormat.rgba8unorm}],
            },
            primitive={"topology": wgpu.PrimitiveTopology.triangle_strip},
        )
        self._sampler = device.create_sampler(
            label="invert",
            min_filter="linear",
            mag_filter="linear",
        )
        logger.debug("InvertEffect: pipeline compiled")
