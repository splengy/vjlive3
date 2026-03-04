"""
P1-R6 — WGSL Base Shader Library
Spec: docs/specs/_01_skeletons/P1-R6_WGSL.md
Tier: 🌐 Bifurcated-Safe — pure WGSL string constants portable to browser WebGPU.

Five canonical infrastructure shader strings used by the VJLive3 render pipeline.
No classes. No runtime GPU calls. No imports required.
"""

import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# BASE_VERTEX_WGSL
# Fullscreen quad (triangle strip, 4 vertices) with multi-node UV stitching.
# Uniforms bind group 0, binding 0.
# ---------------------------------------------------------------------------
BASE_VERTEX_WGSL: str = """
struct Uniforms {
    view_offset:      vec2<f32>,   // pixel offset of this node on global canvas
    view_resolution:  vec2<f32>,   // this node resolution (e.g. 1920x1080)
    total_resolution: vec2<f32>,   // full canvas resolution (e.g. 5760x1080)
    _pad:             vec2<f32>,   // std140 alignment
}

struct VertexOutput {
    @builtin(position) position: vec4<f32>,
    @location(0) v_uv: vec2<f32>,  // local UV [0,1] for texture sampling
    @location(1) uv:   vec2<f32>,  // global UV [0,1] across full node canvas
}

@group(0) @binding(0) var<uniform> u: Uniforms;

@vertex
fn vs_main(@builtin(vertex_index) vid: u32) -> VertexOutput {
    // Fullscreen triangle strip: bottom-left, bottom-right, top-left, top-right
    var ndc = array<vec2<f32>, 4>(
        vec2<f32>(-1.0, -1.0),
        vec2<f32>( 1.0, -1.0),
        vec2<f32>(-1.0,  1.0),
        vec2<f32>( 1.0,  1.0),
    );
    // WebGPU UV: (0,0) top-left, (1,1) bottom-right
    var uvs = array<vec2<f32>, 4>(
        vec2<f32>(0.0, 1.0),
        vec2<f32>(1.0, 1.0),
        vec2<f32>(0.0, 0.0),
        vec2<f32>(1.0, 0.0),
    );

    var out: VertexOutput;
    out.position = vec4<f32>(ndc[vid], 0.0, 1.0);
    out.v_uv     = uvs[vid];

    // Global UV: node pixel position / total canvas.
    // Falls back to local UV when total_resolution is zero (single-node mode).
    let total = select(u.view_resolution, u.total_resolution,
                       u.total_resolution.x > 0.5);
    let pixel  = uvs[vid] * u.view_resolution + u.view_offset;
    out.uv     = pixel / total;

    return out;
}
"""

# ---------------------------------------------------------------------------
# PASSTHROUGH_FRAGMENT_WGSL
# Identity blit: samples tex0 at v_uv. Used as the no-op effect stage.
# ---------------------------------------------------------------------------
PASSTHROUGH_FRAGMENT_WGSL: str = """
@group(0) @binding(1) var tex0:         texture_2d<f32>;
@group(0) @binding(2) var tex0_sampler: sampler;

@fragment
fn fs_main(@location(0) v_uv: vec2<f32>) -> @location(0) vec4<f32> {
    return textureSample(tex0, tex0_sampler, v_uv);
}
"""

# ---------------------------------------------------------------------------
# OVERLAY_FRAGMENT_WGSL
# Copies overlay texture into render target at full alpha.
# Used for text/debug overlays that should not composite — just replace.
# ---------------------------------------------------------------------------
OVERLAY_FRAGMENT_WGSL: str = """
@group(0) @binding(1) var tex_overlay:         texture_2d<f32>;
@group(0) @binding(2) var tex_overlay_sampler: sampler;

@fragment
fn fs_main(@location(0) v_uv: vec2<f32>) -> @location(0) vec4<f32> {
    let colour = textureSample(tex_overlay, tex_overlay_sampler, v_uv);
    // Pass through at full alpha — caller controls blending state
    return vec4<f32>(colour.rgb, 1.0);
}
"""

# ---------------------------------------------------------------------------
# WARP_VERTEX_WGSL
# Corner-pin and optional Bézier mesh warp.
# warp_mode uniform: 0 = none, 1 = corner-pin, 2 = Bézier (falls back to 1).
# Corner positions: unit-square UV corners (TL, TR, BL, BR) stored in a 4×2 array.
# ---------------------------------------------------------------------------
WARP_VERTEX_WGSL: str = """
struct WarpUniforms {
    view_offset:      vec2<f32>,
    view_resolution:  vec2<f32>,
    total_resolution: vec2<f32>,
    warp_mode:        u32,          // 0=none, 1=corner-pin, 2=bezier(→1)
    _pad:             u32,
    // Corner pin: target UV positions for TL, TR, BL, BR
    corner_tl:        vec2<f32>,
    corner_tr:        vec2<f32>,
    corner_bl:        vec2<f32>,
    corner_br:        vec2<f32>,
}

struct VertexOutput {
    @builtin(position) position: vec4<f32>,
    @location(0) v_uv: vec2<f32>,
    @location(1) uv:   vec2<f32>,
}

@group(0) @binding(0) var<uniform> u: WarpUniforms;

fn bilinear_warp(local_uv: vec2<f32>) -> vec2<f32> {
    // Bilinear interpolation across four corner UV targets
    let top    = mix(u.corner_tl, u.corner_tr, local_uv.x);
    let bottom = mix(u.corner_bl, u.corner_br, local_uv.x);
    return mix(top, bottom, local_uv.y);
}

@vertex
fn vs_main(@builtin(vertex_index) vid: u32) -> VertexOutput {
    var ndc = array<vec2<f32>, 4>(
        vec2<f32>(-1.0, -1.0),
        vec2<f32>( 1.0, -1.0),
        vec2<f32>(-1.0,  1.0),
        vec2<f32>( 1.0,  1.0),
    );
    var uvs = array<vec2<f32>, 4>(
        vec2<f32>(0.0, 1.0),
        vec2<f32>(1.0, 1.0),
        vec2<f32>(0.0, 0.0),
        vec2<f32>(1.0, 0.0),
    );

    var warped_uv: vec2<f32>;
    if (u.warp_mode >= 1u) {
        // Corner-pin warp (mode 1) or Bézier fallback (mode 2 → 1)
        warped_uv = bilinear_warp(uvs[vid]);
    } else {
        warped_uv = uvs[vid];
    }

    let total  = select(u.view_resolution, u.total_resolution,
                        u.total_resolution.x > 0.5);
    let pixel  = warped_uv * u.view_resolution + u.view_offset;

    var out: VertexOutput;
    out.position = vec4<f32>(ndc[vid], 0.0, 1.0);
    out.v_uv     = warped_uv;
    out.uv       = pixel / total;
    return out;
}
"""

# ---------------------------------------------------------------------------
# WARP_BLEND_FRAGMENT_WGSL
# Edge feathering for multi-projector overlap blending.
# nodeSide: 0=left, 1=middle, 2=right.
# edgeFeather: blend width as fraction of screen [0.0, 1.0].
# calibrationMode: 1=show grid, 0=normal.
# ---------------------------------------------------------------------------
WARP_BLEND_FRAGMENT_WGSL: str = """
struct BlendUniforms {
    edge_feather:     f32,   // blend width as fraction of screen width
    node_side:        i32,   // 0=left, 1=middle, 2=right
    calibration_mode: u32,   // 1=show alignment grid, 0=normal
    _pad:             f32,
}

@group(0) @binding(0) var<uniform> b: BlendUniforms;
@group(0) @binding(1) var tex0:         texture_2d<f32>;
@group(0) @binding(2) var tex0_sampler: sampler;

@fragment
fn fs_main(
    @location(0) v_uv: vec2<f32>,
    @location(1) uv:   vec2<f32>,
) -> @location(0) vec4<f32> {
    var colour = textureSample(tex0, tex0_sampler, v_uv);

    // Edge feather: ramp alpha at left/right edges depending on node side
    var alpha: f32 = 1.0;
    let fw = max(b.edge_feather, 0.001);

    if (b.node_side == 0) {
        // Left node: feather right edge
        alpha = smoothstep(1.0, 1.0 - fw, v_uv.x);
    } else if (b.node_side == 2) {
        // Right node: feather left edge
        alpha = smoothstep(0.0, fw, v_uv.x);
    } else {
        // Middle node: feather both edges
        let left_ramp  = smoothstep(0.0, fw, v_uv.x);
        let right_ramp = smoothstep(1.0, 1.0 - fw, v_uv.x);
        alpha = min(left_ramp, right_ramp);
    }

    // Calibration grid overlay (white grid lines at 10% intervals)
    if (b.calibration_mode == 1u) {
        let grid_x = fract(v_uv.x * 10.0);
        let grid_y = fract(v_uv.y * 10.0);
        let line_w = 0.03;
        if (grid_x < line_w || grid_y < line_w) {
            return vec4<f32>(1.0, 0.0, 1.0, 1.0);  // magenta grid
        }
    }

    return vec4<f32>(colour.rgb, colour.a * alpha);
}
"""

# ---------------------------------------------------------------------------
# Validation helper — CPU only, no GPU context required.
# ---------------------------------------------------------------------------

_VERTEX_MARKERS = ("@vertex",)
_FRAGMENT_MARKERS = ("@fragment",)
_GLSL_MARKERS = ("#version", "gl_Position", "gl_FragColor", "uniform ")


def validate_wgsl(source: str) -> bool:
    """
    Lightweight pre-submission check for WGSL source strings.

    Returns True if source is non-empty, contains at least one WGSL entry
    point marker (@vertex or @fragment), and contains no GLSL contamination.

    Does NOT invoke the GPU compiler. Call from unit tests — no wgpu needed.

    Args:
        source: WGSL source string to validate.

    Returns:
        True if validation passes, False on any failure (also logs WARNING).
    """
    if not source or not source.strip():
        logger.warning("validate_wgsl: source is empty")
        return False

    for glsl in _GLSL_MARKERS:
        if glsl in source:
            logger.warning("validate_wgsl: GLSL contamination detected: %r", glsl)
            return False

    has_entry = any(m in source for m in _VERTEX_MARKERS + _FRAGMENT_MARKERS)
    if not has_entry:
        logger.warning("validate_wgsl: no @vertex or @fragment entry point found")
        return False

    return True


# ---------------------------------------------------------------------------
# SCREEN_BLIT_WGSL
# Self-contained fullscreen blit shader — samples a texture to the screen.
# group(0) binding(0) = source texture (2d<f32>)
# group(0) binding(1) = sampler
# No uniforms — intentionally decoupled from BASE_VERTEX_WGSL so this shader
# can be used to blit any offscreen GPUTextureView to the screen surface
# without group-0 / binding-0 conflicts.
# ---------------------------------------------------------------------------
SCREEN_BLIT_WGSL: str = """
struct VSOut {
    @builtin(position) pos: vec4<f32>,
    @location(0) uv:       vec2<f32>,
}

@vertex
fn vs_main(@builtin(vertex_index) vi: u32) -> VSOut {
    // Triangle-strip positions covering [-1,1] x [-1,1]
    var positions = array<vec2<f32>, 4>(
        vec2<f32>(-1.0,  1.0),
        vec2<f32>(-1.0, -1.0),
        vec2<f32>( 1.0,  1.0),
        vec2<f32>( 1.0, -1.0),
    );
    // UV: Y is flipped relative to NDC (screen top = UV 0, screen bottom = UV 1)
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

@group(0) @binding(0) var blit_tex:  texture_2d<f32>;
@group(0) @binding(1) var blit_samp: sampler;

@fragment
fn fs_main(in: VSOut) -> @location(0) vec4<f32> {
    return textureSample(blit_tex, blit_samp, in.uv);
}
"""
