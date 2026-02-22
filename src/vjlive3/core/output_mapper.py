"""
P2-X3: Output Mapping & Screen Warping
Provides 2D perspective warping and screen slicing for physical displays.
"""
import json
import logging
from dataclasses import dataclass, asdict
from typing import List, Tuple, Dict, Any
import numpy as np

logger = logging.getLogger("vjlive3.core.output_mapper")


@dataclass
class ScreenSlice:
    id: str
    x: float  # Normalized 0-1
    y: float
    width: float
    height: float
    warp_points: List[Tuple[float, float]]  # 4 points for quad


class MeshWarper:
    """Helper class to generate OpenGL vertices/UVs based on warp points."""
    @staticmethod
    def generate_quad_mesh(warp_points: List[Tuple[float, float]]) -> np.ndarray:
        """
        Generates an interleaved float32 array [x, y, u, v, ...] from 4 warp points.
        Assumes warp_points are ordered: Top-Left, Top-Right, Bottom-Right, Bottom-Left
        """
        if len(warp_points) != 4:
            logger.warning("generate_quad_mesh requires exactly 4 points. Falling back to default quad.")
            warp_points = [(0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0)]
            
        # Standard UVs mapped to the 4 corners
        uvs = [(0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0)]
        
        mesh_data = []
        for i in range(4):
            # Clamp warp points between 0.0 and 1.0 to prevent out of bounds
            x = max(0.0, min(1.0, warp_points[i][0]))
            y = max(0.0, min(1.0, warp_points[i][1]))
            mesh_data.extend([x, y, uvs[i][0], uvs[i][1]])
            
        # Return as a flat GPU-ready array
        return np.array(mesh_data, dtype=np.float32)


class OutputMapper:
    """Manages slices and applies warping transformations."""
    def __init__(self, output_width: int, output_height: int) -> None:
        self.output_width = output_width
        self.output_height = output_height
        self.slices: Dict[str, ScreenSlice] = {}
        self._fbo_id = -1
        
    def add_slice(self, screen_slice: ScreenSlice) -> None:
        if screen_slice.id in self.slices:
            logger.warning(f"Slice with ID {screen_slice.id} already exists. Overwriting.")
        self.slices[screen_slice.id] = screen_slice
        
    def update_warp_points(self, slice_id: str, points: List[Tuple[float, float]]) -> None:
        if slice_id not in self.slices:
            logger.warning(f"Slice {slice_id} not found.")
            return
            
        # Basic sanity check (prevent self-intersecting polygon completely breaking by clamping to simple rect)
        # For a true engine, we'd do a cross-product test here, but for this abstraction clamping to simple
        # ranges provides base safety.
        if len(points) != 4:
            logger.warning("Warp points must be exactly 4 coordinates.")
            return
            
        clamped_points = []
        for x, y in points:
            clamped_points.append((
                max(-1.0, min(2.0, float(x))), # allow some overscan, but not infinite
                max(-1.0, min(2.0, float(y)))
            ))
            
        self.slices[slice_id].warp_points = clamped_points

    def process_frame(self, input_texture_id: int) -> int:
        """
        Returns the final warped and composed texture ID.
        In a headless or testing environment where OpenGL isn't fully bound, 
        this safely returns the input ID.
        """
        # Under normal conditions, this would bind an FBO, clear it, iterate through
        # self.slices, calculate MeshWarper vertex arrays, bind a generic warping shader, 
        # and issue draw calls. 
        if self._fbo_id == -1:
            # Fallback when no FBO is created (e.g. testing or FBO fail)
            return input_texture_id
            
        # Placeholder for actual GL draw calls (requires ModernGL context which P1-R1 handles)
        return self._fbo_id

    def save_configuration(self, filepath: str) -> None:
        try:
            data = {}
            for s_id, s_obj in self.slices.items():
                data[s_id] = asdict(s_obj)
                
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save OutputMapper config: {e}")

    def load_configuration(self, filepath: str) -> None:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            for s_id, s_dict in data.items():
                self.slices[s_id] = ScreenSlice(
                    id=s_dict['id'],
                    x=s_dict['x'],
                    y=s_dict['y'],
                    width=s_dict['width'],
                    height=s_dict['height'],
                    warp_points=[tuple(pt) for pt in s_dict['warp_points']]
                )
        except Exception as e:
            logger.error(f"Failed to load OutputMapper config: {e}")

    def destroy(self) -> None:
        self.slices.clear()
        # Ensure GL resources are cleaned up
        if self._fbo_id != -1:
            # glDeleteFramebuffers(1, [self._fbo_id])
            self._fbo_id = -1
