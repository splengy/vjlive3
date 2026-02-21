"""Effects module for VJLive3.

This module provides a variety of visual effects for video processing.
Effects are modular and can be chained together in a pipeline.

Available effects:
- BlurEffect: Gaussian, box, and median blur
- ColorCorrectionEffect: Brightness, contrast, saturation adjustment
- DistortEffect: Various distortion effects
- TransitionEffect: Scene transitions

Custom effects can be created by inheriting from Effect base class.
"""

from vjlive3.effects.base import Effect
from vjlive3.effects.blur import BlurEffect
from vjlive3.effects.color import ColorCorrectionEffect
from vjlive3.effects.distort import DistortEffect

__all__ = [
    "Effect",
    "BlurEffect",
    "ColorCorrectionEffect",
    "DistortEffect",
]