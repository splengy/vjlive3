"""Core module for VJLive3.

This module contains the fundamental building blocks of the video processing
pipeline, including the main orchestrator, frame handling, timing, state
management, and configuration.

Key components:
- VideoPipeline: Main orchestrator for video processing
- Frame: Frame representation and utilities
- Timing: Timing, BPM detection, and synchronization
- State: Centralized state management
- Config: Configuration loading and validation
- SiliconSigil: The soul of the app (always importable, no GPU required)

Note: GPU/OpenGL components are lazily imported to allow headless operation
(tests, MCP servers, sigil verification) without requiring display hardware.
"""
from __future__ import annotations

# The Sigil is always available — it has no GPU dependencies
from vjlive3.core.sigil import SiliconSigil, sigil

__all__ = [
    "SiliconSigil",
    "sigil",
    "VideoPipeline",
    "Frame",
    "TimingManager",
    "StateManager",
    "Config",
]


def __getattr__(name: str) -> object:
    """Lazy import for GPU-dependent core components."""
    if name == "VideoPipeline":
        from vjlive3.core.pipeline import VideoPipeline
        return VideoPipeline
    if name == "Frame":
        from vjlive3.core.frame import Frame
        return Frame
    if name == "TimingManager":
        from vjlive3.core.timing import TimingManager
        return TimingManager
    if name == "StateManager":
        from vjlive3.core.state import StateManager
        return StateManager
    if name == "Config":
        from vjlive3.core.config import Config
        return Config
    raise AttributeError(f"module 'vjlive3.core' has no attribute {name!r}")