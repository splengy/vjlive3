import os
import logging
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional

logger = logging.getLogger(__name__)

try:
    if os.environ.get("PYTEST_MOCK_GL"):
        raise ImportError("Forced MOCK GL for pytest")
    import OpenGL.GL as gl
    HAS_GL = True
except ImportError:
    HAS_GL = False
    gl = None

@dataclass
class BlendRegion:
    edge: str  # 'left', 'right', 'top', 'bottom'
    width: float
    gamma: float = 1.0
    luminance: float = 0.5

@dataclass
class PolygonMask:
    points: List[Tuple[float, float]]
    inverted: bool = False

class ProjectionMapper:
    """Applies edge blending and masking to a warped slice."""
    
    def __init__(self, slice_width: int, slice_height: int) -> None:
        self.slice_width = slice_width
        self.slice_height = slice_height
        
        self.blends: Dict[str, BlendRegion] = {}
        self.masks: Dict[int, PolygonMask] = {}
        self._next_mask_id = 0
        
        self._mock_mode = not HAS_GL
        self._fbo = None
        self._texture = None
        
        if not self._mock_mode:
            self._init_gl_resources()
            
    def _init_gl_resources(self) -> None:
        try:
            self._fbo = gl.glGenFramebuffers(1)
            self._texture = gl.glGenTextures(1)
            # In a real implementation we would bind and initialize the texture storage here
        except Exception as e:
            logger.warning(f"Failed to initialize GL resources for ProjectionMapper: {e}")
            self._mock_mode = True

    def _enforce_blend_limits(self) -> None:
        """Ensures that opposing blends do not overlap (sum > 1.0). Clamps to 0.5 if they do."""
        left = self.blends.get('left')
        right = self.blends.get('right')
        if left and right and (left.width + right.width > 1.0):
            left.width = 0.5
            right.width = 0.5
            
        top = self.blends.get('top')
        bottom = self.blends.get('bottom')
        if top and bottom and (top.width + bottom.width > 1.0):
            top.width = 0.5
            bottom.width = 0.5

    def set_blend(self, region: BlendRegion) -> None:
        if region.edge not in ['left', 'right', 'top', 'bottom']:
            logger.warning(f"Invalid blend edge '{region.edge}'. Ignored.")
            return
            
        # Clamp width to sensible bounds before overlap check
        region.width = max(0.0, min(1.0, region.width))
        self.blends[region.edge] = region
        self._enforce_blend_limits()

    def clear_blend(self, edge: str) -> None:
        if edge in self.blends:
            del self.blends[edge]

    def add_mask(self, mask: PolygonMask) -> int:
        if len(mask.points) < 3:
            logger.warning("Mask rejected: PolygonMask requires at least 3 points.")
            return -1
            
        mask_id = self._next_mask_id
        self._next_mask_id += 1
        self.masks[mask_id] = mask
        return mask_id

    def remove_mask(self, mask_id: int) -> bool:
        if mask_id in self.masks:
            del self.masks[mask_id]
            return True
        return False

    def process_slice(self, texture_id: int) -> int:
        """Applies blending and masks, returning final texture ID."""
        if self._mock_mode:
            # Bypass GL processing natively and return standard mock or input ID
            return texture_id
            
        # NATIVE GL IMPLEMENTATION
        # In a real application, we would bind self._fbo, render the texture 
        # using a fragment shader handling the blend zones mapped from self.blends
        # and stencil/draw black geometry for self.masks.
        
        return self._texture if self._texture is not None else texture_id

    def shutdown(self) -> None:
        """Clears memory allocated for specific FBO loops."""
        if not self._mock_mode:
            try:
                if self._fbo is not None:
                    gl.glDeleteFramebuffers(1, [self._fbo])
                if self._texture is not None:
                    gl.glDeleteTextures(1, [self._texture])
            except Exception as e:
                logger.error(f"Error deleting GL resources in ProjectionMapper shutdown: {e}")
                
        self._fbo = None
        self._texture = None
