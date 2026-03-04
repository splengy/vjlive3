"""
PerlinEffect — Procedural Perlin noise generator (P3-EXT125).

Spec: docs/specs/_02_fleshed_out/P3-EXT125_PerlinEffect.md
Tier: Pro-Tier Native
Category: generators

Generates animated Perlin noise with configurable octaves, ridging,
turbulence, and HSV colour cycling.  Pure GPU generator — requires no
input texture.  Implements the chain's ``draw()`` protocol with a 48-byte
WGSL uniform buffer updated each frame.
"""

from __future__ import annotations

import logging
import struct
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# WGSL — self-contained; no BASE_VERTEX_WGSL dependency.
# @group(0) @binding(0) — Uniforms (48 bytes)
# ---------------------------------------------------------------------------
_PERLIN_WGSL: str = """
// ---------------------------------------------------------------------------
// Perlin noise WGSL — P3-EXT125 PerlinEffect
// ---------------------------------------------------------------------------

struct Uniforms {
    u_time:        f32,
    u_speed:       f32,
    u_scale:       f32,
    u_octaves:     f32,
    u_persistence: f32,
    u_ridging:     f32,
    u_turbulence:  f32,
    u_color_hue:   f32,
    u_mix:         f32,
    u_width:       f32,
    u_height:      f32,
    _pad:          f32,
}
@group(0) @binding(0) var<uniform> u: Uniforms;

// ---------------------------------------------------------------------------
// Vertex: fullscreen triangle-strip quad
// ---------------------------------------------------------------------------

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

// ---------------------------------------------------------------------------
// Noise functions
// ---------------------------------------------------------------------------

// Smooth easing (Ken Perlin's quintic)
fn fade(t: f32) -> f32 {
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0);
}

// Pseudo-random unit gradient at integer grid point
fn hash2(p: vec2<f32>) -> vec2<f32> {
    let q = vec2<f32>(
        dot(p, vec2<f32>(127.1, 311.7)),
        dot(p, vec2<f32>(269.5, 183.3)),
    );
    return normalize(fract(sin(q) * 43758.5453) * 2.0 - vec2<f32>(1.0));
}

// Classic 2-D Perlin noise — returns value in roughly [-1, 1]
fn perlin(p: vec2<f32>) -> f32 {
    let i  = floor(p);
    let f  = fract(p);

    let g00 = hash2(i + vec2<f32>(0.0, 0.0));
    let g10 = hash2(i + vec2<f32>(1.0, 0.0));
    let g01 = hash2(i + vec2<f32>(0.0, 1.0));
    let g11 = hash2(i + vec2<f32>(1.0, 1.0));

    let d00 = dot(g00, f - vec2<f32>(0.0, 0.0));
    let d10 = dot(g10, f - vec2<f32>(1.0, 0.0));
    let d01 = dot(g01, f - vec2<f32>(0.0, 1.0));
    let d11 = dot(g11, f - vec2<f32>(1.0, 1.0));

    let ux = fade(f.x);
    let uy = fade(f.y);
    let nx0 = mix(d00, d10, ux);
    let nx1 = mix(d01, d11, ux);
    return mix(nx0, nx1, uy);
}

// Fractal (fBm) layering — octaves must be ≥1
fn fractal_noise(p: vec2<f32>, oct: i32, persistence: f32) -> f32 {
    var total: f32    = 0.0;
    var amplitude: f32 = 1.0;
    var frequency: f32 = 1.0;
    var max_val: f32   = 0.0;
    for (var i: i32 = 0; i < oct; i = i + 1) {
        total     += perlin(p * frequency) * amplitude;
        max_val   += amplitude;
        amplitude *= persistence;
        frequency *= 2.0;
    }
    return total / max_val;   // normalised to [-1, 1]
}

// iq's compact HSV→RGB (avoids branch-heavy if-else)
fn hsv2rgb(h: f32, s: f32, v: f32) -> vec3<f32> {
    let k = vec4<f32>(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
    let p = abs(fract(vec3<f32>(h) + k.xyz) * 6.0 - vec3<f32>(k.w));
    return v * mix(vec3<f32>(k.x), clamp(p - vec3<f32>(k.x), vec3<f32>(0.0), vec3<f32>(1.0)), s);
}

// ---------------------------------------------------------------------------
// Fragment
// ---------------------------------------------------------------------------

@fragment
fn fs_main(in: VSOut) -> @location(0) vec4<f32> {
    let t   = u.u_time * u.u_speed;
    var p   = in.uv * u.u_scale;
    let oct = clamp(i32(u.u_octaves), 1, 8);
    let per = clamp(u.u_persistence, 0.1, 1.0);

    // Turbulence: domain warp using two independent noise channels
    if u.u_turbulence > 0.0 {
        let wx = fractal_noise(p + vec2<f32>(123.4, 456.7), 3, 0.5) * u.u_turbulence;
        let wy = fractal_noise(p + vec2<f32>(789.1, 234.5), 3, 0.5) * u.u_turbulence;
        p = p + vec2<f32>(wx, wy);
    }

    var n = fractal_noise(p + vec2<f32>(t, t * 0.7), oct, per);

    // Ridging: fold noise to create sharp luminous ridges
    if u.u_ridging > 0.0 {
        n = mix(n, abs(n), u.u_ridging);
    }

    // Map [-1,1] → [0,1]
    let gray = clamp((n + 1.0) * 0.5, 0.0, 1.0);

    var rgb: vec3<f32>;
    if u.u_color_hue > 0.001 {
        let hue = fract(gray * u.u_color_hue + t * 0.05);
        rgb = hsv2rgb(hue, 0.8, 0.9);
    } else {
        rgb = vec3<f32>(gray);
    }

    return vec4<f32>(rgb, 1.0);
}
"""

# Uniform struct size: 12 × f32 = 48 bytes (16-byte aligned ✓)
_UNIFORM_SIZE: int = 48
_UNIFORM_FORMAT: str = "12f"


class PerlinEffect:
    """
    Real-time Perlin noise generator effect.

    Implements the chain's ``draw(render_pass, input_view, device)`` protocol.
    The chain calls ``apply_uniforms(time, resolution, ...)`` before each draw
    to update animation time and resolution in the per-frame uniform buffer.

    Parameters (all in ``self.params``)
    ------------------------------------
    speed       : float  [0.0–10.0]  animation speed multiplier
    scale       : float  [0.1–100.0] base noise frequency
    octaves     : float  [1.0–8.0]   number of fractal layers
    persistence : float  [0.1–1.0]   amplitude decay per octave
    ridging     : float  [0.0–1.0]   ridge-fold blend
    turbulence  : float  [0.0–1.0]   domain warp amount
    color_hue   : float  [0.0–1.0]   HSV hue rotation (0 = greyscale)
    u_mix       : float  [0.0–1.0]   reserved for future background blend
    """

    METADATA: Dict[str, Any] = {
        "spec": "P3-EXT125",
        "tier": "Pro-Tier Native",
        "version": "1.0.0",
        "category": "generators",
        "tags": ["noise", "procedural", "perlin", "fractal"],
        "origin": "vjlive-v2:effects/generators/perlin",
        "dreamer_flag": False,
        "logic_purity": "clean",
        "role_assignment": "worker",
        "kitten_status": True,
        "performance_impact": "medium",
    }

    name: str = "perlin"
    enabled: bool = True

    def __init__(self) -> None:
        self.params: Dict[str, float] = {
            "speed":       0.6,
            "scale":       2.0,
            "octaves":     5.0,
            "persistence": 0.5,
            "ridging":     0.0,
            "turbulence":  0.0,
            "color_hue":   0.0,
            "u_mix":       1.0,
        }

        self._time: float = 0.0
        self._resolution: Tuple[float, float] = (1280.0, 720.0)

        self._gpu_pipeline: Optional[Any] = None
        self._uniform_buf: Optional[Any] = None

    # ------------------------------------------------------------------
    # Chain protocol
    # ------------------------------------------------------------------

    def apply_uniforms(
        self,
        time: float = 0.0,
        resolution: Tuple[int, int] = (1280, 720),
        audio_reactor: Any = None,
        semantic_layer: Any = None,
    ) -> None:
        """Called by EffectChain before each draw; stores time + resolution."""
        self._time = float(time)
        self._resolution = (float(resolution[0]), float(resolution[1]))

    def draw(self, render_pass: Any, input_view: Any, device: Any) -> None:
        """
        Called by EffectChain._draw_effect each frame.

        Builds the GPU pipeline on first call, then writes updated uniforms
        and sets the pipeline + bind group on the active render pass.

        Args:
            render_pass: Active ``wgpu.GPURenderPassEncoder``.
            input_view:  Ping-pong texture view (unused for a generator — present
                         for API compatibility with the draw() protocol).
            device:      Active ``wgpu.GPUDevice``.
        """
        self._ensure_pipeline(device)

        # Write per-frame uniforms
        raw = self._pack_uniforms()
        device.queue.write_buffer(self._uniform_buf, 0, raw)

        bg = device.create_bind_group(
            layout=self._gpu_pipeline.get_bind_group_layout(0),
            entries=[{
                "binding": 0,
                "resource": {
                    "buffer": self._uniform_buf,
                    "offset": 0,
                    "size":   _UNIFORM_SIZE,
                },
            }],
        )
        render_pass.set_pipeline(self._gpu_pipeline)
        render_pass.set_bind_group(0, bg)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_fragment_shader(self) -> str:
        """Return the WGSL source for inspection / unit tests."""
        return _PERLIN_WGSL

    def get_state(self) -> Dict[str, Any]:
        """Serialise current params for preset save/load."""
        return dict(self.params)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_pipeline(self, device: Any) -> None:
        """Lazily compile pipeline and allocate uniform buffer on first call."""
        if self._gpu_pipeline is not None:
            return

        import wgpu
        module = device.create_shader_module(code=_PERLIN_WGSL, label="perlin")
        self._gpu_pipeline = device.create_render_pipeline(
            layout="auto",
            label="perlin",
            vertex={"module": module, "entry_point": "vs_main"},
            fragment={
                "module": module,
                "entry_point": "fs_main",
                "targets": [{"format": wgpu.TextureFormat.rgba8unorm}],
            },
            primitive={"topology": wgpu.PrimitiveTopology.triangle_strip},
        )
        self._uniform_buf = device.create_buffer(
            size=_UNIFORM_SIZE,
            usage=wgpu.BufferUsage.UNIFORM | wgpu.BufferUsage.COPY_DST,
            label="perlin-uniforms",
        )
        logger.debug("PerlinEffect: pipeline compiled")

    def _pack_uniforms(self) -> bytes:
        """Pack current params + time/resolution into a 48-byte struct."""
        p = self.params
        # Clamp octaves and persistence within spec limits
        octaves = max(1.0, min(8.0, p.get("octaves", 5.0)))
        persistence = max(0.1, min(1.0, p.get("persistence", 0.5)))
        scale = max(0.1, min(100.0, p.get("scale", 2.0)))

        return struct.pack(
            _UNIFORM_FORMAT,
            self._time,
            float(p.get("speed",       0.6)),
            scale,
            octaves,
            persistence,
            float(p.get("ridging",     0.0)),
            float(p.get("turbulence",  0.0)),
            float(p.get("color_hue",   0.0)),
            float(p.get("u_mix",       1.0)),
            self._resolution[0],
            self._resolution[1],
            0.0,   # _pad — struct alignment
        )
