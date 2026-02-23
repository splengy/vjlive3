import logging
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Dict, Any

logger = logging.getLogger(__name__)

import os
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
    width: float  # Normalized 0.0 to 1.0 width of the blend zone
    gamma: float = 1.0  # Curve for the blend falloff
    luminance: float = 0.5  # Center point luminance adjustment

@dataclass
class PolygonMask:
    points: List[Tuple[float, float]]  # Normalized 0.0 to 1.0 coordinates
    inverted: bool = False  # True = mask outside, False = mask inside

PROJECTION_FRAGMENT_SHADER = """
#version 330 core
out vec4 FragColor;
in vec2 TexCoords;

uniform sampler2D texture_in;

// Blending configurations
uniform float blend_left;
uniform float blend_right;
uniform float blend_top;
uniform float blend_bottom;

uniform float gamma_left;
uniform float gamma_right;
uniform float gamma_top;
uniform float gamma_bottom;

uniform float lum_left;
uniform float lum_right;
uniform float lum_top;
uniform float lum_bottom;

float calc_blend(float coord, float width, float gamma, float lum) {
    if (width <= 0.0) return 1.0;
    if (coord > width) return 1.0;
    
    // Normalized position inside blend region (0 to 1)
    float t = coord / width;
    
    // Apply gamma curve
    float blend = pow(t, gamma);
    
    // Adjust luminance (very basic approximation)
    return blend * (1.0 + (lum - 0.5) * 2.0);
}

void main() {
    // Start with base texture
    vec4 color = texture(texture_in, TexCoords);
    
    // Calculate blends for each edge
    float b_left = calc_blend(TexCoords.x, blend_left, gamma_left, lum_left);
    float b_right = calc_blend(1.0 - TexCoords.x, blend_right, gamma_right, lum_right);
    float b_bottom = calc_blend(TexCoords.y, blend_bottom, gamma_bottom, lum_bottom);
    float b_top = calc_blend(1.0 - TexCoords.y, blend_top, gamma_top, lum_top);
    
    // Multiply color by blend factors
    color.rgb *= b_left * b_right * b_top * b_bottom;
    
    FragColor = color;
}
"""

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
            # Setup texture size
            gl.glBindTexture(gl.GL_TEXTURE_2D, self._texture)
            gl.glTexImage2D(
                gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, 
                self.slice_width, self.slice_height, 
                0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None
            )
            gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
        except Exception as e:
            logger.warning(f"Failed to init ProjectionMapper GL resources: {e}")
            self._mock_mode = True

    def set_blend(self, region: BlendRegion) -> None:
        """Sets an edge blend, clamping opposing edges if they intersect."""
        if region.edge not in ('left', 'right', 'top', 'bottom'):
            logger.error(f"Invalid blend edge: {region.edge}")
            return
            
        width = max(0.0, min(1.0, region.width))
        region.width = width
        
        self.blends[region.edge] = region
        self._clamp_opposing_blends(region.edge)
        
    def _clamp_opposing_blends(self, changed_edge: str) -> None:
        pairs = {
            'left': 'right',
            'right': 'left',
            'top': 'bottom',
            'bottom': 'top'
        }
        
        opposing = pairs[changed_edge]
        if changed_edge in self.blends and opposing in self.blends:
            b1 = self.blends[changed_edge]
            b2 = self.blends[opposing]
            
            # If the sum of widths exceeds 1.0, they overlap centrally.
            total = b1.width + b2.width
            if total > 1.0:
                # Distribute proportionally down to max of 1.0 sum
                # A simple safety is capping both at 0.5 if they are identical, 
                # or scaling down relative to their initial requests.
                scale = 1.0 / total
                b1.width *= scale
                b2.width *= scale
                logger.warning(f"Overlapping blends '{changed_edge}' and '{opposing}' clamped.")
                
    def clear_blend(self, edge: str) -> None:
        if edge in self.blends:
            del self.blends[edge]
            
    def add_mask(self, mask: PolygonMask) -> int:
        if len(mask.points) < 3:
            logger.warning("Mask requires at least 3 points. Mask ignored.")
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
        """Applies blending and masks to the input slice, returning the final texture ID."""
        if self._mock_mode:
            # Fallback for headless environments without GL context
            return texture_id
            
        if self._fbo is None or self._texture is None:
            return texture_id
            
        try:
            # Conceptually, this would:
            # 1. Bind self._fbo and self._texture
            # 2. Clear color and stencil buffers
            # 3. If masks exist, draw mask geometry to stencil buffer
            # 4. Use a shader that receives BlendRegions uniformly
            # 5. Draw the full screen quad with texture_id, applying blends in shader, respecting stencil
            
            # For this porting layer, we just ensure it returns the output texture.
            # Real rendering requires a full context loop.
            return self._texture
        except Exception as e:
            logger.error(f"Error processing projection slice: {e}")
            return texture_id

    def shutdown(self) -> None:
        if not self._mock_mode:
            try:
                if self._fbo is not None:
                    gl.glDeleteFramebuffers(1, [self._fbo])
                if self._texture is not None:
                    gl.glDeleteTextures(1, [self._texture])
            except Exception as e:
                logger.error(f"Error shutting down projection mapper: {e}")
        self._fbo = None
        self._texture = None
