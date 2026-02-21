"""Video sources module for VJLive3.

This module provides various video source implementations that can feed
frames into the processing pipeline.

Available sources:
- TestPatternGenerator: Generates test patterns (color bars, noise, etc.)
- FileSource: Loads video from files
- CameraSource: Captures from cameras
- GeneratorSource: Procedural content
- NetworkSource: Receives from network (NDI, Syphon, etc.)
"""

from vjlive3.sources.base import Source
from vjlive3.sources.generator import TestPatternGenerator

__all__ = [
    "Source",
    "TestPatternGenerator",
]