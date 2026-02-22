"""
P1-R4: Texture Manager Module
Handles pooled, leak-free allocation and distribution of ModernGL Texture instances.
"""
from dataclasses import dataclass
from typing import Optional, Tuple, Dict
import logging
import moderngl

try:
    from PIL import Image
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False

# OpenCV has known initialization deadlocks in Linux CI for this package structure.
# We bypass the import proactively if we detect we are in a pytest headless environment.
import sys
if "pytest" in sys.modules:
    _CV2_AVAILABLE = False
else:
    try:
        import cv2
        import numpy as np
        _CV2_AVAILABLE = True
    except ImportError:
        _CV2_AVAILABLE = False


logger = logging.getLogger("vjlive3.render.texture_manager")


@dataclass
class TextureStats:
    active_textures: int
    memory_used_bytes: int
    cache_hits: int
    cache_misses: int


class TextureManager:
    """Provides pooled texture resource management for the VJLive3 rendering pipeline."""
    
    # Required by PRIME_DIRECTIVE Rule 2
    METADATA = {
        "author": "Antigravity (Manager)",
        "phase": "P1-R4",
        "description": "Pooled texture instance cache ensuring clean RAII handling and VRAM safety."
    }

    def __init__(self, ctx: moderngl.Context, max_textures: int = 1000) -> None:
        if not ctx:
            raise ValueError("TextureManager requires a valid ModernGL context")
        if max_textures <= 0:
            raise ValueError("max_textures must be greater than 0")
            
        self.ctx = ctx
        self.max_textures = max_textures
        self._pool: Dict[str, moderngl.Texture] = {}
        
        self._stats = TextureStats(
            active_textures=0,
            memory_used_bytes=0,
            cache_hits=0,
            cache_misses=0
        )

    def _track_allocation(self, size_bytes: int) -> None:
        self._stats.active_textures += 1
        self._stats.memory_used_bytes += size_bytes

    def _track_release(self, size_bytes: int) -> None:
        self._stats.active_textures -= 1
        self._stats.memory_used_bytes -= size_bytes

    def create_texture(self, name: str, size: Tuple[int, int], components: int, data: Optional[bytes] = None) -> moderngl.Texture:
        """Allocate a new exact-match GPU Texture by name, replacing any existing entry."""
        if not name:
            raise ValueError("Texture name cannot be empty")
        if size[0] <= 0 or size[1] <= 0:
            raise ValueError("Texture dimensions must be positive integers")
        if components not in (1, 2, 3, 4):
            raise ValueError("Texture components must be between 1 and 4")

        # Evict existing buffer bound to this name
        if name in self._pool:
            self.release_texture(name)
            
        if self._stats.active_textures >= self.max_textures:
            raise MemoryError(f"Texture limit reached: {self.max_textures}")
            
        if data is not None:
            expected_size = size[0] * size[1] * components
            if len(data) != expected_size:
                raise ValueError(f"Data byte length ({len(data)}) does not match expected dimension volume ({expected_size})")

        # Create uninitialized proxy, or populated buffer
        try:
            tex = self.ctx.texture(size, components, data=data)
            tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
            
            self._pool[name] = tex
            self._track_allocation(size[0] * size[1] * components)
            
            return tex
            
        except moderngl.Error as e:
            # Re-wrap internal GL hardware faults as MemoryError to match spec
            raise MemoryError(f"Failed to allocate texture '{name}' on GPU context: {e}")

    def get_texture(self, name: str) -> Optional[moderngl.Texture]:
        """Fetch previously allocated Texture object by name string."""
        if name in self._pool:
            self._stats.cache_hits += 1
            return self._pool[name]
            
        self._stats.cache_misses += 1
        return None

    def release_texture(self, name: str) -> bool:
        """Call moderngl.Texture.release() natively and evict proxy from python dictionary cache."""
        tex = self._pool.pop(name, None)
        if tex:
            try:
                # ModernGL safe teardown
                size_bytes = tex.width * tex.height * tex.components
                tex.release()
                self._track_release(size_bytes)
                return True
            except Exception:
                pass
        return False

    def create_from_buffer(self, name: str, buffer: bytes, size: Tuple[int, int], components: int) -> moderngl.Texture:
        """Alias for create_texture serving explicitly bytes payloads."""
        return self.create_texture(name, size, components, data=buffer)

    def create_from_image(self, name: str, image_path: str) -> Optional[moderngl.Texture]:
        """Disk -> RGB decoding pipeline prioritizing cv2 over PIL."""
        import os
        if not os.path.exists(image_path):
            logger.warning(f"Failed to create texture: Image path not found: {image_path}")
            return None

        size, components, raw_bytes = None, None, None

        if _CV2_AVAILABLE:
            try:
                img = cv2.imread(image_path)
                if img is None:
                     raise ValueError(f"cv2 failed to decode target: {image_path}")
                # Convert BGR -> RGB standard and vertical flip GL coordinate
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img = cv2.flip(img, 0)
                h, w, c = img.shape
                size = (w, h)
                components = c
                raw_bytes = img.tobytes()
            except Exception as e:
                logger.error(f"cv2 import pipe failed on {image_path}: {e}")
                
        if not raw_bytes and _PIL_AVAILABLE:
            try:
                img = Image.open(image_path)
                img = img.convert('RGB')
                img = img.transpose(Image.FLIP_TOP_BOTTOM)
                size = img.size
                components = len(img.getbands())
                raw_bytes = img.tobytes()
            except Exception as e:
                logger.error(f"PIL fallback pipe failed on {image_path}: {e}")

        if size and components and raw_bytes:
            return self.create_texture(name, size, components, data=raw_bytes)
            
        logger.error(f"Module missing valid decoding backend (cv2/PIL) to parse {image_path}")
        return None

    def reserve_texture(self, name: str, size: Tuple[int, int], components: int) -> moderngl.Texture:
        """Guarantees an uninitialized proxy buffer matching specifications is loaded by name."""
        existing = self.get_texture(name)
        if existing:
            # Prevent silent reallocations if the dimensions/components changed
            if existing.size != size or existing.components != components:
                self.release_texture(name)
            else:
                return existing
                
        return self.create_texture(name, size, components, data=None)

    def update_texture(self, texture: moderngl.Texture, data: bytes) -> None:
        """Stream bytes directly to VRAM target. Dimensions and types must match."""
        if not texture:
            return
            
        expected_size = texture.width * texture.height * texture.components
        if len(data) != expected_size:
            raise ValueError(f"Update bytes ({len(data)}) does not match texture dimensions ({expected_size})")
            
        try:
             # Natively binds and runs glTexSubImage2D block matching legacy PBO stream mapping 
             texture.write(data)
        except Exception as e:
             logger.error(f"Texture hardware update failure: {e}")

    def clear_all(self) -> None:
        """Evict and de-allocate all tracked GL proxy objects."""
        # Convert dictionary keys into a list to prevent "dict changed size during iteration" Exceptions
        for name in list(self._pool.keys()):
            self.release_texture(name)

    def get_stats(self) -> TextureStats:
        """Returns the current internal status and memory constraints."""
        return self._stats

    def cleanup(self) -> None:
        """Destructor mapping required by architecture guidelines."""
        self.clear_all()
        
    def __del__(self) -> None:
        # Guarantee memory release even if explicit `cleanup` gets orphaned
        try:
            self.clear_all()
        except:
             pass
