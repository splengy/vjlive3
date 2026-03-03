"""
Tests for P1-R6 — WGSL Base Shader Library
Spec: docs/specs/_01_skeletons/P1-R6_WGSL.md

All tests are CPU-only. No GPU context required.
"""

import pytest
from vjlive3.render.shaders import (
    BASE_VERTEX_WGSL,
    PASSTHROUGH_FRAGMENT_WGSL,
    OVERLAY_FRAGMENT_WGSL,
    WARP_VERTEX_WGSL,
    WARP_BLEND_FRAGMENT_WGSL,
    validate_wgsl,
)


# ---------------------------------------------------------------------------
# Entry point checks
# ---------------------------------------------------------------------------

def test_base_vertex_is_wgsl():
    """BASE_VERTEX_WGSL must contain a @vertex entry point."""
    assert "@vertex" in BASE_VERTEX_WGSL
    assert "vs_main" in BASE_VERTEX_WGSL


def test_passthrough_is_wgsl():
    """PASSTHROUGH_FRAGMENT_WGSL must contain a @fragment entry point."""
    assert "@fragment" in PASSTHROUGH_FRAGMENT_WGSL
    assert "fs_main" in PASSTHROUGH_FRAGMENT_WGSL


def test_overlay_is_wgsl():
    """OVERLAY_FRAGMENT_WGSL must contain a @fragment entry point."""
    assert "@fragment" in OVERLAY_FRAGMENT_WGSL
    assert "fs_main" in OVERLAY_FRAGMENT_WGSL


def test_warp_vertex_is_wgsl():
    """WARP_VERTEX_WGSL must contain a @vertex entry point."""
    assert "@vertex" in WARP_VERTEX_WGSL
    assert "vs_main" in WARP_VERTEX_WGSL


def test_warp_blend_is_wgsl():
    """WARP_BLEND_FRAGMENT_WGSL must contain a @fragment entry point."""
    assert "@fragment" in WARP_BLEND_FRAGMENT_WGSL
    assert "fs_main" in WARP_BLEND_FRAGMENT_WGSL


# ---------------------------------------------------------------------------
# GLSL contamination scan
# ---------------------------------------------------------------------------

_ALL_SHADERS = [
    ("BASE_VERTEX_WGSL",           BASE_VERTEX_WGSL),
    ("PASSTHROUGH_FRAGMENT_WGSL",  PASSTHROUGH_FRAGMENT_WGSL),
    ("OVERLAY_FRAGMENT_WGSL",      OVERLAY_FRAGMENT_WGSL),
    ("WARP_VERTEX_WGSL",           WARP_VERTEX_WGSL),
    ("WARP_BLEND_FRAGMENT_WGSL",   WARP_BLEND_FRAGMENT_WGSL),
]

_GLSL_FORBIDDEN = ("#version", "gl_Position", "gl_FragColor", "uniform ")


@pytest.mark.parametrize("name,source", _ALL_SHADERS)
def test_no_glsl_keywords(name, source):
    """No shader constant may contain GLSL keywords."""
    for kw in _GLSL_FORBIDDEN:
        assert kw not in source, (
            f"{name} contains GLSL keyword {kw!r} — ADR-021 violation"
        )


# ---------------------------------------------------------------------------
# validate_wgsl() helper
# ---------------------------------------------------------------------------

def test_validate_wgsl_empty_string():
    assert validate_wgsl("") is False


def test_validate_wgsl_whitespace_only():
    assert validate_wgsl("   \n\t  ") is False


def test_validate_wgsl_no_entry_point():
    assert validate_wgsl("fn helper() -> f32 { return 0.0; }") is False


def test_validate_wgsl_glsl_contamination():
    glsl_snippet = "#version 330 core\nvoid main() { gl_Position = vec4(0.0); }"
    assert validate_wgsl(glsl_snippet) is False


def test_validate_wgsl_base_vertex():
    assert validate_wgsl(BASE_VERTEX_WGSL) is True


def test_validate_wgsl_passthrough():
    assert validate_wgsl(PASSTHROUGH_FRAGMENT_WGSL) is True


def test_validate_wgsl_warp_blend():
    assert validate_wgsl(WARP_BLEND_FRAGMENT_WGSL) is True


# ---------------------------------------------------------------------------
# Structural content checks
# ---------------------------------------------------------------------------

def test_base_vertex_has_multi_node_uniforms():
    """BASE_VERTEX_WGSL must define the multi-node stitching uniforms."""
    assert "view_offset" in BASE_VERTEX_WGSL
    assert "view_resolution" in BASE_VERTEX_WGSL
    assert "total_resolution" in BASE_VERTEX_WGSL


def test_warp_vertex_has_warp_mode():
    """WARP_VERTEX_WGSL must handle warp_mode uniform."""
    assert "warp_mode" in WARP_VERTEX_WGSL


def test_warp_blend_has_edge_uniforms():
    """WARP_BLEND_FRAGMENT_WGSL must define edge_feather, node_side, calibration_mode."""
    assert "edge_feather" in WARP_BLEND_FRAGMENT_WGSL
    assert "node_side" in WARP_BLEND_FRAGMENT_WGSL
    assert "calibration_mode" in WARP_BLEND_FRAGMENT_WGSL


def test_passthrough_uses_textureSample():
    """Passthrough must use WGSL textureSample, not GLSL texture()."""
    assert "textureSample" in PASSTHROUGH_FRAGMENT_WGSL
    # Ensure no bare GLSL texture() call
    assert "texture(" not in PASSTHROUGH_FRAGMENT_WGSL


def test_all_shaders_are_strings():
    for name, src in _ALL_SHADERS:
        assert isinstance(src, str), f"{name} is not a str"
        assert len(src) > 20, f"{name} is suspiciously short"
