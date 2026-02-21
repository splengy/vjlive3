"""
GPU Capability Detection System for VJLive3.

Provides automatic detection of GPU capabilities and classification into tiers
(NONE, LOW, MEDIUM, HIGH, ULTRA) to support the gpu_tier licensing model
and capability-aware plugin loading.

Source: Based on docs/architecture/gpu_detector_design.md
"""

from __future__ import annotations

import logging
import os
import re
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Set, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# GPU Tier Enumeration
# ---------------------------------------------------------------------------

class GPUTier(Enum):
    """GPU capability tiers for licensing and plugin compatibility."""
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    ULTRA = "ULTRA"


# ---------------------------------------------------------------------------
# Capability Profile
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CapabilityProfile:
    """
    Immutable snapshot of GPU capabilities.

    Attributes:
        opengl_version_major: Major OpenGL version number
        opengl_version_minor: Minor OpenGL version number
        extensions: Set of available OpenGL extension strings
        vendor: GPU vendor name (e.g., "NVIDIA", "AMD", "Intel")
        renderer: Full GPU renderer string from driver
        gpu_model: Simplified model name extracted from renderer
        vram_bytes: Video memory in bytes (0 if undetectable)
        detection_method: Backend used ("moderngl", "pyopengl", "mock")
        is_headless: Whether detection occurred without a display
        context_created: Whether a new OpenGL context was created
    """

    # OpenGL version
    opengl_version_major: int
    opengl_version_minor: int

    # Extensions
    extensions: Set[str]

    # GPU identification
    vendor: str
    renderer: str
    gpu_model: str

    # Memory
    vram_bytes: int

    # Detection metadata
    detection_method: str
    is_headless: bool
    context_created: bool

    # Computed properties
    _tier: Optional[GPUTier] = field(default=None, compare=False, hash=False)

    @property
    def opengl_version(self) -> Tuple[int, int]:
        """OpenGL version as (major, minor) tuple."""
        return (self.opengl_version_major, self.opengl_version_minor)

    @property
    def vram_gb(self) -> float:
        """VRAM in gigabytes (float)."""
        return self.vram_bytes / (1024 ** 3)

    def get_tier(self) -> GPUTier:
        """Get the tier classification for this profile."""
        if self._tier is None:
            self._tier = TierClassifier.classify(self)
        return self._tier

    def has_extension(self, ext: str) -> bool:
        """Check if a specific extension is available."""
        return ext in self.extensions

    def supports_version(self, major: int, minor: int) -> bool:
        """Check if OpenGL version meets or exceeds the specified version."""
        if self.opengl_version_major > major:
            return True
        if self.opengl_version_major == major:
            return self.opengl_version_minor >= minor
        return False


# ---------------------------------------------------------------------------
# Tier Classification
# ---------------------------------------------------------------------------

class TierClassifier:
    """Classifies GPU capabilities into tiers."""

    # Tier thresholds configuration
    TIER_SPECS = {
        GPUTier.NONE: {
            'min_opengl_version': (0, 0),
            'required_extensions': set(),
            'min_vram_gb': 0,
            'description': 'No GPU or headless mode'
        },
        GPUTier.LOW: {
            'min_opengl_version': (3, 3),
            'required_extensions': set(),
            'min_vram_gb': 0,
            'description': 'OpenGL 3.3, basic effects only'
        },
        GPUTier.MEDIUM: {
            'min_opengl_version': (4, 0),
            'required_extensions': {
                'GL_ARB_compute_shader',
                'GL_EXT_texture_filter_anisotropic'
            },
            'min_vram_gb': 2,
            'description': 'OpenGL 4.0+ with compute shaders and anisotropy'
        },
        GPUTier.HIGH: {
            'min_opengl_version': (4, 5),
            'required_extensions': {
                'GL_ARB_compute_shader',
                'GL_ARB_gpu_shader_fp64',
                'GL_EXT_texture_filter_anisotropic',
                'GL_ARB_direct_state_access'
            },
            'min_vram_gb': 4,
            'description': 'OpenGL 4.5+ with most advanced extensions'
        },
        GPUTier.ULTRA: {
            'min_opengl_version': (4, 6),
            'required_extensions': {
                'GL_ARB_compute_shader',
                'GL_ARB_gpu_shader_fp64',
                'GL_ARB_gpu_shader_int64',
                'GL_EXT_texture_filter_anisotropic',
                'GL_ARB_direct_state_access',
                'GL_NV_mesh_shader',  # NVIDIA-specific
                'GL_NV_ray_tracing'   # NVIDIA-specific
            },
            'min_vram_gb': 8,
            'description': 'Latest OpenGL with all advanced extensions'
        }
    }

    @classmethod
    def classify(cls, profile: CapabilityProfile) -> GPUTier:
        """
        Classify a capability profile into the highest tier it qualifies for.

        Args:
            profile: The GPU capability profile to classify

        Returns:
            The highest GPU_TIER the system meets requirements for
        """
        # Check from highest to lowest tier
        for tier in [GPUTier.ULTRA, GPUTier.HIGH, GPUTier.MEDIUM, GPUTier.LOW]:
            if cls._meets_tier(profile, tier):
                return tier

        # If no tier matched, it's NONE
        return GPUTier.NONE

    @classmethod
    def _meets_tier(cls, profile: CapabilityProfile, tier: GPUTier) -> bool:
        """Check if profile meets all requirements for a specific tier."""
        spec = cls.TIER_SPECS[tier]

        # Check OpenGL version
        if not profile.supports_version(*spec['min_opengl_version']):
            return False

        # Check required extensions
        required_exts = spec['required_extensions']
        if required_exts and not all(profile.has_extension(ext) for ext in required_exts):
            return False

        # Check VRAM (if detectable)
        if profile.vram_gb < spec['min_vram_gb']:
            return False

        return True


# ---------------------------------------------------------------------------
# Backend Interface and Implementations
# ---------------------------------------------------------------------------

class Backend(ABC):
    """Abstract base class for GPU detection backends."""

    @abstractmethod
    def detect(self) -> Optional[CapabilityProfile]:
        """
        Perform detection and return a capability profile.

        Returns:
            CapabilityProfile if detection successful, None if this backend
            cannot detect (e.g., no GPU present)
        """
        pass


class ModernGLBackend(Backend):
    """Detection using ModernGL (preferred, requires active context)."""

    def detect(self) -> Optional[CapabilityProfile]:
        try:
            import moderngl

            # Try to get/create a context
            ctx = moderngl.create_context(require=330)
            if ctx is None:
                logger.warning("ModernGL: Could not create context")
                return None

            # Extract version
            version = ctx.version_code
            major = version // 100
            minor = (version % 100) // 10

            # Get extensions
            extensions = set(ctx.extensions)

            # Get vendor/renderer
            vendor = ctx.info.get('GL_VENDOR', 'Unknown')
            renderer = ctx.info.get('GL_RENDERER', 'Unknown')

            # Try to estimate VRAM (ModernGL doesn't expose this directly)
            vram_bytes = self._estimate_vram(vendor, renderer)

            # Clean up temporary context if we created one
            if not self._is_existing_context(ctx):
                ctx.release()

            return CapabilityProfile(
                opengl_version_major=major,
                opengl_version_minor=minor,
                extensions=extensions,
                vendor=vendor,
                renderer=renderer,
                gpu_model=self._parse_model(renderer, vendor),
                vram_bytes=vram_bytes,
                detection_method='moderngl',
                is_headless=False,
                context_created=not self._is_existing_context(ctx)
            )
        except Exception as exc:
            logger.debug(f"ModernGL backend error: {exc}")
            return None

    def _is_existing_context(self, ctx) -> bool:
        """Check if we're using an already-existing context."""
        # For simplicity, we assume any context we get is new unless we're
        # passed one (which we don't currently support)
        return False

    def _estimate_vram(self, vendor: str, renderer: str) -> int:
        """Estimate VRAM based on GPU model (rough heuristic)."""
        # This is a fallback when we can't query actual VRAM
        # Returns bytes
        vendor_lower = vendor.lower()
        renderer_lower = renderer.lower()

        # Known high-end GPUs
        if 'rtx 4090' in renderer_lower or 'rx 7900' in renderer_lower:
            return 24 * 1024**3
        elif 'rtx 4080' in renderer_lower or 'rx 7800' in renderer_lower:
            return 16 * 1024**3
        elif 'rtx 4070' in renderer_lower or 'rx 7700' in renderer_lower:
            return 12 * 1024**3
        elif 'rtx 3090' in renderer_lower or 'rx 6800' in renderer_lower:
            return 24 * 1024**3
        elif 'rtx 3080' in renderer_lower or 'rx 6700' in renderer_lower:
            return 12 * 1024**3

        # Default estimate for modern GPUs
        if any(word in renderer_lower for word in ['geforce', 'radeon', 'arc']):
            return 8 * 1024**3

        return 0

    def _parse_model(self, renderer: str, vendor: str) -> str:
        """Extract a simplified GPU model name from renderer string."""
        renderer_lower = renderer.lower()

        # NVIDIA patterns
        if 'nvidia' in vendor.lower() or 'geforce' in renderer_lower:
            # Extract RTX/GTX pattern
            match = re.search(r'(rtx|gtx) [a-z0-9]+', renderer_lower)
            if match:
                return match.group(0).upper()

        # AMD patterns
        elif 'amd' in vendor.lower() or 'radeon' in renderer_lower:
            match = re.search(r'rx [a-z0-9]+', renderer_lower)
            if match:
                return match.group(0).upper()

        # Intel patterns
        elif 'intel' in vendor.lower():
            if 'arc' in renderer_lower:
                return 'Intel Arc'
            elif 'iris' in renderer_lower:
                return 'Intel Iris'
            elif 'uhd' in renderer_lower:
                return 'Intel UHD Graphics'

        # Fallback: return first part of renderer string
        return renderer.split()[0] if renderer else 'Unknown'


class PyOpenGLBackend(Backend):
    """Detection using PyOpenGL (fallback, can work without context)."""

    def detect(self) -> Optional[CapabilityProfile]:
        try:
            from OpenGL import GL

            # Try to get info without context first
            try:
                vendor_bytes = GL.glGetString(GL.GL_VENDOR)
                renderer_bytes = GL.glGetString(GL.GL_RENDERER)
                version_bytes = GL.glGetString(GL.GL_VERSION)
            except Exception:
                # No context available
                logger.warning("PyOpenGL: No active OpenGL context")
                return None

            # Decode bytes to strings
            vendor = vendor_bytes.decode('utf-8') if vendor_bytes else 'Unknown'
            renderer = renderer_bytes.decode('utf-8') if renderer_bytes else 'Unknown'
            version_str = version_bytes.decode('utf-8') if version_bytes else '0.0'

            # Parse version
            match = re.search(r'(\d+)\.(\d+)', version_str)
            if not match:
                major, minor = 0, 0
            else:
                major, minor = int(match.group(1)), int(match.group(2))

            # Get extensions (requires context)
            try:
                ext_count = GL.glGetIntegerv(GL.GL_NUM_EXTENSIONS)
                extensions = {
                    GL.glGetStringi(GL.GL_EXTENSIONS, i).decode('utf-8')
                    for i in range(ext_count)
                }
            except Exception:
                extensions = set()

            # VRAM not available via PyOpenGL without platform-specific calls
            vram_bytes = 0

            return CapabilityProfile(
                opengl_version_major=major,
                opengl_version_minor=minor,
                extensions=extensions,
                vendor=vendor,
                renderer=renderer,
                gpu_model=self._parse_model(renderer, vendor),
                vram_bytes=vram_bytes,
                detection_method='pyopengl',
                is_headless=False,
                context_created=False
            )
        except ImportError:
            return None
        except Exception as exc:
            logger.debug(f"PyOpenGL backend error: {exc}")
            return None

    def _parse_model(self, renderer: str, vendor: str) -> str:
        """Extract a simplified GPU model name from renderer string."""
        renderer_lower = renderer.lower()

        # NVIDIA patterns
        if 'nvidia' in vendor.lower() or 'geforce' in renderer_lower:
            match = re.search(r'(rtx|gtx) [a-z0-9]+', renderer_lower)
            if match:
                return match.group(0).upper()

        # AMD patterns
        elif 'amd' in vendor.lower() or 'radeon' in renderer_lower:
            match = re.search(r'rx [a-z0-9]+', renderer_lower)
            if match:
                return match.group(0).upper()

        # Intel patterns
        elif 'intel' in vendor.lower():
            if 'arc' in renderer_lower:
                return 'Intel Arc'
            elif 'iris' in renderer_lower:
                return 'Intel Iris'
            elif 'uhd' in renderer_lower:
                return 'Intel UHD Graphics'

        return renderer.split()[0] if renderer else 'Unknown'


class MockBackend(Backend):
    """Fallback detection for headless environments or when all else fails."""

    def detect(self) -> CapabilityProfile:
        """Return a safe default profile."""
        logger.warning("Using mock GPU detection - actual capabilities unknown")

        # Check environment variables for hints
        headless = bool(os.environ.get('DISPLAY') is None or
                       os.environ.get('WAYLAND_DISPLAY') is None)

        # If we're in CI or headless, assume minimal capabilities
        if headless or os.environ.get('CI') == 'true':
            return CapabilityProfile(
                opengl_version_major=3,
                opengl_version_minor=3,
                extensions=set(),
                vendor='Unknown',
                renderer='Software (Headless)',
                gpu_model='Software',
                vram_bytes=0,
                detection_method='mock',
                is_headless=True,
                context_created=False
            )

        # If we have a display but couldn't detect, assume LOW tier
        # This is conservative but safe
        return CapabilityProfile(
            opengl_version_major=3,
            opengl_version_minor=3,
            extensions=set(),
            vendor='Unknown',
            renderer='Unknown (Default)',
            gpu_model='Unknown',
            vram_bytes=0,
            detection_method='mock',
            is_headless=False,
            context_created=False
        )


# ---------------------------------------------------------------------------
# GPU Detector Singleton
# ---------------------------------------------------------------------------

class GPUDetector:
    """
    Singleton GPU capability detector with fallback support.

    Provides automatic detection using multiple backends with graceful fallback.
    Thread-safe and caches results after first detection.
    """

    _instance: Optional['GPUDetector'] = None
    _lock: threading.RLock = threading.RLock()

    @classmethod
    def get_instance(cls) -> GPUDetector:
        """Get or create the singleton instance."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def __init__(self) -> None:
        """Initialize detector (called only by get_instance)."""
        if GPUDetector._instance is not None:
            raise RuntimeError("GPUDetector is a singleton. Use get_instance().")

        self._profile: Optional[CapabilityProfile] = None
        self._detected: bool = False
        self._backend: Optional[Backend] = None
        self._lock = threading.RLock()

    def detect(self, force: bool = False) -> CapabilityProfile:
        """
        Perform GPU capability detection.

        Args:
            force: Re-run detection even if already detected

        Returns:
            CapabilityProfile with detected capabilities

        Note:
            Non-blocking - falls back to mock detection on failure.
            Results are cached for subsequent calls.
        """
        with self._lock:
            if self._detected and not force:
                return self._profile  # type: ignore[return-value]

            profile = self._try_detect()
            self._profile = profile
            self._detected = True
            return profile

    def get_profile(self) -> CapabilityProfile:
        """
        Get the current capability profile.

        Returns:
            CapabilityProfile (triggers detection if not yet done)

        Raises:
            RuntimeError: If detection fails and no fallback available
        """
        if self._profile is None:
            return self.detect()
        return self._profile

    def get_tier(self) -> GPUTier:
        """Get the current GPU tier classification."""
        profile = self.get_profile()
        return profile.get_tier()

    def can_run_tier(self, required_tier: GPUTier) -> bool:
        """
        Check if the current system can run plugins requiring the given tier.

        Args:
            required_tier: The required GPU tier

        Returns:
            True if system meets or exceeds the requirement
        """
        current = self.get_tier()
        return self._tier_meets_requirement(current, required_tier)

    def _try_detect(self) -> CapabilityProfile:
        """Attempt detection using available backends with fallback."""
        # Try ModernGL first (if context exists or can be created)
        try:
            import moderngl
            self._backend = ModernGLBackend()
            profile = self._backend.detect()
            if profile:
                return profile
        except ImportError:
            logger.warning("ModernGL not available, trying PyOpenGL...")
        except Exception as exc:
            logger.warning(f"ModernGL detection failed: {exc}, trying PyOpenGL...")

        # Try PyOpenGL fallback
        try:
            self._backend = PyOpenGLBackend()
            profile = self._backend.detect()
            if profile:
                return profile
        except ImportError:
            logger.warning("PyOpenGL not available, using mock detection...")
        except Exception as exc:
            logger.warning(f"PyOpenGL detection failed: {exc}, using mock detection...")

        # Final fallback: mock detection (headless-safe)
        self._backend = MockBackend()
        profile = self._backend.detect()
        return profile

    @staticmethod
    def _tier_meets_requirement(
        current_tier: GPUTier,
        required_tier: GPUTier
    ) -> bool:
        """Check if current tier meets or exceeds required tier."""
        tier_order = [
            GPUTier.NONE,
            GPUTier.LOW,
            GPUTier.MEDIUM,
            GPUTier.HIGH,
            GPUTier.ULTRA
        ]
        current_idx = tier_order.index(current_tier)
        required_idx = tier_order.index(required_tier)
        return current_idx >= required_idx


# ---------------------------------------------------------------------------
# Module-Level Convenience Functions
# ---------------------------------------------------------------------------

def get_gpu_profile() -> CapabilityProfile:
    """Quick access to GPU profile (singleton)."""
    return GPUDetector.get_instance().get_profile()


def get_current_gpu_tier() -> GPUTier:
    """Quick access to current GPU tier."""
    return GPUDetector.get_instance().get_tier()


def gpu_supports_tier(tier: GPUTier | str) -> bool:
    """
    Check if current GPU meets tier requirement.

    Args:
        tier: Required tier (can be GPUTier enum or string)

    Returns:
        True if current GPU meets or exceeds the requirement
    """
    if isinstance(tier, str):
        try:
            tier = GPUTier(tier)
        except ValueError:
            logger.warning(f"Invalid GPU tier: {tier}, defaulting to NONE")
            tier = GPUTier.NONE
    return GPUDetector.get_instance().can_run_tier(tier)
