"""Tests for VD70/72/73/74/75 depth plugins."""
import pytest
from unittest.mock import MagicMock, patch
import sys

mock_gl = MagicMock()
mock_gl.GL_VERTEX_SHADER   = 35633; mock_gl.GL_FRAGMENT_SHADER = 35632
mock_gl.GL_COMPILE_STATUS  = 35713; mock_gl.GL_LINK_STATUS     = 35714
mock_gl.GL_TEXTURE_2D      = 3553;  mock_gl.GL_RGBA            = 6408
mock_gl.GL_UNSIGNED_BYTE   = 5121;  mock_gl.GL_LINEAR           = 9729
mock_gl.GL_CLAMP_TO_EDGE   = 33071; mock_gl.GL_FRAMEBUFFER      = 36160
mock_gl.GL_COLOR_ATTACHMENT0 = 36064; mock_gl.GL_COLOR_BUFFER_BIT = 16384
mock_gl.GL_TRIANGLE_STRIP  = 5
mock_gl.GL_FALSE = 0; mock_gl.GL_TRUE = 1
mock_gl.glCreateShader.return_value    = 1
mock_gl.glGetShaderiv.return_value     = mock_gl.GL_TRUE
mock_gl.glGetProgramiv.return_value    = mock_gl.GL_TRUE
mock_gl.glGenVertexArrays.return_value = 44
_c = {"fbo": 50, "tex": 60, "prog": 98}
def _gp():     _c["prog"]+=1; return _c["prog"]
def _gfbo(n):  _c["fbo"] +=1; return _c["fbo"]
def _gtex(n):  _c["tex"] +=1; return _c["tex"]
mock_gl.glCreateProgram.side_effect   = _gp
mock_gl.glGenFramebuffers.side_effect = _gfbo
mock_gl.glGenTextures.side_effect     = _gtex

sys.modules['OpenGL']    = MagicMock()
sys.modules['OpenGL.GL'] = mock_gl


def _reset():
    mock_gl.reset_mock()
    mock_gl.glGetShaderiv.return_value  = mock_gl.GL_TRUE
    mock_gl.glGetProgramiv.return_value = mock_gl.GL_TRUE
    mock_gl.glGenVertexArrays.return_value = 44
    _c.update({"fbo": 50, "tex": 60, "prog": 98})


def make_context():
    ctx = MagicMock()(MagicMock())
    ctx.width = 1920; ctx.height = 1080
    ctx.inputs = {"video_in": 777, "depth_in": 888}
    ctx.time = 1.0; ctx.outputs = {}
    return ctx


# ── VD70 ─────────────────────────────────────────────────────────────────────
from vjlive3.plugins.depth_video_projection import DepthVideoProjectionPlugin, METADATA as M70

class TestDepthVideoProjection:
    def setup_method(self): _reset()

    def test_metadata(self):
        assert M70["name"] == "Depth Video Projection"
        assert len([p["name"] for p in M70["parameters"]]) == 8

    @patch('vjlive3.plugins.depth_video_projection.gl', mock_gl)
    def test_initialize(self):
        p = DepthVideoProjectionPlugin()
        assert p.initialize(make_context()) is True

    @patch('vjlive3.plugins.depth_video_projection.gl', mock_gl)
    def test_empty_input(self):
        p = DepthVideoProjectionPlugin(); p.initialize(make_context())
        assert p.process_frame(0, {}, make_context()) == 0

    @patch('vjlive3.plugins.depth_video_projection.gl', mock_gl)
    def test_process(self):
        p = DepthVideoProjectionPlugin(); p.initialize(make_context())
        p.process_frame(777, {"projection": 0.8}, make_context())
        mock_gl.glDrawArrays.assert_called()

    @patch('vjlive3.plugins.depth_video_projection.gl', mock_gl)
    def test_cleanup(self):
        p = DepthVideoProjectionPlugin(); p.initialize(make_context())
        p.prog = 99; p.cleanup()
        mock_gl.glDeleteProgram.assert_any_call(99)


# ── VD72 ─────────────────────────────────────────────────────────────────────
from vjlive3.plugins.depth_displacement import DepthDisplacementPlugin, METADATA as M72

class TestDepthDisplacement:
    def setup_method(self): _reset()

    def test_metadata(self):
        assert M72["name"] == "Depth Displacement"
        assert len([p["name"] for p in M72["parameters"]]) == 6

    @patch('vjlive3.plugins.depth_displacement.gl', mock_gl)
    def test_initialize(self):
        p = DepthDisplacementPlugin()
        assert p.initialize(make_context()) is True

    @patch('vjlive3.plugins.depth_displacement.gl', mock_gl)
    def test_empty_input(self):
        p = DepthDisplacementPlugin(); p.initialize(make_context())
        assert p.process_frame(0, {}, make_context()) == 0

    @patch('vjlive3.plugins.depth_displacement.gl', mock_gl)
    def test_process(self):
        p = DepthDisplacementPlugin(); p.initialize(make_context())
        p.process_frame(777, {"displace_scale": 0.05}, make_context())
        mock_gl.glDrawArrays.assert_called()

    @patch('vjlive3.plugins.depth_displacement.gl', mock_gl)
    def test_cleanup(self):
        p = DepthDisplacementPlugin(); p.initialize(make_context())
        p.prog = 99; p.cleanup()
        mock_gl.glDeleteProgram.assert_any_call(99)


# ── VD73 ─────────────────────────────────────────────────────────────────────
from vjlive3.plugins.depth_echo import DepthEchoPlugin, METADATA as M73

class TestDepthEcho:
    def setup_method(self): _reset()

    def test_metadata(self):
        assert M73["name"] == "Depth Echo"
        assert len([p["name"] for p in M73["parameters"]]) == 5

    @patch('vjlive3.plugins.depth_echo.gl', mock_gl)
    def test_initialize(self):
        p = DepthEchoPlugin()
        assert p.initialize(make_context()) is True

    @patch('vjlive3.plugins.depth_echo.gl', mock_gl)
    def test_empty_input(self):
        p = DepthEchoPlugin(); p.initialize(make_context())
        assert p.process_frame(0, {}, make_context()) == 0

    @patch('vjlive3.plugins.depth_echo.gl', mock_gl)
    def test_process(self):
        p = DepthEchoPlugin(); p.initialize(make_context())
        p.process_frame(777, {"echo_strength": 0.8}, make_context())
        mock_gl.glDrawArrays.assert_called()

    @patch('vjlive3.plugins.depth_echo.gl', mock_gl)
    def test_cleanup(self):
        p = DepthEchoPlugin(); p.initialize(make_context())
        p.prog = 99; p.cleanup()
        mock_gl.glDeleteProgram.assert_any_call(99)


# ── VD74 ─────────────────────────────────────────────────────────────────────
from vjlive3.plugins.ml_depth_estimation import MLDepthEstimationPlugin, METADATA as M74

class TestMLDepthEstimation:
    def setup_method(self): _reset()

    def test_metadata(self):
        assert M74["name"] == "ML Depth Estimation"
        assert len([p["name"] for p in M74["parameters"]]) == 6

    @patch('vjlive3.plugins.ml_depth_estimation.gl', mock_gl)
    def test_initialize(self):
        p = MLDepthEstimationPlugin()
        assert p.initialize(make_context()) is True

    @patch('vjlive3.plugins.ml_depth_estimation.gl', mock_gl)
    def test_empty_input(self):
        p = MLDepthEstimationPlugin(); p.initialize(make_context())
        assert p.process_frame(0, {}, make_context()) == 0

    @patch('vjlive3.plugins.ml_depth_estimation.gl', mock_gl)
    def test_process(self):
        p = MLDepthEstimationPlugin(); p.initialize(make_context())
        p.process_frame(777, {"depth_scale": 1.0}, make_context())
        mock_gl.glDrawArrays.assert_called()

    @patch('vjlive3.plugins.ml_depth_estimation.gl', mock_gl)
    def test_cleanup(self):
        p = MLDepthEstimationPlugin(); p.initialize(make_context())
        p.prog = 99; p.cleanup()
        mock_gl.glDeleteProgram.assert_any_call(99)


# ── VD75 ─────────────────────────────────────────────────────────────────────
from vjlive3.plugins.quantum_depth_nexus import QuantumDepthNexusPlugin, METADATA as M75

class TestQuantumDepthNexus:
    def setup_method(self): _reset()

    def test_metadata(self):
        assert M75["name"] == "Quantum Depth Nexus"
        assert len([p["name"] for p in M75["parameters"]]) == 8

    @patch('vjlive3.plugins.quantum_depth_nexus.gl', mock_gl)
    def test_initialize(self):
        p = QuantumDepthNexusPlugin()
        assert p.initialize(make_context()) is True

    @patch('vjlive3.plugins.quantum_depth_nexus.gl', mock_gl)
    def test_empty_input(self):
        p = QuantumDepthNexusPlugin(); p.initialize(make_context())
        assert p.process_frame(0, {}, make_context()) == 0

    @patch('vjlive3.plugins.quantum_depth_nexus.gl', mock_gl)
    def test_process(self):
        p = QuantumDepthNexusPlugin(); p.initialize(make_context())
        p.process_frame(777, {"quantum_intensity": 0.5}, make_context())
        mock_gl.glDrawArrays.assert_called()

    @patch('vjlive3.plugins.quantum_depth_nexus.gl', mock_gl)
    def test_cleanup(self):
        p = QuantumDepthNexusPlugin(); p.initialize(make_context())
        p.prog = 99; p.cleanup()
        mock_gl.glDeleteProgram.assert_any_call(99)
