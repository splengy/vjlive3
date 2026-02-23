"""
tests/conftest.py — Shared test fixtures for VJLive3.

CRITICAL RULE (TOOL_TIPS.md):
    ALL imports of optional modules MUST use try/except ImportError guards.
    Never add a bare import here — it causes collection hangs for ALL agents.
    Pattern:
        try:
            from vjlive3.x import Y
            _X_AVAILABLE = True
        except ImportError:
            _X_AVAILABLE = False

References:
    - WORKSPACE/KNOWLEDGE/TOOL_TIPS.md (import guard rule)
    - WORKSPACE/VERIFICATION_CHECKPOINTS.md (conftest note at bottom)
    - docs/specs/P0-INF1_package_skeleton.md
"""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

# ── Optional rendering imports (GPU may not be available in CI) ──────────────
try:
    import moderngl  # type: ignore
    _MODERNGL_AVAILABLE = True
except ImportError:
    _MODERNGL_AVAILABLE = False

# ── Optional audio imports ────────────────────────────────────────────────────
try:
    import sounddevice as sd  # type: ignore
    _SOUNDDEVICE_AVAILABLE = True
except ImportError:
    _SOUNDDEVICE_AVAILABLE = False

# ── Optional plugin system ────────────────────────────────────────────────────
try:
    from vjlive3.plugins.registry import PluginRegistry
    from vjlive3.plugins.loader import PluginLoader
    _PLUGIN_SYSTEM_AVAILABLE = True
except ImportError:
    _PLUGIN_SYSTEM_AVAILABLE = False
    # Mock fallback for test collection if module is deleted
    PluginRegistry = MagicMock
    PluginLoader = MagicMock

_log = logging.getLogger(__name__)


# ─────────────────────────── FILESYSTEM FIXTURES ─────────────────────────────

@pytest.fixture
def tmp_plugin_dir(tmp_path: Path) -> Path:
    """Isolated, empty plugin directory for a single test.

    Creates the directory structure expected by PluginLoader:
        <tmp>/plugins/
            my_plugin/
                plugin.json
                __init__.py

    Returns the root ``plugins/`` directory path.
    """
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()
    return plugins_dir


@pytest.fixture
def plugin_manifest(tmp_plugin_dir: Path) -> dict:
    """Write a minimal valid plugin.json to tmp_plugin_dir and return the dict.

    Creates:
        <tmp_plugin_dir>/test_plugin/plugin.json
        <tmp_plugin_dir>/test_plugin/__init__.py
    """
    import json

    plugin_dir = tmp_plugin_dir / "test_plugin"
    plugin_dir.mkdir()

    manifest = {
        "id": "test_plugin",
        "name": "Test Plugin",
        "version": "1.0.0",
        "main": "__init__.py",
        "description": "Minimal plugin for unit testing. Does nothing, breaks nothing.",
        "author": "VJLive3 Test Suite",
        "api_version": "3.0",
        "parameters": [],
        "metadata": {
            "tags": ["test"],
            "category": "core",
            "complexity": "low",
            "performance_impact": "low",
        },
    }

    (plugin_dir / "plugin.json").write_text(json.dumps(manifest, indent=2))
    (plugin_dir / "__init__.py").write_text(
        '"""Minimal test plugin stub."""\n\n\nclass TestPlugin:\n    METADATA = {}\n\n    def process(self, frame, audio_data):\n        return frame\n'
    )

    return manifest


# ─────────────────────────── FRAME / ARRAY FIXTURES ──────────────────────────

@pytest.fixture
def sample_frame() -> np.ndarray:
    """A blank 720p RGB frame (numpy uint8 array).

    Shape: (720, 1280, 3) — height × width × channels.
    All pixels are black (zeros). Provides a valid input for process() calls.
    """
    return np.zeros((720, 1280, 3), dtype=np.uint8)


@pytest.fixture
def sample_frame_1080p() -> np.ndarray:
    """A blank 1080p RGB frame for performance / FPS tests.

    Shape: (1080, 1920, 3).
    """
    return np.zeros((1080, 1920, 3), dtype=np.uint8)


# ─────────────────────────── AUDIO FIXTURES ──────────────────────────────────

@pytest.fixture
def mock_audio_stream() -> MagicMock:
    """A mock sounddevice.InputStream that yields silence.

    Returns a MagicMock with the same API surface that audio modules expect:
        stream.start()
        stream.stop()
        stream.close()
        stream.read(n) -> (np.zeros((n,)), False)

    Usable without any audio hardware present.
    """
    mock = MagicMock(spec=["start", "stop", "close", "read", "active"])
    mock.active = True
    mock.read.return_value = (np.zeros(1024, dtype=np.float32), False)
    return mock


@pytest.fixture
def mock_audio_data() -> MagicMock:
    """Fake AudioData object used by audio-reactive effects.

    Provides the fields that reactivity_bus and effects expect:
        .rms          → float  (0.0–1.0)
        .bpm          → float  (120.0)
        .beat         → bool
        .spectrum     → np.ndarray shape (512,)   FFT magnitudes
        .waveform     → np.ndarray shape (1024,)  raw samples
    """
    mock = MagicMock()
    mock.rms = 0.5
    mock.bpm = 120.0
    mock.beat = False
    mock.spectrum = np.random.rand(512).astype(np.float32)
    mock.waveform = np.zeros(1024, dtype=np.float32)
    return mock


# ─────────────────────────── RENDERING FIXTURES ──────────────────────────────

@pytest.fixture
def headless_gl_context() -> Generator:
    """A ModernGL standalone context for headless rendering tests.

    Behaviour:
        - If moderngl is importable AND can create a standalone context
          (i.e. real GPU/EGL available), returns the real Context object.
        - Otherwise, returns a MagicMock with the same attribute surface.
          This allows rendering tests to run in CI without GPU hardware.

    Pattern from VJlive-2/core/opengl_raii.py graceful fallback.

    Yields the context; ensures release on test teardown.
    """
    if _MODERNGL_AVAILABLE:
        try:
            ctx = moderngl.create_standalone_context()
            yield ctx
            ctx.release()
            return
        except Exception as exc:  # noqa: BLE001
            _log.debug("ModernGL standalone context failed (%s) — using mock", exc)

    # Fallback: MagicMock with the interface rendering code expects
    mock_ctx = MagicMock()
    mock_ctx.version_code = 330
    mock_ctx.screen = MagicMock()
    mock_ctx.framebuffer = MagicMock(return_value=MagicMock())
    mock_ctx.texture = MagicMock(return_value=MagicMock())
    mock_ctx.program = MagicMock(return_value=MagicMock())
    mock_ctx.buffer = MagicMock(return_value=MagicMock())
    yield mock_ctx


# ─────────────────────────── PLUGIN SYSTEM FIXTURES ──────────────────────────

@pytest.fixture
def plugin_registry(tmp_plugin_dir: Path):
    """A PluginRegistry pointed at a temporary plugin directory.

    Skips the test if the plugin system is not importable.
    """
    if not _PLUGIN_SYSTEM_AVAILABLE:
        pytest.skip("Plugin system not importable — skipping")
    registry = PluginRegistry(plugin_dir=tmp_plugin_dir)
    return registry


@pytest.fixture
def plugin_loader(tmp_plugin_dir: Path):
    """A PluginLoader pointed at a temporary plugin directory.

    Skips the test if the plugin system is not importable.
    """
    if not _PLUGIN_SYSTEM_AVAILABLE:
        pytest.skip("Plugin system not importable — skipping")
    loader = PluginLoader(plugin_dir=tmp_plugin_dir)
    return loader
