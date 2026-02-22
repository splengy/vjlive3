"""
Unit tests for the P1-R5 Core Rendering Engine.
"""
import pytest
import time
from unittest.mock import MagicMock

import moderngl

from vjlive3.render.engine import RenderEngine
from vjlive3.render.opengl_context import OpenGLContext
from vjlive3.plugins.api import PluginBase

def test_init_no_hardware():
    with pytest.raises(ValueError):
        RenderEngine(ctx=None, width=100, height=100)
        
    ctx = MagicMock(spec=moderngl.Context)
    with pytest.raises(ValueError):
        RenderEngine(ctx, -1, 100)
    with pytest.raises(ValueError):
        RenderEngine(ctx, 100, 0)

def test_start_stop():
    hw = OpenGLContext(1280, 720, headless=True)
    hw.make_current()
    if not hw.ctx:
        hw.terminate()
        pytest.skip("No modernGL context")
        
    try:
        engine = RenderEngine(hw.ctx, 800, 600)
        assert not engine.is_running()
        
        engine.start()
        assert engine.is_running()
        assert engine.get_frame_count() == 0
        
        engine.stop()
        assert not engine.is_running()
        
        engine.cleanup()
    finally:
        hw.terminate()

def test_plugin_chain():
    hw = OpenGLContext(1280, 720, headless=True)
    hw.make_current()
    if not hw.ctx:
        hw.terminate()
        pytest.skip("No modernGL context")
        
    try:
        engine = RenderEngine(hw.ctx, 800, 600)
        
        p1 = MagicMock(spec=PluginBase)
        p1.id = "p1"
        p2 = MagicMock(spec=PluginBase)
        p2.id = "p2"
        
        # Add single
        engine.add_plugin(p1)
        assert len(engine._plugin_wrappers) == 1
        
        # Add duplicate ignores
        engine.add_plugin(p1)
        assert len(engine._plugin_wrappers) == 1
        
        # Set chain wholesale
        engine.set_plugin_chain([p1, p2])
        assert len(engine._plugin_wrappers) == 2
        
        # Remove single
        engine.remove_plugin(p1)
        assert len(engine._plugin_wrappers) == 1
        assert "p2" in engine._plugin_wrappers
        
        # Empty/None checks ignore silently
        engine.remove_plugin(None)
        assert len(engine._plugin_wrappers) == 1
        
        engine.cleanup()
    finally:
        hw.terminate()

def test_frame_output():
    hw = OpenGLContext(1280, 720, headless=True)
    hw.make_current()
    if not hw.ctx:
        hw.terminate()
        pytest.skip("No modernGL context")
        
    try:
        engine = RenderEngine(hw.ctx, 800, 600)
        # Verify pre-render state empty
        assert engine.get_frame_count() == 0
        assert engine.get_current_frame() is None
        
        # Ensure frame output skips if stopped
        engine.render_frame()
        assert engine.get_frame_count() == 0
        
        # Render a frame
        engine.start()
        engine.render_frame()
        
        assert engine.get_frame_count() == 1
        tex = engine.get_current_frame()
        assert tex is not None
        
        engine.cleanup()
    finally:
        hw.terminate()

def test_fps_counter():
    hw = OpenGLContext(1280, 720, headless=True)
    hw.make_current()
    if not hw.ctx:
        hw.terminate()
        pytest.skip("No modernGL context")
        
    try:
        engine = RenderEngine(hw.ctx, 800, 600)
        engine.start()
        
        # Fake a burst of 5 frames running instantaneously
        # Standard sleep throttle logic will apply
        for _ in range(5):
            engine.render_frame()
            
        assert engine.get_fps() == 5.0
        assert engine.get_frame_count() == 5
        
        engine.cleanup()
    finally:
        hw.terminate()

def test_resize():
    hw = OpenGLContext(1280, 720, headless=True)
    hw.make_current()
    if not hw.ctx:
        hw.terminate()
        pytest.skip("No modernGL context")
        
    try:
        engine = RenderEngine(hw.ctx, 800, 600)
        
        # Bad resize ignored silently
        engine.on_resize(0, -50)
        assert engine.width == 800
        
        p1 = MagicMock(spec=PluginBase)
        p1.id = "p1"
        engine.add_plugin(p1)
        
        # Valid resize rebuilds chains
        engine.on_resize(1920, 1080)
        assert engine.width == 1920
        assert engine.height == 1080
        assert len(engine._plugin_wrappers) == 1
        
        engine.start()
        engine.render_frame()
        
        # Ensure updated output reflects resize boundaries
        tex = engine.get_current_frame()
        assert tex is not None
        
        engine.cleanup()
    finally:
        hw.terminate()

def test_plugin_error():
    hw = OpenGLContext(1280, 720, headless=True)
    hw.make_current()
    if not hw.ctx:
        hw.terminate()
        pytest.skip("No modernGL context")
        
    try:
        engine = RenderEngine(hw.ctx, 800, 600)
        
        # Create a plugin that dies hard internally
        p_crash = MagicMock(spec=PluginBase)
        p_crash.id = "crash"
        p_crash.process = MagicMock()
        p_crash.process.side_effect = Exception("Internal divide by zero or logic error")
        
        engine.add_plugin(p_crash)
        assert len(engine._plugin_wrappers) == 1
        
        engine.start()
        # Should gracefully absorb the error and eject the plugin
        engine.render_frame()
        
        assert engine.get_frame_count() == 1
        assert engine.is_running() is True # Overall app loop doesn't die
        assert len(engine._plugin_wrappers) == 0 # Crashing plugin evicted
        
        engine.cleanup()
    finally:
        hw.terminate()

def test_cleanup():
    hw = OpenGLContext(1280, 720, headless=True)
    hw.make_current()
    if not hw.ctx:
        hw.terminate()
        pytest.skip("No modernGL context")
        
    try:
        engine = RenderEngine(hw.ctx, 800, 600)
        
        p1 = MagicMock(spec=PluginBase)
        engine.add_plugin(p1)
        
        engine.cleanup()
        
        # Ensure tracking lists wiped
        assert len(engine._plugin_wrappers) == 0
        
    finally:
        hw.terminate()
