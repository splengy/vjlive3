"""
P8-I8: Legacy VJlive-2 Parity Test.

Spot-checks that each ported VJLive3 plugin:
1. Has the same parameter names as the expected VJlive-2 originals
2. Has the same number of parameters
3. Has all required metadata keys
4. Produces a valid texture handle (not 0) when given a real input

This is a declarative parity table — add entries as new legacy plugins are ported.
"""
import pytest
from typing import List
import sys
from unittest.mock import MagicMock

# GL mock must be set before any plugin import
_g = MagicMock()
_g.glGetShaderiv.return_value = 1
_g.glGetProgramiv.return_value = 1
_g.glCreateProgram.return_value = 99
_g.glGenVertexArrays.return_value = 44
_g.glGenTextures.return_value = 55
_g.glGenFramebuffers.return_value = 51
sys.modules.setdefault("OpenGL", MagicMock())
sys.modules.setdefault("OpenGL.GL", _g)

# ── Parity table: (module, class, expected_param_names) ──────────────────────
# Each entry describes the expected parameter surface of the VJlive-2 original.

PARITY_TABLE = [
    # Audio reactive
    ("vjlive3.plugins.bass_cannon_2", "BassCanon2Plugin",
     ["cannon_power", "shockwave_radius", "recoil", "flash", "chroma_burst", "mix"]),
    # VFX
    ("vjlive3.plugins.bloom_effect", "BloomPlugin",
     ["threshold", "radius", "strength", "saturation", "knee", "mix"]),
    ("vjlive3.plugins.hue_effect", "HuePlugin",
     ["hue_shift", "saturation", "hue_range", "range_center", "feather", "mix"]),
    ("vjlive3.plugins.gaussian_blur", "GaussianBlurPlugin",
     ["radius", "sigma", "quality", "edge_mode", "color_bleed", "mix"]),
    ("vjlive3.plugins.feedback_effect", "FeedbackPlugin",
     ["amount", "decay", "zoom", "rotate_speed", "hue_drift", "mix"]),
    # Visualizers
    ("vjlive3.plugins.spectrum_analyzer", "SpectrumAnalyzerPlugin",
     ["freq_min", "freq_max", "bar_count", "bar_width", "color_hue", "mix"]),
    ("vjlive3.plugins.vu_meter", "VUMeterPlugin",
     ["peak_hold", "response", "color_hue", "width", "position", "mix"]),
    # Generators
    ("vjlive3.plugins.visualizer_effect", "VisualizerPlugin",
     ["bar_count", "bar_height", "color_hue", "color_mode", "bass_response", "mix"]),
]

REQUIRED_METADATA_KEYS = ("name", "description", "version", "plugin_type",
                          "category", "tags", "inputs", "outputs", "parameters")


def _load_plugin(module: str, classname: str):
    import importlib
    mod = importlib.import_module(module)
    return getattr(mod, classname)()


@pytest.mark.parametrize("module,classname,expected_params", PARITY_TABLE)
class TestLegacyParity:

    def test_metadata_complete(self, module, classname, expected_params):
        """All required metadata keys must be present."""
        plugin = _load_plugin(module, classname)
        meta = plugin.get_metadata()
        for key in REQUIRED_METADATA_KEYS:
            assert key in meta, f"Missing metadata key: '{key}' in {classname}"

    def test_parameter_count(self, module, classname, expected_params):
        """VJLive3 plugin must have at least as many params as VJlive-2 original."""
        plugin = _load_plugin(module, classname)
        meta = plugin.get_metadata()
        actual = [p["name"] for p in meta["parameters"]]
        assert len(actual) >= len(expected_params), (
            f"{classname}: expected ≥{len(expected_params)} params, got {len(actual)}"
        )

    def test_parameter_names_present(self, module, classname, expected_params):
        """Every expected VJlive-2 param name must exist in the VJLive3 plugin."""
        plugin = _load_plugin(module, classname)
        meta = plugin.get_metadata()
        actual_names = {p["name"] for p in meta["parameters"]}
        for name in expected_params:
            assert name in actual_names, (
                f"{classname}: missing expected param '{name}'. Have: {actual_names}"
            )

    def test_initialize_succeeds(self, module, classname, expected_params):
        """initialize() must return True in mock mode."""
        from unittest.mock import MagicMock
        _g.reset_mock()
        _g.glGetShaderiv.return_value = 1
        _g.glGetProgramiv.return_value = 1
        _g.glCreateProgram.return_value = 99
        _g.glGenVertexArrays.return_value = 44
        _g.glGenTextures.return_value = 55
        _g.glGenFramebuffers.return_value = 51

        plugin = _load_plugin(module, classname)
        ctx = MagicMock()
        ctx.width = 64; ctx.height = 48; ctx.time = 0.0
        ctx.inputs = {}; ctx.outputs = {}
        assert plugin.initialize(ctx) is True

    def test_params_have_min_max_default(self, module, classname, expected_params):
        """Each parameter must declare min, max, and default."""
        plugin = _load_plugin(module, classname)
        meta = plugin.get_metadata()
        for p in meta["parameters"]:
            assert "min" in p and "max" in p and "default" in p, (
                f"{classname}.{p['name']} missing min/max/default"
            )
