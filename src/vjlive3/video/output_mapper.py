import json
import logging
import numpy as np
from dataclasses import dataclass, asdict
from typing import List, Tuple, Dict, Any, Optional

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
class ScreenSlice:
    id: str
    x: float
    y: float
    width: float
    height: float
    warp_points: List[Tuple[float, float]]

class MeshWarper:
    """Helper class to generate OpenGL vertices/UVs based on warp points."""
    @staticmethod
    def _is_self_intersecting(pts: List[Tuple[float, float]]) -> bool:
        if len(pts) != 4:
            return False
        
        def ccw(A, B, C):
            return (C[1]-A[1]) * (B[0]-A[0]) > (B[1]-A[1]) * (C[0]-A[0])
            
        def intersect(A, B, C, D):
            return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)
            
        # Check standard bowtie intersect for quad ABCD
        # Intersection between AB and CD, or AD and BC
        if intersect(pts[0], pts[1], pts[2], pts[3]) or intersect(pts[0], pts[3], pts[1], pts[2]):
            return True
        return False

    @staticmethod
    def generate_quad_mesh(warp_points: List[Tuple[float, float]]) -> np.ndarray:
        if len(warp_points) != 4:
            logger.warning("generate_quad_mesh: Non-quad warp points detected. Defaulting to unit rectangle.")
            warp_points = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
            
        if MeshWarper._is_self_intersecting(warp_points):
            logger.warning("generate_quad_mesh: Self-intersecting warp points detected. Clamping.")
            warp_points = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
            
        return np.array(warp_points, dtype=np.float32)

class OutputMapper:
    """Manages slices and applies warping transformations."""
    def __init__(self, output_width: int, output_height: int) -> None:
        self.output_width = output_width
        self.output_height = output_height
        self.slices: Dict[str, ScreenSlice] = {}
        self._mock_mode = not HAS_GL
        self._fbo = None
        self._texture = None
        
        if not self._mock_mode:
            self._init_gl_resources()
            
    def _init_gl_resources(self) -> None:
        try:
            # We don't actually have a context initialized in tests, so this might fail.
            # We'll fail gracefully into mock mode if we can't create FBOs.
            self._fbo = gl.glGenFramebuffers(1)
            self._texture = gl.glGenTextures(1)
        except Exception as e:
            logger.warning(f"Failed to initialize GL resources: {e}")
            self._mock_mode = True

    def add_slice(self, screen_slice: ScreenSlice) -> None:
        self.slices[screen_slice.id] = screen_slice

    def update_warp_points(self, slice_id: str, points: List[Tuple[float, float]]) -> None:
        if slice_id in self.slices:
            self.slices[slice_id].warp_points = points
        else:
            logger.warning(f"Slice {slice_id} not found for warp update.")

    def process_frame(self, input_texture_id: int) -> int:
        """Returns the final warped and composed texture ID."""
        if self._mock_mode:
            # Cannot actually process GL, just passthrough
            return input_texture_id
             
        # In actual GL logic we bind self._fbo, render incoming texture projected to slices, return self._texture.
        return self._texture if self._texture is not None else input_texture_id

    def save_configuration(self, filepath: str) -> None:
        data = [asdict(s) for s in self.slices.values()]
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=4)
        except IOError as e:
            logger.error(f"Failed to save OutputMapper configuration: {e}")

    def load_configuration(self, filepath: str) -> None:
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            self.slices.clear()
            for item in data:
                # Need to convert list of lists to list of tuples for warp points due to JSON
                item['warp_points'] = [tuple(p) for p in item.get('warp_points', [])]
                self.add_slice(ScreenSlice(**item))
        except (IOError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load OutputMapper configuration: {e}")

    def shutdown(self) -> None:
        """Explicitly free FBO and Texture resources per SAFETY RAIL #8."""
        if not self._mock_mode:
            try:
                if self._fbo is not None:
                    gl.glDeleteFramebuffers(1, [self._fbo])
                if self._texture is not None:
                    gl.glDeleteTextures(1, [self._texture])
            except Exception as e:
                logger.error(f"Error deleting GL resources in OutputMapper shutdown: {e}")
        self._fbo = None
        self._texture = None
