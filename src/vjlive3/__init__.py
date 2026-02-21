"""VJLive3 - Next Generation Visual Performance System.

This package provides a professional-grade live visual performance system
with real-time video processing, modular effects, and multi-platform support.

Note: All hardware-dependent components (GPU, audio, camera) are lazily
imported on first use. The package can be safely imported in headless
environments (tests, MCP servers, CI) without any hardware present.

Example:
    >>> from vjlive3.core import sigil        # always works — no hardware
    >>> from vjlive3 import VideoPipeline     # lazy — no import-time GPU init
    >>> app = VideoPipeline(config)
    >>> app.run()
"""
from __future__ import annotations

__version__ = "0.1.0"
__author__ = "VJLive Team"
__email__ = "team@vjlive.com"
__license__ = "MIT"
__url__ = "https://github.com/vjlive/vjlive3"

# Only the Sigil is eager — it has zero hardware dependencies
# and must be verifiable from any context.
from vjlive3.core.sigil import SiliconSigil, sigil  # noqa: E402

__all__ = [
    "__version__",
    "sigil",
    "SiliconSigil",
    "VideoPipeline",
    "Effect",
    "Source",
]


def __getattr__(name: str) -> object:
    """Lazy import for all hardware/GPU-dependent components."""
    if name == "VideoPipeline":
        from vjlive3.core.pipeline import VideoPipeline
        return VideoPipeline
    if name == "Effect":
        from vjlive3.effects.base import Effect
        return Effect
    if name == "Source":
        from vjlive3.sources.base import Source
        return Source
    raise AttributeError(f"module 'vjlive3' has no attribute {name!r}")